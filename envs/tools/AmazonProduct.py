
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Price(BaseModel):
    """Price information."""
    amount: float = Field(..., ge=0, description="Price amount")
    currency: str = Field(..., description="Currency code")

class Product(BaseModel):
    """Product search result."""
    ASIN: str = Field(..., pattern=r"^[A-Z0-9]{10}$", description="Amazon ASIN")
    title: str = Field(..., description="Product title")
    detail_page_url: str = Field(..., description="Product URL")
    price: Optional[Price] = Field(default=None, description="Product price")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Rating")
    total_reviews: Optional[int] = Field(default=None, ge=0, description="Review count")

class Item(BaseModel):
    """Detailed product item."""
    ASIN: str = Field(..., pattern=r"^[A-Z0-9]{10}$", description="Amazon ASIN")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(default=None, description="Description")
    features: Optional[List[str]] = Field(default=None, description="Features")
    price: Optional[Price] = Field(default=None, description="Product price")
    images: Optional[List[str]] = Field(default=None, description="Image URLs")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Rating")
    total_reviews: Optional[int] = Field(default=None, ge=0, description="Review count")
    availability: Optional[str] = Field(default=None, description="Availability status")

class Variation(BaseModel):
    """Product variation."""
    ASIN: str = Field(..., pattern=r"^[A-Z0-9]{10}$", description="Amazon ASIN")
    title: str = Field(..., description="Product title")
    variation_attributes: Optional[Dict[str, str]] = Field(default=None, description="Variation attributes")
    price: Optional[Price] = Field(default=None, description="Product price")
    availability: Optional[str] = Field(default=None, description="Availability status")

class BrowseNode(BaseModel):
    """Browse node category."""
    id: str = Field(..., description="Browse node ID")
    name: str = Field(..., description="Category name")
    is_root: bool = Field(..., description="Is root category")
    children: Optional[List[str]] = Field(default=None, description="Child node IDs")
    ancestors: Optional[List[str]] = Field(default=None, description="Ancestor node IDs")

class Deal(BaseModel):
    """Product deal."""
    ASIN: str = Field(..., pattern=r"^[A-Z0-9]{10}$", description="Amazon ASIN")
    title: str = Field(..., description="Product title")
    deal_price: float = Field(..., ge=0, description="Deal price")
    list_price: float = Field(..., ge=0, description="List price")
    discount_percent: int = Field(..., ge=0, le=100, description="Discount percentage")
    end_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Deal end time")

class AmazonProductScenario(BaseModel):
    """Amazon Product API scenario."""
    products: Dict[str, Product] = Field(default={}, description="Products by ASIN")
    items: Dict[str, Item] = Field(default={}, description="Detailed items by ASIN")
    variations: Dict[str, List[Variation]] = Field(default={}, description="Variations by parent ASIN")
    browse_nodes: Dict[str, BrowseNode] = Field(default={}, description="Browse nodes by ID")
    deals: List[Deal] = Field(default=[], description="Active deals")
    search_index_map: Dict[str, List[str]] = Field(default={
        "All": [], "Electronics": [], "Books": [], "Clothing": [], "Home": [],
        "Sports": [], "Toys": [], "Beauty": [], "Automotive": [], "Garden": []
    }, description="Search index to ASIN mapping")

Scenario_Schema = [Price, Product, Item, Variation, BrowseNode, Deal, AmazonProductScenario]

# Section 2: Class
class AmazonProductAPI:
    def __init__(self):
        """Initialize Amazon Product API with empty state."""
        self.products: Dict[str, Product] = {}
        self.items: Dict[str, Item] = {}
        self.variations: Dict[str, List[Variation]] = {}
        self.browse_nodes: Dict[str, BrowseNode] = {}
        self.deals: List[Deal] = []
        self.search_index_map: Dict[str, List[str]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = AmazonProductScenario(**scenario)
        self.products = model.products
        self.items = model.items
        self.variations = model.variations
        self.browse_nodes = model.browse_nodes
        self.deals = model.deals
        self.search_index_map = model.search_index_map

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "products": {asin: prod.model_dump() for asin, prod in self.products.items()},
            "items": {asin: item.model_dump() for asin, item in self.items.items()},
            "variations": {asin: [v.model_dump() for v in vars] for asin, vars in self.variations.items()},
            "browse_nodes": {nid: node.model_dump() for nid, node in self.browse_nodes.items()},
            "deals": [deal.model_dump() for deal in self.deals],
            "search_index_map": self.search_index_map
        }

    def search_items(self, keywords: str, search_index: str, item_page: int, resources: Optional[List[str]]) -> dict:
        """Search products by keywords and category."""
        index_asins = self.search_index_map.get(search_index, [])
        matching = [p for asin, p in self.products.items() 
                   if keywords.lower() in p.title.lower() and (not index_asins or asin in index_asins)]
        start = (item_page - 1) * 10
        page_results = matching[start:start + 10]
        return {"products": [p.model_dump() for p in page_results]}

    def get_items(self, asins: List[str], resources: Optional[List[str]]) -> dict:
        """Retrieve detailed items by ASINs."""
        results = [self.items[asin].model_dump() for asin in asins if asin in self.items]
        return {"items": results}

    def get_variations(self, asin: str, resources: Optional[List[str]]) -> dict:
        """Retrieve product variations for parent ASIN."""
        vars = self.variations.get(asin, [])
        return {"variations": [v.model_dump() for v in vars]}

    def get_browse_nodes(self, browse_node_ids: List[str]) -> dict:
        """Retrieve browse nodes by IDs."""
        results = [self.browse_nodes[nid].model_dump() for nid in browse_node_ids if nid in self.browse_nodes]
        return {"browse_nodes": results}

    def get_deals(self, deal_types: Optional[List[str]]) -> dict:
        """Retrieve active deals."""
        return {"deals": [deal.model_dump() for deal in self.deals]}

