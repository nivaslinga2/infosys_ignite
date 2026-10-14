import re
from typing import Dict, Any, List, Optional
from app.models.decision import CheckResult
from app.models.action import ActionContract

FORBIDDEN_TOPIC_PATTERNS = {
    "POLITICS_AND_ELECTIONS": [
        r"\b(?:who\s+should\s+i\s+vote\s+for|presidential\s+election|democrat\s+vs\s+republican|political\s+party|prime\s+minister\s+opinion)\b",
        r"\b(?:election\s+fraud|politicians\s+are|impeach\s+the\s+president)\b"
    ],
    "MEDICAL_AND_HEALTH_ADVICE": [
        r"\b(?:diagnose\s+my\s+(?:symptoms|illness)|what\s+medicine\s+should\s+i\s+take|medical\s+treatment\s+for)\b",
        r"\b(?:cure\s+cancer|how\s+to\s+treat\s+infection\s+at\s+home)\b"
    ],
    "LEGAL_ADVICE": [
        r"\b(?:sue\s+my\s+employer|legal\s+advice\s+for\s+lawsuit|how\s+to\s+evade\s+taxes)\b"
    ],
    "CRYPTO_AND_GAMBLING": [
        r"\b(?:which\s+crypto\s+will\s+100x|betting\s+odds|best\s+online\s+casino|roulette\s+strategy)\b"
    ],
    "UNAUTHORIZED_HACKING_AND_EXPLOITATION": [
        r"\b(?:hack\s+a\s+bank|hack(?:ing)?\s+firewall|bypass\s+firewall|illegal\s+penetration|break\s+into\s+network)\b",
        r"\b(?:steal\s+credentials|ddos\s+attack|exploit\s+vulnerability|how\s+to\s+hack)\b"
    ],
    "UNRELATED_PHILOSOPHY_AND_ENTERTAINMENT": [
        r"\b(?:meaning\s+of\s+life|tell\s+me\s+a\s+bedtime\s+story|celebrity\s+gossip)\b"
    ],
    "SYNTHETIC_MEDIA_AND_DEEPFAKES": [
        r"\b(?:morph\s+(?:a\s+)?(?:video|image|photo|face)|deepfake|face\s*swap|swap\s+faces|generate\s+(?:fake|nude)\s+video)\b"
    ]
}

ALLOWED_TOPIC_DOMAINS = [
    "CUSTOMER_SUPPORT",
    "FINANCE_AND_BILLING",
    "DATABASE_AND_DATA_OPS",
    "SYSTEM_ADMINISTRATION",
    "COMMUNICATIONS_AND_TICKETING"
]

class TopicControlEngine:
    def __init__(self):
        self.rules = {
            topic: [re.compile(p, re.IGNORECASE) for p in patterns]
            for topic, patterns in FORBIDDEN_TOPIC_PATTERNS.items()
        }

    def evaluate_text(self, text: str) -> CheckResult:
        if not text or not text.strip():
            return CheckResult(
                passed=True,
                status="PASS",
                reason="Topic Control: Neutral input accepted within enterprise scope.",
                metadata={"topic": "GENERAL_ENTERPRISE", "allowed": True}
            )

        for topic, patterns in self.rules.items():
            for pat in patterns:
                match = pat.search(text)
                if match:
                    redirect_message = (
                        f"I am AgentShield, an enterprise assistant specialized in "
                        f"{', '.join(ALLOWED_TOPIC_DOMAINS[:3])}. "
                        f"I cannot address '{topic.replace('_', ' ').title()}' queries. "
                        f"Please submit an inquiry regarding customer support, billing, or enterprise operations."
                    )
                    return CheckResult(
                        passed=False,
                        status="FAIL",
                        reason=f"Topic Rail Violation: Inquiry classified under prohibited topic '{topic}'. Conversation rail BLOCK.",
                        metadata={
                            "detected_topic": topic,
                            "matched_term": match.group(0),
                            "allowed": False,
                            "allowed_topics": ALLOWED_TOPIC_DOMAINS,
                            "redirect_response": redirect_message
                        }
                    )

        return CheckResult(
            passed=True,
            status="PASS",
            reason="Topic Rail Passed: Inquiry conforms to authorized enterprise operational topics.",
            metadata={"topic": "AUTHORIZED_ENTERPRISE", "allowed": True}
        )

    def evaluate(self, contract: ActionContract) -> CheckResult:
        prompt = contract.user_prompt or ""
        return self.evaluate_text(prompt)

topic_control_engine = TopicControlEngine()
