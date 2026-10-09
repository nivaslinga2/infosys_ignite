package agentshield.database

default allow = false
default review = false
default block = false
default reason = "Default database safety policy"

# Rule 1: Read-only queries or customer lookups are allowed
allow {
    input.tool == "get_customer_details"
}

allow {
    input.tool == "execute_sql"
    startswith(lower(input.query), "select")
}

# Rule 2: Hard Block on destructive DDL or bulk DELETE operations in production
block {
    input.tool == "execute_sql"
    contains(lower(input.query), "delete")
    input.environment == "production"
}

block {
    input.tool == "execute_sql"
    contains(lower(input.query), "drop")
}

block {
    input.tool == "execute_sql"
    contains(lower(input.query), "truncate")
}

# Rule 3: Updates require review
review {
    input.tool == "execute_sql"
    contains(lower(input.query), "update")
}
