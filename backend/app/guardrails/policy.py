from app.policy.opa_client import opa_client, OPAClient

def check_policy(action_contract):
    """Evaluates declarative OPA / Rego policy rules."""
    return opa_client.evaluate(action_contract)

__all__ = ["opa_client", "OPAClient", "check_policy"]
