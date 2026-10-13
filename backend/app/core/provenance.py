import re
from typing import List
from app.models.action import ActionContract, ProvenanceSource
from app.models.decision import CheckResult

INJECTION_SIGNATURES: List[str] = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s*:\s*you\s+are\s+now",
    r"bypass\s+(all\s+)?security",
    r"send\s+(the\s+)?(database|passwords|keys|pii|customer)",
    r"exfiltrate",
    r"attacker@example\.com",
    r"drop\s+table",
    r"delete\s+from",
    r"eval\(",
    r"<script",
    r"<\|im_start\|>",
    r"<\|system\|>",
    r"<<SYS>>",
    r"\[SYSTEM\s+NOTE\]",
    r"\[INST\]",
    r"do\s+anything\s+now",
    r"\bdan\s+mode\b",
    r"developer\s+mode\s+(is\s+)?enabled",
    r"pretend\s+you\s+(are|have)\s+no\s+(rules|ethics|restrictions)",
    r"reveal\s+(the\s+|your\s+)?(system\s+)?prompt",
    r"print\s+(the\s+|your\s+)?(system\s+)?prompt",
    r"what\s+are\s+your\s+(initial\s+|secret\s+)?instructions",
    r"!\[.*?\]\(https?://.*?/.*?\)",
    r"https?://(webhook\.site|pipedream\.net|requestcatcher\.com|burpcollaborator\.net|ngrok\.io)",
    r"(__import__|os\.system|subprocess|powershell\s+-enc)"
]

def evaluate_provenance(contract: ActionContract) -> CheckResult:
    prov = contract.provenance
    user_prompt = contract.user_prompt or ""

    if not prov.trusted or prov.source in [ProvenanceSource.EXTERNAL_WEB, ProvenanceSource.UNTRUSTED_DOCUMENT]:
        if contract.tool in ["export_data", "execute_sql", "transfer_funds", "send_email"]:
            return CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Security Alert: Untrusted provenance source ('{prov.source.value}') attempting sensitive tool '{contract.tool}'. Provenance gate BLOCK.",
                metadata={
                    "source": prov.source.value,
                    "trusted": False,
                    "context_url": prov.context_url,
                    "taint_level": "CRITICAL"
                }
            )

    detected_signatures = [sig for sig in INJECTION_SIGNATURES if re.search(sig, user_prompt, re.IGNORECASE)]

    if detected_signatures:
        return CheckResult(
            passed=False,
            status="FAIL",
            reason=f"Prompt Injection Detected: Input pattern matched adversarial attack signature ({detected_signatures[0]}). Provenance gate BLOCK.",
            metadata={
                "source": prov.source.value,
                "trusted": False,
                "detected_patterns": detected_signatures,
                "taint_level": "ADVERSARIAL_INJECTION"
            }
        )

    return CheckResult(
        passed=True,
        status="PASS",
        reason=f"Provenance Verified: Origin '{prov.source.value}' is authenticated and trusted with clean input vectors.",
        metadata={
            "source": prov.source.value,
            "trusted": True,
            "taint_level": "CLEAN"
        }
    )

class ProvenanceEngine:
    evaluate = staticmethod(evaluate_provenance)

provenance_engine = ProvenanceEngine()
