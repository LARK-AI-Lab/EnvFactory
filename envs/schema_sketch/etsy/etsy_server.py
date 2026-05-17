# Data Source: https://developer.etsy.com/documentation/
# Server: EtsyServer
# Category: ecommerce


def search_listings(keywords: str, category: str = None, min_price: float = None, 
                   max_price: float = None, limit: int = 10) -> dict:
    """
    Search for listings on Etsy marketplace.
    
    Args:
        keywords (str): Search keywords/query terms
        category (str): [Optional] Category slug to filter results
        min_price (float): [Optional] Minimum price filter
        max_price (float): [Optional] Maximum price filter
        limit (int): [Optional] Maximum number of results (default: 10, max: 100)
        
    Returns:
        dict: {
            "count": int,
            "results": [
                {
                    "listing_id": int,
                    "title": str,
                    "price": {"amount": float, "currency": str},
                    "quantity": int,
                    "shop_name": str,
                    "url": str,
                    "images": [str]
                }
            ]
        }
    """
    pass


def get_listing_details(listing_id: int) -> dict:
    """
    Get detailed information about a specific Etsy listing.
    
    Args:
        listing_id (int): Etsy listing ID
        
    Returns:
        dict: {
            "listing_id": int,
            "title": str,
            "description": str,
            "price": {"amount": float, "currency": str, "divisor": int},
            "quantity": int,
            "shop": {
                "shop_id": int,
                "shop_name": str,
                "url": str,
                "rating": float
            },
            "images": [{"url": str, "full_height": int, "full_width": int}],
            "tags": [str],
            "materials": [str],
            "shipping_profile": dict
        }
    """
    pass


def create_listing(shop_id: int, title: str, description: str, price: float, 
                   quantity: int, taxonomy_id: int, who_made: str = "i_did") -> dict:
    """
    Create a new listing in an Etsy shop (requires OAuth).
    
    Args:
        shop_id (int): Etsy shop ID
        title (str): Listing title (max 140 chars)
        description (str): Item description
        price (float): Item price
        quantity (int): Available quantity
        taxonomy_id (int): Etsy taxonomy/category ID
        who_made (str): [Optional] Who made the item (default: "i_did")
        
    Returns:
        dict: {
            "listing_id": int,
            "title": str,
            "state": str,
            "creation_tsz": float,
            "url": str
        }
    """
    pass


def get_shop_listings(shop_id: int, status: str = "active", limit: int = 25) -> dict:
    """
    Get all listings for a specific Etsy shop.
    
    Args:
        shop_id (int): Etsy shop ID
        status (str): [Optional] Listing status filter (active, inactive, expired, sold_out)
        limit (int): [Optional] Results per page (default: 25, max: 100)
        
    Returns:
        dict: {
            "count": int,
            "results": [
                {
                    "listing_id": int,
                    "title": str,
                    "state": str,
                    "price": {"amount": float, "currency": str}
                }
            ]
        }
    """
    pass


def get_receipts(shop_id: int, min_created: int = None, max_created: int = None) -> dict:
    """
    Get shop receipts (orders) for a seller.
    
    Args:
        shop_id (int): Etsy shop ID
        min_created (int): [Optional] Min creation timestamp (epoch)
        max_created (int): [Optional] Max creation timestamp (epoch)
        
    Returns:
        dict: {
            "count": int,
            "results": [
                {
                    "receipt_id": int,
                    "buyer_email": str,
                    "name": str,
                    "grandtotal": {"amount": float, "currency": str},
                    "status": str,
                    "created_tsz": float,
                    "transactions": [dict]
                }
            ]
        }
    """
    pass
