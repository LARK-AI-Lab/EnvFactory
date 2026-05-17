
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class EmailAddress(BaseModel):
    """Email address with verification status."""
    address: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", description="Email address")
    verification_status: str = Field(default="Pending", description="Verification status")
    verification_token: Optional[str] = Field(default=None, description="Verification token for domains")

class Destination(BaseModel):
    """Email destination addresses."""
    ToAddresses: List[str] = Field(default=[], description="To recipients")
    CcAddresses: List[str] = Field(default=[], description="Cc recipients")
    BccAddresses: List[str] = Field(default=[], description="Bcc recipients")

class Message(BaseModel):
    """Email message content."""
    Subject: Dict[str, str] = Field(..., description="Subject line")
    Body: Dict[str, Any] = Field(..., description="Email body")

class SendDataPoint(BaseModel):
    """Email sending statistics data point."""
    Timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Timestamp")
    DeliveryAttempts: int = Field(default=0, ge=0, description="Delivery attempts")
    Bounces: int = Field(default=0, ge=0, description="Bounces")
    Complaints: int = Field(default=0, ge=0, description="Complaints")
    Rejects: int = Field(default=0, ge=0, description="Rejects")

class SentEmail(BaseModel):
    """Sent email record."""
    message_id: str = Field(..., description="Message ID")
    source: str = Field(..., description="Source email")
    destination: Destination = Field(..., description="Destination")
    timestamp: str = Field(..., description="Sent timestamp")

class SESScenario(BaseModel):
    """Amazon SES scenario state."""
    verified_identities: Dict[str, EmailAddress] = Field(default={}, description="Verified email identities")
    sent_emails: Dict[str, SentEmail] = Field(default={}, description="Sent email records")
    send_statistics: List[SendDataPoint] = Field(default=[], description="Send statistics")
    templates: Dict[str, str] = Field(default={}, description="Email templates")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp")
    message_id_counter: int = Field(default=1, ge=1, description="Message ID counter")

Scenario_Schema = [EmailAddress, Destination, Message, SendDataPoint, SentEmail, SESScenario]

# Section 2: Class
class AmazonSESAPI:
    def __init__(self):
        """Initialize Amazon SES API with empty state."""
        self.verified_identities: Dict[str, EmailAddress] = {}
        self.sent_emails: Dict[str, SentEmail] = {}
        self.send_statistics: List[SendDataPoint] = []
        self.templates: Dict[str, str] = {}
        self.current_time: str = ""
        self.message_id_counter: int = 1

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = SESScenario(**scenario)
        self.verified_identities = model.verified_identities
        self.sent_emails = model.sent_emails
        self.send_statistics = model.send_statistics
        self.templates = model.templates
        self.current_time = model.current_time
        self.message_id_counter = model.message_id_counter

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "verified_identities": {k: v.model_dump() for k, v in self.verified_identities.items()},
            "sent_emails": {k: v.model_dump() for k, v in self.sent_emails.items()},
            "send_statistics": [s.model_dump() for s in self.send_statistics],
            "templates": self.templates,
            "current_time": self.current_time,
            "message_id_counter": self.message_id_counter
        }

    def send_email(self, destination: dict, message: dict, source: str, reply_to_addresses: Optional[List[str]], return_path: Optional[str]) -> dict:
        """Send a formatted email."""
        dest = Destination(**destination)
        msg = Message(**message)
        message_id = f"msg-{self.message_id_counter:08d}"
        self.message_id_counter += 1
        
        sent_email = SentEmail(
            message_id=message_id,
            source=source,
            destination=dest,
            timestamp=self.current_time
        )
        self.sent_emails[message_id] = sent_email
        
        return {"MessageId": message_id, "RequestId": f"req-{message_id}"}

    def send_raw_email(self, raw_message: str, source: Optional[str], destinations: Optional[List[str]]) -> dict:
        """Send a raw MIME-formatted email."""
        message_id = f"msg-{self.message_id_counter:08d}"
        self.message_id_counter += 1
        return {"MessageId": message_id}

    def send_templated_email(self, destination: dict, template: str, template_data: str, source: str) -> dict:
        """Send an email using a template."""
        dest = Destination(**destination)
        message_id = f"msg-{self.message_id_counter:08d}"
        self.message_id_counter += 1
        
        sent_email = SentEmail(
            message_id=message_id,
            source=source,
            destination=dest,
            timestamp=self.current_time
        )
        self.sent_emails[message_id] = sent_email
        
        return {"MessageId": message_id}

    def get_send_statistics(self) -> dict:
        """Retrieve email sending statistics."""
        return {"SendDataPoints": [s.model_dump() for s in self.send_statistics]}

    def verify_email_identity(self, email_address: str) -> dict:
        """Initiate email verification process."""
        if email_address in self.verified_identities:
            status = self.verified_identities[email_address].verification_status
            return {"status": status.lower()}
        
        email = EmailAddress(address=email_address, verification_status="Pending")
        self.verified_identities[email_address] = email
        return {"status": "pending"}

    def get_identity_verification_attributes(self, identities: List[str]) -> dict:
        """Retrieve verification status for identities."""
        result = {}
        for identity in identities:
            if identity in self.verified_identities:
                email = self.verified_identities[identity]
                result[identity] = {
                    "VerificationStatus": email.verification_status,
                    "VerificationToken": email.verification_token
                }
        return {"VerificationAttributes": result}

