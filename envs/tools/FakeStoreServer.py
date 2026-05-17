
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Rating(BaseModel):
    """Product rating statistics."""
    rate: float = Field(..., ge=0, le=5, description="Average rating score (0-5)")
    count: int = Field(..., ge=0, description="Total number of ratings")

class Product(BaseModel):
    """Product entity."""
    id: int = Field(..., ge=1, description="Product ID")
    title: str = Field(..., description="Product name")
    price: float = Field(..., ge=0, description="Product price in USD")
    description: str = Field(..., description="Product description")
    category: str = Field(..., description="Product category")
    image: str = Field(..., description="Product image URL")
    rating: Rating = Field(..., description="Product rating")

class CartItem(BaseModel):
    """Cart item entity."""
    productId: int = Field(..., ge=1, description="Product ID")
    quantity: int = Field(..., ge=1, description="Quantity")

class Cart(BaseModel):
    """Shopping cart entity."""
    id: int = Field(..., ge=1, description="Cart ID")
    userId: int = Field(..., ge=1, description="User ID")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$", description="Cart date in ISO 8601 format")
    products: List[CartItem] = Field(default=[], description="Cart items")

class FakeStoreScenario(BaseModel):
    """Main scenario model for fake store."""
    products: Dict[int, Product] = Field(default={}, description="Product catalog")
    carts: Dict[int, Cart] = Field(default={}, description="Shopping carts")
    categories: List[str] = Field(default=["electronics", "jewelery", "men's clothing", "women's clothing"], description="Available categories")
    next_product_id: int = Field(default=1, ge=1, description="Next product ID")
    user_credentials: Dict[str, str] = Field(default={
        "mor_2314": "83r5^_",
        "johnd": "m38rmF$",
        "kevinryan": "kev02937@",
        "donero": "ewedon",
        "derek": "jklg*_56"
    }, description="Username to password mapping")

Scenario_Schema = [Rating, Product, CartItem, Cart, FakeStoreScenario]

