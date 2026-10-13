from app.models.action import ActionContract
from app.models.decision import CheckResult, ReversibilityTier

def evaluate_reversibility(contract: ActionContract) -> CheckResult:
    tool = contract.tool
    target = contract.target
    query = str(target.get("query", "")).lower()

    if tool == "execute_sql":
        if any(k in query for k in ["drop", "truncate", "delete"]):
            return CheckResult(
                passed=False,
                status="FAIL",
                reason="R3 (Irreversible): Permanent data/schema destruction. Cannot be rolled back automatically.",
                metadata={"tier": ReversibilityTier.R3.value, "rollback_window": "None", "undoable": False}
            )
        elif "update" in query:
            return CheckResult(
                passed=True,
                status="WARN",
                reason="R2 (Partially Reversible): Record updates require compensating transaction or rollback script.",
                metadata={"tier": ReversibilityTier.R2.value, "rollback_window": "Snapshot dependent", "undoable": True}
            )
        else:
            return CheckResult(
                passed=True,
                status="PASS",
                reason="R1 (Reversible): Read-only query has zero side-effects on persistent state.",
                metadata={"tier": ReversibilityTier.R1.value, "rollback_window": "N/A", "undoable": True}
            )

    if tool in ["refund_payment", "transfer_funds"]:
        return CheckResult(
            passed=True,
            status="WARN",
            reason="R2 (Reversible): Financial transaction can be counter-settled or reversed within a 24-hour clearing window.",
            metadata={"tier": ReversibilityTier.R2.value, "rollback_window": "24 hours", "undoable": True}
        )

    if tool == "export_data":
        return CheckResult(
            passed=False,
            status="WARN",
            reason="R3 (Irreversible): Data sent externally cannot be revoked once transmitted.",
            metadata={"tier": ReversibilityTier.R3.value, "rollback_window": "None", "undoable": False}
        )

    return CheckResult(
        passed=True,
        status="PASS",
        reason="R1 (Reversible/Low Impact): Operation can be cancelled, deleted, or has no adverse persistent footprint.",
        metadata={"tier": ReversibilityTier.R1.value, "rollback_window": "Instant", "undoable": True}
    )

class ReversibilityEngine:
    evaluate = staticmethod(evaluate_reversibility)

reversibility_engine = ReversibilityEngine()
