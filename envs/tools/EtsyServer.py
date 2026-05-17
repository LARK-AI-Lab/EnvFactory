
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Price(BaseModel):
    """Price information for a listing."""
    amount: float = Field(..., ge=0, description="Numeric price value")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="Three-letter ISO currency code")

class PriceWithDivisor(BaseModel):
    """Price information with divisor for formatting."""
    amount: float = Field(..., ge=0, description="Raw numeric price value")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="Three-letter ISO currency code")
    divisor: int = Field(..., gt=0, description="Divisor to convert raw amount")

class SearchListing(BaseModel):
    """Search result listing."""
    listing_id: int = Field(..., ge=0, description="Unique listing identifier")
    title: str = Field(..., description="Listing title")
    price: Price = Field(..., description="Price information")
    quantity: int = Field(..., ge=0, description="Available stock quantity")
    shop_name: str = Field(..., description="Shop name")
    url: str = Field(..., description="Listing URL")
    images: List[str] = Field(default=[], description="Image URLs")

class Shop(BaseModel):
    """Shop information."""
    shop_id: int = Field(..., ge=0, description="Unique shop identifier")
    shop_name: str = Field(..., description="Shop name")
    url: str = Field(..., description="Shop URL")
    rating: float = Field(..., ge=0, le=5, description="Average rating")

class Image(BaseModel):
    """Image with dimensions."""
    url: str = Field(..., description="Image URL")
    full_height: int = Field(..., gt=0, description="Image height in pixels")
    full_width: int = Field(..., gt=0, description="Image width in pixels")

class ListingDetails(BaseModel):
    """Detailed listing information."""
    listing_id: int = Field(..., ge=0, description="Unique listing identifier")
    title: str = Field(..., description="Listing title")
    description: str = Field(..., description="Item description")
    price: PriceWithDivisor = Field(..., description="Price information")
    quantity: int = Field(..., ge=0, description="Available stock quantity")
    shop: Shop = Field(..., description="Shop information")
    images: List[Image] = Field(default=[], description="Image objects")
    tags: List[str] = Field(default=[], description="Search tags")
    materials: List[str] = Field(default=[], description="Materials used")
    shipping_profile: Dict[str, Any] = Field(default={}, description="Shipping configuration")

class CreatedListing(BaseModel):
    """Newly created listing."""
    listing_id: int = Field(..., ge=0, description="Unique listing identifier")
    title: str = Field(..., description="Listing title")
    state: str = Field(..., description="Listing state")
    creation_tsz: float = Field(..., ge=0, description="Creation timestamp")
    url: str = Field(..., description="Listing URL")

class ShopListing(BaseModel):
    """Shop listing summary."""
    listing_id: int = Field(..., ge=0, description="Unique listing identifier")
    title: str = Field(..., description="Listing title")
    state: str = Field(..., description="Listing state")
    price: Price = Field(..., description="Price information")

class Receipt(BaseModel):
    """Order receipt."""
    receipt_id: int = Field(..., ge=0, description="Unique receipt identifier")
    buyer_email: str = Field(..., description="Buyer email")
    name: str = Field(..., description="Buyer name")
    grandtotal: Price = Field(..., description="Total amount")
    status: str = Field(..., description="Fulfillment status")
    created_tsz: float = Field(..., ge=0, description="Creation timestamp")
    transactions: List[Dict[str, Any]] = Field(default=[], description="Transaction objects")

class EtsyScenario(BaseModel):
    """Main scenario model for Etsy marketplace."""
    listings: Dict[int, ListingDetails] = Field(default={}, description="All listings by ID")
    shops: Dict[int, Shop] = Field(default={}, description="All shops by ID")
    receipts: Dict[int, Receipt] = Field(default={}, description="All receipts by ID")
    shop_listings: Dict[int, List[int]] = Field(default={}, description="Shop ID to listing IDs mapping")

Scenario_Schema = [Price, PriceWithDivisor, SearchListing, Shop, Image, ListingDetails, CreatedListing, ShopListing, Receipt, EtsyScenario]

