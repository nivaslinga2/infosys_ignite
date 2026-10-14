import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.decision_engine import decision_engine
from benchmark.run_evaluation import convert_to_contract, DATASET_PATH

async def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        ds = json.load(f)

    for case_id in ["BENCH-084", "BENCH-085", "BENCH-086", "BENCH-088"]:
        case = next(c for c in ds if c["id"] == case_id)
        contract = convert_to_contract(case)
        rep = await decision_engine.evaluate_action(contract)
        print(f"\n--- {case_id}: {case['user_prompt']} ---")
        print(f"Tool: {case['tool']}, Role: {case['role']}, Target: {case['target']}")
        print(f"Decision: {rep.decision.value}")
        print(f"Explanation: {rep.explanation}")
        checks = {}
        for attr in ["ai_semantic", "authorization", "risk_assessment", "reversibility", "intent_alignment", "provenance", "content_safety", "topic_control", "pii_assessment", "jailbreak_defense"]:
            val = getattr(rep, attr, None)
            if val:
                checks[attr] = f"{val.status} - {val.reason[:40]}"
        for k, v in checks.items():
            print(f"  {k:20s}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
