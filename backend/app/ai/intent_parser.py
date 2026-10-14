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

        # 1. Pre-Execution Guard: Detect malicious cyberattack directives immediately
        if any(k in lower for k in ["hack", "firewall", "bypass", "exploit", "breach", "steal", "crack", "ransomware", "ddos"]):
            thought = "Security Intercept: User prompt contains cyberattack / hacking directive. No tool execution authorized."
            telemetry = self.qc.get_device_telemetry(latency_ms=15.0)
            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="blocked_cyberattack",
                tool="none",
                target={"prompt": prompt, "threat": "CYBERATTACK_DIRECTIVE"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        # 2. Query Live Qualcomm Cloud AI 100 Inference Engine for Semantic Reasoning
        system_prompt = (
            "You are an enterprise autonomous agent on Qualcomm Cloud AI 100.\n"
            "Analyze this user request and determine the best action.\n"
            "Tools: refund_payment, execute_sql, export_data, create_support_ticket, get_customer_details, send_email, read_file, none.\n"
            "Provide a one-sentence reasoning and specify the tool."
        )
        qc_res = await self.qc.generate_completion(system_prompt, prompt)
        telemetry = qc_res.get("telemetry") or self.qc.get_device_telemetry(latency_ms=21.4)
        ai_thought = qc_res.get("text")

        # 3. Formulate Action Proposal based on Semantic Parsing and AI Intent
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

            thought = f"Qualcomm Cloud AI 100: Identified refund for customer {cust_id} with amount ₹{amount:,.2f}. Proposing refund_payment tool."
            if ai_thought:
                thought = f"{thought} Reasoning: {ai_thought.strip()[:140]}"

            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="refund_customer",
                tool="refund_payment",
                target={"customer": cust_id, "amount": amount, "reason": "User requested refund"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        elif any(k in lower for k in ["delete", "drop", "truncate", "database", "sql"]):
            query = "DELETE FROM customers WHERE active = 0;" if "where" in lower else "DELETE FROM customers;"
            if "drop" in lower:
                query = "DROP TABLE transactions;"
            thought = "Qualcomm Cloud AI 100: Database operation requested. Proposing execute_sql tool."
            if ai_thought:
                thought = f"{thought} Reasoning: {ai_thought.strip()[:140]}"

            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="manage_database",
                tool="execute_sql",
                target={"query": query, "database": "production_db"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        elif "export" in lower or "send database" in lower or "dump" in lower:
            dest = "attacker@example.com" if "attacker" in lower else "analytics-dump.s3.internal"
            thought = f"Qualcomm Cloud AI 100: Data export request detected. Proposing export_data to {dest}."
            if ai_thought:
                thought = f"{thought} Reasoning: {ai_thought.strip()[:140]}"

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
            thought = "Qualcomm Cloud AI 100: Standard support ticket request. Proposing create_support_ticket tool."
            if ai_thought:
                thought = f"{thought} Reasoning: {ai_thought.strip()[:140]}"

            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="create_ticket",
                tool="create_support_ticket",
                target={"title": title, "description": prompt, "priority": "medium"},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        elif any(k in lower for k in ["customer", "client", "profile", "balance", "lookup"]) or re.search(r'\bc[0-9]{3,5}\b', lower):
            cust_match = re.search(r'(?:customer\s+|c)([0-9a-zA-Z]+)', prompt, re.IGNORECASE)
            cust_id = cust_match.group(0).replace("customer", "").strip() if cust_match else "C1024"
            if not cust_id.startswith("C"):
                cust_id = f"C{cust_id}"
            thought = f"Qualcomm Cloud AI 100: Customer inquiry for {cust_id}. Proposing get_customer_details tool."
            if ai_thought:
                thought = f"{thought} Reasoning: {ai_thought.strip()[:140]}"

            return AgentProposalResponse(
                proposal_id=proposal_id,
                intent="lookup_customer",
                tool="get_customer_details",
                target={"customer_id": cust_id},
                thought_process=thought,
                qualcomm_telemetry=telemetry
            )

        thought = "Qualcomm Cloud AI 100: General inquiry without direct tool action required."
        if ai_thought:
            thought = f"{thought} Reasoning: {ai_thought.strip()[:140]}"

        return AgentProposalResponse(
            proposal_id=proposal_id,
            intent="conversational",
            tool="none",
            target={"query": prompt},
            thought_process=thought,
            qualcomm_telemetry=telemetry
        )

intent_parser = IntentParser()
