from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.models.action import ActionContract
from app.models.decision import DecisionOutcome
from app.models.audit import AuditRecord
from app.database.connection import audit_db
from app.core.approval_engine import approval_engine, compute_canonical_hash
from app.core.authorization_engine import authorization_engine
from app.schemas.tool_schemas import schema_validator
from app.api.execution import dispatch_tool_execution

class ExecutionIntegrityGate:
    """
    Mandatory Execution Integrity Gate (Policy Enforcement Point - PEP).
    Placed directly in the execution path before any sandboxed tool dispatch.
    
    Guarantees:
    1. Zero Direct Tool Access: All executions must be mediated by this gate.
    2. Real-Time Revalidation: Re-checks schema, authorization, and approval immediately before dispatch.
    3. Tamper Prevention: Halts execution if executable arguments deviate from approved hash.
    4. Replay Prevention: Halts execution if action was already dispatched.
    5. Fail-Closed Execution: Any error or missing approval causes an immediate halt.
    """

    async def execute_action(
        self,
        action_id: str,
        execution_override_target: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        record: Optional[AuditRecord] = audit_db.get_record(action_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found in registry.")

        contract = record.action_contract

        # 1. Integrity check (tampering, replay, unapproved review, hard blocks)
        valid, reason = approval_engine.verify_execution_integrity(
            record=record,
            proposed_target=execution_override_target
        )
        if not valid:
            audit_db.save_record(record)
            raise HTTPException(status_code=403, detail=reason)

        # 2. Re-validate parameter schema
        schema_res = schema_validator.validate(contract)
        if not schema_res.passed:
            record.execution_status = "BLOCKED"
            audit_db.save_record(record)
            raise HTTPException(status_code=400, detail=f"Schema re-validation failed: {schema_res.reason}")

        # 3. Re-validate authorization policy
        auth_res = authorization_engine.evaluate(contract)
        if not auth_res.passed:
            record.execution_status = "BLOCKED"
            audit_db.save_record(record)
            raise HTTPException(status_code=403, detail=f"Authorization re-validation failed: {auth_res.reason}")

        # 4. Dispatch through protected tool sandbox
        try:
            # Update target if valid override was provided
            if execution_override_target is not None:
                contract.target = execution_override_target

            record.execution_status = "EXECUTING"
            audit_db.save_record(record)

            tool_result = await dispatch_tool_execution(contract)

            record.execution_status = "EXECUTED"
            record.execution_result = tool_result
            audit_db.save_record(record)

            return {
                "action_id": action_id,
                "status": "EXECUTED",
                "result": tool_result
            }
        except Exception as e:
            record.execution_status = "FAILED"
            record.execution_error = str(e)
            audit_db.save_record(record)
            raise HTTPException(status_code=500, detail=f"Tool dispatch failed: {str(e)}")

execution_gate = ExecutionIntegrityGate()
