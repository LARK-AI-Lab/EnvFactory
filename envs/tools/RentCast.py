
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Property(BaseModel):
    """Represents a property with detailed information."""
    id: str = Field(..., description="Unique property identifier")
    address: str = Field(..., description="Complete street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State abbreviation")
    zipcode: str = Field(..., pattern=r"^\d{5}$", description="5-digit ZIP code")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    sqft: int = Field(..., ge=0, description="Living area in square feet")
    year_built: int = Field(..., ge=1800, le=2100, description="Year constructed")
    property_type: str = Field(..., description="Property classification")
    owner_name: str = Field(..., description="Current owner name")

class Valuation(BaseModel):
    """Represents a property valuation."""
    property_id: str = Field(..., description="Property identifier")
    estimated_value: float = Field(..., ge=0, description="Estimated market value")
    value_range_low: float = Field(..., ge=0, description="Lower value bound")
    value_range_high: float = Field(..., ge=0, description="Upper value bound")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence level")
    valuation_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Valuation date")

class SaleListing(BaseModel):
    """Represents a property for sale."""
    id: str = Field(..., description="Property identifier")
    address: str = Field(..., description="Complete street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State abbreviation")
    list_price: float = Field(..., ge=0, description="Asking price")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    sqft: int = Field(..., ge=0, description="Living area in square feet")
    days_on_market: int = Field(..., ge=0, description="Days listed")

class RentalListing(BaseModel):
    """Represents a rental property."""
    id: str = Field(..., description="Property identifier")
    address: str = Field(..., description="Complete street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State abbreviation")
    monthly_rent: float = Field(..., ge=0, description="Monthly rent")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    available_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Availability date")

class MarketData(BaseModel):
    """Represents market statistics for a ZIP code."""
    zip_code: str = Field(..., pattern=r"^\d{5}$", description="5-digit ZIP code")
    average_sale_price: float = Field(..., ge=0, description="Average sale price")
    average_rent: float = Field(..., ge=0, description="Average monthly rent")
    price_per_sqft: float = Field(..., ge=0, description="Price per square foot")
    inventory_count: int = Field(..., ge=0, description="Active listings count")
    days_on_market_avg: int = Field(..., ge=0, description="Average days on market")

class RentCastScenario(BaseModel):
    """Main scenario model for RentCast real estate data."""
    properties: Dict[str, Property] = Field(default={}, description="Properties by ID")
    valuations: Dict[str, Valuation] = Field(default={}, description="Valuations by property ID")
    sale_listings: List[SaleListing] = Field(default=[], description="Active sale listings")
    rental_listings: List[RentalListing] = Field(default=[], description="Active rental listings")
    market_data: Dict[str, MarketData] = Field(default={}, description="Market data by ZIP code")

Scenario_Schema = [Property, Valuation, SaleListing, RentalListing, MarketData, RentCastScenario]

# Section 2: Class
class RentCastAPI:
    def __init__(self):
        """Initialize RentCast API with empty state."""
        self.properties: Dict[str, Property] = {}
        self.valuations: Dict[str, Valuation] = {}
        self.sale_listings: List[SaleListing] = []
        self.rental_listings: List[RentalListing] = []
        self.market_data: Dict[str, MarketData] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = RentCastScenario(**scenario)
        self.properties = model.properties
        self.valuations = model.valuations
        self.sale_listings = model.sale_listings
        self.rental_listings = model.rental_listings
        self.market_data = model.market_data

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "properties": {pid: prop.model_dump() for pid, prop in self.properties.items()},
            "valuations": {pid: val.model_dump() for pid, val in self.valuations.items()},
            "sale_listings": [listing.model_dump() for listing in self.sale_listings],
            "rental_listings": [listing.model_dump() for listing in self.rental_listings],
            "market_data": {zc: md.model_dump() for zc, md in self.market_data.items()}
        }

    def get_property_by_address(self, address: str) -> dict:
        """Retrieve property details by address."""
        for prop in self.properties.values():
            if prop.address.lower() == address.lower():
                return {
                    "id": prop.id,
                    "address": prop.address,
                    "city": prop.city,
                    "state": prop.state,
                    "zipcode": prop.zipcode,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "sqft": prop.sqft,
                    "year_built": prop.year_built,
                    "property_type": prop.property_type,
                    "owner_name": prop.owner_name
                }
        return {}

    def get_property_valuation(self, address: str) -> dict:
        """Obtain valuation estimate for a property."""
        for prop in self.properties.values():
            if prop.address.lower() == address.lower():
                if prop.id in self.valuations:
                    val = self.valuations[prop.id]
                    return {
                        "estimated_value": val.estimated_value,
                        "value_range_low": val.value_range_low,
                        "value_range_high": val.value_range_high,
                        "confidence_score": val.confidence_score,
                        "valuation_date": val.valuation_date
                    }
        return {}

    def search_sale_listings(self, city: str, state: str, min_price: Optional[int], max_price: Optional[int]) -> dict:
        """Search for active sale listings."""
        results = []
        for listing in self.sale_listings:
            if listing.city.lower() == city.lower() and listing.state.upper() == state.upper():
                if min_price is not None and listing.list_price < min_price:
                    continue
                if max_price is not None and listing.list_price > max_price:
                    continue
                results.append({
                    "id": listing.id,
                    "address": listing.address,
                    "list_price": listing.list_price,
                    "bedrooms": listing.bedrooms,
                    "bathrooms": listing.bathrooms,
                    "sqft": listing.sqft,
                    "days_on_market": listing.days_on_market
                })
        return {"listings": results}

    def search_rental_listings(self, city: str, state: str, min_rent: Optional[int], max_rent: Optional[int]) -> dict:
        """Search for available rental listings."""
        results = []
        for listing in self.rental_listings:
            if listing.city.lower() == city.lower() and listing.state.upper() == state.upper():
                if min_rent is not None and listing.monthly_rent < min_rent:
                    continue
                if max_rent is not None and listing.monthly_rent > max_rent:
                    continue
                results.append({
                    "id": listing.id,
                    "address": listing.address,
                    "monthly_rent": listing.monthly_rent,
                    "bedrooms": listing.bedrooms,
                    "bathrooms": listing.bathrooms,
                    "available_date": listing.available_date
                })
        return {"listings": results}

    def get_market_data(self, zip_code: str) -> dict:
        """Retrieve market statistics for a ZIP code."""
        if zip_code in self.market_data:
            md = self.market_data[zip_code]
            return {
                "average_sale_price": md.average_sale_price,
                "average_rent": md.average_rent,
                "price_per_sqft": md.price_per_sqft,
                "inventory_count": md.inventory_count,
                "days_on_market_avg": md.days_on_market_avg
            }
        return {}