# Section 2: Class
class EtsyServer:
    def __init__(self):
        """Initialize Etsy server with empty state."""
        self.listings: Dict[int, ListingDetails] = {}
        self.shops: Dict[int, Shop] = {}
        self.receipts: Dict[int, Receipt] = {}
        self.shop_listings: Dict[int, List[int]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the server instance."""
        model = EtsyScenario(**scenario)
        self.listings = model.listings
        self.shops = model.shops
        self.receipts = model.receipts
        self.shop_listings = model.shop_listings

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "listings": {lid: listing.model_dump() for lid, listing in self.listings.items()},
            "shops": {sid: shop.model_dump() for sid, shop in self.shops.items()},
            "receipts": {rid: receipt.model_dump() for rid, receipt in self.receipts.items()},
            "shop_listings": self.shop_listings
        }

    def search_listings(self, keywords: str, category: Optional[str], min_price: Optional[float], max_price: Optional[float], limit: int) -> dict:
        """Search for active listings using keywords and filters."""
        results = []
        for listing in self.listings.values():
            if keywords.lower() not in listing.title.lower() and keywords.lower() not in listing.description.lower() and not any(keywords.lower() in tag.lower() for tag in listing.tags):
                continue
            if category and category.lower() not in listing.tags:
                continue
            price_val = listing.price.amount / listing.price.divisor
            if min_price is not None and price_val < min_price:
                continue
            if max_price is not None and price_val > max_price:
                continue
            results.append({
                "listing_id": listing.listing_id,
                "title": listing.title,
                "price": {"amount": price_val, "currency": listing.price.currency},
                "quantity": listing.quantity,
                "shop_name": listing.shop.shop_name,
                "url": f"https://www.etsy.com/listing/{listing.listing_id}",
                "images": [img.url for img in listing.images]
            })
            if len(results) >= limit:
                break
        return {"count": len(results), "results": results}

    def get_listing_details(self, listing_id: int) -> dict:
        """Retrieve comprehensive details for a specific listing."""
        listing = self.listings[listing_id]
        return listing.model_dump()

    def create_listing(self, shop_id: int, title: str, description: str, price: float, quantity: int, taxonomy_id: int, who_made: str) -> dict:
        """Create a new product listing within a shop."""
        listing_id = max(self.listings.keys(), default=0) + 1
        shop = self.shops[shop_id]
        new_listing = ListingDetails(
            listing_id=listing_id,
            title=title,
            description=description,
            price=PriceWithDivisor(amount=price * 100, currency="USD", divisor=100),
            quantity=quantity,
            shop=shop,
            images=[],
            tags=[],
            materials=[],
            shipping_profile={}
        )
        self.listings[listing_id] = new_listing
        if shop_id not in self.shop_listings:
            self.shop_listings[shop_id] = []
        self.shop_listings[shop_id].append(listing_id)
        return {
            "listing_id": listing_id,
            "title": title,
            "state": "active",
            "creation_tsz": 1709640834.0,
            "url": f"https://www.etsy.com/listing/{listing_id}"
        }

    def get_shop_listings(self, shop_id: int, status: str, limit: int) -> dict:
        """Retrieve all listings for a specific shop."""
        listing_ids = self.shop_listings.get(shop_id, [])
        results = []
        for lid in listing_ids[:limit]:
            if lid in self.listings:
                listing = self.listings[lid]
                price_val = listing.price.amount / listing.price.divisor
                results.append({
                    "listing_id": listing.listing_id,
                    "title": listing.title,
                    "state": status,
                    "price": {"amount": price_val, "currency": listing.price.currency}
                })
        return {"count": len(results), "results": results}

    def get_receipts(self, shop_id: int, min_created: Optional[int], max_created: Optional[int]) -> dict:
        """Retrieve order receipts for a seller's shop."""
        results = []
        for receipt in self.receipts.values():
            if min_created is not None and receipt.created_tsz < min_created:
                continue
            if max_created is not None and receipt.created_tsz > max_created:
                continue
            results.append(receipt.model_dump())
        return {"count": len(results), "results": results}

# Section 3: MCP Tools
mcp = FastMCP(name="EtsyServer")
server = EtsyServer()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Etsy server.

    Args:
        scenario (dict): Scenario dictionary matching EtsyScenario schema.

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
    Save current Etsy server state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return server.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_listings(keywords: str, category: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, limit: int = 10) -> dict:
    """
    Search for active listings on the Etsy marketplace.

    Args:
        keywords (str): Search keywords to match against listing titles, tags, and descriptions.
        category (str) [Optional]: Category slug to filter results.
        min_price (float) [Optional]: Minimum price threshold.
        max_price (float) [Optional]: Maximum price threshold.
        limit (int): Maximum number of results to return (default: 10, maximum: 100).

    Returns:
        count (int): Total number of listings matching criteria.
        results (list): Array of listing objects.
    """
    try:
        if not keywords or not isinstance(keywords, str):
            raise ValueError("Keywords must be a non-empty string")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        return server.search_listings(keywords, category, min_price, max_price, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_listing_details(listing_id: int) -> dict:
    """
    Retrieve comprehensive details for a specific Etsy listing.

    Args:
        listing_id (int): Unique identifier of the Etsy listing.

    Returns:
        listing_id (int): Unique listing identifier.
        title (str): Listing title.
        description (str): Item description.
        price (dict): Price information with divisor.
        quantity (int): Available stock quantity.
        shop (dict): Shop information.
        images (list): Image objects with dimensions.
        tags (list): Search tags.
        materials (list): Materials used.
        shipping_profile (dict): Shipping configuration.
    """
    try:
        if listing_id not in server.listings:
            raise ValueError(f"Listing {listing_id} not found")
        return server.get_listing_details(listing_id)
    except Exception as e:
        raise e

@mcp.tool()
def create_listing(shop_id: int, title: str, description: str, price: float, quantity: int, taxonomy_id: int, who_made: str = "i_did") -> dict:
    """
    Create a new product listing within a specified Etsy shop.

    Args:
        shop_id (int): Unique identifier of the Etsy shop.
        title (str): Listing title (maximum 140 characters).
        description (str): Detailed item description.
        price (float): Item price in shop's default currency.
        quantity (int): Available quantity for sale.
        taxonomy_id (int): Etsy taxonomy/category classification ID.
        who_made (str) [Optional]: Who manufactured the item (default: 'i_did').

    Returns:
        listing_id (int): Unique identifier of newly created listing.
        title (str): Title of created listing.
        state (str): Current state of listing.
        creation_tsz (float): Unix timestamp of creation.
        url (str): URL to view the listing.
    """
    try:
        if shop_id not in server.shops:
            raise ValueError(f"Shop {shop_id} not found")
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValueError("Description must be a non-empty string")
        result = server.create_listing(shop_id, title, description, price, quantity, taxonomy_id, who_made)
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_shop_listings(shop_id: int, status: str = "active", limit: int = 25) -> dict:
    """
    Retrieve all listings for a specific Etsy shop.

    Args:
        shop_id (int): Unique identifier of the Etsy shop.
        status (str) [Optional]: Filter by listing state (default: 'active').
        limit (int) [Optional]: Maximum number of listings per page (default: 25, maximum: 100).

    Returns:
        count (int): Total number of listings returned.
        results (list): Array of listing summary objects.
    """
    try:
        if shop_id not in server.shops:
            raise ValueError(f"Shop {shop_id} not found")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        return server.get_shop_listings(shop_id, status, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_receipts(shop_id: int, min_created: Optional[int] = None, max_created: Optional[int] = None) -> dict:
    """
    Retrieve order receipts for a seller's shop.

    Args:
        shop_id (int): Unique identifier of the Etsy shop.
        min_created (int) [Optional]: Minimum creation timestamp (Unix epoch seconds).
        max_created (int) [Optional]: Maximum creation timestamp (Unix epoch seconds).

    Returns:
        count (int): Total number of receipts matching criteria.
        results (list): Array of order receipt objects.
    """
    try:
        if shop_id not in server.shops:
            raise ValueError(f"Shop {shop_id} not found")
        return server.get_receipts(shop_id, min_created, max_created)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
