from app.core.intent_alignment import evaluate_intent, IntentAlignmentEngine, intent_alignment_engine

def assess_intent(action_contract):
    """Compares proposed action against original user intent."""
    return intent_alignment_engine.evaluate(action_contract)

__all__ = ["evaluate_intent", "IntentAlignmentEngine", "intent_alignment_engine", "assess_intent"]
