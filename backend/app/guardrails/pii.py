import re
import uuid
from typing import Dict, Any, List, Tuple, Optional
from app.models.decision import CheckResult
from app.models.action import ActionContract

def _luhn_checksum(card_number_str: str) -> bool:
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0

PII_PATTERNS = {
    "SECRET_API_KEY": re.compile(
        r"\b(?:sk-[A-Za-z0-9_\-]{20,}|AIzaSy[A-Za-z0-9_\-]{33}|ghp_[A-Za-z0-9]{36}|Bearer\s+[A-Za-z0-9\.\_\-]{20,})\b",
        re.IGNORECASE
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b(?:\d{4}[-\s]?){3}\d{1,4}\b"
    ),
    "SSN": re.compile(
        r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"
    ),
    "AADHAAR": re.compile(
        r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b"
    ),
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b"
    ),
    "PHONE_NUMBER": re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b(?:\+91[\-\s]?)?[6-9]\d{9}\b"
    ),
    "IP_ADDRESS": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    )
}

class PIIVault:
    """In-memory session vault for reversible PII de-anonymization."""
    def __init__(self):
        self._vaults: Dict[str, Dict[str, str]] = {}

    def store_mapping(self, vault_id: str, mapping: Dict[str, str]):
        if vault_id not in self._vaults:
            self._vaults[vault_id] = {}
        self._vaults[vault_id].update(mapping)

    def get_mapping(self, vault_id: str) -> Dict[str, str]:
        return self._vaults.get(vault_id, {})

    def clear(self, vault_id: str):
        if vault_id in self._vaults:
            del self._vaults[vault_id]

pii_vault = PIIVault()

class PIIMaskingEngine:
    def __init__(self):
        self.vault = pii_vault

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Scans text and returns detailed list of identified PII entities."""
        findings = []
        if not text:
            return findings

        for entity_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                val = match.group(0)
                # Extra validation for credit cards
                if entity_type == "CREDIT_CARD":
                    digits = re.sub(r"\D", "", val)
                    if len(digits) not in [13, 15, 16, 19]:
                        continue
                findings.append({
                    "entity_type": entity_type,
                    "value": val,
                    "start": match.start(),
                    "end": match.end()
                })
        # Sort by start position descending to facilitate clean masking
        findings.sort(key=lambda x: x["start"], reverse=True)
        return findings

    def mask_text(
        self,
        text: str,
        vault_id: Optional[str] = None,
        redact_only: bool = False
    ) -> Tuple[str, Dict[str, str], List[Dict[str, Any]]]:
        """
        Masks all identified PII entities in the text.
        Returns:
            masked_text: Anonymized text with tokens (e.g. [EMAIL_1] or [REDACTED_EMAIL])
            token_vault: Map of token -> original value
            detected: List of detected entities
        """
        if not text:
            return text, {}, []

        entities = self.detect_pii(text)
        token_vault: Dict[str, str] = {}
        counts: Dict[str, int] = {}
        masked_chars = list(text)

        # Process from right to left using the descending start position
        for ent in entities:
            e_type = ent["entity_type"]
            counts[e_type] = counts.get(e_type, 0) + 1
            idx = counts[e_type]

            if redact_only:
                token = f"[REDACTED_{e_type}]"
            else:
                token = f"[{e_type}_{idx}]"

            token_vault[token] = ent["value"]
            start, end = ent["start"], ent["end"]
            masked_chars[start:end] = list(token)

        masked_text = "".join(masked_chars)

        if vault_id and token_vault:
            self.vault.store_mapping(vault_id, token_vault)

        return masked_text, token_vault, entities

    def unmask_text(self, masked_text: str, vault_id_or_dict: Any) -> str:
        """Restores original PII using the mapping vault."""
        if not masked_text:
            return masked_text

        if isinstance(vault_id_or_dict, str):
            mapping = self.vault.get_mapping(vault_id_or_dict)
        elif isinstance(vault_id_or_dict, dict):
            mapping = vault_id_or_dict
        else:
            mapping = {}

        result = masked_text
        for token, original_val in mapping.items():
            result = result.replace(token, original_val)
        return result

    def mask_payload(self, data: Any, vault_id: Optional[str] = None) -> Tuple[Any, Dict[str, str]]:
        """Recursively masks dictionary or list payloads."""
        all_vault: Dict[str, str] = {}

        if isinstance(data, str):
            masked, v, _ = self.mask_text(data, vault_id)
            all_vault.update(v)
            return masked, all_vault
        elif isinstance(data, dict):
            new_dict = {}
            for k, val in data.items():
                m_val, v = self.mask_payload(val, vault_id)
                new_dict[k] = m_val
                all_vault.update(v)
            return new_dict, all_vault
        elif isinstance(data, list):
            new_list = []
            for item in data:
                m_item, v = self.mask_payload(item, vault_id)
                new_list.append(m_item)
                all_vault.update(v)
            return new_list, all_vault
        return data, all_vault

    def evaluate(self, contract: ActionContract) -> CheckResult:
        """
        Evaluates ActionContract for PII leaks and untrusted exposures.
        Blocks unmasked PII exfiltration to external/untrusted tools.
        """
        prompt = contract.user_prompt or ""
        target_str = str(contract.target)

        prompt_pii = self.detect_pii(prompt)
        target_pii = self.detect_pii(target_str)

        total_detected = len(prompt_pii) + len(target_pii)
        entity_types = list(set([e["entity_type"] for e in (prompt_pii + target_pii)]))

        # Check for unmasked secret/credential exfiltration
        has_secrets = "SECRET_API_KEY" in entity_types
        has_financial = "CREDIT_CARD" in entity_types or "SSN" in entity_types or "AADHAAR" in entity_types

        # If exfiltrating via sensitive tools (export_data, external email, curl/cmd)
        is_export_tool = contract.tool in ["export_data", "send_email", "execute_sql"]

        if total_detected > 0:
            if has_secrets:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=f"PII Leakage Blocked: Detected active secret or API credential ({', '.join(entity_types)}) in action payload.",
                    metadata={
                        "entities_detected": entity_types,
                        "count": total_detected,
                        "action": "BLOCK_SECRET_EXPOSURE"
                    }
                )

            if is_export_tool and (has_financial or "customer_pii" in target_str.lower()):
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=f"PII Leakage Blocked: Unmasked sensitive data ({', '.join(entity_types)}) routed to export tool '{contract.tool}'. Masking required.",
                    metadata={
                        "entities_detected": entity_types,
                        "count": total_detected,
                        "action": "BLOCK_EXPORT_PII"
                    }
                )

            return CheckResult(
                passed=True,
                status="WARN",
                reason=f"PII Detected & Monitored: Identified {total_detected} sensitive token(s) ({', '.join(entity_types)}). Anonymization vault active.",
                metadata={
                    "entities_detected": entity_types,
                    "count": total_detected,
                    "anonymized": True
                }
            )

        return CheckResult(
            passed=True,
            status="PASS",
            reason="PII Verification Passed: No unmasked sensitive personal or credential data detected.",
            metadata={"entities_detected": [], "count": 0}
        )

pii_engine = PIIMaskingEngine()
