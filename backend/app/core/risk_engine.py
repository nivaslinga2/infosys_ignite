from typing import Dict, Any, Tuple
from app.models.action import ActionContract
from app.models.decision import CheckResult, ReversibilityTier

class RiskEngine:
    @staticmethod
    def calculate_risk(
        contract: ActionContract,
        semantic_result: CheckResult,
        reversibility_tier: ReversibilityTier
    ) -> Tuple[float, str, Dict[str, float]]:
        """
        Calculates explainable, deterministic composite risk score (0 - 100).
        Factors:
        - Action sensitivity (0-30)
        - Financial operation (0-25)
        - Environment penalty (0-15)
        - Blast radius / scope (0-15)
        - Reversibility penalty (0-15)
        """
        breakdown: Dict[str, float] = {}

        # 1. Action Sensitivity (0 - 30)
        sem_meta = semantic_result.metadata.get("classification", {})
        sens = sem_meta.get("sensitivity", "low")
        if sens == "critical":
            sensitivity_pts = 30.0
        elif sens == "high":
            sensitivity_pts = 22.0
        elif sens == "medium":
            sensitivity_pts = 12.0
        else:
            sensitivity_pts = 5.0
        breakdown["action_sensitivity"] = sensitivity_pts

        # 2. Financial Operation (0 - 25)
        tool = contract.tool
        amount = float(contract.target.get("amount", 0.0))
        financial_pts = 0.0
        if tool in ["refund_payment", "transfer_funds"]:
            if amount > 50000:
                financial_pts = 25.0
            elif amount > 5000:
                financial_pts = 18.0
            elif amount > 1000:
                financial_pts = 10.0
            else:
                financial_pts = 5.0
        breakdown["financial_impact"] = financial_pts

        # 3. Environment Penalty (0 - 15)
        env = contract.environment.lower()
        if env == "production":
            env_pts = 15.0
        elif env == "staging":
            env_pts = 5.0
        else:
            env_pts = 0.0
        breakdown["environment_exposure"] = env_pts

        # 4. Blast Radius (0 - 15)
        query = str(contract.target.get("query", "")).lower()
        if tool == "execute_sql" and any(k in query for k in ["delete", "drop", "truncate"]):
            blast_pts = 15.0
        elif tool == "export_data":
            blast_pts = 14.0
        elif tool in ["refund_payment", "transfer_funds"] and amount > 5000:
            blast_pts = 10.0
        else:
            blast_pts = 3.0
        breakdown["blast_radius"] = blast_pts

        # 5. Reversibility Penalty (0 - 15)
        if reversibility_tier == ReversibilityTier.R3:
            rev_pts = 15.0
        elif reversibility_tier == ReversibilityTier.R2:
            rev_pts = 8.0
        else:
            rev_pts = 2.0
        breakdown["reversibility_risk"] = rev_pts

        # Total score
        total_score = min(100.0, sum(breakdown.values()))

        # Risk Tier
        if total_score >= 80:
            level = "CRITICAL"
        elif total_score >= 60:
            level = "HIGH"
        elif total_score >= 35:
            level = "MEDIUM"
        else:
            level = "LOW"

        return round(total_score, 1), level, breakdown

risk_engine = RiskEngine()