# Section 3: MCP Tools
mcp = FastMCP(name="AmazonProduct")
api = AmazonProductAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Amazon Product API.

    Args:
        scenario (dict): Scenario dictionary matching AmazonProductScenario schema.

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
    Save current Amazon Product state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_items(keywords: str, search_index: str = "All", item_page: int = 1, resources: Optional[List[str]] = None) -> dict:
    """
    Search the Amazon product catalog by keywords with optional category filtering and pagination.

    Args:
        keywords (str): Search query terms to find products in the Amazon catalog.
        search_index (str): [Optional] Product category to search within (e.g., 'All', 'Electronics', 'Books'). Defaults to 'All'.
        item_page (int): [Optional] Pagination page number (1-10) for navigating large result sets. Defaults to 1.
        resources (List[str]): [Optional] Specific data fields to include in the response, such as 'Images', 'ItemInfo', 'Offers', or 'CustomerReviews'.

    Returns:
        products (List[dict]): Array of product results matching the search criteria.
    """
    try:
        if not keywords or not isinstance(keywords, str):
            raise ValueError("Keywords must be a non-empty string")
        return api.search_items(keywords, search_index, item_page, resources)
    except Exception as e:
        raise e

@mcp.tool()
def get_items(asins: List[str], resources: Optional[List[str]] = None) -> dict:
    """
    Retrieve detailed product information for specific Amazon items by their ASINs.

    Args:
        asins (List[str]): List of Amazon Standard Identification Numbers (ASINs) to retrieve detailed information for (maximum 10 items).
        resources (List[str]): [Optional] Specific data fields to include in the response, such as 'Images', 'ItemInfo', 'Offers', or 'CustomerReviews'.

    Returns:
        items (List[dict]): Array of detailed product information objects.
    """
    try:
        if not asins or not isinstance(asins, list):
            raise ValueError("ASINs must be a non-empty list")
        return api.get_items(asins, resources)
    except Exception as e:
        raise e

@mcp.tool()
def get_variations(asin: str, resources: Optional[List[str]] = None) -> dict:
    """
    Retrieve product variations (size, color, style options) for a parent ASIN.

    Args:
        asin (str): The parent product ASIN for which to retrieve size, color, or style variations.
        resources (List[str]): [Optional] Specific data fields to include in the response, such as 'Images', 'ItemInfo', 'Offers', or 'CustomerReviews'.

    Returns:
        variations (List[dict]): Array of product variation objects representing different size, color, or style options.
    """
    try:
        if not asin or not isinstance(asin, str):
            raise ValueError("ASIN must be a non-empty string")
        return api.get_variations(asin, resources)
    except Exception as e:
        raise e

@mcp.tool()
def get_browse_nodes(browse_node_ids: List[str]) -> dict:
    """
    Retrieve category hierarchy and metadata for specific browse node IDs.

    Args:
        browse_node_ids (List[str]): List of category/browse node identifiers to retrieve hierarchy information for.

    Returns:
        browse_nodes (List[dict]): Array of browse node objects representing categories and their hierarchy.
    """
    try:
        if not browse_node_ids or not isinstance(browse_node_ids, list):
            raise ValueError("Browse node IDs must be a non-empty list")
        return api.get_browse_nodes(browse_node_ids)
    except Exception as e:
        raise e

@mcp.tool()
def get_deals(deal_types: Optional[List[str]] = None) -> dict:
    """
    Retrieve current deals, promotions, and discounts available on Amazon.

    Args:
        deal_types (List[str]): [Optional] Types of promotions to filter by (e.g., 'LightningDeals', 'BestDeals').

    Returns:
        deals (List[dict]): Array of active deal and promotion objects.
    """
    try:
        return api.get_deals(deal_types)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
