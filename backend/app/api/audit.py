from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.audit import AuditRecord
from app.models.decision import DecisionOutcome
from app.database.connection import audit_db

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditRecord])
async def get_audit_trail():
    return audit_db.list_records()

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    records = audit_db.list_records()
    total = len(records)
    allowed = sum(1 for r in records if r.decision == DecisionOutcome.ALLOW)
    reviewed = sum(1 for r in records if r.decision == DecisionOutcome.REVIEW)
    blocked = sum(1 for r in records if r.decision == DecisionOutcome.BLOCK)
    executed = sum(1 for r in records if r.execution_status == "EXECUTED")
    avg_risk = sum(r.validation_report.composite_risk_score for r in records) / total if total > 0 else 0.0

    return {
        "total_actions": total,
        "allowed_count": allowed,
        "reviewed_count": reviewed,
        "blocked_count": blocked,
        "executed_count": executed,
        "average_risk_score": round(avg_risk, 1),
        "prevention_rate_percent": round((blocked / total * 100), 1) if total > 0 else 100.0
    }

@router.get("/{action_id}", response_model=AuditRecord)
async def get_audit_record(action_id: str):
    record = audit_db.get_record(action_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Audit record '{action_id}' not found.")
    return record

@router.post("/clear")
async def clear_audit_trail():
    audit_db.clear()
    return {"message": "Audit store cleared successfully."}
