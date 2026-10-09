from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum

class DecisionOutcome(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"

class ReversibilityTier(str, Enum):
    R1 = "R1"  # Easily reversible (e.g. create draft, ticket)
    R2 = "R2"  # Reversible with effort/window (e.g. payment refund within 24h)
    R3 = "R3"  # Irreversible / Destructive (e.g. database drop, permanent wipe)

class SemanticClassification(BaseModel):
    category: str
    sensitivity: str  # low, medium, high, critical
    destructive: bool
    external_side_effect: bool
    bulk_operation: bool = False
    details: str = ""

class CheckResult(BaseModel):
    passed: bool
    status: str  # PASS, WARN, FAIL
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
    composite_risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    reversibility_tier: ReversibilityTier
    decision: DecisionOutcome
    explanation: str
    qualcomm_telemetry: Dict[str, Any] = Field(default_factory=dict)
