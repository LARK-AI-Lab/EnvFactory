
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Email(BaseModel):
    """Represents a sent email."""
    id: str = Field(..., description="Unique message identifier")
    to_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    status: str = Field(..., description="Delivery status")
    timestamp: float = Field(..., ge=0, description="Send timestamp")

class Event(BaseModel):
    """Represents an email event."""
    event: str = Field(..., description="Event type")
    id: str = Field(..., description="Event identifier")
    timestamp: float = Field(..., ge=0, description="Event timestamp")
    recipient: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Recipient email")
    domain: str = Field(..., description="Sending domain")
    message: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")

class MailgunScenario(BaseModel):
    """Main scenario model for Mailgun communication."""
    emails: Dict[str, Email] = Field(default_factory=dict, description="Sent emails by ID")
    events: List[Event] = Field(default_factory=list, description="Email events log")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")
    default_from_email: str = Field(default="noreply@mailgun.example.com", pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Default sender address")
    domains: List[str] = Field(default_factory=lambda: ["mailgun.example.com"], description="Available sending domains")

Scenario_Schema = [Email, Event, MailgunScenario]

# Section 2: Class
class MailgunCommunication:
    def __init__(self):
        """Initialize Mailgun communication API with empty state."""
        self.emails: Dict[str, Email] = {}
        self.events: List[Event] = []
        self.current_time: str = ""
        self.default_from_email: str = "noreply@mailgun.example.com"
        self.domains: List[str] = ["mailgun.example.com"]

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = MailgunScenario(**scenario)
        self.emails = model.emails
        self.events = model.events
        self.current_time = model.current_time
        self.default_from_email = model.default_from_email
        self.domains = model.domains

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "emails": {email_id: email.model_dump() for email_id, email in self.emails.items()},
            "events": [event.model_dump() for event in self.events],
            "current_time": self.current_time,
            "default_from_email": self.default_from_email,
            "domains": self.domains
        }

    def send_email(self, to_email: str, subject: str, text: str, from_email: Optional[str], html: Optional[str], template: Optional[str], tracking_clicks: bool, tracking_opens: bool) -> dict:
        """Send a transactional email."""
        import time
        email_id = f"msg_{len(self.emails) + 1}"
        sender = from_email if from_email else self.default_from_email
        timestamp = time.mktime(time.strptime(self.current_time, "%Y-%m-%dT%H:%M:%S"))
        
        email = Email(id=email_id, to_email=to_email, subject=subject, status="queued", timestamp=timestamp)
        self.emails[email_id] = email
        
        event = Event(event="accepted", id=f"evt_{len(self.events) + 1}", timestamp=timestamp, recipient=to_email, domain=sender.split("@")[1], message={"headers": {"subject": subject}})
        self.events.append(event)
        
        return {"id": email_id, "message": "Queued. Thank you.", "status": "queued"}

    def send_mime_email(self, to_email: str, mime_message: str, from_email: Optional[str]) -> dict:
        """Send a pre-formatted MIME message."""
        import time
        email_id = f"msg_{len(self.emails) + 1}"
        sender = from_email if from_email else self.default_from_email
        timestamp = time.mktime(time.strptime(self.current_time, "%Y-%m-%dT%H:%M:%S"))
        
        email = Email(id=email_id, to_email=to_email, subject="MIME Message", status="queued", timestamp=timestamp)
        self.emails[email_id] = email
        
        event = Event(event="accepted", id=f"evt_{len(self.events) + 1}", timestamp=timestamp, recipient=to_email, domain=sender.split("@")[1], message={})
        self.events.append(event)
        
        return {"id": email_id, "message": "Queued. Thank you."}

    def get_events(self, domain: str, event_types: Optional[List[str]], begin_time: Optional[str], end_time: Optional[str], limit: int) -> dict:
        """Retrieve detailed event logs."""
        import time
        filtered = [e for e in self.events if e.domain == domain]
        
        if event_types:
            filtered = [e for e in filtered if e.event in event_types]
        
        if begin_time:
            begin_ts = time.mktime(time.strptime(begin_time, "%a, %d %b %Y %H:%M:%S %Z"))
            filtered = [e for e in filtered if e.timestamp >= begin_ts]
        
        if end_time:
            end_ts = time.mktime(time.strptime(end_time, "%a, %d %b %Y %H:%M:%S %Z"))
            filtered = [e for e in filtered if e.timestamp <= end_ts]
        
        items = [e.model_dump() for e in filtered[:limit]]
        return {"items": items, "paging": {"next": "", "previous": ""}}

    def validate_email(self, email: str) -> dict:
        """Verify email address validity."""
        parts = email.split("@")
        if len(parts) != 2:
            return {"address": email, "is_valid": False, "mailbox_verification": "false", "parts": {}, "did_you_mean": ""}
        
        return {
            "address": email,
            "is_valid": True,
            "mailbox_verification": "unknown",
            "parts": {"local_part": parts[0], "domain": parts[1], "display_name": ""},
            "did_you_mean": ""
        }

    def get_stats(self, domain: str, event_types: Optional[List[str]]) -> dict:
        """Retrieve aggregated email statistics."""
        filtered = [e for e in self.events if e.domain == domain]
        
        if event_types:
            filtered = [e for e in filtered if e.event in event_types]
        
        stats_map = {}
        for event in filtered:
            event_type = event.event
            stats_map[event_type] = stats_map.get(event_type, 0) + 1
        
        return {
            "stats": [{
                "time": self.current_time,
                "accepted": {"incoming": 0, "outgoing": stats_map.get("accepted", 0)},
                "delivered": {"smtp": stats_map.get("delivered", 0), "http": 0},
                "failed": {"temporary": 0, "permanent": stats_map.get("failed", 0)},
                "opened": stats_map.get("opened", 0),
                "clicked": stats_map.get("clicked", 0),
                "complained": stats_map.get("complained", 0),
                "unsubscribed": stats_map.get("unsubscribed", 0)
            }],
            "total_stats": stats_map
        }

