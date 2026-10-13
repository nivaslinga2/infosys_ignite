from fastapi import APIRouter, HTTPException
from typing import List
from app.models.agent import AgentProposalRequest, AgentProposalResponse, AgentProfile
from app.ai.intent_parser import intent_parser

router = APIRouter(prefix="/api/agent", tags=["Agent"])

AGENT_PROFILES = [
    AgentProfile(
        id="FinanceAgent",
        name="Finance Agent",
        role="finance_operator",
        allowed_tools=["refund_payment", "transfer_funds", "get_customer_details"],
        description="Processes refunds and settlements within predefined fiscal policy limits."
    ),
    AgentProfile(
        id="DatabaseOpsAgent",
        name="Database Operations Agent",
        role="db_administrator",
        allowed_tools=["execute_sql", "read_file"],
        description="Handles database maintenance tasks and telemetry queries."
    ),
    AgentProfile(
        id="SupportAgent",
        name="Customer Support Agent",
        role="support_operator",
        allowed_tools=["create_support_ticket", "send_email", "get_customer_details"],
        description="Manages customer ticket creation and notification workflows."
    )
]

@router.get("/profiles", response_model=List[AgentProfile])
async def get_profiles():
    return AGENT_PROFILES

@router.post("/propose", response_model=AgentProposalResponse)
async def propose_action(request: AgentProposalRequest):
    try:
        return await intent_parser.plan_agent_proposal(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proposal generation failed: {str(e)}")
