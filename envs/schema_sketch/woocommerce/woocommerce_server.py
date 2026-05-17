# Data Source: https://woocommerce.github.io/woocommerce-rest-api-docs/
# Server: WooCommerce
# Category: E-commerce Platform


def get_products(per_page: int = 10, page: int = 1, category: str = None, 
                search: str = None) -> list:
    """
    Retrieve products from the WooCommerce store.
    
    Args:
        per_page (int): [Optional] Items per page (max 100, default 10)
        page (int): [Optional] Page number (default 1)
        category (str): [Optional] Filter by category slug
        search (str): [Optional] Search keyword
        
    Returns:
        list: Array of product objects:
        {
            "id": int,
            "name": str,
            "slug": str,
            "type": str,
            "status": str,
            "price": str,
            "regular_price": str,
            "sale_price": str,
            "stock_quantity": int,
            "categories": list[{"id": int, "name": str}],
            "images": list[{"src": str}]
        }
    """
    pass


def create_product(name: str, type: str = "simple", regular_price: str = "0.00",
                  sale_price: str = None, description: str = None, 
                  stock_quantity: int = None) -> dict:
    """
    Create a new product in the WooCommerce store.
    
    Args:
        name (str): Product name
        type (str): [Optional] "simple", "grouped", "external", "variable"
        regular_price (str): [Optional] Regular price (default "0.00")
        sale_price (str): [Optional] Sale price
        description (str): [Optional] Full description (HTML allowed)
        stock_quantity (int): [Optional] Stock quantity
        
    Returns:
        dict: Created product object with ID and details
    """
    pass


def get_orders(status: str = None, per_page: int = 10, page: int = 1,
              customer_id: int = None) -> list:
    """
    Retrieve orders from the store.
    
    Args:
        status (str): [Optional] "pending", "processing", "completed", "cancelled"
        per_page (int): [Optional] Items per page (default 10)
        page (int): [Optional] Page number (default 1)
        customer_id (int): [Optional] Filter by customer ID
        
    Returns:
        list: Array of order objects:
        {
            "id": int,
            "number": str,
            "status": str,
            "currency": str,
            "total": str,
            "customer_id": int,
            "billing": dict,
            "shipping": dict,
            "line_items": list[{"product_id": int, "name": str, "quantity": int, "price": str}],
            "date_created": str
        }
    """
    pass


def create_order(line_items: list, billing: dict = None, shipping: dict = None,
                payment_method: str = None, set_paid: bool = False) -> dict:
    """
    Create a new order in the store.
    
    Args:
        line_items (list): List of items with product_id and quantity
        billing (dict): [Optional] Billing address
        shipping (dict): [Optional] Shipping address
        payment_method (str): [Optional] Payment method ID
        set_paid (bool): [Optional] Mark order as paid
        
    Returns:
        dict: Created order object with ID and details
    """
    pass


def get_customers(per_page: int = 10, page: int = 1, search: str = None) -> list:
    """
    Retrieve customers from the store.
    
    Args:
        per_page (int): [Optional] Items per page (default 10)
        page (int): [Optional] Page number (default 1)
        search (str): [Optional] Search by name or email
        
    Returns:
        list: Array of customer objects:
        {
            "id": int,
            "email": str,
            "first_name": str,
            "last_name": str,
            "billing": dict,
            "shipping": dict,
            "orders_count": int,
            "total_spent": str
        }
    """
    pass
