
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class EmailMessage(BaseModel):
    """Represents an email message to be sent."""
    To: str = Field(..., description="Recipient email address")
    Subject: str = Field(..., description="Email subject line")
    TextBody: Optional[str] = Field(default=None, description="Plain text content")
    HtmlBody: Optional[str] = Field(default=None, description="HTML content")
    From: str = Field(..., description="Sender email address")
    Tag: Optional[str] = Field(default=None, description="Email tag for categorization")
    TrackOpens: bool = Field(default=True, description="Track email opens")
    TrackLinks: str = Field(default="HtmlAndText", description="Link tracking mode")
    MessageID: Optional[str] = Field(default=None, description="Unique message identifier")
    SubmittedAt: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Submission timestamp")
    ErrorCode: int = Field(default=0, description="Error code (0 = success)")
    Message: str = Field(default="OK", description="Status message")

class BounceRecord(BaseModel):
    """Represents an email bounce record."""
    ID: int = Field(..., ge=0, description="Bounce record ID")
    Type: str = Field(..., description="Bounce type (HardBounce/SoftBounce)")
    TypeCode: int = Field(..., description="Numeric bounce type code")
    Name: str = Field(..., description="Bounce reason name")
    Tag: Optional[str] = Field(default=None, description="Email tag")
    MessageID: str = Field(..., description="Message identifier")
    ServerID: int = Field(..., ge=0, description="Server identifier")
    Description: str = Field(..., description="Bounce description")
    Details: str = Field(..., description="Technical details")
    Email: str = Field(..., description="Bounced email address")
    From: str = Field(..., description="Sender email address")
    BouncedAt: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Bounce timestamp")
    DumpAvailable: bool = Field(default=False, description="SMTP dump available")
    Inactive: bool = Field(default=False, description="Email address inactive")
    CanActivate: bool = Field(default=True, description="Can reactivate address")
    Subject: str = Field(..., description="Email subject")
    Content: str = Field(..., description="Email content excerpt")

class OpenEvent(BaseModel):
    """Represents an email open event."""
    FirstOpen: bool = Field(..., description="First open flag")
    Client: Dict[str, str] = Field(default={}, description="Email client info")
    OS: Dict[str, str] = Field(default={}, description="Operating system info")
    Platform: str = Field(..., description="Device platform")
    UserAgent: str = Field(..., description="User agent string")
    ReadSeconds: int = Field(..., ge=0, description="Read time in seconds")
    Geo: Dict[str, str] = Field(default={}, description="Geographic location")
    MessageID: str = Field(..., description="Message identifier")
    ReceivedAt: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Open timestamp")
    Tag: Optional[str] = Field(default=None, description="Email tag")
    Recipient: str = Field(..., description="Recipient email address")

class PostmarkScenario(BaseModel):
    """Main scenario model for Postmark email service."""
    messages: Dict[str, EmailMessage] = Field(default={}, description="Sent messages by MessageID")
    bounces: Dict[int, BounceRecord] = Field(default={}, description="Bounce records by ID")
    opens: Dict[str, List[OpenEvent]] = Field(default={}, description="Open events by MessageID")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Current timestamp")
    next_message_id: int = Field(default=1, ge=1, description="Next message ID counter")
    next_bounce_id: int = Field(default=1, ge=1, description="Next bounce ID counter")

Scenario_Schema = [EmailMessage, BounceRecord, OpenEvent, PostmarkScenario]

