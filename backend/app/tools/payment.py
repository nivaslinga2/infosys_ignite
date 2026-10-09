from typing import Dict, Any

class PaymentTool:
    @staticmethod
    def refund_payment(customer_id: str, amount: float, reason: str = "Customer request") -> Dict[str, Any]:
        """
        Executes customer refund. Side effect: initiates financial ledger reversal.
        """
        return {
            "status": "SUCCESS",
            "transaction_id": f"TXN-REF-{customer_id}-992",
            "tool": "refund_payment",
            "customer_id": customer_id,
            "amount_refunded": amount,
            "currency": "INR",
            "message": f"Successfully initiated refund of ₹{amount:,.2f} for customer {customer_id}.",
            "reversible_until_hours": 24
        }

    @staticmethod
    def transfer_funds(account_id: str, amount: float) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "transaction_id": f"TXN-TRF-{account_id}-551",
            "tool": "transfer_funds",
            "account_id": account_id,
            "amount": amount,
            "message": f"Transferred ₹{amount:,.2f} to {account_id}."
        }
