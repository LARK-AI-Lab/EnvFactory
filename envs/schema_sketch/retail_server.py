# Server: Retail

def find_user_by_email(email: str) -> dict:
    """
    Find user information by email address.
    
    Args:
        email (str): Registered email address of the user
        
    Returns:
        dict: {
            "user_id": str,
            "name": str,
            "email": str
            "zip_code": str
        }
    """
    pass

def find_user_by_name_zip(first_name: str, last_name: str, zip_code: str) -> dict:
    """
    Find user information by name and zip code.
    
    Args:
        first_name (str): Legal first name of the user
        last_name (str): Legal last name of the user
        zip_code (str): Five-digit postal zip code
        
    Returns:
        dict: {
            "user_id": str,
            "name": str,
            "email": str,
            "zip_code": str
        }
    """
    pass

def get_user_details(user_id: str) -> dict:
    """
    Get comprehensive user profile including address and orders.
    
    Args:
        user_id (str): Unique identifier for the customer
        
    Returns:
        dict: {
            "user_id": str,
            "name": dict,
            "email": str,
            "address": dict,
            "payment_methods": list,
            "zip_code": str,
            "order_ids": list[str]
        }
    """
    pass

def modify_user_address(
    user_id: str,
    address: str,
    city: str,
    state: str,
    country: str,
    zip_code: str,
) -> dict:
    """
    Update the default shipping address for a user.
    
    Args:
        user_id (str): Unique identifier for the customer
        address (str): Primary line of the shipping address
        city (str): City name for the shipping address
        state (str): State or province code for the shipping address
        country (str): Country name for the shipping address
        zip_code (str): Five-digit postal zip code

    Returns:
        dict: {
            "user_id": str,
            "updated_address": dict
        }
    """
    pass

def list_product_types() -> list[dict]:
    """
    List all available product categories and their basic info.
    
    Returns:
        list: Each item contains {
            "product_id": str,
            "name": str
        }
    """
    pass

def get_product_details(product_id: str) -> dict:
    """
    Get detailed inventory, pricing, and variants for a product.
    
    Args:
        product_id (str): Unique identifier for the product type
        
    Returns:
        dict: {
            "name": str,
            "description": str,
            "item_ids": list[str]
        }
    """
    pass

def get_order_details(order_id: str) -> dict:
    """
    Get status and items of a specific order.
    
    Args:
        order_id (str): Unique identifier for the order, including the '#' prefix
        
    Returns:
        dict: {
            "order_id": str,
            "user_id": str,
            "status": str,  # e.g., 'pending', 'delivered', 'cancelled'
            "items": list[dict],  # Each item contains item_id, product_id, name, price, etc.
            "total_amount": float,
            "address": dict,
        }
    """
    pass

def modify_pending_order_address(
    order_id: str,
    address: str,
    city: str,
    state: str,
    country: str,
    zip_code: str,
) -> dict:
    """
    Change shipping address for an order that is still pending.
    
    Args:
        order_id (str): Unique identifier for the order, including the '#' prefix
        address (str):  primary line for the shipping address
        city (str):  city name for the shipping address
        state (str):  state or province code
        country (str):  country name
        zip_code (str):  five-digit postal zip code
        
    Returns:
        dict: Updated order object
    """
    pass

def modify_pending_order_items(
    order_id: str,
    item_ids: list[str],
    new_item_ids: list[str],
    payment_method: str
) -> dict:
    """
    Swap items in a pending order with other variants of the same product.
    
    Args:
        order_id (str): Unique identifier for the order, including the '#' prefix
        item_ids (list[str]): List of current item identifiers to be removed
        new_item_ids (list[str]): List of new item identifiers to be added as replacements
        payment_method (str): Payment method to settle the price difference. [Enum]: ["credit_card", "paypal", "alipay", "wechat_pay"]
        
    Returns:
        dict: Updated order object
    """
    pass

def modify_pending_order_payment(order_id: str, payment_method: str) -> dict:
    """
    Update the payment method used for a pending order.
    
    Args:
        order_id (str): Unique identifier for the order, including the '#' prefix
        payment_method (str): New payment method to be used. [Enum]: ["credit_card", "paypal", "alipay", "wechat_pay"]
        
    Returns:
        dict: Updated order object
    """
    pass

def cancel_pending_order(order_id: str, reason: str) -> dict:
    """
    Cancel a pending order with a specified reason.
    
    Args:
        order_id (str): Unique identifier for the order, including the '#' prefix
        reason (str): Valid reason for the cancellation request
        
    Returns:
        dict: Cancelled order details
    """
    pass

def return_delivered_order_items(
    order_id: str,
    item_ids: list[str],
    payment_method: str
) -> dict:
    """
    Request a return for specific items in a delivered order.
    
    Args:
        order_id (str): Unique identifier for the order, including the '#' prefix
        item_ids (list[str]): List of identifiers for items being returned
        payment_method (str): Payment method to receive the refund. [Enum]: ["credit_card", "paypal", "alipay", "wechat_pay"]
        
    Returns:
        dict: Order details with 'return requested' status
    """
    pass

def exchange_delivered_order_items(
    order_id: str,
    item_ids: list[str],
    new_item_ids: list[str],
    payment_method: str
) -> dict:
    """
    Exchange delivered items for new variants of the same product.
    
    Args:
        order_id (str): Unique identifier for the order, including the '#' prefix
        item_ids (list[str]): List of identifiers for items to be exchanged
        new_item_ids (list[str]): List of identifiers for the new replacement items
        payment_method (str): Payment method to settle the price difference. [Enum]: ["credit_card", "paypal", "alipay", "wechat_pay"]
        
    Returns:
        dict: Order details with 'exchange requested' status
    """
    pass


