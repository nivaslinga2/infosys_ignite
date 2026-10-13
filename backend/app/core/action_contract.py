import uuid
from typing import Dict, Any, Optional
from app.models.action import ActionContract, ProvenanceInfo, ProvenanceSource

def build_contract(
    tool: str,
    target: Dict[str, Any],
    intent: str = "general_operation",
    agent: str = "FinanceAgent",
    user: str = "employee_42",
    role: str = "finance_operator",
    environment: str = "production",
    provenance_source: str = "user",
    trusted: bool = True,
    provenance_url: Optional[str] = None,
    user_prompt: Optional[str] = None,
    action_id: Optional[str] = None
) -> ActionContract:
    if not action_id:
        action_id = f"ACT-{uuid.uuid4().hex[:6].upper()}"

    try:
        source_enum = ProvenanceSource(provenance_source)
    except ValueError:
        source_enum = ProvenanceSource.USER

    provenance = ProvenanceInfo(
        source=source_enum,
        trusted=trusted,
        context_url=provenance_url,
        input_text=user_prompt
    )

    return ActionContract(
        action_id=action_id,
        agent=agent,
        user=user,
        role=role,
        intent=intent,
        tool=tool,
        target=target,
        environment=environment,
        provenance=provenance,
        user_prompt=user_prompt
    )

class ActionContractBuilder:
    build_contract = staticmethod(build_contract)

contract_builder = ActionContractBuilder()
