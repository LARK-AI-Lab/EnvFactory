# Data Source: https://docs.sendgrid.com/api-reference
# Server: SendGrid
# Category: communication


def send_email(to_email: str, subject: str, content: str, from_email: str = None, 
               html_content: str = None, template_id: str = None) -> dict:
    """
    Send an email via SendGrid API.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject line
        content (str): Plain text email content
        from_email (str): [Optional] Sender email address (defaults to verified domain)
        html_content (str): [Optional] HTML version of email content
        template_id (str): [Optional] SendGrid dynamic template ID to use
        
    Returns:
        dict: {
            "message_id": str,  # Unique message identifier
            "status": str,      # accepted | rejected
            "timestamp": str    # ISO 8601 timestamp
        }
    """
    pass


def send_bulk_emails(personalizations: list, template_id: str = None) -> dict:
    """
    Send bulk emails to multiple recipients in a single API call.
    
    Args:
        personalizations (list): List of personalization objects with 'to', 'subject', 
                                 'substitutions' fields
        template_id (str): [Optional] Dynamic template ID for all emails
        
    Returns:
        dict: {
            "batch_id": str,
            "accepted_count": int,
            "rejected_count": int,
            "errors": list      # List of rejected recipients with reasons
        }
    """
    pass


def get_email_stats(start_date: str, end_date: str = None, 
                    aggregated_by: str = None) -> dict:
    """
    Retrieve email statistics including delivery, bounce, and engagement metrics.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): [Optional] End date in YYYY-MM-DD format
        aggregated_by (str): [Optional] Aggregation level: day | week | month
        
    Returns:
        dict: {
            "metrics": [{
                "date": str,
                "delivered": int,
                "opens": int,
                "clicks": int,
                "bounces": int,
                "spam_reports": int,
                "unsubscribes": int
            }],
            "total_stats": dict
        }
    """
    pass


def add_suppression_email(email: str, group_id: str = None) -> dict:
    """
    Add an email address to the suppression list (unsubscribes/bounces/spam).
    
    Args:
        email (str): Email address to suppress
        group_id (str): [Optional] Suppression group/unsubscribe group ID
        
    Returns:
        dict: {
            "email": str,
            "added": bool,
            "group_id": str
        }
    """
    pass


def validate_email(email: str) -> dict:
    """
    Validate an email address for deliverability using SendGrid's validation API.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        dict: {
            "email": str,
            "valid": bool,
            "score": float,           # 0.0 - 1.0 deliverability score
            "checks": {
                "domain": str,        # valid | invalid | risk
                "local_part": str,    # valid | invalid
                "mx_record": bool,
                "has_disposable_address": bool
            },
            "suggestion": str         # [Optional] Corrected email suggestion
        }
    """
    pass
