# Data Source: https://resend.com/docs/api-reference/introduction
# Server: Resend
# Category: communication


def send_email(to: str, subject: str, html: str = None, text: str = None,
               from_email: str = None, reply_to: str = None,
               cc: list = None, bcc: list = None) -> dict:
    """
    Send an email via Resend API.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject line
        html (str): [Optional] HTML version of the email
        text (str): [Optional] Plain text version of the email
        from_email (str): [Optional] Sender email address
        reply_to (str): [Optional] Reply-to email address
        cc (list): [Optional] List of CC recipients
        bcc (list): [Optional] List of BCC recipients
        
    Returns:
        dict: {
            "id": str               # Unique email identifier
        }
    """
    pass


def send_batch_emails(emails: list) -> dict:
    """
    Send multiple emails in a single batch request.
    
    Args:
        emails (list): List of email objects with to, subject, html, text, from, 
                       reply_to, cc, bcc fields
        
    Returns:
        dict: {
            "data": [{
                "id": str,
                "to": str,
                "from": str,
                "created_at": str      # ISO 8601 timestamp
            }]
        }
    """
    pass


def get_email(email_id: str) -> dict:
    """
    Retrieve information about a sent email.
    
    Args:
        email_id (str): Resend email ID
        
    Returns:
        dict: {
            "object": str,          # email
            "id": str,
            "to": list,
            "from": str,
            "created_at": str,      # ISO 8601 timestamp
            "subject": str,
            "html": str,
            "text": str,
            "bcc": list,
            "cc": list,
            "reply_to": list,
            "last_event": str       # delivered | opened | clicked | etc.
        }
    """
    pass


def list_emails(domain_id: str = None, limit: int = 50) -> dict:
    """
    List sent emails with optional filtering.
    
    Args:
        domain_id (str): [Optional] Filter by domain
        limit (int): [Optional] Number of emails to return (default: 50, max: 100)
        
    Returns:
        dict: {
            "object": str,          # list
            "data": [{
                "id": str,
                "to": list,
                "from": str,
                "created_at": str,
                "subject": str,
                "status": str         # pending | delivered | bounced | etc.
            }]
        }
    """
    pass


def update_email(email_id: str, scheduled_at: str = None) -> dict:
    """
    Update a scheduled email (e.g., change send time).
    
    Args:
        email_id (str): Resend email ID
        scheduled_at (str): [Optional] New scheduled time (ISO 8601)
        
    Returns:
        dict: {
            "id": str,
            "scheduled_at": str     # ISO 8601 timestamp
        }
    """
    pass
