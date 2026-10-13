import asyncio
from typing import Dict, Any
from app.models.action import ActionContract
from app.models.decision import (
    ValidationReport,
    DecisionOutcome,
    ReversibilityTier,
    CheckResult
)
from app.ai.semantic_validator import semantic_validator
from app.policy.opa_client import opa_client
from app.core.risk_engine import risk_engine
from app.core.reversibility import reversibility_engine
from app.core.provenance import provenance_engine
from app.core.intent_alignment import intent_alignment_engine
from app.guardrails.content_safety import content_safety_engine
from app.guardrails.topic_control import topic_control_engine
from app.guardrails.jailbreak import jailbreak_guard
from app.guardrails.pii import pii_engine
from app.schemas.tool_schemas import schema_validator
from app.ai.explanation import explanation_engine

class DecisionEngine:
    async def evaluate_action(self, contract: ActionContract) -> ValidationReport:
        # P0 OWASP LLM05: Validate argument schema before execution
        schema_res = schema_validator.validate(contract)

        # Fail-closed execution wrappers for all async validators (OWASP LLM10)
        try:
            semantic_res = await semantic_validator.validate_semantics(contract)
        except Exception as e:
            semantic_res = CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Fail-Closed Defense (AI Semantic Validator Offline): {str(e)}"
            )

        from app.core.authorization_engine import authorization_engine
        custom_auth_res = authorization_engine.evaluate(contract)

        try:
            opa_res = await opa_client.evaluate(contract)
        except Exception as e:
            opa_res = CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Fail-Closed Defense (OPA Policy Engine Offline): {str(e)}"
            )

        # Authoritative Authorization: Custom RBAC engine takes precedence
        if not custom_auth_res.passed or custom_auth_res.status == "FAIL":
            auth_res = custom_auth_res
        elif not opa_res.passed or opa_res.status == "FAIL":
            auth_res = opa_res
        elif custom_auth_res.status == "WARN":
            auth_res = custom_auth_res
        else:
            auth_res = opa_res

        try:
            content_safety_res = await content_safety_engine.evaluate(contract)
        except Exception as e:
            content_safety_res = CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Fail-Closed Defense (Content Safety Service Offline): {str(e)}"
            )

        reversibility_res = reversibility_engine.evaluate(contract)
        provenance_res = provenance_engine.evaluate(contract)
        intent_res = intent_alignment_engine.evaluate(contract)
        topic_res = topic_control_engine.evaluate(contract)
        jailbreak_res = jailbreak_guard.evaluate(contract)
        pii_res = pii_engine.evaluate(contract)

        rev_tier_val = reversibility_res.metadata.get("tier", "R1")
        reversibility_tier = ReversibilityTier(rev_tier_val)

        risk_score, risk_level, risk_breakdown = risk_engine.calculate_risk(
            contract=contract,
            semantic_result=semantic_res,
            reversibility_tier=reversibility_tier
        )

        risk_check = CheckResult(
            passed=risk_score < 80.0,
            status="PASS" if risk_score < 40.0 else ("WARN" if risk_score < 80.0 else "FAIL"),
            score=risk_score,
            reason=f"Calculated composite risk of {risk_score}/100 ({risk_level}).",
            metadata={"breakdown": risk_breakdown, "risk_level": risk_level}
        )

        decision = DecisionOutcome.ALLOW

        # Hard Block evaluations (Fail Closed)
        if not schema_res.passed or schema_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not auth_res.passed or auth_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not provenance_res.passed or provenance_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not jailbreak_res.passed or jailbreak_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not content_safety_res.passed or content_safety_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not topic_res.passed or topic_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not pii_res.passed or pii_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not intent_res.passed or intent_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not semantic_res.passed or semantic_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif reversibility_tier == ReversibilityTier.R3 and contract.environment == "production":
            decision = DecisionOutcome.BLOCK
        elif risk_score >= 85.0:
            decision = DecisionOutcome.BLOCK
        elif auth_res.status == "WARN" or auth_res.metadata.get("rule") in ["review_refund_threshold", "review_transfer_threshold", "review_destructive_sql_staging"]:
            decision = DecisionOutcome.REVIEW
        elif risk_score >= 60.0:
            decision = DecisionOutcome.REVIEW
        elif semantic_res.status == "WARN":
            decision = DecisionOutcome.REVIEW
        elif pii_res.status == "WARN":
            decision = DecisionOutcome.REVIEW
        elif reversibility_res.status == "WARN" and float(contract.target.get("amount", 0) or 0) > 5000:
            decision = DecisionOutcome.REVIEW

        explanation = explanation_engine.generate_explanation(
            outcome=decision,
            tool=contract.tool,
            risk_score=risk_score,
            reversibility=reversibility_tier,
            auth_reason=auth_res.reason,
            semantic_reason=semantic_res.reason,
            intent_reason=intent_res.reason,
            provenance_reason=provenance_res.reason,
            content_safety_reason=content_safety_res.reason,
            topic_reason=topic_res.reason,
            pii_reason=pii_res.reason,
            jailbreak_reason=jailbreak_res.reason,
            schema_reason=schema_res.reason
        )


        qc_telemetry = semantic_res.metadata.get("telemetry", {})

        return ValidationReport(
            action_id=contract.action_id,
            ai_semantic=semantic_res,
            authorization=auth_res,
            risk_assessment=risk_check,
            reversibility=reversibility_res,
            intent_alignment=intent_res,
            provenance=provenance_res,
            content_safety=content_safety_res,
            topic_control=topic_res,
            pii_assessment=pii_res,
            jailbreak_defense=jailbreak_res,
            composite_risk_score=risk_score,
            risk_level=risk_level,
            reversibility_tier=reversibility_tier,
            decision=decision,
            explanation=explanation,
            qualcomm_telemetry=qc_telemetry
        )

decision_engine = DecisionEngine()

