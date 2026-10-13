import pytest
from app.core.action_contract import contract_builder
from app.core.decision_engine import decision_engine
from app.models.decision import DecisionOutcome
from app.models.audit import HumanApprovalRequest, AuditRecord
from app.database.connection import audit_db
from app.api.approval import submit_human_approval

@pytest.mark.asyncio
async def test_threshold_triggers_human_review():
    contract = contract_builder.build_contract(
        tool="refund_payment",
        target={"customer": "C1024", "amount": 7500.0},
        intent="refund_customer",
        user_prompt="Refund ₹7,500 to customer C1024",
        role="finance_operator"
    )
    report = await decision_engine.evaluate_action(contract)
    assert report.decision == DecisionOutcome.REVIEW
    assert report.authorization.status == "WARN"
    assert report.composite_risk_score >= 60.0

@pytest.mark.asyncio
async def test_human_approval_executes_tool():
    contract = contract_builder.build_contract(
        tool="refund_payment",
        target={"customer": "C1024", "amount": 7500.0},
        intent="refund_customer",
        user_prompt="Refund ₹7,500 to customer C1024",
        role="finance_operator"
    )
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
        execution_status="PENDING"
    )
    audit_db.save_record(audit_record)

    approval_req = HumanApprovalRequest(
        action_id=contract.action_id,
        approved=True,
        reviewer="manager_21",
        review_notes="Approved verified VIP refund."
    )
    updated = await submit_human_approval(approval_req)

    assert updated.approved_by == "manager_21"
    assert updated.execution_status == "EXECUTED"
    assert updated.execution_result is not None
    assert updated.execution_result.get("status") == "SUCCESS"
