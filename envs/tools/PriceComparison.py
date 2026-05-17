from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import random

# Section 1: Schema
class Product(BaseModel):
    """Represents a product in the catalog."""
    pid: str = Field(..., description="Unique product identifier")
    pos: int = Field(..., ge=0, description="Product position identifier")
    name: str = Field(..., description="Product name")

class RetailerPrice(BaseModel):
    """Represents pricing information from a retailer."""
    store_name: str = Field(..., description="Name of the retailer")
    price: float = Field(..., ge=0, description="Current listed price")
    availability: str = Field(..., description="Stock availability status")

class PriceData(BaseModel):
    """Represents a price data point with date and trend."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date in YYYY-MM-DD format")
    predicted_price: float = Field(..., ge=0, description="Predicted price")
    trend: str = Field(..., description="Trend direction (up/down/stable)")

class HistoricalPrice(BaseModel):
    """Represents historical price record."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date in YYYY-MM-DD format")
    price: float = Field(..., ge=0, description="Recorded price")
    retailer: str = Field(..., description="Name of the retailer")

class DiscountInfo(BaseModel):
    """Represents discount information for a product."""
    discount_percentage: float = Field(..., ge=0, le=100, description="Percentage discount")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date in YYYY-MM-DD format")
    original_price: float = Field(..., ge=0, description="Original price before discount")
    discounted_price: float = Field(..., ge=0, description="Price after discount")

class PriceComparisonScenario(BaseModel):
    """Main scenario model for price comparison service."""
    products: Dict[str, Product] = Field(default={}, description="Product catalog")
    retailerPrices: Dict[str, List[RetailerPrice]] = Field(default={}, description="Current prices by product")
    priceHistory: Dict[str, List[HistoricalPrice]] = Field(default={}, description="Historical price data by product")
    priceTrends: Dict[str, List[PriceData]] = Field(default={}, description="Predicted price trends by product")
    discountInfo: Dict[str, Dict[str, List[DiscountInfo]]] = Field(default={}, description="Discount information by product and retailer")
    retailerList: List[str] = Field(default=["Amazon", "Walmart", "Target", "Best Buy", "Newegg", "eBay", "Costco", "Home Depot", "Lowe's", "Macy's"], description="Available retailers")
    availabilityStatuses: List[str] = Field(default=["In Stock", "Out of Stock", "Limited Stock", "Backorder", "Pre-order"], description="Stock availability statuses")

Scenario_Schema = [Product, RetailerPrice, PriceData, HistoricalPrice, DiscountInfo, PriceComparisonScenario]

# Section 2: Class
class PriceComparisonAPI:
    def __init__(self):
        """Initialize price comparison API with empty state."""
        self.products: Dict[str, Product] = {}
        self.retailerPrices: Dict[str, List[RetailerPrice]] = {}
        self.priceHistory: Dict[str, List[HistoricalPrice]] = {}
        self.priceTrends: Dict[str, List[PriceData]] = {}
        self.discountInfo: Dict[str, Dict[str, List[DiscountInfo]]] = {}
        self.retailerList: List[str] = []
        self.availabilityStatuses: List[str] = []
        self.random_seed: Optional[int] = None
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = PriceComparisonScenario(**scenario)
        self.products = model.products
        self.retailerPrices = model.retailerPrices
        self.priceHistory = model.priceHistory
        self.priceTrends = model.priceTrends
        self.discountInfo = model.discountInfo
        self.retailerList = model.retailerList
        self.availabilityStatuses = model.availabilityStatuses

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "products": {pid: product.model_dump() for pid, product in self.products.items()},
            "retailerPrices": {pid: [rp.model_dump() for rp in rps] for pid, rps in self.retailerPrices.items()},
            "priceHistory": {pid: [ph.model_dump() for ph in phs] for pid, phs in self.priceHistory.items()},
            "priceTrends": {pid: [pt.model_dump() for pt in pts] for pid, pts in self.priceTrends.items()},
            "discountInfo": {pid: {retailer: [d.model_dump() for d in discounts] for retailer, discounts in ret_dict.items()} for pid, ret_dict in self.discountInfo.items()},
            "retailerList": self.retailerList,
            "availabilityStatuses": self.availabilityStatuses
        }

    def get_pid_pos_details(self, name: str) -> dict:
        """Retrieve product identifier and position for a product by name."""
        for product in self.products.values():
            if product.name.lower() == name.lower():
                return {"pid": product.pid, "pos": product.pos, "name": product.name}
        return {"pid": "", "pos": 0, "name": ""}

    def compare_price(self, pid: str, pos: int, max_retailers: int = 10) -> dict:
        """Fetch and compare current prices for a product across retailers."""
        if pid not in self.retailerPrices:
            return {"pid": pid, "pos": pos, "retailers": []}
        
        retailers = self.retailerPrices[pid][:max_retailers]
        return {"pid": pid, "pos": pos, "retailers": [r.model_dump() for r in retailers]}

    def price_trend(self, pid: str, pos: int) -> dict:
        """Fetch predicted future price trend data for a product."""
        if pid not in self.priceTrends:
            return {"pid": pid, "pos": pos, "price_data": []}
        
        return {"pid": pid, "pos": pos, "price_data": [pt.model_dump() for pt in self.priceTrends[pid]]}

    def get_price_history(self, pid: str, pos: int, retailers: Optional[List[str]] = None) -> dict:
        """Retrieve historical price data for a product."""
        if pid not in self.priceHistory:
            return {"pid": pid, "pos": pos, "price_history": []}
        
        history = self.priceHistory[pid]
        if retailers:
            history = [h for h in history if h.retailer in retailers]
        
        return {"pid": pid, "pos": pos, "price_history": [h.model_dump() for h in history]}

    def get_discount_info(self, pid: str, pos: int, retailer: str, time_period: str) -> dict:
        """Retrieve discount information for a product at a specific retailer."""
        if pid not in self.discountInfo or retailer not in self.discountInfo[pid]:
            return {"pid": pid, "pos": pos, "retailer": retailer, "discounts": []}
        
        discounts = self.discountInfo[pid][retailer]
        filtered_discounts = []
        
        for discount in discounts:
            if time_period == "current":
                filtered_discounts.append(discount)
            elif time_period == "past":
                filtered_discounts.append(discount)
            elif time_period == "upcoming":
                filtered_discounts.append(discount)
        
        return {"pid": pid, "pos": pos, "retailer": retailer, "discounts": [d.model_dump() for d in filtered_discounts]}