# Section 2: Class
class PostmarkEmailService:
    def __init__(self):
        """Initialize Postmark email service with empty state."""
        self.messages: Dict[str, EmailMessage] = {}
        self.bounces: Dict[int, BounceRecord] = {}
        self.opens: Dict[str, List[OpenEvent]] = {}
        self.current_time: str = ""
        self.next_message_id: int = 1
        self.next_bounce_id: int = 1

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the service instance."""
        model = PostmarkScenario(**scenario)
        self.messages = model.messages
        self.bounces = model.bounces
        self.opens = model.opens
        self.current_time = model.current_time
        self.next_message_id = model.next_message_id
        self.next_bounce_id = model.next_bounce_id

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "messages": {msg_id: msg.model_dump() for msg_id, msg in self.messages.items()},
            "bounces": {bounce_id: bounce.model_dump() for bounce_id, bounce in self.bounces.items()},
            "opens": {msg_id: [event.model_dump() for event in events] for msg_id, events in self.opens.items()},
            "current_time": self.current_time,
            "next_message_id": self.next_message_id,
            "next_bounce_id": self.next_bounce_id
        }

    def send_email(self, to_email: str, subject: str, text_body: Optional[str], html_body: Optional[str], 
                   from_email: str, tag: Optional[str], track_opens: bool, track_links: str) -> dict:
        """Send a single email."""
        message_id = f"msg-{self.next_message_id}"
        self.next_message_id += 1
        
        msg = EmailMessage(
            To=to_email,
            Subject=subject,
            TextBody=text_body,
            HtmlBody=html_body,
            From=from_email,
            Tag=tag,
            TrackOpens=track_opens,
            TrackLinks=track_links,
            MessageID=message_id,
            SubmittedAt=self.current_time,
            ErrorCode=0,
            Message="OK"
        )
        self.messages[message_id] = msg
        
        return {
            "To": msg.To,
            "SubmittedAt": msg.SubmittedAt,
            "MessageID": msg.MessageID,
            "ErrorCode": msg.ErrorCode,
            "Message": msg.Message
        }

    def send_email_batch(self, messages: List[dict]) -> dict:
        """Send multiple emails in batch."""
        results = []
        for msg_data in messages:
            result = self.send_email(
                to_email=msg_data.get("To", ""),
                subject=msg_data.get("Subject", ""),
                text_body=msg_data.get("TextBody"),
                html_body=msg_data.get("HtmlBody"),
                from_email=msg_data.get("From", ""),
                tag=msg_data.get("Tag"),
                track_opens=msg_data.get("TrackOpens", True),
                track_links=msg_data.get("TrackLinks", "HtmlAndText")
            )
            results.append(result)
        
        return {"results": results}

    def get_bounces(self, count: int, offset: int, inactive: Optional[bool], email_filter: Optional[str]) -> dict:
        """Retrieve bounce records."""
        filtered_bounces = list(self.bounces.values())
        
        if inactive is not None:
            filtered_bounces = [b for b in filtered_bounces if b.Inactive == inactive]
        
        if email_filter:
            filtered_bounces = [b for b in filtered_bounces if b.Email == email_filter]
        
        total = len(filtered_bounces)
        paginated = filtered_bounces[offset:offset + count]
        
        return {
            "total_count": total,
            "bounces": [b.model_dump() for b in paginated]
        }

    def get_outbound_stats(self, tag: Optional[str], from_date: Optional[str], to_date: Optional[str]) -> dict:
        """Retrieve outbound email statistics."""
        filtered_messages = list(self.messages.values())
        
        if tag:
            filtered_messages = [m for m in filtered_messages if m.Tag == tag]
        
        if from_date:
            filtered_messages = [m for m in filtered_messages if m.SubmittedAt and m.SubmittedAt >= from_date]
        
        if to_date:
            filtered_messages = [m for m in filtered_messages if m.SubmittedAt and m.SubmittedAt <= to_date]
        
        sent = len(filtered_messages)
        
        filtered_bounces = list(self.bounces.values())
        if tag:
            filtered_bounces = [b for b in filtered_bounces if b.Tag == tag]
        
        hard_bounces = len([b for b in filtered_bounces if b.Type == "HardBounce"])
        soft_bounces = len([b for b in filtered_bounces if b.Type == "SoftBounce"])
        
        total_opens = 0
        unique_opens = 0
        tracked = 0
        
        for msg in filtered_messages:
            if msg.TrackOpens:
                tracked += 1
                msg_opens = self.opens.get(msg.MessageID, [])
                total_opens += len(msg_opens)
                if msg_opens:
                    unique_opens += 1
        
        return {
            "Sent": sent,
            "HardBounces": hard_bounces,
            "SoftBounces": soft_bounces,
            "TotalBounces": hard_bounces + soft_bounces,
            "SpamComplaints": 0,
            "Opens": total_opens,
            "UniqueOpens": unique_opens,
            "TotalClicks": 0,
            "UniqueClicks": 0,
            "Unsubscribes": 0,
            "Tracked": tracked
        }

    def get_message_opens(self, message_id: str, count: int, offset: int) -> dict:
        """Retrieve open events for a message."""
        opens = self.opens.get(message_id, [])
        total = len(opens)
        paginated = opens[offset:offset + count]
        
        return {
            "total_count": total,
            "opens": [o.model_dump() for o in paginated]
        }

# Section 3: MCP Tools
mcp = FastMCP(name="PostmarkEmailService")
service = PostmarkEmailService()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Postmark email service.

    Args:
        scenario (dict): Scenario dictionary matching PostmarkScenario schema.

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
def send_email(to_email: str, subject: str, text_body: str = None, html_body: str = None, 
               from_email: str = "", tag: str = None, track_opens: bool = True, 
               track_links: str = "HtmlAndText") -> dict:
    """
    Send a single transactional email to a recipient with optional tracking and categorization.

    Args:
        to_email (str): The recipient's email address where the message will be delivered.
        subject (str): The subject line that appears in the recipient's inbox.
        text_body (str) [Optional]: Plain text version of the email content for clients that don't support HTML.
        html_body (str) [Optional]: HTML-formatted version of the email content for rich formatting and styling.
        from_email (str): The sender's email address that appears in the From field.
        tag (str) [Optional]: A label for categorizing and filtering emails in reports and analytics.
        track_opens (bool): Whether to track when recipients open the email (default: true).
        track_links (str): Link click tracking mode: HtmlAndText (both formats), HtmlOnly, TextOnly, or None (default: HtmlAndText).

    Returns:
        To (str): The recipient's email address that received the message.
        SubmittedAt (str): ISO 8601 timestamp indicating when the email was submitted to Postmark for delivery.
        MessageID (str): Unique identifier assigned to this email message for tracking and reference.
        ErrorCode (int): Numeric error code (0 indicates success, non-zero indicates failure).
        Message (str): Status message indicating success (OK) or describing the error that occurred.
    """
    try:
        if not to_email or not isinstance(to_email, str):
            raise ValueError("to_email must be a non-empty string")
        if not subject or not isinstance(subject, str):
            raise ValueError("subject must be a non-empty string")
        if not from_email or not isinstance(from_email, str):
            raise ValueError("from_email must be a non-empty string")
        return service.send_email(to_email, subject, text_body, html_body, from_email, tag, track_opens, track_links)
    except Exception as e:
        raise e

@mcp.tool()
def send_email_batch(messages: list) -> dict:
    """
    Send multiple transactional emails in a single API request for improved efficiency (maximum 500 messages per batch).

    Args:
        messages (list): Collection of email message objects, each containing To, Subject, TextBody, HtmlBody, From, and Tag fields.

    Returns:
        results (list): Delivery results for each email in the batch, maintaining the same order as the input.
    """
    try:
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list")
        return service.send_email_batch(messages)
    except Exception as e:
        raise e

@mcp.tool()
def get_bounces(count: int = 100, offset: int = 0, inactive: bool = None, email_filter: str = None) -> dict:
    """
    Retrieve detailed information about emails that failed to deliver due to hard bounces, soft bounces, or other delivery issues.

    Args:
        count (int) [Optional]: Maximum number of bounce records to return in the response (default: 100).
        offset (int) [Optional]: Number of bounce records to skip for pagination (default: 0).
        inactive (bool) [Optional]: Filter bounces by active status (true for inactive bounces, false for active, null for all).
        email_filter (str) [Optional]: Filter bounces by a specific recipient email address.

    Returns:
        total_count (int): Total number of bounce records matching the filter criteria.
        bounces (list): Collection of bounce records containing delivery failure details.
    """
    try:
        return service.get_bounces(count, offset, inactive, email_filter)
    except Exception as e:
        raise e

@mcp.tool()
def get_outbound_stats(tag: str = None, from_date: str = None, to_date: str = None) -> dict:
    """
    Retrieve aggregated statistics about sent emails including delivery rates, engagement metrics, and bounce information.

    Args:
        tag (str) [Optional]: A label for categorizing and filtering emails in reports and analytics.
        from_date (str) [Optional]: Start date for the statistics period in YYYY-MM-DD format.
        to_date (str) [Optional]: End date for the statistics period in YYYY-MM-DD format.

    Returns:
        Sent (int): Total number of emails successfully sent during the period.
        HardBounces (int): Number of emails that permanently failed delivery due to invalid addresses or blocked domains.
        SoftBounces (int): Number of emails that temporarily failed delivery due to full mailboxes or server issues.
        TotalBounces (int): Combined count of all hard and soft bounces.
        SpamComplaints (int): Number of recipients who marked the email as spam.
        Opens (int): Total number of times emails were opened, including multiple opens by the same recipient.
        UniqueOpens (int): Number of unique recipients who opened the email at least once.
        TotalClicks (int): Total number of link clicks across all emails, including multiple clicks by the same recipient.
        UniqueClicks (int): Number of unique recipients who clicked at least one link in the email.
        Unsubscribes (int): Number of recipients who opted out of future emails.
        Tracked (int): Number of emails that had tracking enabled for opens and clicks.
    """
    try:
        return service.get_outbound_stats(tag, from_date, to_date)
    except Exception as e:
        raise e

@mcp.tool()
def get_message_opens(message_id: str, count: int = 100, offset: int = 0) -> dict:
    """
    Retrieve detailed tracking information about when and how recipients opened a specific email, including device, location, and engagement data.

    Args:
        message_id (str): Unique identifier assigned to this email message for tracking and reference.
        count (int) [Optional]: Maximum number of open event records to return in the response (default: 100).
        offset (int) [Optional]: Number of open event records to skip for pagination (default: 0).

    Returns:
        total_count (int): Total number of open events recorded for this email message.
        opens (list): Collection of open events with detailed recipient engagement information.
    """
    try:
        if not message_id or not isinstance(message_id, str):
            raise ValueError("message_id must be a non-empty string")
        if message_id not in service.messages:
            raise ValueError(f"Message {message_id} not found")
        return service.get_message_opens(message_id, count, offset)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
