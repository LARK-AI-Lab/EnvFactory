# Data Source: https://fakestoreapi.com/docs
# Server: FakeStoreServer
# Category: ecommerce


def get_all_products(limit: int = None, sort: str = None) -> list:
    """
    Get all products from the fake store.
    
    Args:
        limit (int): [Optional] Limit number of results
        sort (str): [Optional] Sort order ("asc" or "desc")
        
    Returns:
        list: [
            {
                "id": int,
                "title": str,
                "price": float,
                "description": str,
                "category": str,
                "image": str,
                "rating": {"rate": float, "count": int}
            }
        ]
    """
    pass


def get_product_by_id(product_id: int) -> dict:
    """
    Get a specific product by ID.
    
    Args:
        product_id (int): Product ID
        
    Returns:
        dict: {
            "id": int,
            "title": str,
            "price": float,
            "description": str,
            "category": str,
            "image": str,
            "rating": {"rate": float, "count": int}
        }
    """
    pass


def get_products_by_category(category: str) -> list:
    """
    Get all products in a specific category.
    
    Args:
        category (str): Category name (e.g., "electronics", "jewelery", "men's clothing", "women's clothing")
        
    Returns:
        list: Products array with full details
    """
    pass


def get_all_categories() -> list:
    """
    Get all available product categories.
    
    Returns:
        list: ["electronics", "jewelery", "men's clothing", "women's clothing"]
    """
    pass


def create_product(title: str, price: float, description: str, 
                  category: str, image: str) -> dict:
    """
    Create a new product (returns mock response).
    
    Args:
        title (str): Product title
        price (float): Product price
        description (str): Product description
        category (str): Product category
        image (str): Product image URL
        
    Returns:
        dict: {
            "id": int,
            "title": str,
            "price": float,
            "description": str,
            "category": str,
            "image": str
        }
    """
    pass


def get_all_carts(limit: int = None, sort: str = None) -> list:
    """
    Get all shopping carts.
    
    Args:
        limit (int): [Optional] Limit number of results
        sort (str): [Optional] Sort order ("asc" or "desc")
        
    Returns:
        list: [
            {
                "id": int,
                "userId": int,
                "date": str,
                "products": [
                    {"productId": int, "quantity": int}
                ]
            }
        ]
    """
    pass


def get_user_cart(user_id: int) -> dict:
    """
    Get cart for a specific user.
    
    Args:
        user_id (int): User ID
        
    Returns:
        dict: {
            "id": int,
            "userId": int,
            "date": str,
            "products": [
                {"productId": int, "quantity": int}
            ]
        }
    """
    pass


def user_login(username: str, password: str) -> dict:
    """
    Authenticate a user and get token.
    
    Args:
        username (str): Username
        password (str): Password
        
    Returns:
        dict: {
            "token": str
        }
    """
    pass
