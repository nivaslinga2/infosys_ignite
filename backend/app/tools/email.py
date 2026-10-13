from typing import Dict, Any

class EmailTool:
    @staticmethod
    def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "tool": "send_email",
            "message_id": f"MSG-EML-{hash(to) % 100000}",
            "recipient": to,
            "subject": subject,
            "message": f"Email successfully dispatched to {to}."
        }

    @staticmethod
    def create_support_ticket(title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "tool": "create_support_ticket",
            "ticket_id": f"TICK-{abs(hash(title)) % 9000 + 1000}",
            "title": title,
            "priority": priority,
            "message": "Support ticket created successfully."
        }
