from typing import Dict, Any, Optional
from app.models.decision import DecisionOutcome, ReversibilityTier

def generate_explanation(
    outcome: DecisionOutcome,
    tool: str,
    risk_score: float,
    reversibility: ReversibilityTier,
    auth_reason: str,
    semantic_reason: str,
    intent_reason: str,
    provenance_reason: str,
    content_safety_reason: Optional[str] = None,
    topic_reason: Optional[str] = None,
    pii_reason: Optional[str] = None,
    jailbreak_reason: Optional[str] = None,
    schema_reason: Optional[str] = None
) -> str:
    if outcome == DecisionOutcome.BLOCK:
        lines = [
            f"ACTION BLOCKED: Execution of '{tool}' exceeds security risk tolerance (Risk: {risk_score:.0f}/100, Reversibility: {reversibility.value}).",
            f"- Policy: {auth_reason}",
            f"- Intent: {intent_reason}",
            f"- Provenance: {provenance_reason}"
        ]
        if semantic_reason and any(k in semantic_reason.lower() for k in ["fail", "fail-closed", "offline", "error", "block"]):
            lines.append(f"- AI Semantic Validator: {semantic_reason}")
        if schema_reason and any(k in schema_reason.lower() for k in ["fail", "schema", "invalid", "malformed"]):
            lines.append(f"- Schema Validation: {schema_reason}")
        if jailbreak_reason and any(k in jailbreak_reason.lower() for k in ["fail", "block", "attack", "injection", "adversarial"]):
            lines.append(f"- Jailbreak Defense: {jailbreak_reason}")
        if content_safety_reason and any(k in content_safety_reason.lower() for k in ["fail", "violation", "unsafe", "block", "prohibited"]):
            lines.append(f"- Content Safety: {content_safety_reason}")
        if topic_reason and any(k in topic_reason.lower() for k in ["fail", "violation", "prohibited", "rail", "block"]):
            lines.append(f"- Topic Control: {topic_reason}")
        if pii_reason and any(k in pii_reason.lower() for k in ["fail", "leakage", "block", "secret"]):
            lines.append(f"- PII Assessment: {pii_reason}")

        lines.append("Execution halted at policy enforcement gateway. No changes applied.")
        return "\n".join(lines)


    if outcome == DecisionOutcome.REVIEW:
        lines = [
            f"APPROVAL REQUIRED: Action '{tool}' requires supervisor authorization (Risk: {risk_score:.0f}/100, Reversibility: {reversibility.value}).",
            f"- Trigger: {auth_reason}",
            f"- Context: {semantic_reason}"
        ]
        if pii_reason and "warn" in pii_reason.lower():
            lines.append(f"- PII Alert: {pii_reason}")
        lines.append("Execution paused pending review.")
        return "\n".join(lines)

    return (
        f"ACTION ALLOWED: Tool '{tool}' passed validation criteria "
        f"(Risk: {risk_score:.0f}/100, Reversibility: {reversibility.value}).\n"
        f"- Authorization: {auth_reason}\n"
        f"- Intent: Verified\n"
        f"- Provenance: Authenticated\n"
        f"- Guardrails: Content Safety, Topic Boundary & PII Verified"
    )

class ExplanationEngine:
    generate_explanation = staticmethod(generate_explanation)

explanation_engine = ExplanationEngine()

