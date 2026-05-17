
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Price(BaseModel):
    """Price with currency."""
    value: float = Field(..., ge=0, description="Monetary amount")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="ISO 4217 currency code")

class Seller(BaseModel):
    """Seller information."""
    username: str = Field(..., description="Seller username")
    feedback_score: int = Field(..., ge=0, description="Feedback score")
    feedback_percentage: Optional[float] = Field(None, ge=0, le=100, description="Positive feedback percentage")

class Buyer(BaseModel):
    """Buyer information."""
    username: str = Field(..., description="Buyer username")
    email: str = Field(..., description="Buyer email")

class SearchItem(BaseModel):
    """Search result item."""
    item_id: str = Field(..., description="Item ID")
    title: str = Field(..., description="Item title")
    price: Price = Field(..., description="Item price")
    condition: str = Field(..., description="Item condition")
    seller: Seller = Field(..., description="Seller info")
    listing_url: str = Field(..., description="Listing URL")
    thumbnail: str = Field(..., description="Thumbnail URL")

class ItemDetails(BaseModel):
    """Full item details."""
    item_id: str = Field(..., description="Item ID")
    title: str = Field(..., description="Item title")
    description: str = Field(..., description="Item description")
    price: Price = Field(..., description="Item price")
    condition: str = Field(..., description="Item condition")
    seller: Seller = Field(..., description="Seller info")
    images: List[str] = Field(default=[], description="Image URLs")
    item_specifics: Dict[str, Any] = Field(default={}, description="Item attributes")
    shipping_options: List[Dict[str, Any]] = Field(default=[], description="Shipping options")
    return_policy: Dict[str, Any] = Field(default={}, description="Return policy")

class Listing(BaseModel):
    """Created listing."""
    listing_id: str = Field(..., description="Listing ID")
    status: str = Field(..., description="Listing status")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Creation timestamp")
    url: str = Field(..., description="Listing URL")

class Order(BaseModel):
    """Order details."""
    order_id: str = Field(..., description="Order ID")
    status: str = Field(..., description="Order status")
    buyer: Buyer = Field(..., description="Buyer info")
    items: List[Dict[str, Any]] = Field(default=[], description="Order items")
    total: Price = Field(..., description="Order total")
    shipping_address: Dict[str, Any] = Field(default={}, description="Shipping address")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Order timestamp")

class Category(BaseModel):
    """Category information."""
    category_id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    level: int = Field(..., ge=0, description="Category level")

class EbayScenario(BaseModel):
    """eBay marketplace scenario."""
    items: Dict[str, ItemDetails] = Field(default={}, description="All items")
    listings: Dict[str, Listing] = Field(default={}, description="All listings")
    orders: Dict[str, Order] = Field(default={}, description="All orders")
    categories: Dict[str, Category] = Field(default={}, description="All categories")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp")

Scenario_Schema = [Price, Seller, Buyer, SearchItem, ItemDetails, Listing, Order, Category, EbayScenario]

