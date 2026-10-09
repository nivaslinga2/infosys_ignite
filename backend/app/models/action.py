from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum

class ProvenanceSource(str, Enum):
    USER = "user"
    SYSTEM = "system"
    EXTERNAL_WEB = "external_web"
    UNTRUSTED_DOCUMENT = "untrusted_document"
    THIRD_PARTY_TOOL = "third_party_tool"

class ProvenanceInfo(BaseModel):
    source: ProvenanceSource = ProvenanceSource.USER
    trusted: bool = True
    context_url: Optional[str] = None
    input_text: Optional[str] = None

class ActionContract(BaseModel):
    action_id: str = Field(..., description="Unique action identifier e.g. ACT-001")
    agent: str = Field(..., description="Agent identifier e.g. FinanceAgent")
    user: str = Field(..., description="User identifier e.g. employee_42")
    role: str = Field(default="operator", description="User/Agent operational role")
    intent: str = Field(..., description="High-level intent e.g. refund_customer")
    tool: str = Field(..., description="Target tool identifier e.g. refund_payment")
    target: Dict[str, Any] = Field(default_factory=dict, description="Tool execution payload and targets")
    environment: str = Field(default="production", description="Environment e.g. production, staging")
    provenance: ProvenanceInfo = Field(default_factory=ProvenanceInfo, description="Provenance metadata")
    user_prompt: Optional[str] = Field(default=None, description="Original user prompt for intent alignment")
