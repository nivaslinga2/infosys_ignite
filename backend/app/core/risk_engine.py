from typing import Dict, Any, Tuple
from app.models.action import ActionContract
from app.models.decision import CheckResult, ReversibilityTier

def calculate_risk(
    contract: ActionContract,
    semantic_result: CheckResult,
    reversibility_tier: ReversibilityTier
) -> Tuple[float, str, Dict[str, float]]:
    breakdown: Dict[str, float] = {}

    sens_weights = {"critical": 30.0, "high": 22.0, "medium": 12.0}
    sens = semantic_result.metadata.get("classification", {}).get("sensitivity", "low")
    breakdown["action_sensitivity"] = sens_weights.get(sens, 5.0)

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

    env = contract.environment.lower()
    env_weights = {"production": 15.0, "staging": 5.0}
    breakdown["environment_exposure"] = env_weights.get(env, 0.0)

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

    rev_weights = {ReversibilityTier.R3: 15.0, ReversibilityTier.R2: 8.0}
    breakdown["reversibility_risk"] = rev_weights.get(reversibility_tier, 2.0)

    total_score = min(100.0, sum(breakdown.values()))

    if total_score >= 80:
        level = "CRITICAL"
    elif total_score >= 60:
        level = "HIGH"
    elif total_score >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    return round(total_score, 1), level, breakdown

class RiskEngine:
    calculate_risk = staticmethod(calculate_risk)

risk_engine = RiskEngine()
