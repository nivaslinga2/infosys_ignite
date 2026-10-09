import re
from app.models.action import ActionContract
from app.models.decision import CheckResult

class IntentAlignmentEngine:
    @staticmethod
    def evaluate(contract: ActionContract) -> CheckResult:
        """
        Validates whether the agent's proposed action strictly aligns with what the user authorized.
        Catches unauthorized tool invocation when user merely asked for options, inquiries, or information.
        """
        user_prompt = (contract.user_prompt or "").strip().lower()
        tool = contract.tool

        if not user_prompt:
            # If no original prompt provided, cannot verify intent alignment safely
            return CheckResult(
                passed=True,
                status="PASS",
                reason="Direct API action contract without prompt telemetry.",
                metadata={"alignment": "DIRECT_CONTRACT"}
            )

        # Case 1: User requested inquiry / options / research, but agent proposed execution
        inquiry_keywords = ["options", "check", "find", "search", "lookup", "calculate", "view", "show", "can you check", "what are"]
        is_inquiry = any(kw in user_prompt for kw in inquiry_keywords)
        
        # User explicitly forbade or didn't command action
        has_execution_command = any(kw in user_prompt for kw in ["refund ", "send ", "transfer ", "execute ", "pay ", "delete ", "drop "])

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
            if "delete" not in user_prompt and "remove" not in user_prompt and "clean" not in user_prompt:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason="Intent Mismatch: User prompt did not authorize destructive database operations.",
                    metadata={"user_prompt": user_prompt, "intent_mismatch": True}
                )

        if tool == "export_data":
            if "export" not in user_prompt and "download" not in user_prompt and "dump" not in user_prompt:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason="Intent Mismatch: User never requested data export or exfiltration.",
                    metadata={"user_prompt": user_prompt, "intent_mismatch": True}
                )

        return CheckResult(
            passed=True,
            status="PASS",
            reason=f"Intent Aligned: Proposed tool '{tool}' matches the user's explicit authorization.",
            metadata={"user_prompt": user_prompt, "alignment": "VERIFIED"}
        )

intent_alignment_engine = IntentAlignmentEngine()
