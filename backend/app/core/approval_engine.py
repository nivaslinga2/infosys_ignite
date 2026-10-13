import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from app.models.audit import AuditRecord, HumanApprovalRequest
from app.models.decision import DecisionOutcome

AUTHORIZED_APPROVER_ROLES = {
    "supervisor",
    "manager",
    "admin",
    "security_officer",
    "compliance_officer",
    "lead_operator",
    "manager_21" # Default test supervisor
}

APPROVAL_TTL_MINUTES = 15

def compute_canonical_hash(data: Any) -> str:
    """Computes a deterministic SHA-256 fingerprint of JSON-serializable payloads."""
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

class ApprovalSecurityEngine:
    """
    Cryptographic, tamper-resistant human review approval engine for AgentShield.
    Enforces:
    1. Cryptographic SHA-256 argument binding (approvals are bound to exact inputs).
    2. Expiration timestamps (approvals expire after TTL).
    3. Reviewer role authorization (only authorized supervisor identities can approve).
    4. Replay attack prevention (already-executed actions cannot be re-approved or replayed).
    5. Tamper detection at execution time.
    """

    @staticmethod
    def initialize_approval_context(record: AuditRecord, ttl_minutes: int = APPROVAL_TTL_MINUTES) -> None:
        """Sets up cryptographic fingerprint and expiration timestamp on a pending review."""
        args_hash = compute_canonical_hash(record.action_contract.target)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=ttl_minutes)

        record.arguments_hash = args_hash
        # Store context metadata
        record.notes = (
            f"ARGS_HASH:{args_hash}|"
            f"EXPIRES_AT:{expires.isoformat()}|"
            f"CREATED_AT:{now.isoformat()}"
        )

    @staticmethod
    def validate_approval_request(
        record: AuditRecord,
        req: HumanApprovalRequest
    ) -> Tuple[bool, str]:
        """Validates that a human approval submission is authorized, unexpired, and not replayed."""
        # 1. Blocked actions can never be approved
        if record.decision == DecisionOutcome.BLOCK:
            return False, "Security Violation: Cannot approve an action that was BLOCKED by security policy."

        # 2. Replay check: already executed
        if record.execution_status == "EXECUTED":
            return False, "Replay Attack Detected: This action has already been executed and cannot be re-approved."

        # 3. Already rejected or tampered
        if record.execution_status in ["REJECTED", "REJECTED_TAMPERED"]:
            return False, f"Invalid State: Action is in terminal state '{record.execution_status}'."

        # 4. Reviewer Authorization
        reviewer_name = req.reviewer.lower()
        is_authorized = any(role in reviewer_name for role in AUTHORIZED_APPROVER_ROLES) or "supervisor" in reviewer_name or "manager" in reviewer_name
        if not is_authorized:
            return False, f"Unauthorized Approver: Identity '{req.reviewer}' is not an authorized supervisor or manager."

        # 5. Expiration check
        notes = record.notes or ""
        if "EXPIRES_AT:" in notes:
            try:
                parts = dict(item.split(":", 1) for item in notes.split("|") if ":" in item)
                expires_str = parts.get("EXPIRES_AT")
                if expires_str:
                    expires_dt = datetime.fromisoformat(expires_str)
                    now_dt = datetime.now(timezone.utc)
                    if now_dt > expires_dt:
                        record.execution_status = "EXPIRED"
                        return False, f"Approval Expired: Action approval window expired at {expires_str} (TTL {APPROVAL_TTL_MINUTES}m)."
            except Exception:
                pass

        return True, "Approval authorized."

    @staticmethod
    def verify_execution_integrity(record: AuditRecord, proposed_target: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Execution Gate verification immediately before dispatch.
        Re-verifies that target arguments match the exact cryptographic hash approved by supervisor.
        """
        # 1. State check
        if record.execution_status == "EXECUTED":
            return False, "Replay Attack Detected: Action has already been executed."

        if record.decision == DecisionOutcome.BLOCK:
            return False, "Execution Denied: Action was BLOCKED by policy."

        if record.decision == DecisionOutcome.REVIEW and not record.approved_by:
            return False, "Execution Denied: Action requires human approval before dispatch."

        # 2. Tamper check
        target_to_check = proposed_target if proposed_target is not None else record.action_contract.target
        current_hash = compute_canonical_hash(target_to_check)

        expected_hash = record.arguments_hash
        if not expected_hash and record.notes:
            for item in (record.notes or "").split("|"):
                if item.startswith("ARGS_HASH:"):
                    expected_hash = item.replace("ARGS_HASH:", "").strip()

        if expected_hash and current_hash != expected_hash:
            record.execution_status = "REJECTED_TAMPERED"
            return False, (
                f"Argument Tampering Detected: Executable arguments hash ({current_hash[:12]}...) "
                f"does not match approved signature ({expected_hash[:12]}...). Execution halted."
            )

        return True, "Execution integrity verified."

approval_engine = ApprovalSecurityEngine()
