import hashlib
import json
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.schemas.action import ProposedAction
from app.models.action import ActionContract, ProvenanceInfo, ProvenanceSource
from app.models.decision import DecisionOutcome, ValidationReport
from app.models.audit import AuditRecord
from app.core.decision_engine import decision_engine
from app.schemas.tool_schemas import schema_validator
from app.database.connection import audit_db
from app.api.execution import dispatch_tool_execution
from app.guardrails.normalize import inspect_text

def compute_args_hash(arguments: Dict[str, Any]) -> str:
    """Computes a deterministic hash of action arguments for tamper-proof binding."""
    canonical = json.dumps(arguments, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def proposed_action_to_contract(action: ProposedAction) -> ActionContract:
    """Adapts ProposedAction into internal ActionContract."""
    tool_map = {
        "create_ticket": "create_support_ticket",
        "issue_refund": "refund_payment",
        "delete_record": "execute_sql"
    }
    tool_name = tool_map.get(action.tool_name, action.tool_name)

    # Map sources
    source_map = {
        "user": ProvenanceSource.USER,
        "trusted_application": ProvenanceSource.SYSTEM,
        "external_content": ProvenanceSource.UNTRUSTED_DOCUMENT,
        "tool_output": ProvenanceSource.THIRD_PARTY_TOOL,
        "external_web": ProvenanceSource.EXTERNAL_WEB,
        "untrusted_document": ProvenanceSource.UNTRUSTED_DOCUMENT
    }
    prov_source = source_map.get(action.source, ProvenanceSource.USER)
    trusted = action.source in ["user", "trusted_application"]

    return ActionContract(
        action_id=action.action_id,
        agent="EnterpriseAgent",
        user=action.user_id,
        role="finance_operator" if action.user_role in ["support", "user"] else "db_administrator",
        intent=f"execute_{action.tool_name}",
        tool=tool_name,
        target=action.arguments,
        environment=action.environment,
        provenance=ProvenanceInfo(
            source=prov_source,
            trusted=trusted,
            input_text=action.original_request
        ),
        user_prompt=action.original_request
    )

class MandatoryInterceptor:
    """
    Mandatory Execution Interceptor (OWASP LLM06 Excessive Agency defense).
    Enforces server-side validation, fail-closed evaluation, and tamper-proof approval binding.
    """
    async def validate_and_execute(
        self,
        action: ProposedAction,
        supervisor_token: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Inspect text for adversarial Unicode manipulation (arXiv:2504.09559)
        text_inspection = inspect_text(action.original_request)

        # 2. Validate action schema and tool arguments
        contract = proposed_action_to_contract(action)
        schema_result = schema_validator.validate(contract)
        if not schema_result.passed:
            record = self._record_rejection(contract, "Schema validation failed", DecisionOutcome.BLOCK)
            return {
                "decision": "BLOCK",
                "status": "BLOCKED",
                "reason": schema_result.reason,
                "action_id": action.action_id
            }

        # 3. Evaluate through Decision Engine (OPA Rego, Qualcomm AI, Risk, Provenance)
        report: ValidationReport = await decision_engine.evaluate_action(contract)

        # If suspicious Unicode formatting detected, escalate ALLOW to REVIEW
        if text_inspection["needs_review"] and report.decision == DecisionOutcome.ALLOW:
            report.decision = DecisionOutcome.REVIEW
            report.explanation = (
                f"{report.explanation} [Suspicious Unicode/Invisible Format Characters Detected: "
                f"{', '.join(c['codepoint'] for c in text_inspection['suspicious_characters'])}; escalated to HUMAN_REVIEW]"
            )

        args_hash = compute_args_hash(action.arguments)

        # 4. Handle Decision Outcomes
        if report.decision == DecisionOutcome.BLOCK:
            record = self._record_rejection(contract, report.explanation, DecisionOutcome.BLOCK)
            return {
                "decision": "BLOCK",
                "status": "BLOCKED",
                "reason": report.explanation,
                "action_id": action.action_id
            }

        if report.decision == DecisionOutcome.REVIEW:
            # Check if this exact action was already approved and verify argument integrity
            existing = audit_db.get_record(action.action_id)
            if not existing or existing.execution_status != "PENDING_EXECUTION" or not existing.approved_by:
                record = AuditRecord(
                    action_id=action.action_id,
                    user=action.user_id,
                    agent="EnterpriseAgent",
                    role=action.user_role,
                    intent=contract.intent,
                    tool=contract.tool,
                    target=action.arguments,
                    environment=action.environment,
                    action_contract=contract,
                    validation_report=report,
                    decision=DecisionOutcome.REVIEW,
                    execution_status="PENDING_REVIEW",
                    notes=f"ARGS_HASH:{args_hash}"
                )
                audit_db.save_record(record)
                return {
                    "decision": "HUMAN_REVIEW",
                    "status": "AWAITING_APPROVAL",
                    "reason": report.explanation,
                    "action_id": action.action_id,
                    "arguments_hash": args_hash
                }

            # Human Approval Tamper Verification (Anti-Tampering Gate)
            expected_hash_marker = f"ARGS_HASH:{args_hash}"
            if expected_hash_marker not in (existing.notes or ""):
                existing.execution_status = "REJECTED_TAMPERED"
                audit_db.save_record(existing)
                return {
                    "decision": "BLOCK",
                    "status": "BLOCKED",
                    "reason": "Argument Tampering Detected: Action arguments were modified after human approval. Execution rejected. Fresh validation required.",
                    "action_id": action.action_id
                }

        # 4. Execute only through the approved sandboxed tool registry
        try:
            tool_result = await dispatch_tool_execution(contract)
            record = AuditRecord(
                action_id=action.action_id,
                user=action.user_id,
                agent="EnterpriseAgent",
                role=action.user_role,
                intent=contract.intent,
                tool=contract.tool,
                target=action.arguments,
                environment=action.environment,
                action_contract=contract,
                validation_report=report,
                decision=DecisionOutcome.ALLOW,
                execution_status="EXECUTED",
                execution_result=tool_result,
                notes=f"ARGS_HASH:{args_hash}"
            )
            audit_db.save_record(record)
            return {
                "decision": "ALLOW",
                "status": "EXECUTED",
                "result": tool_result,
                "action_id": action.action_id
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

    def _record_rejection(self, contract: ActionContract, reason: str, outcome: DecisionOutcome) -> AuditRecord:
        record = AuditRecord(
            action_id=contract.action_id,
            user=contract.user,
            agent=contract.agent,
            role=contract.role,
            intent=contract.intent,
            tool=contract.tool,
            target=contract.target,
            environment=contract.environment,
            action_contract=contract,
            decision=outcome,
            execution_status="BLOCKED"
        )
        audit_db.save_record(record)
        return record

interceptor = MandatoryInterceptor()
