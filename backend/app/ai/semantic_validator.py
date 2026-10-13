import json
from typing import Dict, Any
from app.ai.qualcomm_client import qualcomm_client
from app.models.action import ActionContract
from app.models.decision import CheckResult, SemanticClassification

class SemanticValidator:
    def __init__(self):
        self.qc = qualcomm_client

    async def validate_semantics(self, contract: ActionContract) -> CheckResult:
        tool = contract.tool
        target = contract.target
        amount = float(target.get("amount", 0.0))
        query = str(target.get("query", ""))

        system_prompt = (
            "You are Qualcomm AI Semantic Validator. Analyze the proposed agent tool call.\n"
            "Return JSON with: category (financial|database|communication|system),\n"
            "sensitivity (low|medium|high|critical), destructive (bool), external_side_effect (bool), details (str)."
        )
        user_prompt = f"Tool: {tool}, Target payload: {json.dumps(target)}, Environment: {contract.environment}"

        qc_response = await self.qc.generate_completion(system_prompt, user_prompt)
        
        category = "system"
        sensitivity = "low"
        destructive = False
        external_side_effect = False
        bulk = False
        details = ""

        if tool in ["refund_payment", "transfer_funds"]:
            category = "financial"
            external_side_effect = True
            if amount > 50000:
                sensitivity = "critical"
                details = f"Large-scale capital outflow (₹{amount:,.2f}) detected."
            elif amount > 5000:
                sensitivity = "high"
                details = f"Substantial financial transaction (₹{amount:,.2f}) with fiscal impact."
            else:
                sensitivity = "medium"
                details = f"Routine micro-financial transaction (₹{amount:,.2f})."

        elif tool == "execute_sql":
            category = "database"
            lower_q = query.lower()
            if any(k in lower_q for k in ["delete", "drop", "truncate"]):
                destructive = True
                sensitivity = "critical"
                bulk = True
                details = f"Destructive database query targeting persistent schema or tables: '{query[:45]}'."
            elif "update" in lower_q:
                sensitivity = "high"
                details = f"State-modifying SQL UPDATE statement: '{query[:45]}'."
            else:
                sensitivity = "low"
                details = "Read-only analytical SQL query."

        elif tool == "export_data":
            category = "data_management"
            external_side_effect = True
            sensitivity = "high"
            details = f"Data export towards destination: {target.get('destination_url', 'external')}."

        elif tool in ["send_email", "create_support_ticket"]:
            category = "communication"
            external_side_effect = True
            sensitivity = "low" if tool == "create_support_ticket" else "medium"
            details = "Outbound dispatch of communication payload."

        elif tool == "read_file":
            category = "filesystem"
            sensitivity = "low"
            details = "Read-only file retrieval operation."

        status = "PASS"
        passed = True
        if sensitivity == "critical" or destructive:
            status = "FAIL"
            passed = False
        elif sensitivity == "high":
            status = "WARN"
            passed = True

        classification = SemanticClassification(
            category=category,
            sensitivity=sensitivity,
            destructive=destructive,
            external_side_effect=external_side_effect,
            bulk_operation=bulk,
            details=details
        )

        return CheckResult(
            passed=passed,
            status=status,
            reason=f"Qualcomm AI Semantic Analysis: {category.upper()} operation with {sensitivity.upper()} sensitivity. {details}",
            metadata={
                "classification": classification.model_dump(),
                "telemetry": qc_response["telemetry"]
            }
        )

semantic_validator = SemanticValidator()