# Section 2: Class
class EbayServer:
    def __init__(self):
        """Initialize eBay server with empty state."""
        self.items: Dict[str, ItemDetails] = {}
        self.listings: Dict[str, Listing] = {}
        self.orders: Dict[str, Order] = {}
        self.categories: Dict[str, Category] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the server."""
        model = EbayScenario(**scenario)
        self.items = model.items
        self.listings = model.listings
        self.orders = model.orders
        self.categories = model.categories
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "items": {k: v.model_dump() for k, v in self.items.items()},
            "listings": {k: v.model_dump() for k, v in self.listings.items()},
            "orders": {k: v.model_dump() for k, v in self.orders.items()},
            "categories": {k: v.model_dump() for k, v in self.categories.items()},
            "current_time": self.current_time
        }

    def search_items(self, keywords: str, category_id: Optional[str], limit: Optional[int], sort: Optional[str]) -> dict:
        """Search for items matching criteria."""
        results = []
        for item in self.items.values():
            if keywords.lower() in item.title.lower() or keywords.lower() in item.description.lower():
                if category_id is None or category_id in item.item_specifics.get("category_id", ""):
                    results.append(SearchItem(
                        item_id=item.item_id,
                        title=item.title,
                        price=item.price,
                        condition=item.condition,
                        seller=Seller(username=item.seller.username, feedback_score=item.seller.feedback_score),
                        listing_url=f"https://ebay.com/itm/{item.item_id}",
                        thumbnail=item.images[0] if item.images else ""
                    ))
        
        if sort == "price":
            results.sort(key=lambda x: x.price.value)
        elif sort == "-price":
            results.sort(key=lambda x: x.price.value, reverse=True)
        
        max_limit = limit if limit else 10
        results = results[:max_limit]
        
        return {
            "total": len(results),
            "items": [r.model_dump() for r in results]
        }

    def get_item_details(self, item_id: str) -> dict:
        """Retrieve full item details."""
        item = self.items[item_id]
        return item.model_dump()

    def create_listing(self, title: str, description: str, category_id: str, price: float, currency: Optional[str], condition: Optional[str], quantity: Optional[int]) -> dict:
        """Create a new listing."""
        listing_id = f"LST{len(self.listings) + 1:06d}"
        curr = currency if currency else "USD"
        cond = condition if condition else "NEW"
        qty = quantity if quantity else 1
        
        listing = Listing(
            listing_id=listing_id,
            status="ACTIVE",
            created_at=self.current_time,
            url=f"https://ebay.com/itm/{listing_id}"
        )
        
        item = ItemDetails(
            item_id=listing_id,
            title=title,
            description=description,
            price=Price(value=price, currency=curr),
            condition=cond,
            seller=Seller(username="current_user", feedback_score=0),
            item_specifics={"category_id": category_id, "quantity": qty}
        )
        
        self.listings[listing_id] = listing
        self.items[listing_id] = item
        
        return listing.model_dump()

    def get_order_details(self, order_id: str) -> dict:
        """Retrieve order details."""
        order = self.orders[order_id]
        return order.model_dump()

    def get_categories(self, marketplace_id: Optional[str]) -> dict:
        """Retrieve category taxonomy."""
        return {
            "categories": [c.model_dump() for c in self.categories.values()]
        }

# Section 3: MCP Tools
mcp = FastMCP(name="EbayServer")
server = EbayServer()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the eBay server.

    Args:
        scenario (dict): Scenario dictionary matching EbayScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        server.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current eBay server state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return server.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_items(keywords: str, category_id: str = None, limit: int = None, sort: str = None) -> dict:
    """
    Search for items on the eBay marketplace using keywords and optional filters.

    Args:
        keywords (str): Search query terms used to find items on the eBay marketplace.
        category_id (str): [Optional] The eBay category ID used to classify items into specific product taxonomies.
        limit (int): [Optional] Maximum number of search results to return (default: 10, maximum: 100).
        sort (str): [Optional] Sort order for results (e.g., 'bestMatch', 'price' for ascending price, '-price' for descending price).

    Returns:
        total (int): Total number of items matching the search criteria.
        items (list): List of items matching the search query.
    """
    try:
        if not keywords or not isinstance(keywords, str):
            raise ValueError("Keywords must be a non-empty string")
        return server.search_items(keywords, category_id, limit, sort)
    except Exception as e:
        raise e

@mcp.tool()
def get_item_details(item_id: str) -> dict:
    """
    Retrieve comprehensive details for a specific eBay item listing.

    Args:
        item_id (str): The unique identifier of the eBay item listing.

    Returns:
        item_id (str): The unique identifier of the eBay item listing.
        title (str): The title of the item listing.
        description (str): Detailed text description of the item.
        price (dict): Item price with value and currency.
        condition (str): The physical condition state of the item.
        seller (dict): Seller information.
        images (list): URLs of item images.
        item_specifics (dict): Key-value pairs of item attributes and specifications.
        shipping_options (list): Available shipping methods and costs.
        return_policy (dict): Details of the seller's return policy.
    """
    try:
        if not item_id or not isinstance(item_id, str):
            raise ValueError("Item ID must be a non-empty string")
        if item_id not in server.items:
            raise ValueError(f"Item {item_id} not found")
        return server.get_item_details(item_id)
    except Exception as e:
        raise e

@mcp.tool()
def create_listing(title: str, description: str, category_id: str, price: float, currency: str = None, condition: str = None, quantity: int = None) -> dict:
    """
    Create a new item listing on eBay for selling products (seller operation).

    Args:
        title (str): The title of the item listing.
        description (str): Detailed text description of the item.
        category_id (str): The eBay category ID used to classify items into specific product taxonomies.
        price (float): The numerical monetary amount for the item price.
        currency (str): [Optional] The ISO 4217 currency code representing the monetary unit (e.g., USD, EUR, GBP).
        condition (str): [Optional] The physical condition state of the item (e.g., NEW, USED, REFURBISHED).
        quantity (int): [Optional] Number of items available for sale.

    Returns:
        listing_id (str): The unique identifier of the created eBay listing.
        status (str): Current status of the listing (e.g., ACTIVE, PENDING).
        created_at (str): ISO 8601 timestamp when the listing was created.
        url (str): The URL to view the created listing on eBay.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValueError("Description must be a non-empty string")
        if not category_id or not isinstance(category_id, str):
            raise ValueError("Category ID must be a non-empty string")
        return server.create_listing(title, description, category_id, price, currency, condition, quantity)
    except Exception as e:
        raise e

@mcp.tool()
def get_order_details(order_id: str) -> dict:
    """
    Retrieve detailed information about a specific eBay order transaction.

    Args:
        order_id (str): The unique identifier of the eBay order transaction.

    Returns:
        order_id (str): The unique identifier of the eBay order transaction.
        status (str): Current fulfillment status of the order.
        buyer (dict): Buyer information.
        items (list): Line items included in the order.
        total (dict): Order total with value and currency.
        shipping_address (dict): Delivery address for the order.
        created_at (str): ISO 8601 timestamp when the order was placed.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        if order_id not in server.orders:
            raise ValueError(f"Order {order_id} not found")
        return server.get_order_details(order_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_categories(marketplace_id: str = None) -> dict:
    """
    Retrieve the category taxonomy for a specific eBay marketplace.

    Args:
        marketplace_id (str): [Optional] The eBay marketplace ID (e.g., 'EBAY_US', 'EBAY_GB') to retrieve categories for.

    Returns:
        categories (list): List of available categories in the marketplace.
    """
    try:
        return server.get_categories(marketplace_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
