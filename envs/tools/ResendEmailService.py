
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Email(BaseModel):
    """Represents a sent email."""
    id: str = Field(..., description="Unique email identifier")
    to: List[str] = Field(..., description="Recipient email addresses")
    from_email: str = Field(..., description="Sender email address")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Creation timestamp in ISO 8601 format")
    subject: str = Field(..., description="Email subject line")
    html: Optional[str] = Field(default=None, description="HTML content")
    text: Optional[str] = Field(default=None, description="Plain text content")
    bcc: List[str] = Field(default_factory=list, description="BCC recipients")
    cc: List[str] = Field(default_factory=list, description="CC recipients")
    reply_to: List[str] = Field(default_factory=list, description="Reply-to addresses")
    last_event: str = Field(default="sent", description="Most recent delivery event")
    status: str = Field(default="delivered", description="Current delivery status")
    scheduled_at: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Scheduled delivery time in ISO 8601 format")

class ResendScenario(BaseModel):
    """Main scenario model for email service."""
    emails: Dict[str, Email] = Field(default={}, description="Sent emails by ID")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Email, ResendScenario]

# Section 2: Class
class ResendEmailService:
    def __init__(self):
        """Initialize email service with empty state."""
        self.emails: Dict[str, Email] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the service instance."""
        model = ResendScenario(**scenario)
        self.emails = model.emails
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "emails": {email_id: email.model_dump() for email_id, email in self.emails.items()},
            "current_time": self.current_time
        }

    def send_email(self, to: str, subject: str, html: Optional[str], text: Optional[str], 
                   from_email: Optional[str], reply_to: Optional[str], 
                   cc: Optional[List[str]], bcc: Optional[List[str]]) -> dict:
        """Send a single email."""
        email_id = f"email_{len(self.emails) + 1}"
        email = Email(
            id=email_id,
            to=[to],
            from_email=from_email or "noreply@example.com",
            created_at=self.current_time,
            subject=subject,
            html=html,
            text=text,
            bcc=bcc or [],
            cc=cc or [],
            reply_to=[reply_to] if reply_to else []
        )
        self.emails[email_id] = email
        return {"id": email_id}

    def send_batch_emails(self, emails: List[dict]) -> dict:
        """Send multiple emails in batch."""
        results = []
        for email_data in emails:
            email_id = f"email_{len(self.emails) + 1}"
            email = Email(
                id=email_id,
                to=[email_data["to"]],
                from_email=email_data.get("from", "noreply@example.com"),
                created_at=self.current_time,
                subject=email_data["subject"],
                html=email_data.get("html"),
                text=email_data.get("text"),
                bcc=email_data.get("bcc", []),
                cc=email_data.get("cc", []),
                reply_to=[email_data["reply_to"]] if email_data.get("reply_to") else []
            )
            self.emails[email_id] = email
            results.append({
                "id": email_id,
                "to": email_data["to"],
                "from": email.from_email,
                "created_at": self.current_time
            })
        return {"data": results}

    def get_email(self, email_id: str) -> dict:
        """Retrieve email details by ID."""
        email = self.emails[email_id]
        return {
            "object": "email",
            "id": email.id,
            "to": email.to,
            "from": email.from_email,
            "created_at": email.created_at,
            "subject": email.subject,
            "html": email.html,
            "text": email.text,
            "bcc": email.bcc,
            "cc": email.cc,
            "reply_to": email.reply_to,
            "last_event": email.last_event
        }

    def list_emails(self, domain_id: Optional[str], limit: Optional[int]) -> dict:
        """List sent emails with pagination."""
        limit = limit or 50
        email_list = list(self.emails.values())[:limit]
        return {
            "object": "list",
            "data": [{
                "id": email.id,
                "to": email.to,
                "from": email.from_email,
                "created_at": email.created_at,
                "subject": email.subject,
                "status": email.status
            } for email in email_list]
        }

    def update_email(self, email_id: str, scheduled_at: Optional[str]) -> dict:
        """Update scheduled email delivery time."""
        email = self.emails[email_id]
        if scheduled_at:
            email.scheduled_at = scheduled_at
        return {
            "id": email.id,
            "scheduled_at": email.scheduled_at
        }

# Section 3: MCP Tools
mcp = FastMCP(name="ResendEmailService")
service = ResendEmailService()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the email service.

    Args:
        scenario (dict): Scenario dictionary matching ResendScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        service.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current email service state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return service.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def send_email(to: str, subject: str, html: str = None, text: str = None, 
               from_email: str = None, reply_to: str = None, 
               cc: List[str] = None, bcc: List[str] = None) -> dict:
    """
    Send a single email to a recipient with optional HTML and plain text content.

    Args:
        to (str): The recipient's email address where the email will be delivered.
        subject (str): The subject line that appears in the recipient's inbox.
        html (str) [Optional]: The HTML-formatted content of the email body.
        text (str) [Optional]: The plain text version of the email body, used as fallback when HTML is not supported.
        from_email (str) [Optional]: The sender's email address that appears in the 'From' field.
        reply_to (str) [Optional]: The email address where replies will be directed.
        cc (List[str]) [Optional]: List of email addresses to receive a carbon copy of the email.
        bcc (List[str]) [Optional]: List of email addresses to receive a blind carbon copy of the email.

    Returns:
        id (str): The unique identifier assigned to the sent email by Resend.
    """
    try:
        if not to or not isinstance(to, str):
            raise ValueError("Recipient email address is required")
        if not subject or not isinstance(subject, str):
            raise ValueError("Subject is required")
        return service.send_email(to, subject, html, text, from_email, reply_to, cc, bcc)
    except Exception as e:
        raise e

@mcp.tool()
def send_batch_emails(emails: List[dict]) -> dict:
    """
    Send multiple emails in a single API request for improved efficiency.

    Args:
        emails (List[dict]): List of email objects, each containing to, subject, html, text, from, reply_to, cc, and bcc fields.

    Returns:
        data (List[dict]): List of successfully sent emails with their metadata.
            id (str): The unique identifier assigned to the sent email by Resend.
            to (str): The recipient's email address where the email was delivered.
            from (str): The sender's email address that appears in the 'From' field.
            created_at (str): The timestamp when the email was created, in ISO 8601 format.
    """
    try:
        if not emails or not isinstance(emails, list):
            raise ValueError("Emails list is required")
        return service.send_batch_emails(emails)
    except Exception as e:
        raise e

@mcp.tool()
def get_email(email_id: str) -> dict:
    """
    Retrieve detailed information about a previously sent email, including delivery status and content.

    Args:
        email_id (str): The unique identifier assigned to the sent email by Resend.

    Returns:
        object (str): The object type, always 'email' for this response.
        id (str): The unique identifier assigned to the sent email by Resend.
        to (List[str]): List of recipient email addresses where the email was delivered.
        from (str): The sender's email address that appears in the 'From' field.
        created_at (str): The timestamp when the email was created, in ISO 8601 format.
        subject (str): The subject line that appears in the recipient's inbox.
        html (str): The HTML-formatted content of the email body.
        text (str): The plain text version of the email body.
        bcc (List[str]): List of email addresses that received a blind carbon copy of the email.
        cc (List[str]): List of email addresses that received a carbon copy of the email.
        reply_to (List[str]): List of email addresses where replies are directed.
        last_event (str): The most recent delivery event status, such as delivered, opened, clicked, bounced, or complained.
    """
    try:
        if not email_id or not isinstance(email_id, str):
            raise ValueError("Email ID is required")
        if email_id not in service.emails:
            raise ValueError(f"Email {email_id} not found")
        return service.get_email(email_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_emails(domain_id: str = None, limit: int = None) -> dict:
    """
    Retrieve a paginated list of sent emails with optional domain filtering.

    Args:
        domain_id (str) [Optional]: The unique identifier of the domain to filter emails by.
        limit (int) [Optional]: The maximum number of emails to return in the response (default: 50, maximum: 100).

    Returns:
        object (str): The object type, always 'list' for this response.
        data (List[dict]): List of emails matching the query criteria.
            id (str): The unique identifier assigned to the sent email by Resend.
            to (List[str]): List of recipient email addresses where the email was delivered.
            from (str): The sender's email address that appears in the 'From' field.
            created_at (str): The timestamp when the email was created, in ISO 8601 format.
            subject (str): The subject line that appears in the recipient's inbox.
            status (str): The current delivery status of the email, such as pending, delivered, bounced, or failed.
    """
    try:
        return service.list_emails(domain_id, limit)
    except Exception as e:
        raise e

@mcp.tool()
def update_email(email_id: str, scheduled_at: str = None) -> dict:
    """
    Modify a scheduled email's send time before it is delivered.

    Args:
        email_id (str): The unique identifier assigned to the sent email by Resend.
        scheduled_at (str) [Optional]: The new scheduled delivery time for the email, in ISO 8601 format.

    Returns:
        id (str): The unique identifier assigned to the sent email by Resend.
        scheduled_at (str): The updated scheduled delivery time for the email, in ISO 8601 format.
    """
    try:
        if not email_id or not isinstance(email_id, str):
            raise ValueError("Email ID is required")
        if email_id not in service.emails:
            raise ValueError(f"Email {email_id} not found")
        return service.update_email(email_id, scheduled_at)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
