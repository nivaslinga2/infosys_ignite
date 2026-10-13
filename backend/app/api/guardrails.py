import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.guardrails.pii import pii_engine, pii_vault
from app.guardrails.content_safety import content_safety_engine
from app.guardrails.topic_control import topic_control_engine
from app.guardrails.jailbreak import jailbreak_guard
from app.guardrails.orchestrator import guardrails_orchestrator
from app.models.decision import CheckResult

router = APIRouter(prefix="/api/guardrails", tags=["Guardrails (NeMo Suite)"])

class PIIMaskRequest(BaseModel):
    text: str = Field(..., description="Raw text containing potential PII")
    vault_id: Optional[str] = Field(default=None, description="Optional session vault ID")
    redact_only: bool = Field(default=False, description="Replace with [REDACTED_TYPE] instead of token")

class PIIUnmaskRequest(BaseModel):
    masked_text: str
    vault_id: str

class TextCheckRequest(BaseModel):
    text: str

@router.post("/pii/mask")
async def mask_pii(request: PIIMaskRequest):
    try:
        vault_id = request.vault_id or f"vault-{uuid.uuid4().hex[:8]}"
        masked_text, token_vault, detected = pii_engine.mask_text(
            text=request.text,
            vault_id=vault_id,
            redact_only=request.redact_only
        )
        return {
            "vault_id": vault_id,
            "masked_text": masked_text,
            "detected_entities": detected,
            "count": len(detected),
            "tokens_stored": list(token_vault.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pii/unmask")
async def unmask_pii(request: PIIUnmaskRequest):
    try:
        unmasked = pii_engine.unmask_text(request.masked_text, request.vault_id)
        return {"unmasked_text": unmasked}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content-safety/check", response_model=CheckResult)
async def check_content_safety(request: TextCheckRequest):
    try:
        return await content_safety_engine.evaluate_text(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/topic/check", response_model=CheckResult)
async def check_topic_control(request: TextCheckRequest):
    try:
        return topic_control_engine.evaluate_text(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jailbreak/check", response_model=CheckResult)
async def check_jailbreak(request: TextCheckRequest):
    try:
        return jailbreak_guard.evaluate_text(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inspect-all")
async def inspect_all_guardrails(request: TextCheckRequest):
    try:
        return await guardrails_orchestrator.inspect_prompt(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
