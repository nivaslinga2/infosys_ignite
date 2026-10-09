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
from app.ai.explanation import explanation_engine

class DecisionEngine:
    async def evaluate_action(self, contract: ActionContract) -> ValidationReport:
        """
        Coordinates parallel multi-vector validation of an Action Contract.
        Returns a comprehensive ValidationReport and definitive DecisionOutcome.
        """
        # Execute independent checks concurrently
        semantic_task = semantic_validator.validate_semantics(contract)
        opa_task = opa_client.evaluate(contract)
        reversibility_res = reversibility_engine.evaluate(contract)
        provenance_res = provenance_engine.evaluate(contract)
        intent_res = intent_alignment_engine.evaluate(contract)

        semantic_res, opa_res = await asyncio.gather(semantic_task, opa_task)

        # Extract reversibility tier
        rev_tier_val = reversibility_res.metadata.get("tier", "R1")
        reversibility_tier = ReversibilityTier(rev_tier_val)

        # Compute composite risk score
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

        # -----------------------------------------------------------------
        # Deterministic Decision Matrix
        # -----------------------------------------------------------------
        decision = DecisionOutcome.ALLOW

        # Hard BLOCK conditions:
        if not opa_res.passed or opa_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not provenance_res.passed or provenance_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not intent_res.passed or intent_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif not semantic_res.passed or semantic_res.status == "FAIL":
            decision = DecisionOutcome.BLOCK
        elif reversibility_tier == ReversibilityTier.R3 and contract.environment == "production":
            decision = DecisionOutcome.BLOCK
        elif risk_score >= 85.0:
            decision = DecisionOutcome.BLOCK

        # If not blocked, determine if REVIEW is required
        elif opa_res.status == "WARN" or opa_res.metadata.get("rule") == "review_refund_threshold":
            decision = DecisionOutcome.REVIEW
        elif risk_score >= 60.0:
            decision = DecisionOutcome.REVIEW
        elif semantic_res.status == "WARN":
            decision = DecisionOutcome.REVIEW
        elif reversibility_res.status == "WARN" and float(contract.target.get("amount", 0)) > 5000:
            decision = DecisionOutcome.REVIEW

        # Generate natural language transparent explanation
        explanation = explanation_engine.generate_explanation(
            outcome=decision,
            tool=contract.tool,
            risk_score=risk_score,
            reversibility=reversibility_tier,
            auth_reason=opa_res.reason,
            semantic_reason=semantic_res.reason,
            intent_reason=intent_res.reason,
            provenance_reason=provenance_res.reason
        )

        # Telemetry from Qualcomm AI
        qc_telemetry = semantic_res.metadata.get("telemetry", {})

        return ValidationReport(
            action_id=contract.action_id,
            ai_semantic=semantic_res,
            authorization=opa_res,
            risk_assessment=risk_check,
            reversibility=reversibility_res,
            intent_alignment=intent_res,
            provenance=provenance_res,
            composite_risk_score=risk_score,
            risk_level=risk_level,
            reversibility_tier=reversibility_tier,
            decision=decision,
            explanation=explanation,
            qualcomm_telemetry=qc_telemetry
        )

decision_engine = DecisionEngine()