# Section 3: MCP Tools
mcp = FastMCP(name="MailgunCommunication")
api = MailgunCommunication()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Mailgun API.

    Args:
        scenario (dict): Scenario dictionary matching MailgunScenario schema.

    Returns:
        success_message (str): Success message.
    """
    if not isinstance(scenario, dict):
        raise ValueError("Scenario must be a dictionary")
    api.load_scenario(scenario)
    return "Successfully loaded scenario"

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Mailgun state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    return api.save_scenario()

@mcp.tool()
def send_email(to_email: str, subject: str, text: str, from_email: str = None, html: str = None, template: str = None, tracking_clicks: bool = True, tracking_opens: bool = True) -> dict:
    """
    Send a transactional email with optional HTML content and tracking.

    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject line.
        text (str): Plain text version of the email body.
        from_email (str) [Optional]: The sender's email address.
        html (str) [Optional]: HTML-formatted version of the email body.
        template (str) [Optional]: Name of a pre-configured Mailgun template.
        tracking_clicks (bool) [Optional]: Enable tracking of link clicks (default: true).
        tracking_opens (bool) [Optional]: Enable tracking of email opens (default: true).

    Returns:
        id (str): Unique message identifier.
        message (str): Status message.
        status (str): Delivery status ('queued' or 'sent').
    """
    if not to_email or not isinstance(to_email, str):
        raise ValueError("to_email must be a non-empty string")
    if not subject or not isinstance(subject, str):
        raise ValueError("subject must be a non-empty string")
    if not text or not isinstance(text, str):
        raise ValueError("text must be a non-empty string")
    return api.send_email(to_email, subject, text, from_email, html, template, tracking_clicks, tracking_opens)

@mcp.tool()
def send_mime_email(to_email: str, mime_message: str, from_email: str = None) -> dict:
    """
    Send a pre-formatted MIME message.

    Args:
        to_email (str): The recipient's email address.
        mime_message (str): Complete MIME-encoded email message.
        from_email (str) [Optional]: The sender's email address.

    Returns:
        id (str): Unique message identifier.
        message (str): Status message.
    """
    if not to_email or not isinstance(to_email, str):
        raise ValueError("to_email must be a non-empty string")
    if not mime_message or not isinstance(mime_message, str):
        raise ValueError("mime_message must be a non-empty string")
    return api.send_mime_email(to_email, mime_message, from_email)

@mcp.tool()
def get_events(domain: str, event_types: List[str] = None, begin_time: str = None, end_time: str = None, limit: int = 100) -> dict:
    """
    Retrieve detailed event logs for email lifecycle tracking.

    Args:
        domain (str): The Mailgun sending domain to query events for.
        event_types (List[str]) [Optional]: Filter by specific event types.
        begin_time (str) [Optional]: Start of time range (RFC 2822 format).
        end_time (str) [Optional]: End of time range (RFC 2822 format).
        limit (int) [Optional]: Maximum number of events to return (default: 100).

    Returns:
        items (List[dict]): Array of email events.
        paging (dict): Pagination controls.
    """
    if not domain or not isinstance(domain, str):
        raise ValueError("domain must be a non-empty string")
    if domain not in api.domains:
        raise ValueError(f"Domain {domain} not found")
    return api.get_events(domain, event_types, begin_time, end_time, limit)

@mcp.tool()
def validate_email(email: str) -> dict:
    """
    Verify email address validity and syntax correctness.

    Args:
        email (str): The email address to validate.

    Returns:
        address (str): The normalized email address.
        is_valid (bool): Overall validation result.
        mailbox_verification (str): Mailbox existence check result.
        parts (dict): Parsed components of the email address.
        did_you_mean (str): Suggested correction if typo detected.
    """
    if not email or not isinstance(email, str):
        raise ValueError("email must be a non-empty string")
    return api.validate_email(email)

@mcp.tool()
def get_stats(domain: str, event_types: List[str] = None) -> dict:
    """
    Retrieve aggregated email delivery and engagement statistics.

    Args:
        domain (str): The Mailgun sending domain to retrieve statistics for.
        event_types (List[str]) [Optional]: Filter statistics by specific event types.

    Returns:
        stats (List[dict]): Time-series statistics broken down by time period.
        total_stats (dict): Aggregated totals across all time periods.
    """
    if not domain or not isinstance(domain, str):
        raise ValueError("domain must be a non-empty string")
    if domain not in api.domains:
        raise ValueError(f"Domain {domain} not found")
    return api.get_stats(domain, event_types)

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
