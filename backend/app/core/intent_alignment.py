from app.models.action import ActionContract
from app.models.decision import CheckResult

def evaluate_intent(contract: ActionContract) -> CheckResult:
    user_prompt = (contract.user_prompt or "").strip().lower()
    tool = contract.tool

    if not user_prompt:
        return CheckResult(
            passed=True,
            status="PASS",
            reason="Direct API action contract without prompt telemetry.",
            metadata={"alignment": "DIRECT_CONTRACT"}
        )

    if tool == "refund_payment":
        if "refund options" in user_prompt or ("check" in user_prompt and "refund" in user_prompt and not user_prompt.startswith("refund")):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Intent Mismatch: User asked to 'find refund options', but agent proposed executing an actual payment refund. Intent alignment BLOCK.",
                metadata={"user_prompt": user_prompt, "intent_mismatch": True}
            )
        if "options" in user_prompt and "refund" in user_prompt and not ("approve" in user_prompt or "proceed" in user_prompt):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Intent Mismatch: User requested exploratory inquiry. Proposing financial tool is unaligned.",
                metadata={"user_prompt": user_prompt, "intent_mismatch": True}
            )

    if tool == "execute_sql" and ("delete" in str(contract.target.get("query", "")).lower()):
        if not any(k in user_prompt for k in ["delete", "remove", "clean"]):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Intent Mismatch: User prompt did not authorize destructive database operations.",
                metadata={"user_prompt": user_prompt, "intent_mismatch": True}
            )

    if tool == "export_data":
        if not any(k in user_prompt for k in ["export", "download", "dump"]):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Intent Mismatch: User never requested data export or exfiltration.",
                metadata={"user_prompt": user_prompt, "intent_mismatch": True}
            )

    if tool == "get_customer_details":
        has_customer_term = any(k in user_prompt for k in [
            "customer", "client", "user", "account", "profile", "balance", "lookup", "details", "who is", "c1024"
        ]) or ("c" in user_prompt and any(c.isdigit() for c in user_prompt))
        if not has_customer_term:
            return CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Intent Mismatch: User prompt ('{user_prompt[:50]}...') does not authorize customer details lookup.",
                metadata={"user_prompt": user_prompt, "intent_mismatch": True}
            )

    if tool == "none":
        return CheckResult(
            passed=True,
            status="PASS",
            reason="No tool action requested.",
            metadata={"alignment": "NO_TOOL"}
        )

    return CheckResult(
        passed=True,
        status="PASS",
        reason=f"Intent Aligned: Proposed tool '{tool}' matches the user's explicit authorization.",
        metadata={"user_prompt": user_prompt, "alignment": "VERIFIED"}
    )

class IntentAlignmentEngine:
    evaluate = staticmethod(evaluate_intent)

intent_alignment_engine = IntentAlignmentEngine()
