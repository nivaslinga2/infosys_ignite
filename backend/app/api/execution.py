from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.action import ActionContract
from app.models.decision import DecisionOutcome
from app.models.audit import AuditRecord
from app.database.connection import audit_db
from app.tools.payment import PaymentTool
from app.tools.database import DatabaseTool
from app.tools.email import EmailTool
from app.tools.files import FilesTool

router = APIRouter(prefix="/api/execution", tags=["Execution Layer"])

async def dispatch_tool_execution(contract: ActionContract) -> Dict[str, Any]:
    tool = contract.tool
    target = contract.target

    if tool == "refund_payment":
        customer_id = target.get("customer", "") or target.get("customer_id", "C1024")
        amount = float(target.get("amount", 0.0))
        reason = target.get("reason", "Customer requested refund")
        return PaymentTool.refund_payment(customer_id=customer_id, amount=amount, reason=reason)

    if tool == "transfer_funds":
        account = target.get("account_id", "ACC-789")
        amount = float(target.get("amount", 0.0))
        return PaymentTool.transfer_funds(account_id=account, amount=amount)

    if tool == "execute_sql":
        query = target.get("query", "SELECT 1;")
        db = target.get("database", "production_db")
        return DatabaseTool.execute_sql(query=query, database=db)

    if tool == "get_customer_details":
        customer_id = target.get("customer_id", "C1024")
        return DatabaseTool.get_customer_details(customer_id=customer_id)

    if tool == "create_support_ticket":
        title = target.get("title", "Support Request")
        desc = target.get("description", "")
        prio = target.get("priority", "medium")
        return EmailTool.create_support_ticket(title=title, description=desc, priority=prio)

    if tool == "send_email":
        to = target.get("to", "user@example.com")
        subject = target.get("subject", "Notice")
        body = target.get("body", "")
        return EmailTool.send_email(to=to, subject=subject, body=body)

    if tool == "read_file":
        path = target.get("path", "/data/readme.txt")
        return FilesTool.read_file(path=path)

    if tool == "export_data":
        ds = target.get("dataset_name", "dataset")
        dest = target.get("destination_url", "http://external")
        return FilesTool.export_data(dataset_name=ds, destination_url=dest)

    return {
        "status": "SUCCESS",
        "tool": tool,
        "message": f"Tool '{tool}' executed with parameters: {target}"
    }

@router.post("/execute/{action_id}")
async def execute_action(action_id: str):
    from app.middleware.execution_gate import execution_gate
    return await execution_gate.execute_action(action_id)
