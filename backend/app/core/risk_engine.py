from typing import Dict, Any, Tuple, Optional
from app.models.action import ActionContract
from app.models.decision import CheckResult, ReversibilityTier

def calculate_risk(
    contract: ActionContract,
    semantic_result: CheckResult,
    reversibility_tier: ReversibilityTier,
    content_safety_res: Optional[CheckResult] = None,
    jailbreak_res: Optional[CheckResult] = None,
    topic_res: Optional[CheckResult] = None
) -> Tuple[float, str, Dict[str, float]]:
    breakdown: Dict[str, float] = {}

    tool = contract.tool
    is_conversational = (tool == "none")

    # 1. Action / Content Sensitivity Weight
    sens_weights = {"critical": 30.0, "high": 22.0, "medium": 12.0}
    sens = semantic_result.metadata.get("classification", {}).get("sensitivity", "low")
    breakdown["action_sensitivity"] = sens_weights.get(sens, 5.0)

    # 2. Content Safety Harm Penalty (Direct physical violence, cyberattacks, deepfakes)
    if content_safety_res and not content_safety_res.passed:
        violations = content_safety_res.metadata.get("violations", [])
        cat_names = [v.get("category", "") for v in violations]
        if any(c in ["VIOLENCE_AND_THREATS", "CYBERATTACK_AND_MALWARE", "SELF_HARM"] for c in cat_names):
            breakdown["content_safety_harm"] = 70.0
        elif any(c in ["SYNTHETIC_MEDIA_AND_DEEPFAKES", "HATE_SPEECH"] for c in cat_names):
            breakdown["content_safety_harm"] = 55.0
        else:
            breakdown["content_safety_harm"] = 40.0
    elif contract.intent == "blocked_cyberattack":
        breakdown["content_safety_harm"] = 70.0

    # 3. Adversarial Jailbreak & Prompt Injection Threat
    if jailbreak_res and not jailbreak_res.passed:
        threat_score = float(jailbreak_res.metadata.get("threat_score", 60.0))
        breakdown["jailbreak_threat"] = min(60.0, max(30.0, threat_score))

    # 4. Out-of-Domain Topic Boundary Violation
    if topic_res and not topic_res.passed:
        detected_topic = topic_res.metadata.get("detected_topic", "")
        if detected_topic in ["UNAUTHORIZED_HACKING_AND_EXPLOITATION", "SYNTHETIC_MEDIA_AND_DEEPFAKES"]:
            breakdown["topic_boundary_risk"] = 45.0
        else:
            breakdown["topic_boundary_risk"] = 30.0

    # 5. Financial Exposure
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

    # 6. Environmental Exposure
    env = contract.environment.lower()
    if is_conversational and "content_safety_harm" not in breakdown:
        breakdown["environment_exposure"] = 0.0
    else:
        env_weights = {"production": 15.0, "staging": 5.0}
        breakdown["environment_exposure"] = env_weights.get(env, 0.0)

    # 7. Blast Radius / Scope of Execution
    query = str(contract.target.get("query", "")).lower()
    if tool == "execute_sql" and any(k in query for k in ["delete", "drop", "truncate"]):
        blast_pts = 15.0
    elif tool == "export_data":
        blast_pts = 14.0
    elif tool in ["refund_payment", "transfer_funds"] and amount > 5000:
        blast_pts = 10.0
    elif is_conversational and "content_safety_harm" not in breakdown:
        blast_pts = 0.0
    else:
        blast_pts = 3.0
    breakdown["blast_radius"] = blast_pts

    # 8. Reversibility Risk
    if is_conversational and "content_safety_harm" not in breakdown:
        breakdown["reversibility_risk"] = 0.0
    else:
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
