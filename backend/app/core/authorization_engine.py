from typing import Dict, Any, List, Optional
from app.models.action import ActionContract, ProvenanceSource
from app.models.decision import CheckResult

# Explicit Role-Based Tool Matrix
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "finance_operator": [
        "refund_payment",
        "transfer_funds",
        "get_customer_details",
        "create_support_ticket"
    ],
    "support_agent": [
        "get_customer_details",
        "create_support_ticket",
        "send_email"
    ],
    "support_operator": [
        "get_customer_details",
        "create_support_ticket",
        "send_email"
    ],
    "support": [
        "get_customer_details",
        "create_support_ticket",
        "send_email"
    ],
    "db_administrator": [
        "execute_sql",
        "get_customer_details",
        "read_file"
    ],
    "security_auditor": [
        "read_file",
        "get_customer_details"
    ],
    "operator": [
        "create_support_ticket",
        "get_customer_details"
    ],
    "general_user": [
        "create_support_ticket"
    ],
    "user": [
        "create_support_ticket"
    ]
}

# Transaction limits
AUTONOMOUS_REFUND_LIMIT = 5000.0   # $50 or ₹5,000
SUPERVISOR_REFUND_LIMIT = 50000.0  # $5,000 or ₹50,000
AUTONOMOUS_TRANSFER_LIMIT = 1000.0
SUPERVISOR_TRANSFER_LIMIT = 25000.0

class AuthorizationEngine:
    """
    Authoritative, deterministic policy engine for AgentShield.
    Enforces Role-Based Access Control (RBAC), environment constraints,
    tool parameter boundaries, and financial limits independently of AI reasoning.
    """

    def evaluate(self, contract: ActionContract) -> CheckResult:
        role = contract.role.lower()
        tool = contract.tool
        target = contract.target or {}
        env = contract.environment.lower()
        prov = contract.provenance

        # 1. Role-Based Access Control (RBAC)
        allowed_tools = ROLE_PERMISSIONS.get(role, [])
        if tool not in allowed_tools:
            return CheckResult(
                passed=False,
                status="FAIL",
                reason=(
                    f"RBAC Authorization Failure: Role '{contract.role}' is not permitted to execute tool '{tool}'. "
                    f"Allowed tools for this role: {', '.join(allowed_tools) if allowed_tools else 'None'}."
                ),
                metadata={"role": role, "tool": tool, "rule": "rbac_unauthorized_tool"}
            )

        # 2. Tool-Specific Policy Constraints
        if tool == "refund_payment":
            try:
                amount = float(target.get("amount", 0.0))
            except (ValueError, TypeError):
                amount = 0.0

            if amount > SUPERVISOR_REFUND_LIMIT:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=(
                        f"Financial Policy FIN-004: Refund amount ({amount:,.2f}) exceeds absolute allowable threshold "
                        f"({SUPERVISOR_REFUND_LIMIT:,.2f}). Direct BLOCK."
                    ),
                    metadata={"tool": tool, "amount": amount, "threshold": SUPERVISOR_REFUND_LIMIT, "rule": "block_excessive_refund"}
                )
            elif amount > AUTONOMOUS_REFUND_LIMIT:
                return CheckResult(
                    passed=True,
                    status="WARN",
                    reason=(
                        f"Financial Policy FIN-002: Refund amount ({amount:,.2f}) exceeds autonomous limit "
                        f"({AUTONOMOUS_REFUND_LIMIT:,.2f}). Mandatory supervisor review required."
                    ),
                    metadata={"tool": tool, "amount": amount, "threshold": AUTONOMOUS_REFUND_LIMIT, "rule": "review_refund_threshold"}
                )

        elif tool == "transfer_funds":
            try:
                amount = float(target.get("amount", 0.0))
            except (ValueError, TypeError):
                amount = 0.0

            if amount > SUPERVISOR_TRANSFER_LIMIT:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=(
                        f"Financial Policy FIN-005: Fund transfer ({amount:,.2f}) exceeds maximum transfer ceiling "
                        f"({SUPERVISOR_TRANSFER_LIMIT:,.2f}). Direct BLOCK."
                    ),
                    metadata={"tool": tool, "amount": amount, "rule": "block_excessive_transfer"}
                )
            elif amount > AUTONOMOUS_TRANSFER_LIMIT:
                return CheckResult(
                    passed=True,
                    status="WARN",
                    reason=(
                        f"Financial Policy FIN-003: Fund transfer ({amount:,.2f}) exceeds autonomous transfer threshold "
                        f"({AUTONOMOUS_TRANSFER_LIMIT:,.2f}). Escalated to supervisor."
                    ),
                    metadata={"tool": tool, "amount": amount, "rule": "review_transfer_threshold"}
                )

        elif tool == "execute_sql":
            query = str(target.get("query", "")).lower()
            destructive_keywords = ["drop", "truncate", "delete", "alter table"]
            is_destructive = any(kw in query for kw in destructive_keywords)

            if is_destructive and env == "production":
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=(
                        f"Database Policy DB-001: Destructive SQL query ('{query[:60]}...') in production environment "
                        f"is strictly prohibited. Irreversible operation hard blocked."
                    ),
                    metadata={"tool": tool, "environment": env, "rule": "deny_destructive_sql_production"}
                )
            elif is_destructive:
                return CheckResult(
                    passed=True,
                    status="WARN",
                    reason=f"Database Policy DB-002: Destructive SQL query in {env} requires supervisor confirmation.",
                    metadata={"tool": tool, "environment": env, "rule": "review_destructive_sql_staging"}
                )

        elif tool == "export_data":
            if not prov.trusted or prov.source in [ProvenanceSource.EXTERNAL_WEB, ProvenanceSource.UNTRUSTED_DOCUMENT]:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason="Data Governance Policy SEC-003: Untrusted provenance source is prohibited from triggering data exports.",
                    metadata={"tool": tool, "source": prov.source.value, "rule": "block_untrusted_export"}
                )

        # 3. Passed All Deterministic Authorization Checks
        return CheckResult(
            passed=True,
            status="PASS",
            reason=f"Authorization Passed: Role '{contract.role}' authorized for '{tool}' in '{contract.environment}'.",
            metadata={"role": role, "tool": tool, "environment": env, "rule": "authorized"}
        )

authorization_engine = AuthorizationEngine()
