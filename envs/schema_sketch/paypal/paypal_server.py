# Data Source: https://developer.paypal.com/api/rest/
# Server: PayPal
# Category: Payment Processing


def create_order(amount: str, currency_code: str = "USD", intent: str = "CAPTURE",
                description: str = None, items: list = None) -> dict:
    """
    Create a new PayPal order for payment processing.
    
    Args:
        amount (str): Total amount as string (e.g., "100.00")
        currency_code (str): [Optional] Three-letter currency code (default "USD")
        intent (str): [Optional] "CAPTURE" (immediate) or "AUTHORIZE" (delayed)
        description (str): [Optional] Order description
        items (list): [Optional] Line items with name, quantity, unit_amount
        
    Returns:
        dict: {
            "id": str,
            "status": str,
            "intent": str,
            "amount": str,
            "currency": str,
            "links": list
        }
    """
    pass


def capture_order(order_id: str) -> dict:
    """
    Capture payment for an order (completes the transaction).
    
    Args:
        order_id (str): The PayPal order ID
        
    Returns:
        dict: {
            "id": str,
            "status": str,
            "capture_id": str,
            "amount": str,
            "currency": str,
            "payer": dict
        }
    """
    pass


def authorize_order(order_id: str) -> dict:
    """
    Authorize payment without capturing (for delayed capture).
    
    Args:
        order_id (str): The PayPal order ID
        
    Returns:
        dict: {
            "id": str,
            "status": str,
            "authorization_id": str,
            "amount": str,
            "currency": str,
            "expiration_time": str
        }
    """
    pass


def capture_authorized_payment(authorization_id: str, amount: str = None,
                               final_capture: bool = True) -> dict:
    """
    Capture a previously authorized payment.
    
    Args:
        authorization_id (str): The authorization ID
        amount (str): [Optional] Amount to capture (defaults to full authorization)
        final_capture (bool): [Optional] Whether this is the final capture
        
    Returns:
        dict: {
            "id": str,
            "status": str,
            "amount": str,
            "currency": str,
            "final_capture": bool
        }
    """
    pass


def get_order_details(order_id: str) -> dict:
    """
    Retrieve details of an existing order.
    
    Args:
        order_id (str): The PayPal order ID
        
    Returns:
        dict: Full order object with all details:
        {
            "id": str,
            "status": str,
            "intent": str,
            "purchase_units": list,
            "payer": dict,
            "create_time": str,
            "update_time": str
        }
    """
    pass
