from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.action import ActionContract
from app.models.decision import ValidationReport, DecisionOutcome
from app.models.audit import AuditRecord
from app.core.action_contract import contract_builder
from app.core.decision_engine import decision_engine
from app.database.connection import audit_db

router = APIRouter(prefix="/api/validate", tags=["Validation"])

@router.post("", response_model=ValidationReport)
async def validate_action(contract: ActionContract):
    try:
        report = await decision_engine.evaluate_action(contract)

        audit_record = AuditRecord(
            action_id=contract.action_id,
            user=contract.user,
            agent=contract.agent,
            role=contract.role,
            intent=contract.intent,
            tool=contract.tool,
            target=contract.target,
            environment=contract.environment,
            action_contract=contract,
            validation_report=report,
            decision=report.decision,
            execution_status="BLOCKED" if report.decision == DecisionOutcome.BLOCK else "PENDING"
        )
        audit_db.save_record(audit_record)

        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/normalize-and-validate", response_model=ValidationReport)
async def normalize_and_validate(payload: Dict[str, Any]):
    contract = contract_builder.build_contract(
        tool=payload.get("tool", "unknown"),
        target=payload.get("target", {}),
        intent=payload.get("intent", "general_action"),
        agent=payload.get("agent", "FinanceAgent"),
        user=payload.get("user", "employee_42"),
        role=payload.get("role", "finance_operator"),
        environment=payload.get("environment", "production"),
        provenance_source=payload.get("provenance_source", "user"),
        trusted=payload.get("trusted", True),
        provenance_url=payload.get("provenance_url"),
        user_prompt=payload.get("user_prompt"),
        action_id=payload.get("action_id")
    )
    return await validate_action(contract)
