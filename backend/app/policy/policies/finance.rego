package agentshield.finance

default allow = false
default review = false
default block = false
default reason = "No matching finance rule"

# Rule 1: Autonomous refund limit for finance_operator (<= 5,000 INR)
allow {
    input.tool == "refund_payment"
    input.amount <= 5000
    input.role == "finance_operator"
}

# Rule 2: Escalation to Human Review (> 5,000 and <= 50,000 INR)
review {
    input.tool == "refund_payment"
    input.amount > 5000
    input.amount <= 50000
}

# Rule 3: Hard Block (> 50,000 INR)
block {
    input.tool == "refund_payment"
    input.amount > 50000
}

# Rule 4: Fund transfers limits
allow {
    input.tool == "transfer_funds"
    input.amount <= 20000
    input.role == "finance_operator"
}

review {
    input.tool == "transfer_funds"
    input.amount > 20000
    input.amount <= 100000
}

block {
    input.tool == "transfer_funds"
    input.amount > 100000
}
