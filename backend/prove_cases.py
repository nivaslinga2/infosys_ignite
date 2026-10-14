import asyncio
import os
import sys

# Ensure backend root is in sys.path
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.models.action import ActionContract, ProvenanceInfo, ProvenanceSource
from app.models.decision import DecisionOutcome
from app.models.audit import AuditRecord, HumanApprovalRequest
from app.core.decision_engine import decision_engine
from app.database.connection import audit_db
from app.middleware.execution_gate import execution_gate
from app.core.approval_engine import approval_engine
from app.api.approval import submit_human_approval
from fastapi import HTTPException

async def run_proof():
    print("=" * 75)
    print("           AGENTSHIELD SECURITY GATEWAY: 3-CASE PROOF")
    print("=" * 75)

    # --------------------------------------------------------------------------
    # TEST A: Safe action
    # Submit an authorized support-ticket request.
    # Expected: ALLOW, followed by successful mock-tool execution.
    # --------------------------------------------------------------------------
    print("\n[TEST A] Safe Action: Authorized Support Ticket")
    print("---------------------------------------------------------------------------")
    contract_a = ActionContract(
        action_id="CASE-A-SUPPORT",
        agent="SupportAgent",
        user="employee_42",
        role="support_operator",
        intent="create_ticket",
        tool="create_support_ticket",
        target={
            "title": "VPN connection drops after 10 mins",
            "description": "User cannot maintain tunnel to corporate subnet",
            "priority": "medium"
        },
        environment="production",
        provenance=ProvenanceInfo(source=ProvenanceSource.USER, trusted=True),
        user_prompt="Create a support ticket for VPN connection drops after 10 mins"
    )

    # Step 1: Gateway multi-vector validation
    report_a = await decision_engine.evaluate_action(contract_a)
    print(f"  > Decision Engine Verdict : {report_a.decision.value}")
    print(f"  > Composite Risk Score    : {report_a.composite_risk_score}/100")
    print(f"  > OPA Authorization Check : {report_a.authorization.status} ({report_a.authorization.reason})")
    print(f"  > Reversibility Tier      : {report_a.reversibility_tier.value}")
    assert report_a.decision == DecisionOutcome.ALLOW, f"Expected ALLOW, got {report_a.decision}"

    # Step 2: Record in audit database
    record_a = AuditRecord(
        action_id="CASE-A-SUPPORT",
        user=contract_a.user,
        agent=contract_a.agent,
        role=contract_a.role,
        intent=contract_a.intent,
        tool=contract_a.tool,
        target=contract_a.target,
        environment=contract_a.environment,
        action_contract=contract_a,
        validation_report=report_a,
        decision=report_a.decision,
        execution_status="PENDING_EXECUTION"
    )
    approval_engine.initialize_approval_context(record_a)
    audit_db.save_record(record_a)

    # Step 3: Mock-tool execution via ExecutionGate
    exec_result_a = await execution_gate.execute_action("CASE-A-SUPPORT")
    print(f"  > Execution Gate Status   : {exec_result_a.get('status')}")
    print(f"  > Mock Tool Output Payload: {exec_result_a.get('result')}")
    assert exec_result_a["status"] == "EXECUTED"
    assert exec_result_a["result"]["status"] == "SUCCESS"
    assert exec_result_a["result"]["tool"] == "create_support_ticket"
    assert exec_result_a["result"]["ticket_id"].startswith("TICK-")
    print("  RESULT: [PASS] Allowed by policy and mock tool executed successfully.\n")

    # --------------------------------------------------------------------------
    # TEST B: Sensitive action
    # Submit a refund exceeding the configured autonomous limit.
    # Expected: HUMAN_REVIEW; no execution before valid approval.
    # --------------------------------------------------------------------------
    print("[TEST B] Sensitive Action: Refund Exceeding Autonomous Limit (> 5,000 INR)")
    print("---------------------------------------------------------------------------")
    contract_b = ActionContract(
        action_id="CASE-B-REFUND",
        agent="FinanceAgent",
        user="employee_42",
        role="finance_operator",
        intent="refund_customer",
        tool="refund_payment",
        target={"customer": "C1024", "amount": 8500.0, "reason": "Hardware return refund"},
        environment="production",
        provenance=ProvenanceInfo(source=ProvenanceSource.USER, trusted=True),
        user_prompt="Refund ₹8,500 to customer C1024 for hardware return"
    )

    # Step 1: Gateway validation
    report_b = await decision_engine.evaluate_action(contract_b)
    print(f"  > Decision Engine Verdict : {report_b.decision.value}")
    print(f"  > Composite Risk Score    : {report_b.composite_risk_score}/100")
    print(f"  > OPA Authorization Check : {report_b.authorization.status} ({report_b.authorization.reason})")
    assert report_b.decision == DecisionOutcome.REVIEW, f"Expected REVIEW, got {report_b.decision}"

    # Step 2: Initialize approval context
    record_b = AuditRecord(
        action_id="CASE-B-REFUND",
        user=contract_b.user,
        agent=contract_b.agent,
        role=contract_b.role,
        intent=contract_b.intent,
        tool=contract_b.tool,
        target=contract_b.target,
        environment=contract_b.environment,
        action_contract=contract_b,
        validation_report=report_b,
        decision=report_b.decision,
        execution_status="PENDING_REVIEW"
    )
    approval_engine.initialize_approval_context(record_b)
    audit_db.save_record(record_b)

    # Step 3: Attempt execution BEFORE supervisor approval -> MUST FAIL (403)
    execution_blocked_before_approval = False
    try:
        await execution_gate.execute_action("CASE-B-REFUND")
    except HTTPException as exc:
        execution_blocked_before_approval = True
        print(f"  > Pre-Approval Execution  : PREVENTED (HTTP {exc.status_code}: {exc.detail})")
        assert exc.status_code == 403
    assert execution_blocked_before_approval, "Tool execution must be blocked prior to supervisor approval"

    # Step 4: Submit valid human approval from authorized supervisor 'manager_21'
    approval_req = HumanApprovalRequest(
        action_id="CASE-B-REFUND",
        approved=True,
        reviewer="manager_21",
        review_notes="Approved hardware return refund exception."
    )
    approved_record = await submit_human_approval(approval_req)
    print(f"  > Supervisor Review Status: APPROVED by {approved_record.approved_by}")
    print(f"  > Post-Approval Status    : {approved_record.execution_status}")
    print(f"  > Executed Tool Output    : {approved_record.execution_result}")
    assert approved_record.execution_status == "EXECUTED"
    assert approved_record.execution_result["status"] == "SUCCESS"
    assert approved_record.execution_result["amount_refunded"] == 8500.0
    print("  RESULT: [PASS] Flagged for HUMAN_REVIEW, zero tool execution before approval, cleanly executed once approved.\n")

    # --------------------------------------------------------------------------
    # TEST C: Prohibited action
    # Attempt a prohibited database deletion.
    # Expected: BLOCK, with no side effect in the mock tool.
    # --------------------------------------------------------------------------
    print("[TEST C] Prohibited Action: Production Database Deletion")
    print("---------------------------------------------------------------------------")
    contract_c = ActionContract(
        action_id="CASE-C-DELETE",
        agent="DatabaseOpsAgent",
        user="employee_42",
        role="db_administrator",
        intent="clean_database",
        tool="execute_sql",
        target={"query": "DELETE FROM customers WHERE active = 0;", "database": "production_db"},
        environment="production",
        provenance=ProvenanceInfo(source=ProvenanceSource.USER, trusted=True),
        user_prompt="Delete inactive customers from production database"
    )

    # Step 1: Gateway validation
    report_c = await decision_engine.evaluate_action(contract_c)
    print(f"  > Decision Engine Verdict : {report_c.decision.value}")
    print(f"  > Composite Risk Score    : {report_c.composite_risk_score}/100")
    print(f"  > Reversibility Tier      : {report_c.reversibility_tier.value} (Irreversible destructive action)")
    print(f"  > OPA Authorization Check : {report_c.authorization.status} ({report_c.authorization.reason})")
    assert report_c.decision == DecisionOutcome.BLOCK, f"Expected BLOCK, got {report_c.decision}"

    record_c = AuditRecord(
        action_id="CASE-C-DELETE",
        user=contract_c.user,
        agent=contract_c.agent,
        role=contract_c.role,
        intent=contract_c.intent,
        tool=contract_c.tool,
        target=contract_c.target,
        environment=contract_c.environment,
        action_contract=contract_c,
        validation_report=report_c,
        decision=report_c.decision,
        execution_status="BLOCKED"
    )
    audit_db.save_record(record_c)

    # Step 2: Attempt execution -> Tool layer MUST NEVER be reached
    tool_never_reached = False
    try:
        await execution_gate.execute_action("CASE-C-DELETE")
    except HTTPException as exc:
        tool_never_reached = True
        print(f"  > Tool Execution Attempt  : HARD BLOCKED (HTTP {exc.status_code}: {exc.detail})")
        assert exc.status_code == 403

    assert tool_never_reached, "Blocked action must never reach tool"
    print("  RESULT: [PASS] Hard BLOCK enforced; tool layer completely unreachable with zero side effects.\n")

    print("=" * 75)
    print("           VERIFICATION SUMMARY: ALL 3 TESTS PASSED (100%)")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_proof())
