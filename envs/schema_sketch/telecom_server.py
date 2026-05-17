# Server: Telecom

def get_customer_by_phone(phone_number: str) -> dict:
    """
    Find a customer by their primary contact or line phone number.
    
    Args:
        phone_number (str): Primary or line-associated phone number
        
    Returns:
        dict: {
            "customer_id": str,
            "full_name": str,
            "phone_number": str,
            "line_ids": list[str]
        }
    """
    pass

def get_customer_by_id(customer_id: str) -> dict:
    """
    Retrieve customer details by their unique ID.
    
    Args:
        customer_id (str): Unique identifier of the customer
        
    Returns:
        dict: {
            "customer_id": str,
            "full_name": str,
            "phone_number": str,
            "line_ids": list[str]
        }
    """
    pass

def get_customer_by_name(full_name: str, dob: str) -> list:
    """
    Search for customers by name and date of birth.
    
    Args:
        full_name (str): Customer's full legal name
        dob (str): Customer's date of birth in YYYY-MM-DD format
        
    Returns:
        list: Each customer contains {
            "customer_id": str,
            "full_name": str,
            "phone_number": str
            "line_ids": list[str]
        }
    """
    pass

def get_details_by_id(customer_id: str) -> dict:
    """
    Retrieve details for a given object ID .
    
    Args:
        customer_id (str): Unique identifier of the object
        
    Returns:
        dict: {
            "customer_id": str,
            "full_name": str,
            "phone_number": str,
            "line_ids": list[str]
            "biil_ids": list[str]
            "email": str
            "city": str
            "country": str
        }
    """
    pass

def list_bills(customer_id: str, limit: int = None) -> list:
    """
    Retrieve a list of the customer's bills, most recent first.
    
    Args:
        customer_id (str): Unique identifier of the customer
        limit (int): [Optional] Maximum number of bills to return
        
    Returns:
        list: Each bill contains {
            "bill_id": str,
            "issue_date": str,
            "total_due": float,
            "status": str
        }
    """
    pass

def get_usage(customer_id: str, line_id: str) -> dict:
    """
    Retrieve current data usage information for a specific line.
    
    Args:
        customer_id (str): Unique identifier of the customer
        line_id (str): Unique identifier of the mobile line
        
    Returns:
        dict: {
            "line_id": str,
            "data_used_gb": float,
            "data_limit_gb": int,
            "data_refueling_gb": float,
            "cycle_end_date": str
        }
    """
    pass

def suspend_line(customer_id: str, line_id: str, reason: str) -> dict:
    """
    Suspend an active mobile line.
    
    Args:
        customer_id (str): Unique identifier of the customer
        line_id (str): Unique identifier of the mobile line
        reason (str): Reason for the line suspension
        
    Returns:
        dict: {
            "line_id": str,
            "status": str,
            "suspension_start_date": str
        }
    """
    pass

def resume_line(customer_id: str, line_id: str) -> dict:
    """
    Resume a suspended mobile line.
    
    Args:
        customer_id (str): Unique identifier of the customer
        line_id (str): Unique identifier of the mobile line
        
    Returns:
        dict: {
            "line_id": str,
            "status": str
        }
    """
    pass

def enable_roaming(customer_id: str, line_id: str) -> dict:
    """
    Enable international roaming on a mobile line.
    
    Args:
        customer_id (str): Unique identifier of the customer
        line_id (str): Unique identifier of the mobile line
        
    Returns:
        dict: {
            "line_id": str,
            "roaming_enabled": bool
        }
    """
    pass

def disable_roaming(customer_id: str, line_id: str) -> dict:
    """
    Disable international roaming on a mobile line.
    
    Args:
        customer_id (str): Unique identifier of the customer
        line_id (str): Unique identifier of the mobile line
        
    Returns:
        dict: {
            "line_id": str,
            "roaming_enabled": bool
        }
    """
    pass

def refuel_data(customer_id: str, line_id: str, gb_amount: float) -> dict:
    """
    Add more data to a specific mobile line.
    
    Args:
        customer_id (str): Unique identifier of the customer
        line_id (str): Unique identifier of the mobile line
        gb_amount (float): Amount of data to add in gigabytes
        
    Returns:
        dict: {
            "line_id": str,
            "new_data_refueling_gb": float,
            "charge_amount": float
        }
    """
    pass

def send_payment_request(customer_id: str, bill_id: str) -> dict:
    """
    Send a payment request to the customer for a specific bill.
    
    Args:
        customer_id (str): Unique identifier of the customer
        bill_id (str): Unique identifier of the billing statement
        
    Returns:
        dict: {
            "bill_id": str,
            "status": str
        }
    """
    pass


