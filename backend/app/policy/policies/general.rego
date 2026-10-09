package agentshield.general

default allow = false
default review = false
default block = false
default reason = "General policy baseline"

# Rule 1: Safe ticketing and file reads are allowed
allow {
    input.tool == "create_support_ticket"
}

allow {
    input.tool == "read_file"
}

# Rule 2: Routine email communications
allow {
    input.tool == "send_email"
    input.trusted == true
}

# Rule 3: Blocking data exfiltration or untrusted exports
block {
    input.tool == "export_data"
    input.trusted == false
}

review {
    input.tool == "export_data"
    input.trusted == true
}
