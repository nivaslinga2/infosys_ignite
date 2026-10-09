from fastapi import APIRouter, HTTPException
from typing import List
from app.models.agent import AgentProposalRequest, AgentProposalResponse, AgentProfile
from app.ai.intent_parser import intent_parser

router = APIRouter(prefix="/api/agent", tags=["Agent"])

AGENT_PROFILES = [
    AgentProfile(
        id="FinanceAgent",
        name="Qualcomm Autonomous Finance Agent",
        role="finance_operator",
        allowed_tools=["refund_payment", "transfer_funds", "get_customer_details"],
        description="Handles customer refunds and settlements within strict fiscal guardrails."
    ),
    AgentProfile(
        id="DatabaseOpsAgent",
        name="Qualcomm Cloud Infrastructure Agent",
        role="db_administrator",
        allowed_tools=["execute_sql", "read_file"],
        description="Autonomous operations agent for database telemetry and maintenance."
    ),
    AgentProfile(
        id="SupportAgent",
        name="Customer Experience Agent",
        role="support_operator",
        allowed_tools=["create_support_ticket", "send_email", "get_customer_details"],
        description="Customer ticket management and notification operations."
    )
]

@router.get("/profiles", response_model=List[AgentProfile])
async def get_profiles():
    return AGENT_PROFILES

@router.post("/propose", response_model=AgentProposalResponse)
async def propose_action(request: AgentProposalRequest):
    """
    Qualcomm AI Agent reasons on the user's intent and produces an action proposal.
    Notice: The tool is NEVER executed at this stage.
    """
    try:
        proposal = await intent_parser.plan_agent_proposal(request)
        return proposal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent proposal generation failed: {str(e)}")
