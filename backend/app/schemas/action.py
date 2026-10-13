import hashlib
import json
from typing import Any, Literal, Dict
from pydantic import BaseModel, Field

class ProposedAction(BaseModel):
    action_id: str = Field(..., description="Unique action identifier")
    user_id: str = Field(..., description="User requesting action")
    user_role: Literal["user", "support", "admin"] = Field(default="user")
    original_request: str = Field(..., description="Raw user prompt")
    tool_name: Literal[
        "create_ticket",
        "issue_refund",
        "delete_record",
        "refund_payment",
        "create_support_ticket",
        "execute_sql",
        "transfer_funds",
        "get_customer_details",
        "send_email",
        "read_file",
        "export_data"
    ]
    arguments: Dict[str, Any] = Field(default_factory=dict)
    target: str = Field(default="")
    source: Literal[
        "user",
        "trusted_application",
        "external_content",
        "tool_output",
        "external_web",
        "untrusted_document"
    ] = Field(default="user")
    environment: Literal["test", "production"] = Field(default="production")
    data_sensitivity: Literal["public", "internal", "confidential"] = Field(default="internal")
    reversibility_level: Literal["R0", "R1", "R2", "R3"] = Field(default="R1")

    def compute_arguments_hash(self) -> str:
        """Computes deterministic SHA-256 hash of arguments to prevent post-approval tampering."""
        canonical_json = json.dumps(self.arguments, sort_keys=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
