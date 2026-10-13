from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.models.audit import HumanApprovalRequest, AuditRecord
from app.models.decision import DecisionOutcome
from app.database.connection import audit_db
from app.core.approval_engine import approval_engine
from app.middleware.execution_gate import execution_gate

router = APIRouter(prefix="/api/approval", tags=["Human Approval"])

@router.post("", response_model=AuditRecord)
async def submit_human_approval(req: HumanApprovalRequest):
    record = audit_db.get_record(req.action_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Action '{req.action_id}' not found.")

    # Validate approval authenticity, reviewer authority, replay prevention, and expiration
    valid, reason = approval_engine.validate_approval_request(record, req)
    if not valid:
        audit_db.save_record(record)
        raise HTTPException(status_code=403, detail=reason)

    record.approved_by = req.reviewer
    record.approval_timestamp = datetime.now(timezone.utc).isoformat()

    if req.approved:
        # Mark as approved and dispatch through Execution Integrity Gate
        record.execution_status = "PENDING_EXECUTION"
        audit_db.save_record(record)
        try:
            gate_res = await execution_gate.execute_action(req.action_id)
            updated_record = audit_db.get_record(req.action_id)
            return updated_record or record
        except HTTPException:
            raise
        except Exception as e:
            record.execution_status = "FAILED"
            record.execution_error = str(e)
            audit_db.save_record(record)
            raise HTTPException(status_code=500, detail=f"Execution dispatch failed: {str(e)}")
    else:
        record.execution_status = "REJECTED"
        record.execution_result = {
            "status": "REJECTED",
            "message": f"Rejected by reviewer {req.reviewer}. Reason: {req.review_notes}"
        }
        audit_db.save_record(record)
        return record
