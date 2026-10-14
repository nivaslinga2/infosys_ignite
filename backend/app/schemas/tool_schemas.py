import math
import re
from typing import Dict, Any, Tuple
from app.models.decision import CheckResult
from app.models.action import ActionContract

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_tool_arguments(contract: ActionContract) -> CheckResult:
    """
    Validates tool parameters against explicit schema constraints (OWASP LLM05: Improper Output Handling).
    Ensures no malformed, out-of-bound, or type-coerced unsafe payloads reach tools.
    """
    tool = contract.tool
    target = contract.target

    if not isinstance(target, dict):
        return CheckResult(
            passed=False,
            status="FAIL",
            reason="Schema Validation Failed (OWASP LLM05): Action target must be a valid key-value dictionary.",
            metadata={"tool": tool, "error": "TARGET_NOT_DICT"}
        )

    if tool == "none":
        return CheckResult(
            passed=True,
            status="PASS",
            reason="No tool arguments to validate.",
            metadata={"tool": "none"}
        )

    if tool == "refund_payment":
        if "amount" not in target:
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Schema Validation Failed (OWASP LLM05): Missing mandatory 'amount' parameter for refund_payment.",
                metadata={"tool": tool, "error": "MISSING_AMOUNT"}
            )
        try:
            amt = float(target["amount"])
            if math.isnan(amt) or math.isinf(amt) or amt <= 0:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=f"Schema Validation Failed (OWASP LLM05): Refund amount must be a positive, finite number (got {target['amount']}).",
                    metadata={"tool": tool, "error": "INVALID_AMOUNT_VALUE"}
                )
        except (ValueError, TypeError):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Schema Validation Failed (OWASP LLM05): Invalid amount type '{type(target.get('amount')).__name__}'. Expected numeric.",
                metadata={"tool": tool, "error": "INVALID_AMOUNT_TYPE"}
            )

        customer = target.get("customer") or target.get("customer_id")
        if not customer or not str(customer).strip():
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Schema Validation Failed (OWASP LLM05): Missing mandatory 'customer' or 'customer_id' string identifier.",
                metadata={"tool": tool, "error": "MISSING_CUSTOMER"}
            )

    elif tool == "transfer_funds":
        if "amount" not in target:
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Schema Validation Failed (OWASP LLM05): Missing mandatory 'amount' parameter for transfer_funds.",
                metadata={"tool": tool, "error": "MISSING_AMOUNT"}
            )
        try:
            amt = float(target["amount"])
            if math.isnan(amt) or math.isinf(amt) or amt <= 0:
                return CheckResult(
                    passed=False,
                    status="FAIL",
                    reason=f"Schema Validation Failed (OWASP LLM05): Transfer amount must be positive and finite (got {target['amount']}).",
                    metadata={"tool": tool, "error": "INVALID_TRANSFER_AMOUNT"}
                )
        except (ValueError, TypeError):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Schema Validation Failed (OWASP LLM05): Transfer amount must be numeric.",
                metadata={"tool": tool, "error": "INVALID_TRANSFER_TYPE"}
            )

        account = target.get("account_id") or target.get("account")
        if not account or not str(account).strip():
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Schema Validation Failed (OWASP LLM05): Missing mandatory 'account_id' parameter.",
                metadata={"tool": tool, "error": "MISSING_ACCOUNT_ID"}
            )

    elif tool == "execute_sql":
        query = target.get("query")
        if not query or not isinstance(query, str) or not query.strip():
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Schema Validation Failed (OWASP LLM05): Missing non-empty SQL 'query' string parameter.",
                metadata={"tool": tool, "error": "EMPTY_OR_INVALID_SQL_QUERY"}
            )

    elif tool == "create_support_ticket":
        title = target.get("title") or target.get("description")
        if not title or not str(title).strip():
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="Schema Validation Failed (OWASP LLM05): Support ticket requires non-empty 'title' or 'description'.",
                metadata={"tool": tool, "error": "EMPTY_TICKET_DETAILS"}
            )

    elif tool == "send_email":
        to_addr = target.get("to")
        if not to_addr or not EMAIL_REGEX.match(str(to_addr).strip()):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Schema Validation Failed (OWASP LLM05): Invalid destination email address format ('{to_addr}').",
                metadata={"tool": tool, "error": "INVALID_EMAIL_RECIPIENT"}
            )

    elif tool == "read_file":
        path = str(target.get("path", ""))
        if ".." in path or path.startswith(("/etc", "/root", "C:\\Windows")):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason=f"Schema Validation Failed (OWASP LLM05): Path traversal attack pattern detected in target path ('{path}').",
                metadata={"tool": tool, "error": "PATH_TRAVERSAL_DETECTED"}
            )

    return CheckResult(
        passed=True,
        status="PASS",
        reason="Schema Validation Passed (OWASP LLM05): All tool parameters conform to safe schema requirements.",
        metadata={"tool": tool, "schema_valid": True}
    )

class ToolSchemaValidator:
    validate = staticmethod(validate_tool_arguments)

schema_validator = ToolSchemaValidator()
