from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.models.action import ActionContract
from app.models.decision import ValidationReport, DecisionOutcome

class HumanApprovalRequest(BaseModel):
    action_id: str
    approved: bool
    reviewer: str = "manager_21"
    review_notes: Optional[str] = "Approved after reviewing transaction limit and blast radius."

class AuditRecord(BaseModel):
    action_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user: str
    agent: str
    role: str
    intent: str
    tool: str
    target: Dict[str, Any]
    environment: str
    action_contract: ActionContract
    validation_report: Optional[ValidationReport] = None
    decision: DecisionOutcome
    approved_by: Optional[str] = None
    approval_timestamp: Optional[str] = None
    execution_status: str = "PENDING"
    execution_result: Optional[Dict[str, Any]] = None
    execution_error: Optional[str] = None
    notes: Optional[str] = None
    arguments_hash: Optional[str] = None

