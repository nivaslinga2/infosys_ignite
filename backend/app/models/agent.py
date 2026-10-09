from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class AgentProfile(BaseModel):
    id: str = Field(..., description="Agent identifier e.g. FinanceAgent")
    name: str = Field(..., description="Display name e.g. Qualcomm Autonomous Finance Agent")
    role: str = Field(..., description="Role e.g. finance_operator")
    allowed_tools: List[str] = Field(default_factory=list)
    description: str = Field(default="")

class AgentProposalRequest(BaseModel):
    user_id: str = Field(default="employee_42")
    user_prompt: str = Field(..., description="User prompt or instruction")
    agent_id: str = Field(default="FinanceAgent")
    environment: str = Field(default="production")
    provenance_source: str = Field(default="user")
    trusted: bool = Field(default=True)
    provenance_url: Optional[str] = None
    role: Optional[str] = None

class AgentProposalResponse(BaseModel):
    proposal_id: str
    intent: str
    tool: str
    target: Dict[str, Any]
    thought_process: str
    qualcomm_telemetry: Dict[str, Any]
