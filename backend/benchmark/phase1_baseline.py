import asyncio
import os
import sys
import time
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

async def run_baseline_iteration(iteration_num: int) -> Dict[str, Any]:
    iter_start = time.time()
    
    # ---------------------------------------------------------
    # Case A: Safe Action
    # ---------------------------------------------------------
    t_start = time.time()
    act_a_id = f"BASE-A-{iteration_num}-{int(t_start * 1000) % 10000}"
    contract_a = ActionContract(
        action_id=act_a_id,
        agent="SupportAgent",
        user="employee_42",
        role="support_operator",
        intent="create_ticket",
        tool="create_support_ticket",
        target={"title": f"VPN drop issue {iteration_num}", "description": "Tunnel timeout", "priority": "low"},
        environment="production",
        provenance=ProvenanceInfo(source=ProvenanceSource.USER, trusted=True),
        user_prompt=f"Create a support ticket for VPN issue {iteration_num}"
    )
    report_a = await decision_engine.evaluate_action(contract_a)
    assert report_a.decision == DecisionOutcome.ALLOW
    
    rec_a = AuditRecord(
        action_id=act_a_id,
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
    approval_engine.initialize_approval_context(rec_a)
    audit_db.save_record(rec_a)
    res_a = await execution_gate.execute_action(act_a_id)
    assert res_a["status"] == "EXECUTED"
    assert res_a["result"]["status"] == "SUCCESS"
    lat_a = (time.time() - t_start) * 1000

    # ---------------------------------------------------------
    # Case B: Sensitive Action (> autonomous limit)
    # ---------------------------------------------------------
    t_start = time.time()
    act_b_id = f"BASE-B-{iteration_num}-{int(t_start * 1000) % 10000}"
    contract_b = ActionContract(
        action_id=act_b_id,
        agent="FinanceAgent",
        user="employee_42",
        role="finance_operator",
        intent="refund_customer",
        tool="refund_payment",
        target={"customer": "C1024", "amount": 8500.0, "reason": "Hardware return"},
        environment="production",
        provenance=ProvenanceInfo(source=ProvenanceSource.USER, trusted=True),
        user_prompt=f"Refund 8,500 INR to customer C1024 #{iteration_num}"
    )
    report_b = await decision_engine.evaluate_action(contract_b)
    assert report_b.decision == DecisionOutcome.REVIEW
    
    rec_b = AuditRecord(
        action_id=act_b_id,
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
    approval_engine.initialize_approval_context(rec_b)
    audit_db.save_record(rec_b)
    
    # Pre-approval check: MUST be blocked
    pre_blocked = False
    try:
        await execution_gate.execute_action(act_b_id)
    except HTTPException as e:
        if e.status_code == 403:
            pre_blocked = True
    assert pre_blocked, "Pre-approval execution was not blocked!"
    
    # Submit valid supervisor approval
    approval_req = HumanApprovalRequest(
        action_id=act_b_id,
        approved=True,
        reviewer="manager_21",
        review_notes=f"Approved iteration {iteration_num}"
    )
    approved_rec = await submit_human_approval(approval_req)
    assert approved_rec.execution_status == "EXECUTED"
    assert approved_rec.execution_result["status"] == "SUCCESS"
    lat_b = (time.time() - t_start) * 1000

    # ---------------------------------------------------------
    # Case C: Prohibited Action (Database deletion)
    # ---------------------------------------------------------
    t_start = time.time()
    act_c_id = f"BASE-C-{iteration_num}-{int(t_start * 1000) % 10000}"
    contract_c = ActionContract(
        action_id=act_c_id,
        agent="DatabaseOpsAgent",
        user="employee_42",
        role="db_administrator",
        intent="clean_database",
        tool="execute_sql",
        target={"query": "DELETE FROM customers WHERE active = 0;", "database": "production_db"},
        environment="production",
        provenance=ProvenanceInfo(source=ProvenanceSource.USER, trusted=True),
        user_prompt=f"Delete inactive customers #{iteration_num}"
    )
    report_c = await decision_engine.evaluate_action(contract_c)
    assert report_c.decision == DecisionOutcome.BLOCK
    
    rec_c = AuditRecord(
        action_id=act_c_id,
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
    audit_db.save_record(rec_c)
    
    tool_blocked = False
    try:
        await execution_gate.execute_action(act_c_id)
    except HTTPException as e:
        if e.status_code == 403:
            tool_blocked = True
    assert tool_blocked, "Blocked action reached tool!"
    lat_c = (time.time() - t_start) * 1000

    total_lat = (time.time() - iter_start) * 1000
    return {
        "iteration": iteration_num,
        "case_a_lat_ms": round(lat_a, 2),
        "case_b_lat_ms": round(lat_b, 2),
        "case_c_lat_ms": round(lat_c, 2),
        "total_lat_ms": round(total_lat, 2),
        "case_a_passed": True,
        "case_b_pre_blocked": True,
        "case_b_post_executed": True,
        "case_c_tool_blocked": True
    }

async def main():
    print("=" * 75)
    print("PHASE 1 BASELINE: Running 10 repeated iterations of baseline cases")
    print("=" * 75)
    results = []
    for i in range(1, 11):
        r = await run_baseline_iteration(i)
        results.append(r)
        print(f"Iteration {i:2d}/10: Case A={r['case_a_lat_ms']}ms | Case B={r['case_b_lat_ms']}ms | Case C={r['case_c_lat_ms']}ms -> ALL CHECKS VERIFIED")

    avg_a = sum(r["case_a_lat_ms"] for r in results) / len(results)
    avg_b = sum(r["case_b_lat_ms"] for r in results) / len(results)
    avg_c = sum(r["case_c_lat_ms"] for r in results) / len(results)
    print("-" * 75)
    print(f"Phase 1 Summary (10/10 Runs, 100% Deterministic Reproducibility):")
    print(f"  - Case A (Safe Action) Average Latency    : {avg_a:.2f} ms (10/10 Executed)")
    print(f"  - Case B (Sensitive Action) Pre-Block Rate: 100% (10/10 Blocked pre-approval, 10/10 Approved)")
    print(f"  - Case C (Prohibited Action) Block Rate   : 100% (10/10 Hard Blocked, 0% Tool Leaks)")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(main())
