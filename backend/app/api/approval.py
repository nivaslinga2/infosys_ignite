from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.models.audit import HumanApprovalRequest, AuditRecord
from app.models.decision import DecisionOutcome
from app.database.connection import audit_db
from app.api.execution import dispatch_tool_execution

router = APIRouter(prefix="/api/approval", tags=["Human Approval"])

@router.post("", response_model=AuditRecord)
async def submit_human_approval(req: HumanApprovalRequest):
    record = audit_db.get_record(req.action_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Action '{req.action_id}' not found.")

    if record.decision == DecisionOutcome.BLOCK:
        raise HTTPException(status_code=400, detail="Cannot approve an action that was BLOCKED by security policy.")

    record.approved_by = req.reviewer
    record.approval_timestamp = datetime.now(timezone.utc).isoformat()

    if req.approved:
        exec_res = await dispatch_tool_execution(record.action_contract)
        record.execution_status = "EXECUTED" if exec_res.get("status") == "SUCCESS" else "FAILED"
        record.execution_result = exec_res
    else:
        record.execution_status = "REJECTED"
        record.execution_result = {"status": "REJECTED", "message": f"Rejected by reviewer {req.reviewer}. Reason: {req.review_notes}"}

    audit_db.save_record(record)
    return record
