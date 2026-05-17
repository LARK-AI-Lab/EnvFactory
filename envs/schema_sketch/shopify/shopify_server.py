# Data Source: https://shopify.dev/docs/api/admin-rest/latest
# Server: Shopify
# Category: E-commerce Platform


def get_products(limit: int = 10, vendor: str = None, product_type: str = None) -> list:
    """
    Retrieve products from the store catalog.
    
    Args:
        limit (int): [Optional] Number of products to return (max 250, default 10)
        vendor (str): [Optional] Filter by vendor/brand name
        product_type (str): [Optional] Filter by product category/type
        
    Returns:
        list: Array of product objects:
        {
            "id": int,
            "title": str,
            "body_html": str,
            "vendor": str,
            "product_type": str,
            "variants": list[{
                "id": int,
                "title": str,
                "price": str,
                "sku": str,
                "inventory_quantity": int
            }],
            "images": list[{"src": str}]
        }
    """
    pass


def create_product(title: str, body_html: str = None, vendor: str = None,
                  product_type: str = None, variants: list = None) -> dict:
    """
    Create a new product in the store.
    
    Args:
        title (str): Product name/title
        body_html (str): [Optional] Product description in HTML
        vendor (str): [Optional] Brand or vendor name
        product_type (str): [Optional] Product category
        variants (list): [Optional] List of variant objects with price, sku, inventory_quantity
        
    Returns:
        dict: Created product object with ID and details
    """
    pass


def get_orders(status: str = "any", limit: int = 50, created_at_min: str = None) -> list:
    """
    Retrieve orders from the store.
    
    Args:
        status (str): [Optional] Filter by status - "open", "closed", "cancelled", "any"
        limit (int): [Optional] Number of orders to return (max 250, default 50)
        created_at_min (str): [Optional] Filter by creation date (ISO 8601 format)
        
    Returns:
        list: Array of order objects:
        {
            "id": int,
            "name": str,
            "total_price": str,
            "financial_status": str,
            "fulfillment_status": str,
            "line_items": list[{
                "title": str,
                "quantity": int,
                "price": str
            }]
        }
    """
    pass


def create_order(line_items: list, customer: dict = None, financial_status: str = "pending") -> dict:
    """
    Create a new order in the store.
    
    Args:
        line_items (list): List of line items with variant_id, quantity, price
        customer (dict): [Optional] Customer info with email, first_name, last_name
        financial_status (str): [Optional] "pending", "authorized", "paid"
        
    Returns:
        dict: Created order object with ID and details
    """
    pass


def get_customers(limit: int = 50, email: str = None) -> list:
    """
    Retrieve customers from the store.
    
    Args:
        limit (int): [Optional] Number of customers to return (max 250, default 50)
        email (str): [Optional] Filter by email address
        
    Returns:
        list: Array of customer objects:
        {
            "id": int,
            "email": str,
            "first_name": str,
            "last_name": str,
            "orders_count": int,
            "total_spent": str
        }
    """
    pass
