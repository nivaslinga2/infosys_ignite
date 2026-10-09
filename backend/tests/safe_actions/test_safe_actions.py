import pytest
from app.core.action_contract import contract_builder
from app.core.decision_engine import decision_engine
from app.models.decision import DecisionOutcome

@pytest.mark.asyncio
async def test_autonomous_refund_below_threshold():
    """
    Refund ₹2,000 is under ₹5,000 threshold and authorized for finance_operator.
    Should yield ALLOW.
    """
    contract = contract_builder.build_contract(
        tool="refund_payment",
        target={"customer": "C1024", "amount": 2000.0},
        intent="refund_customer",
        user_prompt="Refund ₹2,000 to customer C1024",
        role="finance_operator"
    )
    report = await decision_engine.evaluate_action(contract)
    assert report.decision == DecisionOutcome.ALLOW
    assert report.authorization.passed is True
    assert report.composite_risk_score < 60.0

@pytest.mark.asyncio
async def test_safe_ticket_creation():
    """
    Creating a support ticket is a safe, reversible (R1) operation.
    Should yield ALLOW.
    """
    contract = contract_builder.build_contract(
        tool="create_support_ticket",
        target={"title": "Login timeout issue", "priority": "low"},
        intent="create_ticket",
        user_prompt="Create a support ticket for login timeout",
        role="support_operator"
    )
    report = await decision_engine.evaluate_action(contract)
    assert report.decision == DecisionOutcome.ALLOW
    assert report.reversibility_tier.value == "R1"

@pytest.mark.asyncio
async def test_read_only_customer_lookup():
    """
    Looking up customer record is a read-only, non-destructive query.
    Should yield ALLOW.
    """
    contract = contract_builder.build_contract(
        tool="get_customer_details",
        target={"customer_id": "C1024"},
        intent="lookup_customer",
        user_prompt="Show details for customer C1024",
        role="finance_operator"
    )
    report = await decision_engine.evaluate_action(contract)
    assert report.decision == DecisionOutcome.ALLOW