# Section 3: MCP Tools
mcp = FastMCP(name="AmazonSES")
api = AmazonSESAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Amazon SES API.

    Args:
        scenario (dict): Scenario dictionary matching SESScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Amazon SES state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def send_email(destination: dict, message: dict, source: str = "", reply_to_addresses: list = None, return_path: str = None) -> dict:
    """
    Send a formatted email with subject and body to specified recipients via Amazon SES.

    Args:
        destination (dict): Recipient email addresses organized by delivery type (To, Cc, Bcc).
        message (dict): Email content including subject line and body (text or HTML format).
        source (str): The verified sender email address. Must be verified in Amazon SES.
        reply_to_addresses (list): [Optional] Email addresses that will receive replies when recipients respond to this email.
        return_path (str): [Optional] Email address where bounce and complaint notifications will be sent.

    Returns:
        MessageId (str): Unique identifier assigned to the sent email message by Amazon SES.
        RequestId (str): AWS request identifier for tracking and debugging purposes.
    """
    try:
        if not isinstance(destination, dict):
            raise ValueError("Destination must be a dictionary")
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary")
        if source and source not in api.verified_identities:
            raise ValueError(f"Source email {source} is not verified")
        if source and api.verified_identities[source].verification_status != "Success":
            raise ValueError(f"Source email {source} verification status is not Success")
        return api.send_email(destination, message, source, reply_to_addresses, return_path)
    except Exception as e:
        raise e

@mcp.tool()
def send_raw_email(raw_message: str, source: str = None, destinations: list = None) -> dict:
    """
    Send a raw MIME-formatted email message, allowing full control over email headers and content structure.

    Args:
        raw_message (str): Base64-encoded MIME message containing complete email headers and body.
        source (str): [Optional] The verified sender email address. Must be verified in Amazon SES.
        destinations (list): [Optional] Recipient email addresses that override the To/Cc/Bcc headers in the MIME message.

    Returns:
        MessageId (str): Unique identifier assigned to the sent email message by Amazon SES.
    """
    try:
        if not raw_message or not isinstance(raw_message, str):
            raise ValueError("Raw message must be a non-empty string")
        if source and source not in api.verified_identities:
            raise ValueError(f"Source email {source} is not verified")
        return api.send_raw_email(raw_message, source, destinations)
    except Exception as e:
        raise e

@mcp.tool()
def send_templated_email(destination: dict, template: str, template_data: str, source: str = "") -> dict:
    """
    Send an email using a pre-configured SES template with dynamic variable substitution.

    Args:
        destination (dict): Recipient email addresses organized by delivery type (To, Cc, Bcc).
        template (str): Name of the Amazon SES email template to use for this message.
        template_data (str): JSON string containing key-value pairs for template variable substitution.
        source (str): The verified sender email address. Must be verified in Amazon SES.

    Returns:
        MessageId (str): Unique identifier assigned to the sent email message by Amazon SES.
    """
    try:
        if not isinstance(destination, dict):
            raise ValueError("Destination must be a dictionary")
        if not template or not isinstance(template, str):
            raise ValueError("Template must be a non-empty string")
        if not template_data or not isinstance(template_data, str):
            raise ValueError("Template data must be a non-empty string")
        if source and source not in api.verified_identities:
            raise ValueError(f"Source email {source} is not verified")
        return api.send_templated_email(destination, template, template_data, source)
    except Exception as e:
        raise e

@mcp.tool()
def get_send_statistics() -> dict:
    """
    Retrieve email sending statistics for the AWS account over the last 14 days, including delivery attempts, bounces, and complaints.

    Returns:
        SendDataPoints (list): Time-series data points containing email sending metrics aggregated by time period.
    """
    try:
        return api.get_send_statistics()
    except Exception as e:
        raise e

@mcp.tool()
def verify_email_identity(email_address: str) -> dict:
    """
    Initiate the verification process for an email address to authorize it as a sender in Amazon SES.

    Args:
        email_address (str): The email address to verify as a sender identity in Amazon SES.

    Returns:
        status (str): Current verification status: pending (verification email sent), success (verified), or failed (verification unsuccessful).
    """
    try:
        if not email_address or not isinstance(email_address, str):
            raise ValueError("Email address must be a non-empty string")
        return api.verify_email_identity(email_address)
    except Exception as e:
        raise e

@mcp.tool()
def get_identity_verification_attributes(identities: list) -> dict:
    """
    Retrieve the verification status and attributes for email addresses or domains registered as sender identities.

    Args:
        identities (list): List of email addresses or domain names to check verification status for.

    Returns:
        VerificationAttributes (dict): Map of identity names to their verification status and attributes.
    """
    try:
        if not isinstance(identities, list):
            raise ValueError("Identities must be a list")
        return api.get_identity_verification_attributes(identities)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
