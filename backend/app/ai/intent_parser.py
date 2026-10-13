import re
from typing import Dict, Any, Tuple
from app.ai.qualcomm_client import qualcomm_client
from app.models.agent import AgentProposalRequest, AgentProposalResponse

class IntentParser:
    def __init__(self):
        self.qc = qualcomm_client

    async def plan_agent_proposal(self, req: AgentProposalRequest) -> AgentProposalResponse:
        prompt = req.user_prompt.strip()
        lower = prompt.lower()
        proposal_id = f"PROP-{abs(hash(prompt)) % 90000 + 10000}"

        if "refund" in lower:
            amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.[0-9]{2})?)', prompt, re.IGNORECASE)
            amount = 5000.0
            if amount_match:
                try:
                    amount_str = amount_match.group(1).replace(",", "")
                    if amount_str:
                        amount = float(amount_str)
                except ValueError:
                    amount = 5000.0

            cust_match = re.search(r'(?:customer\s+|c)([0-9a-zA-Z]+)', prompt, re.IGNORECASE)
            cust_id = cust_match.group(0).replace("customer", "").strip() if cust_match else "C1024"
            if not cust_id.startswith("C"):
                cust_id = f"C{cust_id}"

            thought = f"Identified refund request for customer {cust_id} with amount ₹{amount:,.2f}. Proposing refund_payment tool."
            telemetry = self.qc.get_device_telemetry(latency_ms=21.4)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="refund_customer",
                tool="refund_payment",
                target={"customer": cust_id, "amount": amount, "reason": "User requested refund"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        elif any(k in lower for k in ["delete", "drop", "truncate", "database"]):
            query = "DELETE FROM customers WHERE active = 0;" if "where" in lower else "DELETE FROM customers;"
            if "drop" in lower:
                query = "DROP TABLE transactions;"
            thought = f"Identified database maintenance request. Proposing execute_sql tool."
            telemetry = self.qc.get_device_telemetry(latency_ms=18.6)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="manage_database",
                tool="execute_sql",
                target={"query": query, "database": "production_db"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        elif "export" in lower or "send database" in lower:
            dest = "attacker@example.com" if "attacker" in lower else "analytics-dump.s3.internal"
            thought = f"Data export request detected. Proposing export_data to {dest}."
            telemetry = self.qc.get_device_telemetry(latency_ms=19.8)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="export_customer_data",
                tool="export_data",
                target={"dataset_name": "customer_pii_dump", "destination_url": dest},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        elif any(k in lower for k in ["ticket", "issue", "support"]):
            title = prompt[:50]
            thought = "Standard support ticket request. Proposing create_support_ticket tool."
            telemetry = self.qc.get_device_telemetry(latency_ms=16.2)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="create_ticket",
                tool="create_support_ticket",
                target={"title": title, "description": prompt, "priority": "medium"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        thought = "Read request. Proposing get_customer_details tool."
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