# Section 3: MCP Tools
mcp = FastMCP(name="PriceComparison")
api = PriceComparisonAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the price comparison API.
    
    Args:
        scenario (dict): Scenario dictionary matching PriceComparisonScenario schema.
    
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
    Save current price comparison state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_pid_pos_details(name: str) -> dict:
    """
    Retrieve the product identifier and position for a product by searching its name.
    
    Args:
        name (str): The product name to search for in the catalog.
    
    Returns:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        name (str): The matched product name from the catalog.
    """
    try:
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        return api.get_pid_pos_details(name)
    except Exception as e:
        raise e

@mcp.tool()
def compare_price(pid: str, pos: int, max_retailers: int = 10) -> dict:
    """
    Fetch and compare current prices for a product across multiple retailers.
    
    Args:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        max_retailers (int) [Optional]: The maximum number of retailers to include. Defaults to 10.
    
    Returns:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        retailers (list): List of retailer pricing information.
    """
    try:
        if not pid or not isinstance(pid, str):
            raise ValueError("PID must be a non-empty string")
        if not isinstance(pos, int) or pos < 0:
            raise ValueError("POS must be a non-negative integer")
        if not isinstance(max_retailers, int) or max_retailers <= 0:
            raise ValueError("Max retailers must be a positive integer")
        return api.compare_price(pid, pos, max_retailers)
    except Exception as e:
        raise e

@mcp.tool()
def price_trend(pid: str, pos: int) -> dict:
    """
    Fetch predicted future price trend data for a product.
    
    Args:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
    
    Returns:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        price_data (list): List of predicted price data points.
    """
    try:
        if not pid or not isinstance(pid, str):
            raise ValueError("PID must be a non-empty string")
        if not isinstance(pos, int) or pos < 0:
            raise ValueError("POS must be a non-negative integer")
        return api.price_trend(pid, pos)
    except Exception as e:
        raise e

@mcp.tool()
def get_price_history(pid: str, pos: int, retailers: Optional[List[str]] = None) -> dict:
    """
    Retrieve historical price data for a product across retailers.
    
    Args:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        retailers (list) [Optional]: Optional list of retailer names to filter results.
    
    Returns:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        price_history (list): List of historical price records.
    """
    try:
        if not pid or not isinstance(pid, str):
            raise ValueError("PID must be a non-empty string")
        if not isinstance(pos, int) or pos < 0:
            raise ValueError("POS must be a non-negative integer")
        if retailers is not None and not isinstance(retailers, list):
            raise ValueError("Retailers must be a list of strings")
        return api.get_price_history(pid, pos, retailers)
    except Exception as e:
        raise e

@mcp.tool()
def get_discount_info(pid: str, pos: int, retailer: str, time_period: str) -> dict:
    """
    Retrieve discount and promotional information for a product at a specific retailer.
    
    Args:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        retailer (str): The name of the retailer to query.
        time_period (str): The time period to query ('current', 'past', or 'upcoming').
    
    Returns:
        pid (str): The unique product identifier.
        pos (int): The product position identifier.
        retailer (str): The name of the retailer.
        discounts (list): List of discount records.
    """
    try:
        if not pid or not isinstance(pid, str):
            raise ValueError("PID must be a non-empty string")
        if not isinstance(pos, int) or pos < 0:
            raise ValueError("POS must be a non-negative integer")
        if not retailer or not isinstance(retailer, str):
            raise ValueError("Retailer must be a non-empty string")
        if time_period not in ["current", "past", "upcoming"]:
            raise ValueError("Time period must be one of: 'current', 'past', 'upcoming'")
        return api.get_discount_info(pid, pos, retailer, time_period)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()