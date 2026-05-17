# Data Source: https://postmarkapp.com/developer
# Server: Postmark
# Category: communication


def send_email(to_email: str, subject: str, text_body: str = None,
               html_body: str = None, from_email: str = None,
               tag: str = None, track_opens: bool = True,
               track_links: str = "HtmlAndText") -> dict:
    """
    Send a single email via Postmark API.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject line
        text_body (str): [Optional] Plain text email content
        html_body (str): [Optional] HTML email content (at least one body required)
        from_email (str): [Optional] Sender email address
        tag (str): [Optional] Tag for categorizing emails
        track_opens (bool): [Optional] Enable open tracking (default: True)
        track_links (str): [Optional] Link tracking mode: HtmlAndText | HtmlOnly | 
                          TextOnly | None (default: HtmlAndText)
        
    Returns:
        dict: {
            "To": str,
            "SubmittedAt": str,     # ISO 8601 timestamp
            "MessageID": str,       # Unique message identifier
            "ErrorCode": int,
            "Message": str          # OK or error description
        }
    """
    pass


def send_email_batch(messages: list) -> dict:
    """
    Send multiple emails in a single batch request (max 500 messages).
    
    Args:
        messages (list): List of email message objects with To, Subject, TextBody,
                        HtmlBody, From, Tag fields
        
    Returns:
        dict: {
            "results": [{
                "To": str,
                "SubmittedAt": str,
                "MessageID": str,
                "ErrorCode": int,
                "Message": str
            }]
        }
    """
    pass


def get_bounces(count: int = 100, offset: int = 0, 
                inactive: bool = None, email_filter: str = None) -> dict:
    """
    Retrieve bounce information for emails that failed to deliver.
    
    Args:
        count (int): [Optional] Number of bounces to return (default: 100)
        offset (int): [Optional] Pagination offset (default: 0)
        inactive (bool): [Optional] Filter by active/inactive status
        email_filter (str): [Optional] Filter by recipient email address
        
    Returns:
        dict: {
            "total_count": int,
            "bounces": [{
                "ID": int,
                "Type": str,            # HardBounce | SoftBounce | etc.
                "TypeCode": int,
                "Name": str,
                "Tag": str,
                "MessageID": str,
                "ServerID": int,
                "Description": str,
                "Details": str,
                "Email": str,
                "From": str,
                "BouncedAt": str,       # ISO 8601 timestamp
                "DumpAvailable": bool,
                "Inactive": bool,
                "CanActivate": bool,
                "Subject": str,
                "Content": str
            }]
        }
    """
    pass


def get_outbound_stats(tag: str = None, from_date: str = None, 
                       to_date: str = None) -> dict:
    """
    Retrieve outbound email statistics.
    
    Args:
        tag (str): [Optional] Filter by specific tag
        from_date (str): [Optional] Start date (YYYY-MM-DD)
        to_date (str): [Optional] End date (YYYY-MM-DD)
        
    Returns:
        dict: {
            "Sent": int,
            "HardBounces": int,
            "SoftBounces": int,
            "TotalBounces": int,
            "SpamComplaints": int,
            "Opens": int,
            "UniqueOpens": int,
            "TotalClicks": int,
            "UniqueClicks": int,
            "Unsubscribes": int,
            "Tracked": int
        }
    """
    pass


def get_message_opens(message_id: str, count: int = 100, offset: int = 0) -> dict:
    """
    Retrieve open tracking information for a specific email.
    
    Args:
        message_id (str): Postmark message ID
        count (int): [Optional] Number of opens to return (default: 100)
        offset (int): [Optional] Pagination offset (default: 0)
        
    Returns:
        dict: {
            "total_count": int,
            "opens": [{
                "FirstOpen": bool,
                "Client": {
                    "Name": str,
                    "Company": str,
                    "Family": str
                },
                "OS": {
                    "Name": str,
                    "Company": str,
                    "Family": str
                },
                "Platform": str,
                "UserAgent": str,
                "ReadSeconds": int,
                "Geo": {
                    "CountryISOCode": str,
                    "Country": str,
                    "RegionISOCode": str,
                    "Region": str,
                    "City": str,
                    "Zip": str,
                    "Coords": str,
                    "IP": str
                },
                "MessageID": str,
                "ReceivedAt": str,      # ISO 8601 timestamp
                "Tag": str,
                "Recipient": str
            }]
        }
    """
    pass
