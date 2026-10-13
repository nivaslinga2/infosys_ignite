import re
import base64
import unicodedata
from typing import Dict, Any, List, Optional
from app.models.decision import CheckResult
from app.models.action import ActionContract

JAILBREAK_ATTACK_VECTORS = {
    "PERSONA_OVERRIDE": [
        r"\bdan\s+mode\b",
        r"developer\s+mode\s+(is\s+)?enabled",
        r"do\s+anything\s+now",
        r"pretend\s+you\s+(are|have)\s+no\s+(rules|ethics|restrictions|limits)",
        r"hypothetical\s+(scenario|universe|world)\s+where\s+(there\s+are\s+no|you\s+have\s+no)\s+rules",
        r"roleplay\s+as\s+(an\s+)?unrestricted|evil|jailbroken",
        r"you\s+are\s+now\s+free\s+from\s+all\s+constraints",
        r"aim\s*:\s*always\s+intelligent\s+and\s+machiavellian"
    ],
    "INSTRUCTION_BYPASS": [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"bypass\s+(all\s+)?(security|guardrails|filters|rules)",
        r"override\s+(the\s+)?system\s+directives",
        r"disregard\s+(all\s+)?safety\s+guidelines"
    ],
    "SYSTEM_PROMPT_EXTRACTION": [
        r"reveal\s+(the\s+|your\s+)?(system\s+)?prompt",
        r"print\s+(the\s+|your\s+)?(system\s+)?prompt",
        r"repeat\s+everything\s+above\s+verbatim",
        r"what\s+are\s+your\s+(initial\s+|secret\s+)?instructions",
        r"output\s+the\s+full\s+initial\s+prompt"
    ],
    "DELIMITER_INJECTION": [
        r"<\|im_start\|>",
        r"<\|system\|>",
        r"<\|im_end\|>",
        r"<<SYS>>",
        r"<</SYS>>",
        r"\[SYSTEM\s+NOTE\]",
        r"\[INST\]",
        r"\[/INST\]",
        r"###\s*System:",
        r"###\s*Instruction:"
    ],
    "PREFIX_INJECTION": [
        r"start\s+your\s+response\s+with\s*['\"](?:sure|certainly|absolutely|i\s+will|bypass)",
        r"begin\s+(your\s+)?reply\s+by\s+saying\s*['\"]",
        r"you\s+must\s+affirm\s+and\s+never\s+refuse"
    ],
    "DATA_EXFILTRATION_BEACON": [
        r"!\[.*?\]\(https?://.*?/.*?\)",
        r"https?://(?:webhook\.site|pipedream\.net|requestcatcher\.com|burpcollaborator\.net|ngrok\.io)"
    ]
}

class AdvancedJailbreakGuardrail:
    def __init__(self):
        self.vector_rules = {
            vector: [re.compile(p, re.IGNORECASE) for p in patterns]
            for vector, patterns in JAILBREAK_ATTACK_VECTORS.items()
        }

    def detect_obfuscated_base64(self, text: str) -> Optional[str]:
        """Detects base64 payload smuggling embedded in user text."""
        b64_matches = re.findall(r"\b[A-Za-z0-9+/]{28,}={0,2}\b", text)
        for cand in b64_matches:
            try:
                decoded = base64.b64decode(cand).decode("utf-8", errors="ignore")
                if any(k in decoded.lower() for k in ["ignore", "system", "delete", "password", "bypass"]):
                    return decoded
            except Exception:
                continue
        return None

    def evaluate_text(self, text: str) -> CheckResult:
        if not text or not text.strip():
            return CheckResult(
                passed=True,
                status="PASS",
                reason="Jailbreak Guard Passed: Clean baseline prompt.",
                metadata={"detected_vectors": [], "threat_score": 0.0}
            )

        from app.guardrails.normalize import inspect_text
        inspection = inspect_text(text)
        normalized_text = inspection["normalized"]
        # Strip invisible formatting characters for pattern scanning
        canonical_text = "".join(
            c for c in normalized_text 
            if unicodedata.category(c) not in {"Cf", "Cs"} and (unicodedata.category(c) != "Cc" or c in {"\t", "\n", "\r"})
        )

        detected_vectors: List[Dict[str, str]] = []

        # Check across original, normalized, and canonical text versions
        texts_to_scan = [text]
        if normalized_text != text:
            texts_to_scan.append(normalized_text)
        if canonical_text != normalized_text and canonical_text != text:
            texts_to_scan.append(canonical_text)

        for vector_name, patterns in self.vector_rules.items():
            for pat in patterns:
                for scan_target in texts_to_scan:
                    m = pat.search(scan_target)
                    if m:
                        detected_vectors.append({
                            "vector": vector_name,
                            "matched": m.group(0)
                        })
                        break
                if any(v["vector"] == vector_name for v in detected_vectors):
                    break

        b64_payload = self.detect_obfuscated_base64(text)
        if b64_payload:
            detected_vectors.append({
                "vector": "OBFUSCATED_BASE64_INJECTION",
                "matched": b64_payload[:40]
            })

        if detected_vectors:
            vector_names = [v["vector"] for v in detected_vectors]
            return CheckResult(
                passed=False,
                status="FAIL",
                score=100.0,
                reason=f"Adversarial Jailbreak Attack Blocked: Input matched attack vectors ({', '.join(vector_names)}). PEP Gateway hard halt.",
                metadata={
                    "threat_level": "CRITICAL",
                    "threat_score": 100.0,
                    "vectors": detected_vectors,
                    "action": "BLOCK_ADVERSARIAL_INJECTION"
                }
            )

        return CheckResult(
            passed=True,
            status="PASS",
            score=0.0,
            reason="Jailbreak Guard Passed: No adversarial prompt injection or virtualization attempts detected.",
            metadata={"threat_score": 0.0, "detected_vectors": []}
        )

    def evaluate(self, contract: ActionContract) -> CheckResult:
        prompt = contract.user_prompt or ""
        return self.evaluate_text(prompt)

jailbreak_guard = AdvancedJailbreakGuardrail()
