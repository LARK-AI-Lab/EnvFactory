# Data Source: https://developer.ebay.com/api-docs/
# Server: EbayServer
# Category: ecommerce


def search_items(keywords: str, category_id: str = None, limit: int = 10, sort: str = None) -> dict:
    """
    Search for items on eBay marketplace.
    
    Args:
        keywords (str): Search keywords/query terms
        category_id (str): [Optional] eBay category ID to filter results
        limit (int): [Optional] Maximum number of results to return (default: 10, max: 100)
        sort (str): [Optional] Sort order (e.g., 'price', '-price', 'bestMatch')
        
    Returns:
        dict: {
            "total": int,
            "items": [
                {
                    "item_id": str,
                    "title": str,
                    "price": {"value": float, "currency": str},
                    "condition": str,
                    "seller": {"username": str, "feedback_score": int},
                    "listing_url": str,
                    "thumbnail": str
                }
            ]
        }
    """
    pass


def get_item_details(item_id: str) -> dict:
    """
    Get detailed information about a specific eBay item.
    
    Args:
        item_id (str): eBay item ID
        
    Returns:
        dict: {
            "item_id": str,
            "title": str,
            "description": str,
            "price": {"value": float, "currency": str},
            "condition": str,
            "seller": {
                "username": str,
                "feedback_score": int,
                "feedback_percentage": float
            },
            "images": [str],
            "item_specifics": {str: str},
            "shipping_options": [dict],
            "return_policy": dict
        }
    """
    pass


def create_listing(title: str, description: str, category_id: str, price: float, 
                   currency: str = "USD", condition: str = "NEW", quantity: int = 1) -> dict:
    """
    Create a new item listing on eBay (seller operation).
    
    Args:
        title (str): Listing title
        description (str): Item description
        category_id (str): eBay category ID
        price (float): Item price
        currency (str): [Optional] Currency code (default: "USD")
        condition (str): [Optional] Item condition (default: "NEW")
        quantity (int): [Optional] Available quantity (default: 1)
        
    Returns:
        dict: {
            "listing_id": str,
            "status": str,
            "created_at": str,
            "url": str
        }
    """
    pass


def get_order_details(order_id: str) -> dict:
    """
    Retrieve details of a specific order.
    
    Args:
        order_id (str): eBay order ID
        
    Returns:
        dict: {
            "order_id": str,
            "status": str,
            "buyer": {"username": str, "email": str},
            "items": [dict],
            "total": {"value": float, "currency": str},
            "shipping_address": dict,
            "created_at": str
        }
    """
    pass


def get_categories(marketplace_id: str = "EBAY_US") -> dict:
    """
    Get available eBay categories for a marketplace.
    
    Args:
        marketplace_id (str): [Optional] eBay marketplace ID (default: "EBAY_US")
        
    Returns:
        dict: {
            "categories": [
                {
                    "category_id": str,
                    "name": str,
                    "parent_id": str,
                    "level": int
                }
            ]
        }
    """
    pass
