# Data Source: https://docs.stripe.com/api
# Server: Stripe
# Category: Payment Processing


def create_payment_intent(amount: int, currency: str, customer_id: str = None,
                         payment_method_id: str = None, metadata: dict = None) -> dict:
    """
    Create a PaymentIntent to collect payment from a customer.
    
    Args:
        amount (int): Amount to charge in smallest currency unit (e.g., cents for USD)
        currency (str): Three-letter ISO currency code (e.g., "usd", "eur")
        customer_id (str): [Optional] ID of existing customer
        payment_method_id (str): [Optional] ID of saved payment method
        metadata (dict): [Optional] Key-value pairs for custom data
        
    Returns:
        dict: {
            "id": str,
            "client_secret": str,
            "status": str,
            "amount": int,
            "currency": str,
            "created": int
        }
    """
    pass


def retrieve_payment_intent(payment_intent_id: str) -> dict:
    """
    Retrieve details of an existing PaymentIntent.
    
    Args:
        payment_intent_id (str): The PaymentIntent ID
        
    Returns:
        dict: PaymentIntent object with all details
    """
    pass


def create_customer(email: str, name: str = None, phone: str = None, 
                   metadata: dict = None) -> dict:
    """
    Create a new customer for storing payment methods and recurring billing.
    
    Args:
        email (str): Customer email address
        name (str): [Optional] Customer full name
        phone (str): [Optional] Customer phone number
        metadata (dict): [Optional] Custom key-value data
        
    Returns:
        dict: {
            "id": str,
            "email": str,
            "name": str,
            "created": int
        }
    """
    pass


def create_refund(payment_intent_id: str, amount: int = None, reason: str = None) -> dict:
    """
    Create a refund for a payment.
    
    Args:
        payment_intent_id (str): The PaymentIntent to refund
        amount (int): [Optional] Amount to refund (defaults to full amount)
        reason (str): [Optional] "duplicate", "fraudulent", or "requested_by_customer"
        
    Returns:
        dict: {
            "id": str,
            "amount": int,
            "status": str,
            "reason": str
        }
    """
    pass


def list_charges(limit: int = 10, customer_id: str = None) -> list:
    """
    List payment charges with optional filtering.
    
    Args:
        limit (int): [Optional] Number of charges to return (max 100, default 10)
        customer_id (str): [Optional] Filter by customer ID
        
    Returns:
        list: Array of charge objects
    """
    pass
