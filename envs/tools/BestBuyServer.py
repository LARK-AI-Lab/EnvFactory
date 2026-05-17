
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class ProductSummary(BaseModel):
    """Represents a product summary in search results."""
    sku: int = Field(..., description="Product SKU")
    name: str = Field(..., description="Product name")
    salePrice: float = Field(..., ge=0, description="Current sale price")
    regularPrice: float = Field(..., ge=0, description="Regular price")
    onSale: bool = Field(..., description="Is on sale")
    inStoreAvailability: bool = Field(..., description="Available in store")
    onlineAvailability: bool = Field(..., description="Available online")
    thumbnailImage: str = Field(..., description="Thumbnail image URL")
    url: str = Field(..., description="Product page URL")

class CategoryNode(BaseModel):
    """Represents a category node in hierarchy."""
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")

class ProductImages(BaseModel):
    """Product image URLs at various resolutions."""
    thumbnailImage: str = Field(..., description="Thumbnail image URL")
    mediumImage: str = Field(..., description="Medium image URL")
    largeImage: str = Field(..., description="Large image URL")

class ProductFeature(BaseModel):
    """Product feature or specification."""
    feature: str = Field(..., description="Feature description")

class ProductDetail(BaseModel):
    """Detailed product information."""
    sku: int = Field(..., description="Product SKU")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Short description")
    longDescription: str = Field(..., description="Long description")
    salePrice: float = Field(..., ge=0, description="Sale price")
    regularPrice: float = Field(..., ge=0, description="Regular price")
    onSale: bool = Field(..., description="Is on sale")
    customerReviewAverage: float = Field(..., ge=0, le=5, description="Average rating")
    customerReviewCount: int = Field(..., ge=0, description="Review count")
    images: ProductImages = Field(..., description="Product images")
    manufacturer: str = Field(..., description="Manufacturer name")
    modelNumber: str = Field(..., description="Model number")
    categoryPath: List[CategoryNode] = Field(default=[], description="Category path")
    features: List[ProductFeature] = Field(default=[], description="Product features")

class Reviewer(BaseModel):
    """Review author information."""
    displayName: str = Field(..., description="Reviewer display name")

class Review(BaseModel):
    """Customer review."""
    id: int = Field(..., description="Review ID")
    rating: int = Field(..., ge=1, le=5, description="Star rating")
    reviewer: Reviewer = Field(..., description="Reviewer info")
    submissionTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Submission timestamp")
    title: str = Field(..., description="Review title")
    reviewText: str = Field(..., description="Review text")
    helpfulness: int = Field(..., ge=0, description="Helpfulness count")

class Category(BaseModel):
    """Product category with hierarchy."""
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    path: List[CategoryNode] = Field(default=[], description="Category path")
    subCategories: List[Dict[str, Any]] = Field(default=[], description="Subcategories")

class Store(BaseModel):
    """Best Buy store location."""
    storeId: int = Field(..., description="Store ID")
    storeType: str = Field(..., description="Store type")
    name: str = Field(..., description="Store name")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State abbreviation")
    zip: str = Field(..., description="ZIP code")
    phone: str = Field(..., description="Phone number")
    hours: str = Field(..., description="Operating hours")
    services: List[str] = Field(default=[], description="Services offered")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")

class BestBuyScenario(BaseModel):
    """Main scenario model for Best Buy server."""
    products: Dict[int, ProductDetail] = Field(default={}, description="Product catalog by SKU")
    reviews: Dict[int, List[Review]] = Field(default={}, description="Reviews by product SKU")
    categories: List[Category] = Field(default=[], description="Category hierarchy")
    stores: List[Store] = Field(default=[], description="Store locations")

Scenario_Schema = [ProductSummary, CategoryNode, ProductImages, ProductFeature, ProductDetail, Reviewer, Review, Category, Store, BestBuyScenario]

