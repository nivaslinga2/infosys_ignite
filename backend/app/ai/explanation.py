from typing import Dict, Any
from app.models.decision import DecisionOutcome, ReversibilityTier

class ExplanationEngine:
    @staticmethod
    def generate_explanation(
        outcome: DecisionOutcome,
        tool: str,
        risk_score: float,
        reversibility: ReversibilityTier,
        auth_reason: str,
        semantic_reason: str,
        intent_reason: str,
        provenance_reason: str
    ) -> str:
        """
        Synthesizes a transparent, explainable natural-language rationale for the AgentShield verdict.
        """
        if outcome == DecisionOutcome.BLOCK:
            return (
                f"🛑 ACTION BLOCKED: Proposed invocation of '{tool}' poses unacceptable security or operational risk "
                f"(Risk Score: {risk_score:.0f}/100, Reversibility: {reversibility.value}).\n"
                f"• Policy Gate: {auth_reason}\n"
                f"• Intent Check: {intent_reason}\n"
                f"• Provenance Check: {provenance_reason}\n"
                f"Tool invocation was halted at the AgentShield Policy Enforcement Point. No backend state was altered."
            )

        elif outcome == DecisionOutcome.REVIEW:
            return (
                f"⚠️ HUMAN APPROVAL REQUIRED: Action '{tool}' exceeds autonomous execution thresholds "
                f"(Risk Score: {risk_score:.0f}/100, Reversibility: {reversibility.value}).\n"
                f"• Primary Trigger: {auth_reason}\n"
                f"• Semantic Context: {semantic_reason}\n"
                f"Execution is paused. Awaiting explicit authorization from a designated human supervisor."
            )

        else:
            return (
                f"✅ ACTION ALLOWED: Tool '{tool}' passed all security boundaries "
                f"(Risk Score: {risk_score:.0f}/100, Reversibility: {reversibility.value}).\n"
                f"• Authorization: {auth_reason}\n"
                f"• Intent Alignment: Verified.\n"
                f"• Provenance: Authenticated.\n"
                f"Safe for autonomous execution."
            )

explanation_engine = ExplanationEngine()
