# Server: UUPaoTui

def estimate_price(fromAddress: str, toAddress: str, adCode: str, sendType: str) -> dict:
    """
    Get order price estimate based on origin and destination addresses.
    
    Args:
        fromAddress (str): Origin address
        toAddress (str): Destination address
        adCode (str): Order region code, 6-digit administrative division code (GB/T 2260), e.g., "110100" for Beijing
        sendType (str): Order type, one of: "instant" for instant delivery, "scheduled" for scheduled delivery
        
    Returns:
        dict: {
            "priceToken": str,
            "needPayMoney": float
        }
    """
    pass

def create_order(priceToken: str, receiverPhone: str, senderPhone: str) -> dict:
    """
    Create a delivery order using price token from estimate.
    
    Args:
        priceToken (str): Price token from estimate_price() response
        receiverPhone (str): Recipient phone number (mobile)
        senderPhone (str): Sender phone number (mobile)
        
    Returns:
        dict: {
            "orderCode": str
        }
    """
    pass

def list_orders() -> list:
    """
    List all orders for the current account to get order codes.
    
    Returns:
        list: List of dicts, each containing {
            "orderCode": str,
            "fromAddress": str,
            "toAddress": str,
            "state": str,
            "createdAt": str
        }
    """
    pass

def query_order(orderCode: str) -> dict:
    """
    Query order details and status.
    
    Args:
        orderCode (str): UU order code
        
    Returns:
        dict: {
            "orderCode": str,
            "fromAddress": str,
            "toAddress": str,
            "distance": float,
            "state": str
        }
    """
    pass

def cancel_order(orderCode: str, reason: str) -> dict:
    """
    Cancel an existing order.
    
    Args:
        orderCode (str): UU order code
        reason (str): Cancellation reason
        
    Returns:
        dict: {
            "orderCode": str,
            "deductFee": int
        }
    """
    pass

