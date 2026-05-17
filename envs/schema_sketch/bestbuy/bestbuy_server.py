# Data Source: https://bestbuyapis.github.io/api-documentation/
# Server: BestBuyServer
# Category: ecommerce


def search_products(keywords: str, category: str = None, min_price: float = None, 
                   max_price: float = None, in_stock_only: bool = True, limit: int = 10) -> dict:
    """
    Search for products in Best Buy catalog.
    
    Args:
        keywords (str): Search keywords
        category (str): [Optional] Category path name or ID
        min_price (float): [Optional] Minimum price filter
        max_price (float): [Optional] Maximum price filter
        in_stock_only (bool): [Optional] Only show in-stock items (default: True)
        limit (int): [Optional] Maximum results per page (default: 10, max: 100)
        
    Returns:
        dict: {
            "from": int,
            "to": int,
            "total": int,
            "currentPage": int,
            "totalPages": int,
            "products": [
                {
                    "sku": int,
                    "name": str,
                    "salePrice": float,
                    "regularPrice": float,
                    "onSale": bool,
                    "inStoreAvailability": bool,
                    "onlineAvailability": bool,
                    "thumbnailImage": str,
                    "url": str
                }
            ]
        }
    """
    pass


def get_product_details(sku: int) -> dict:
    """
    Get detailed information about a specific product.
    
    Args:
        sku (int): Best Buy product SKU
        
    Returns:
        dict: {
            "sku": int,
            "name": str,
            "description": str,
            "longDescription": str,
            "salePrice": float,
            "regularPrice": float,
            "onSale": bool,
            "customerReviewAverage": float,
            "customerReviewCount": int,
            "images": {
                "thumbnailImage": str,
                "mediumImage": str,
                "largeImage": str
            },
            "manufacturer": str,
            "modelNumber": str,
            "categoryPath": [{"id": str, "name": str}],
            "features": [{"feature": str}]
        }
    """
    pass


def get_product_reviews(sku: int, limit: int = 10) -> dict:
    """
    Get customer reviews for a product.
    
    Args:
        sku (int): Best Buy product SKU
        limit (int): [Optional] Number of reviews to return (default: 10)
        
    Returns:
        dict: {
            "sku": int,
            "overallRating": float,
            "totalReviewCount": int,
            "reviews": [
                {
                    "id": int,
                    "rating": int,
                    "reviewer": {"displayName": str},
                    "submissionTime": str,
                    "title": str,
                    "reviewText": str,
                    "helpfulness": int
                }
            ]
        }
    """
    pass


def get_categories() -> dict:
    """
    Get all product categories available at Best Buy.
    
    Returns:
        dict: {
            "categories": [
                {
                    "id": str,
                    "name": str,
                    "path": [{"id": str, "name": str}],
                    "subCategories": [dict]
                }
            ]
        }
    """
    pass


def get_stores(city: str = None, state: str = None, zip_code: str = None, 
               lat: float = None, lng: float = None, radius: int = 25) -> dict:
    """
    Find Best Buy store locations.
    
    Args:
        city (str): [Optional] City name filter
        state (str): [Optional] State abbreviation filter
        zip_code (str): [Optional] ZIP code filter
        lat (float): [Optional] Latitude for location-based search
        lng (float): [Optional] Longitude for location-based search
        radius (int): [Optional] Search radius in miles (default: 25)
        
    Returns:
        dict: {
            "stores": [
                {
                    "storeId": int,
                    "storeType": str,
                    "name": str,
                    "address": str,
                    "city": str,
                    "state": str,
                    "zip": str,
                    "phone": str,
                    "hours": str,
                    "services": [str],
                    "lat": float,
                    "lng": float
                }
            ]
        }
    """
    pass
