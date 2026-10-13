import re
from typing import Dict, Any, List, Optional
from app.models.decision import CheckResult
from app.models.action import ActionContract
from app.ai.qualcomm_client import qualcomm_client

SAFETY_TAXONOMY_PATTERNS = {
    "VIOLENCE_AND_THREATS": [
        r"\b(?:kill\s+all|assassinate|bomb\s+recipe|build\s+a\s+bomb|massacre|physical\s+violence|shoot\s+up)\b",
        r"\b(?:how\s+to\s+(?:make|build)\s+(?:explosives|weapons|toxins))\b",
        r"\b(?:murder|strangle|decapitate|slaughter)\b"
    ],
    "SELF_HARM": [
        r"\b(?:suicide\s+(?:method|guide|instruction)|how\s+to\s+kill\s+myself)\b",
        r"\b(?:cut\s+(?:my\s+)?wrists|hang\s+myself|overdose\s+instructions)\b"
    ],
    "HATE_SPEECH": [
        r"\b(?:hate\s+speech|genocide\s+against|racial\s+slur|inferior\s+race)\b",
        r"\b(?:death\s+to\s+all\s+(?:immigrants|minorities|jews|muslims|christians))\b"
    ],
    "CYBERATTACK_AND_MALWARE": [
        r"\b(?:ransomware\s+script|create\s+a\s+botnet|ddos\s+target|keylogger\s+payload)\b",
        r"\b(?:exploit\s+zeroday|reverse\s+shell\s+script|trojan\s+downloader)\b",
        r"\b(?:exfiltrate\s+all\s+credentials|dump\s+sam\s+hashes)\b"
    ],
    "TOXICITY_AND_HARASSMENT": [
        r"\b(?:shut\s+the\s+fuck\s+up|worthless\s+piece\s+of\s+shit|go\s+die\s+in\s+a\s+hole)\b"
    ]
}

class ContentSafetyEngine:
    def __init__(self):
        self.qc = qualcomm_client
        self.compiled_rules = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in SAFETY_TAXONOMY_PATTERNS.items()
        }

    def scan_heuristics(self, text: str) -> List[Dict[str, str]]:
        violations = []
        if not text:
            return violations

        for category, patterns in self.compiled_rules.items():
            for pat in patterns:
                match = pat.search(text)
                if match:
                    violations.append({
                        "category": category,
                        "matched_term": match.group(0)
                    })
                    break
        return violations

    async def evaluate_text(self, text: str) -> CheckResult:
        if not text or not text.strip():
            return CheckResult(
                passed=True,
                status="PASS",
                reason="Content Safety Passed: Empty or neutral content.",
                metadata={"violations": [], "safety_score": 100.0}
            )

        # Tier 1: Fast deterministic heuristic scan
        violations = self.scan_heuristics(text)
        if violations:
            flagged_categories = [v["category"] for v in violations]
            return CheckResult(
                passed=False,
                status="FAIL",
                score=10.0,
                reason=f"Content Safety Violation: Input matches prohibited categories ({', '.join(flagged_categories)}). Content safety rail BLOCK.",
                metadata={
                    "violations": violations,
                    "categories": flagged_categories,
                    "action": "BLOCK_HARMFUL_CONTENT"
                }
            )

        # Tier 2: Qualcomm AI Semantic safety analysis if borderline or long
        if len(text.split()) > 6 and any(w in text.lower() for w in ["attack", "destroy", "force", "weapon", "harm", "toxic", "leak"]):
            system_prompt = (
                "You are an enterprise Content Safety Guardrail. Analyze if the text contains hate speech, violence, self-harm, cyberattacks, or extreme toxicity. "
                "Respond with SAFE or UNSAFE followed by a brief reason."
            )
            resp = await self.qc.generate_completion(system_prompt, text)
            if "UNSAFE" in resp.get("response", "").upper():
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    score=20.0,
                    reason=f"Content Safety Semantic Violation: Qualcomm AI flagged text as potentially harmful ({resp.get('response', '')[:60]}).",
                    metadata={"violations": [{"category": "SEMANTIC_UNSAFE", "matched_term": resp.get("response")}]}
                )

        return CheckResult(
            passed=True,
            status="PASS",
            score=99.0,
            reason="Content Safety Passed: No toxic, violent, or unsafe content patterns identified.",
            metadata={"violations": [], "safety_score": 99.0}
        )

    async def evaluate(self, contract: ActionContract) -> CheckResult:
        text_to_check = f"{contract.user_prompt or ''} {contract.intent} {str(contract.target)}"
        return await self.evaluate_text(text_to_check)

content_safety_engine = ContentSafetyEngine()