# Section 3: MCP Tools
mcp = FastMCP(name="RentCast")
api = RentCastAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the RentCast API.

    Args:
        scenario (dict): Scenario dictionary matching RentCastScenario schema.

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
    Save current RentCast state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_property_by_address(address: str) -> dict:
    """
    Retrieve comprehensive property details by address.

    Args:
        address (str): Complete street address of the property.

    Returns:
        id (str): Unique property identifier.
        address (str): Complete street address.
        city (str): City name.
        state (str): State abbreviation.
        zipcode (str): 5-digit ZIP code.
        bedrooms (int): Number of bedrooms.
        bathrooms (float): Number of bathrooms.
        sqft (int): Living area in square feet.
        year_built (int): Year constructed.
        property_type (str): Property classification.
        owner_name (str): Current owner name.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        result = api.get_property_by_address(address)
        if not result:
            raise ValueError(f"Property not found at address: {address}")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_property_valuation(address: str) -> dict:
    """
    Obtain automated valuation estimate for a property.

    Args:
        address (str): Complete street address of the property.

    Returns:
        estimated_value (float): Estimated market value in USD.
        value_range_low (float): Lower value bound in USD.
        value_range_high (float): Upper value bound in USD.
        confidence_score (float): Confidence level (0.0 to 1.0).
        valuation_date (str): Valuation date in ISO 8601 format.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        result = api.get_property_valuation(address)
        if not result:
            raise ValueError(f"Valuation not found for address: {address}")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def search_sale_listings(city: str, state: str, min_price: Optional[int] = None, max_price: Optional[int] = None) -> dict:
    """
    Search for active properties listed for sale.

    Args:
        city (str): City name.
        state (str): State abbreviation.
        min_price (int): [Optional] Minimum listing price in USD.
        max_price (int): [Optional] Maximum listing price in USD.

    Returns:
        listings (list): Collection of sale listings with id, address, list_price, bedrooms, bathrooms, sqft, days_on_market.
    """
    try:
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        if not state or not isinstance(state, str):
            raise ValueError("State must be a non-empty string")
        return api.search_sale_listings(city, state, min_price, max_price)
    except Exception as e:
        raise e

@mcp.tool()
def search_rental_listings(city: str, state: str, min_rent: Optional[int] = None, max_rent: Optional[int] = None) -> dict:
    """
    Search for available long-term rental properties.

    Args:
        city (str): City name.
        state (str): State abbreviation.
        min_rent (int): [Optional] Minimum monthly rent in USD.
        max_rent (int): [Optional] Maximum monthly rent in USD.

    Returns:
        listings (list): Collection of rental listings with id, address, monthly_rent, bedrooms, bathrooms, available_date.
    """
    try:
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        if not state or not isinstance(state, str):
            raise ValueError("State must be a non-empty string")
        return api.search_rental_listings(city, state, min_rent, max_rent)
    except Exception as e:
        raise e

@mcp.tool()
def get_market_data(zip_code: str) -> dict:
    """
    Retrieve aggregated market statistics for a ZIP code area.

    Args:
        zip_code (str): 5-digit ZIP code.

    Returns:
        average_sale_price (float): Average sale price in USD.
        average_rent (float): Average monthly rent in USD.
        price_per_sqft (float): Average price per square foot in USD.
        inventory_count (int): Total active listings count.
        days_on_market_avg (int): Average days on market.
    """
    try:
        if not zip_code or not isinstance(zip_code, str):
            raise ValueError("ZIP code must be a non-empty string")
        result = api.get_market_data(zip_code)
        if not result:
            raise ValueError(f"Market data not found for ZIP code: {zip_code}")
        return result
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
