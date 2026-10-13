from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum

class DecisionOutcome(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"

class ReversibilityTier(str, Enum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"

class SemanticClassification(BaseModel):
    category: str
    sensitivity: str
    destructive: bool
    external_side_effect: bool
    bulk_operation: bool = False
    details: str = ""

class CheckResult(BaseModel):
    passed: bool
    status: str
    score: Optional[float] = None
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ValidationReport(BaseModel):
    action_id: str
    ai_semantic: CheckResult
    authorization: CheckResult
    risk_assessment: CheckResult
    reversibility: CheckResult
    intent_alignment: CheckResult
    provenance: CheckResult
    content_safety: Optional[CheckResult] = None
    topic_control: Optional[CheckResult] = None
    pii_assessment: Optional[CheckResult] = None
    jailbreak_defense: Optional[CheckResult] = None
    composite_risk_score: float
    risk_level: str
    reversibility_tier: ReversibilityTier
    decision: DecisionOutcome
    explanation: str
    qualcomm_telemetry: Dict[str, Any] = Field(default_factory=dict)