# Section 2: Class
class FakeStoreAPI:
    def __init__(self):
        """Initialize fake store API with empty state."""
        self.products: Dict[int, Product] = {}
        self.carts: Dict[int, Cart] = {}
        self.categories: List[str] = []
        self.next_product_id: int = 1
        self.user_credentials: Dict[str, str] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = FakeStoreScenario(**scenario)
        self.products = model.products
        self.carts = model.carts
        self.categories = model.categories
        self.next_product_id = model.next_product_id
        self.user_credentials = model.user_credentials

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "products": {pid: p.model_dump() for pid, p in self.products.items()},
            "carts": {cid: c.model_dump() for cid, c in self.carts.items()},
            "categories": self.categories,
            "next_product_id": self.next_product_id,
            "user_credentials": self.user_credentials
        }

    def get_all_products(self, limit: Optional[int], sort: Optional[str]) -> dict:
        """Retrieve all products with optional limit and sort."""
        products_list = list(self.products.values())
        if sort == "desc":
            products_list.sort(key=lambda p: p.id, reverse=True)
        else:
            products_list.sort(key=lambda p: p.id)
        if limit:
            products_list = products_list[:limit]
        return {"products": [p.model_dump() for p in products_list]}

    def get_product_by_id(self, product_id: int) -> dict:
        """Retrieve product by ID."""
        product = self.products[product_id]
        return product.model_dump()

    def get_products_by_category(self, category: str) -> dict:
        """Retrieve products by category."""
        products_list = [p for p in self.products.values() if p.category == category]
        return {"products": [p.model_dump() for p in products_list]}

    def get_all_categories(self) -> dict:
        """Retrieve all categories."""
        return {"categories": self.categories}

    def create_product(self, title: str, price: float, description: str, category: str, image: str) -> dict:
        """Create a new product."""
        product_id = self.next_product_id
        self.next_product_id += 1
        product = Product(
            id=product_id,
            title=title,
            price=price,
            description=description,
            category=category,
            image=image,
            rating=Rating(rate=0.0, count=0)
        )
        self.products[product_id] = product
        return product.model_dump()

    def get_all_carts(self, limit: Optional[int], sort: Optional[str]) -> dict:
        """Retrieve all carts with optional limit and sort."""
        carts_list = list(self.carts.values())
        if sort == "desc":
            carts_list.sort(key=lambda c: c.id, reverse=True)
        else:
            carts_list.sort(key=lambda c: c.id)
        if limit:
            carts_list = carts_list[:limit]
        return {"carts": [c.model_dump() for c in carts_list]}

    def get_user_cart(self, user_id: int) -> dict:
        """Retrieve cart by user ID."""
        for cart in self.carts.values():
            if cart.userId == user_id:
                return cart.model_dump()
        raise ValueError(f"Cart for user {user_id} not found")

    def user_login(self, username: str, password: str) -> dict:
        """Authenticate user and return token."""
        if username in self.user_credentials and self.user_credentials[username] == password:
            return {"token": f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{username}"}
        raise ValueError("Invalid credentials")

# Section 3: MCP Tools
mcp = FastMCP(name="FakeStoreServer")
api = FakeStoreAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the fake store API.

    Args:
        scenario (dict): Scenario dictionary matching FakeStoreScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current fake store state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_all_products(limit: Optional[int] = None, sort: Optional[str] = None) -> dict:
    """
    Retrieve all products with optional limit and sort.

    Args:
        limit (int) [Optional]: Maximum number of results to return.
        sort (str) [Optional]: Sort order ('asc' or 'desc').

    Returns:
        products (array): List of product objects.
    """
    try:
        return api.get_all_products(limit, sort)
    except Exception as e:
        raise e

@mcp.tool()
def get_product_by_id(product_id: int) -> dict:
    """
    Retrieve product by ID.

    Args:
        product_id (int): The unique identifier of the product.

    Returns:
        id (int): Product ID.
        title (str): Product name.
        price (float): Product price in USD.
        description (str): Product description.
        category (str): Product category.
        image (str): Product image URL.
        rating (object): Product rating statistics.
    """
    try:
        if product_id not in api.products:
            raise ValueError(f"Product {product_id} not found")
        return api.get_product_by_id(product_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_products_by_category(category: str) -> dict:
    """
    Retrieve products by category.

    Args:
        category (str): Product category classification.

    Returns:
        products (array): List of products in the category.
    """
    try:
        if not category or not isinstance(category, str):
            raise ValueError("Category must be a non-empty string")
        return api.get_products_by_category(category)
    except Exception as e:
        raise e

@mcp.tool()
def get_all_categories() -> dict:
    """
    Retrieve all available categories.

    Returns:
        categories (array): List of category names.
    """
    try:
        return api.get_all_categories()
    except Exception as e:
        raise e

@mcp.tool()
def create_product(title: str, price: float, description: str, category: str, image: str) -> dict:
    """
    Create a new product.

    Args:
        title (str): Product name.
        price (float): Product price in USD.
        description (str): Product description.
        category (str): Product category.
        image (str): Product image URL.

    Returns:
        id (int): Assigned product ID.
        title (str): Product name.
        price (float): Product price in USD.
        description (str): Product description.
        category (str): Product category.
        image (str): Product image URL.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValueError("Description must be a non-empty string")
        if not category or not isinstance(category, str):
            raise ValueError("Category must be a non-empty string")
        if not image or not isinstance(image, str):
            raise ValueError("Image must be a non-empty string")
        return api.create_product(title, price, description, category, image)
    except Exception as e:
        raise e

@mcp.tool()
def get_all_carts(limit: Optional[int] = None, sort: Optional[str] = None) -> dict:
    """
    Retrieve all carts with optional limit and sort.

    Args:
        limit (int) [Optional]: Maximum number of results to return.
        sort (str) [Optional]: Sort order ('asc' or 'desc').

    Returns:
        carts (array): List of shopping cart objects.
    """
    try:
        return api.get_all_carts(limit, sort)
    except Exception as e:
        raise e

@mcp.tool()
def get_user_cart(user_id: int) -> dict:
    """
    Retrieve cart by user ID.

    Args:
        user_id (int): The unique identifier of the user.

    Returns:
        id (int): Cart ID.
        userId (int): User ID.
        date (str): Cart date in ISO 8601 format.
        products (array): List of cart items.
    """
    try:
        return api.get_user_cart(user_id)
    except Exception as e:
        raise e

@mcp.tool()
def user_login(username: str, password: str) -> dict:
    """
    Authenticate user and return access token.

    Args:
        username (str): Username credential.
        password (str): Password credential.

    Returns:
        token (str): JWT access token.
    """
    try:
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        return api.user_login(username, password)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
