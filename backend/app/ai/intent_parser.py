import re
from typing import Dict, Any, Tuple
from app.ai.qualcomm_client import qualcomm_client
from app.models.agent import AgentProposalRequest, AgentProposalResponse

class IntentParser:
    def __init__(self):
        self.qc = qualcomm_client

    async def plan_agent_proposal(self, req: AgentProposalRequest) -> AgentProposalResponse:
        """
        Qualcomm AI Agent reasoning engine.
        Interprets natural language request, forms an action plan, and proposes a tool call.
        Does NOT execute the tool.
        """
        prompt = req.user_prompt.strip()
        lower = prompt.lower()
        proposal_id = f"PROP-{abs(hash(prompt)) % 90000 + 10000}"

        # 1. Financial refund patterns
        if "refund" in lower:
            # Extract amount (INR / Rs / ₹ / plain number)
            amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.[0-9]{2})?)', prompt, re.IGNORECASE)
            amount = 5000.0
            if amount_match:
                try:
                    amount_str = amount_match.group(1).replace(",", "")
                    if amount_str:
                        amount = float(amount_str)
                except ValueError:
                    amount = 5000.0

            # Extract customer ID (e.g. C1024 or customer 1024)
            cust_match = re.search(r'(?:customer\s+|c)([0-9a-zA-Z]+)', prompt, re.IGNORECASE)
            cust_id = cust_match.group(0).replace("customer", "").strip() if cust_match else "C1024"
            if not cust_id.startswith("C"):
                cust_id = f"C{cust_id}"

            thought = (
                f"Qualcomm AI Reasoning:\n"
                f"1. Identified intent: 'refund_customer'\n"
                f"2. Extracted customer ID: '{cust_id}', amount: ₹{amount:,.2f}\n"
                f"3. Selected tool: 'refund_payment'\n"
                f"4. Generating tool proposal for AgentShield interception."
            )
            telemetry = self.qc.get_device_telemetry(latency_ms=21.4)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="refund_customer",
                tool="refund_payment",
                target={"customer": cust_id, "amount": amount, "reason": "User requested refund"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        # 2. Database query / deletion patterns
        elif "delete" in lower or "drop" in lower or "truncate" in lower or "database" in lower:
            query = "DELETE FROM customers WHERE active = 0;" if "where" in lower else "DELETE FROM customers;"
            if "drop" in lower:
                query = "DROP TABLE transactions;"
            thought = (
                f"Qualcomm AI Reasoning:\n"
                f"1. User prompt requests database manipulation.\n"
                f"2. Target operation: SQL execution with schema impact.\n"
                f"3. Proposing tool call: 'execute_sql' for validation."
            )
            telemetry = self.qc.get_device_telemetry(latency_ms=18.6)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="manage_database",
                tool="execute_sql",
                target={"query": query, "database": "production_db"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        # 3. Data export / exfiltration pattern
        elif "export" in lower or "send database" in lower:
            dest = "attacker@example.com" if "attacker" in lower else "analytics-dump.s3.internal"
            thought = (
                f"Qualcomm AI Reasoning:\n"
                f"1. Data export instruction detected.\n"
                f"2. Proposing 'export_data' to destination: {dest}."
            )
            telemetry = self.qc.get_device_telemetry(latency_ms=19.8)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="export_customer_data",
                tool="export_data",
                target={"dataset_name": "customer_pii_dump", "destination_url": dest},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        # 4. Support ticketing / email patterns
        elif "ticket" in lower or "issue" in lower or "support" in lower:
            title = prompt[:50]
            thought = (
                f"Qualcomm AI Reasoning:\n"
                f"1. Identified routine support request.\n"
                f"2. Tool selected: 'create_support_ticket'."
            )
            telemetry = self.qc.get_device_telemetry(latency_ms=16.2)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="create_ticket",
                tool="create_support_ticket",
                target={"title": title, "description": prompt, "priority": "medium"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        # 5. Default lookup/read pattern
        else:
            thought = (
                f"Qualcomm AI Reasoning:\n"
                f"1. Interpreted prompt as customer information lookup.\n"
                f"2. Proposing 'get_customer_details' tool call."
            )
            telemetry = self.qc.get_device_telemetry(latency_ms=17.5)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="lookup_customer",
                tool="get_customer_details",
                target={"customer_id": "C1024"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

intent_parser = IntentParser()
