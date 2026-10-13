import asyncio
from typing import Dict, Any, Optional
from app.models.action import ActionContract
from app.models.decision import CheckResult
from app.guardrails.pii import pii_engine
from app.guardrails.content_safety import content_safety_engine
from app.guardrails.topic_control import topic_control_engine
from app.guardrails.jailbreak import jailbreak_guard

class InputSecurityOrchestrator:
    """
    AgentShield Custom Input Security & Guardrails Suite:
    1. Content Safety (Toxicity, Violence, Hate Speech, Cyberattacks)
    2. Jailbreak & Prompt Injection Defense (Adversarial signatures & Unicode normalization)
    3. Topic Control (Enterprise Domain Boundaries)
    4. PII Detection & Reversible Session Token Vault
    """
    def __init__(self):
        self.pii = pii_engine
        self.safety = content_safety_engine
        self.topic = topic_control_engine
        self.jailbreak = jailbreak_guard

    async def evaluate_all(self, contract: ActionContract) -> Dict[str, CheckResult]:
        """Runs all 4 custom guardrails against the action contract."""
        safety_task = self.safety.evaluate(contract)
        topic_res = self.topic.evaluate(contract)
        jailbreak_res = self.jailbreak.evaluate(contract)
        pii_res = self.pii.evaluate(contract)

        safety_res = await safety_task

        return {
            "content_safety": safety_res,
            "topic_control": topic_res,
            "jailbreak_protection": jailbreak_res,
            "pii_assessment": pii_res
        }

    async def inspect_prompt(self, prompt: str, vault_id: Optional[str] = None) -> Dict[str, Any]:
        """Inspects raw text across all guardrails (for direct agent chat input inspection)."""
        safety_res = await self.safety.evaluate_text(prompt)
        topic_res = self.topic.evaluate_text(prompt)
        jb_res = self.jailbreak.evaluate_text(prompt)
        masked_text, vault, detected_pii = self.pii.mask_text(prompt, vault_id=vault_id)

        all_passed = safety_res.passed and topic_res.passed and jb_res.passed

        return {
            "passed": all_passed,
            "content_safety": safety_res.dict(),
            "topic_control": topic_res.dict(),
            "jailbreak_protection": jb_res.dict(),
            "pii": {
                "detected": detected_pii,
                "masked_text": masked_text,
                "vault_count": len(vault)
            }
        }

guardrails_orchestrator = InputSecurityOrchestrator()
GuardrailsOrchestrator = InputSecurityOrchestrator