# Section 2: Class
class BestBuyAPI:
    def __init__(self):
        """Initialize Best Buy API with empty state."""
        self.products: Dict[int, ProductDetail] = {}
        self.reviews: Dict[int, List[Review]] = {}
        self.categories: List[Category] = []
        self.stores: List[Store] = []

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = BestBuyScenario(**scenario)
        self.products = model.products
        self.reviews = model.reviews
        self.categories = model.categories
        self.stores = model.stores

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "products": {sku: prod.model_dump() for sku, prod in self.products.items()},
            "reviews": {sku: [rev.model_dump() for rev in revs] for sku, revs in self.reviews.items()},
            "categories": [cat.model_dump() for cat in self.categories],
            "stores": [store.model_dump() for store in self.stores]
        }

    def search_products(self, keywords: str, category: Optional[str], min_price: Optional[float], max_price: Optional[float], in_stock_only: Optional[bool], limit: Optional[int]) -> dict:
        """Search for products matching criteria."""
        results = []
        for sku, prod in self.products.items():
            if keywords.lower() not in prod.name.lower():
                continue
            if category and not any(cat.name == category for cat in prod.categoryPath):
                continue
            if min_price is not None and prod.salePrice < min_price:
                continue
            if max_price is not None and prod.salePrice > max_price:
                continue
            if in_stock_only and not (prod.inStoreAvailability or prod.onlineAvailability):
                continue
            results.append(prod)
        
        page_limit = limit if limit else 10
        total = len(results)
        total_pages = (total + page_limit - 1) // page_limit if page_limit > 0 else 1
        results = results[:page_limit]
        
        return {
            "from": 1 if results else 0,
            "to": len(results),
            "total": total,
            "currentPage": 1,
            "totalPages": total_pages,
            "products": [{
                "sku": p.sku,
                "name": p.name,
                "salePrice": p.salePrice,
                "regularPrice": p.regularPrice,
                "onSale": p.onSale,
                "inStoreAvailability": getattr(p, 'inStoreAvailability', False),
                "onlineAvailability": getattr(p, 'onlineAvailability', False),
                "thumbnailImage": p.images.thumbnailImage,
                "url": getattr(p, 'url', f"https://bestbuy.com/product/{p.sku}")
            } for p in results]
        }

    def get_product_details(self, sku: int) -> dict:
        """Retrieve detailed product information."""
        prod = self.products[sku]
        return prod.model_dump()

    def get_product_reviews(self, sku: int, limit: Optional[int]) -> dict:
        """Retrieve customer reviews for a product."""
        revs = self.reviews.get(sku, [])
        page_limit = limit if limit else 10
        limited_revs = revs[:page_limit]
        avg_rating = sum(r.rating for r in revs) / len(revs) if revs else 0
        
        return {
            "sku": sku,
            "overallRating": avg_rating,
            "totalReviewCount": len(revs),
            "reviews": [r.model_dump() for r in limited_revs]
        }

    def get_categories(self) -> dict:
        """Retrieve category hierarchy."""
        return {"categories": [cat.model_dump() for cat in self.categories]}

    def get_stores(self, city: Optional[str], state: Optional[str], zip_code: Optional[str], lat: Optional[float], lng: Optional[float], radius: Optional[int]) -> dict:
        """Find store locations matching criteria."""
        results = []
        for store in self.stores:
            if city and store.city.lower() != city.lower():
                continue
            if state and store.state.upper() != state.upper():
                continue
            if zip_code and store.zip != zip_code:
                continue
            if lat is not None and lng is not None:
                search_radius = radius if radius else 25
                dist = ((store.lat - lat) ** 2 + (store.lng - lng) ** 2) ** 0.5 * 69
                if dist > search_radius:
                    continue
            results.append(store)
        
        return {"stores": [s.model_dump() for s in results]}

# Section 3: MCP Tools
mcp = FastMCP(name="BestBuyServer")
api = BestBuyAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Best Buy API.

    Args:
        scenario (dict): Scenario dictionary matching BestBuyScenario schema.

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
    Save current Best Buy state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_products(keywords: str, category: str = None, min_price: float = None, max_price: float = None, in_stock_only: bool = None, limit: int = None) -> dict:
    """
    Search for products in the Best Buy catalog.

    Args:
        keywords (str): Search terms to find matching products.
        category (str) [Optional]: Category to filter results.
        min_price (float) [Optional]: Minimum price threshold.
        max_price (float) [Optional]: Maximum price threshold.
        in_stock_only (bool) [Optional]: Filter for in-stock products only.
        limit (int) [Optional]: Maximum number of results (1-100).

    Returns:
        from (int): Starting index of result set.
        to (int): Ending index of result set.
        total (int): Total matching products.
        currentPage (int): Current page number.
        totalPages (int): Total pages available.
        products (list): Product summaries.
    """
    try:
        if not keywords or not isinstance(keywords, str):
            raise ValueError("Keywords must be a non-empty string")
        return api.search_products(keywords, category, min_price, max_price, in_stock_only, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_product_details(sku: int) -> dict:
    """
    Retrieve comprehensive product details by SKU.

    Args:
        sku (int): Product SKU identifier.

    Returns:
        sku (int): Product SKU.
        name (str): Product name.
        description (str): Short description.
        longDescription (str): Detailed description.
        salePrice (float): Current sale price.
        regularPrice (float): Regular price.
        onSale (bool): Sale status.
        customerReviewAverage (float): Average rating.
        customerReviewCount (int): Review count.
        images (dict): Product images.
        manufacturer (str): Manufacturer name.
        modelNumber (str): Model number.
        categoryPath (list): Category hierarchy.
        features (list): Product features.
    """
    try:
        if sku not in api.products:
            raise ValueError(f"Product {sku} not found")
        return api.get_product_details(sku)
    except Exception as e:
        raise e

@mcp.tool()
def get_product_reviews(sku: int, limit: int = None) -> dict:
    """
    Retrieve customer reviews for a product.

    Args:
        sku (int): Product SKU identifier.
        limit (int) [Optional]: Maximum number of reviews to return.

    Returns:
        sku (int): Product SKU.
        overallRating (float): Average rating across all reviews.
        totalReviewCount (int): Total number of reviews.
        reviews (list): Individual customer reviews.
    """
    try:
        if sku not in api.products:
            raise ValueError(f"Product {sku} not found")
        return api.get_product_reviews(sku, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_categories() -> dict:
    """
    Retrieve the complete category hierarchy.

    Returns:
        categories (list): Complete list of product categories with hierarchy.
    """
    try:
        return api.get_categories()
    except Exception as e:
        raise e

@mcp.tool()
def get_stores(city: str = None, state: str = None, zip_code: str = None, lat: float = None, lng: float = None, radius: int = None) -> dict:
    """
    Find Best Buy store locations using geographic filters.

    Args:
        city (str) [Optional]: City name to filter stores.
        state (str) [Optional]: Two-letter state abbreviation.
        zip_code (str) [Optional]: Postal ZIP code.
        lat (float) [Optional]: Latitude coordinate for radius search.
        lng (float) [Optional]: Longitude coordinate for radius search.
        radius (int) [Optional]: Search radius in miles (default: 25).

    Returns:
        stores (list): Collection of store locations matching criteria.
    """
    try:
        return api.get_stores(city, state, zip_code, lat, lng, radius)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
