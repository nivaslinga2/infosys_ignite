import os
import httpx
from typing import Dict, Any, Optional
from app.models.decision import CheckResult
from app.models.action import ActionContract

OPA_URL = os.getenv("OPA_URL", "http://localhost:8181")

class OPAClient:
    def __init__(self, opa_url: str = OPA_URL):
        self.opa_url = opa_url

    async def evaluate(self, contract: ActionContract) -> CheckResult:
        """
        Evaluates the ActionContract against deterministic authorization policies.
        Attempts HTTP OPA server first; falls back to embedded Rego policy engine.
        """
        payload = {
            "input": {
                "agent": contract.agent,
                "role": contract.role,
                "tool": contract.tool,
                "user": contract.user,
                "environment": contract.environment,
                "trusted": contract.provenance.trusted,
                "source": contract.provenance.source.value,
                "amount": float(contract.target.get("amount", 0)),
                "query": str(contract.target.get("query", "")),
                "customer": str(contract.target.get("customer", "") or contract.target.get("customer_id", ""))
            }
        }

        # Try live OPA HTTP API if reachable
        try:
            async with httpx.AsyncClient(timeout=0.3) as client:
                resp = await client.post(f"{self.opa_url}/v1/data/agentshield", json=payload)
                if resp.status_code == 200:
                    data = resp.json().get("result", {})
                    return self._interpret_opa_response(data, contract)
        except Exception:
            # Fallback cleanly to embedded deterministic Rego rule execution
            pass

        return self._evaluate_embedded_policies(payload["input"], contract)

    def _evaluate_embedded_policies(self, inp: Dict[str, Any], contract: ActionContract) -> CheckResult:
        tool = inp.get("tool", "")
        amount = inp.get("amount", 0.0)
        query = inp.get("query", "").lower()
        role = inp.get("role", "")
        trusted = inp.get("trusted", True)
        env = inp.get("environment", "production")

        # 1. Finance policy rules (finance.rego)
        if tool == "refund_payment":
            if amount > 50000:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=f"OPA Rule FIN-004: Refund of ₹{amount:,.2f} exceeds absolute threshold (₹50,000). Direct BLOCK.",
                    metadata={"policy": "finance.rego", "rule": "block_excessive_refund", "threshold": 50000}
                )
            elif amount > 5000:
                return CheckResult(
                    passed=True,
                    status="WARN",
                    reason=f"OPA Rule FIN-002: Refund of ₹{amount:,.2f} exceeds autonomous limit (₹5,000). HUMAN REVIEW mandatory.",
                    metadata={"policy": "finance.rego", "rule": "review_refund_threshold", "threshold": 5000}
                )
            else:
                return CheckResult(
                    passed=True,
                    status="PASS",
                    reason=f"OPA Rule FIN-001: Refund of ₹{amount:,.2f} is within autonomous limit for role '{role}' (<= ₹5,000).",
                    metadata={"policy": "finance.rego", "rule": "allow_autonomous_refund"}
                )

        if tool == "transfer_funds":
            if amount > 100000:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=f"OPA Rule FIN-008: Transfer of ₹{amount:,.2f} exceeds max ceiling (₹100,000). Direct BLOCK.",
                    metadata={"policy": "finance.rego", "rule": "block_excessive_transfer"}
                )
            elif amount > 20000:
                return CheckResult(
                    passed=True,
                    status="WARN",
                    reason=f"OPA Rule FIN-007: Transfer of ₹{amount:,.2f} exceeds autonomous limit (₹20,000). HUMAN REVIEW required.",
                    metadata={"policy": "finance.rego", "rule": "review_transfer_threshold"}
                )
            else:
                return CheckResult(
                    passed=True,
                    status="PASS",
                    reason=f"OPA Rule FIN-006: Fund transfer of ₹{amount:,.2f} authorized for role '{role}'.",
                    metadata={"policy": "finance.rego", "rule": "allow_transfer"}
                )

        # 2. Database policy rules (database.rego)
        if tool == "execute_sql":
            if any(k in query for k in ["delete", "drop", "truncate"]):
                if env == "production" or "drop" in query or "truncate" in query:
                    return CheckResult(
                        passed=False,
                        status="FAIL",
                        reason=f"OPA Rule DB-003: Destructive query ('{query[:30]}...') in '{env}' blocked by safety policy.",
                        metadata={"policy": "database.rego", "rule": "block_destructive_sql", "query_snippet": query[:40]}
                    )
            if "update" in query:
                return CheckResult(
                    passed=True,
                    status="WARN",
                    reason="OPA Rule DB-002: SQL UPDATE statement modifies state. HUMAN REVIEW required.",
                    metadata={"policy": "database.rego", "rule": "review_sql_update"}
                )
            if query.startswith("select") or not query:
                return CheckResult(
                    passed=True,
                    status="PASS",
                    reason="OPA Rule DB-001: Read-only SELECT query authorized.",
                    metadata={"policy": "database.rego", "rule": "allow_select"}
                )

        if tool == "get_customer_details":
            return CheckResult(
                passed=True,
                status="PASS",
                reason="OPA Rule DB-005: Read customer record lookup permitted.",
                metadata={"policy": "database.rego", "rule": "allow_customer_read"}
            )

        # 3. General policy rules (general.rego)
        if tool in ["create_support_ticket", "read_file"]:
            return CheckResult(
                passed=True,
                status="PASS",
                reason=f"OPA Rule GEN-001: Read/Ticketing tool '{tool}' is safe for execution.",
                metadata={"policy": "general.rego", "rule": "allow_safe_tool"}
            )

        if tool == "send_email":
            if not trusted:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason="OPA Rule GEN-005: Outbound email triggered from untrusted provenance blocked.",
                    metadata={"policy": "general.rego", "rule": "block_untrusted_email"}
                )
            return CheckResult(
                passed=True,
                status="PASS",
                reason="OPA Rule GEN-002: Routine email dispatch authorized.",
                metadata={"policy": "general.rego", "rule": "allow_email"}
            )

        if tool == "export_data":
            if not trusted:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason="OPA Rule SEC-009: Data export requested from untrusted context. Exfiltration protection BLOCK.",
                    metadata={"policy": "general.rego", "rule": "block_untrusted_export"}
                )
            return CheckResult(
                passed=True,
                status="WARN",
                reason="OPA Rule SEC-008: External data export requires manager authorization.",
                metadata={"policy": "general.rego", "rule": "review_data_export"}
            )

        # Default fallback
        return CheckResult(
            passed=True,
            status="WARN",
            reason=f"OPA Rule GEN-999: Tool '{tool}' has no explicit allow rule. Defaulting to HUMAN REVIEW.",
            metadata={"policy": "general.rego", "rule": "default_review"}
        )

    def _interpret_opa_response(self, data: Dict[str, Any], contract: ActionContract) -> CheckResult:
        if data.get("block", False):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason=data.get("reason", "Action denied by OPA security policy"),
                metadata=data
            )
        if data.get("review", False):
            return CheckResult(
                passed=True,
                status="WARN",
                reason=data.get("reason", "Action requires human review per OPA threshold"),
                metadata=data
            )
        return CheckResult(
            passed=True,
            status="PASS",
            reason="Action authorized by OPA policy",
            metadata=data
        )

opa_client = OPAClient()
