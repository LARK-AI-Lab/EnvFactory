
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Property(BaseModel):
    """Represents a real estate property."""
    zpid: str = Field(..., description="Unique Zillow Property ID")
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., pattern=r"^[A-Z]{2}$", description="Two-letter state code")
    zipcode: str = Field(..., pattern=r"^\d{5}$", description="5-digit ZIP code")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    sqft: int = Field(..., ge=0, description="Living area in square feet")
    lot_size: int = Field(..., ge=0, description="Lot size in square feet")
    year_built: int = Field(..., ge=1800, le=2100, description="Year constructed")
    zestimate: float = Field(..., ge=0, description="Estimated market value")
    value_range_low: float = Field(..., ge=0, description="Lower value bound")
    value_range_high: float = Field(..., ge=0, description="Upper value bound")
    last_updated: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Last update date")
    price: float = Field(..., ge=0, description="Listed or estimated price")

class ZillowScenario(BaseModel):
    """Main scenario model for Zillow real estate data."""
    properties: Dict[str, Property] = Field(default={}, description="Properties indexed by zpid")
    comparables_map: Dict[str, List[str]] = Field(default={}, description="Comparable zpids for each property")

Scenario_Schema = [Property, ZillowScenario]

# Section 2: Class
class ZillowRealEstateAPI:
    def __init__(self):
        """Initialize Zillow API with empty state."""
        self.properties: Dict[str, Property] = {}
        self.comparables_map: Dict[str, List[str]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = ZillowScenario(**scenario)
        self.properties = model.properties
        self.comparables_map = model.comparables_map

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "properties": {zpid: prop.model_dump() for zpid, prop in self.properties.items()},
            "comparables_map": self.comparables_map
        }

    def get_zestimate(self, address: str, city_state_zip: str) -> dict:
        """Retrieve Zestimate for a property."""
        for prop in self.properties.values():
            full_addr = f"{prop.street}, {prop.city}, {prop.state} {prop.zipcode}"
            if prop.street.lower() == address.lower() and city_state_zip.lower() in full_addr.lower():
                return {
                    "zestimate": prop.zestimate,
                    "value_range_low": prop.value_range_low,
                    "value_range_high": prop.value_range_high,
                    "last_updated": prop.last_updated
                }
        return {}

    def get_property_details(self, address: str, city_state_zip: str) -> dict:
        """Retrieve property details."""
        for prop in self.properties.values():
            full_addr = f"{prop.street}, {prop.city}, {prop.state} {prop.zipcode}"
            if prop.street.lower() == address.lower() and city_state_zip.lower() in full_addr.lower():
                return {
                    "zpid": prop.zpid,
                    "street": prop.street,
                    "city": prop.city,
                    "state": prop.state,
                    "zipcode": prop.zipcode,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "sqft": prop.sqft,
                    "lot_size": prop.lot_size,
                    "year_built": prop.year_built
                }
        return {}

    def get_comparables(self, zpid: str, count: int) -> dict:
        """Retrieve comparable properties."""
        comp_zpids = self.comparables_map.get(zpid, [])[:count]
        comparables = []
        for comp_zpid in comp_zpids:
            if comp_zpid in self.properties:
                prop = self.properties[comp_zpid]
                comparables.append({
                    "zpid": prop.zpid,
                    "address": f"{prop.street}, {prop.city}, {prop.state} {prop.zipcode}",
                    "price": prop.price,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms
                })
        return {"comparables": comparables}

    def search_properties(self, city: str, state: str, min_price: Optional[int], max_price: Optional[int]) -> dict:
        """Search properties by location and price range."""
        results = []
        for prop in self.properties.values():
            if prop.city.lower() == city.lower() and prop.state.upper() == state.upper():
                if min_price is not None and prop.price < min_price:
                    continue
                if max_price is not None and prop.price > max_price:
                    continue
                results.append({
                    "zpid": prop.zpid,
                    "address": f"{prop.street}, {prop.city}, {prop.state} {prop.zipcode}",
                    "price": prop.price
                })
        return {"results": results, "total_count": len(results)}

# Section 3: MCP Tools
mcp = FastMCP(name="ZillowRealEstate")
api = ZillowRealEstateAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Zillow API.

    Args:
        scenario (dict): Scenario dictionary matching ZillowScenario schema.

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
    Save current Zillow state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_zestimate(address: str, city_state_zip: str) -> dict:
    """
    Retrieve the Zestimate home valuation and value range for a specific property address.

    Args:
        address (str): The street address of the property (e.g., '123 Main St').
        city_state_zip (str): The city, state, and ZIP code of the property (e.g., 'Seattle, WA 98101').

    Returns:
        zestimate (float): The estimated market value of the property in USD.
        value_range_low (float): The lower bound of the estimated value range in USD.
        value_range_high (float): The upper bound of the estimated value range in USD.
        last_updated (str): The date when the Zestimate was last updated (ISO 8601 format).
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if not city_state_zip or not isinstance(city_state_zip, str):
            raise ValueError("City, state, and ZIP must be a non-empty string")
        result = api.get_zestimate(address, city_state_zip)
        if not result:
            raise ValueError(f"Property not found at {address}, {city_state_zip}")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_property_details(address: str, city_state_zip: str) -> dict:
    """
    Retrieve comprehensive details about a property including physical characteristics and location information.

    Args:
        address (str): The street address of the property (e.g., '123 Main St').
        city_state_zip (str): The city, state, and ZIP code of the property (e.g., 'Seattle, WA 98101').

    Returns:
        zpid (str): The unique Zillow Property ID for this property.
        street (str): The street address of the property.
        city (str): The city where the property is located.
        state (str): The state where the property is located.
        zipcode (str): The ZIP code of the property.
        bedrooms (int): The number of bedrooms in the property.
        bathrooms (float): The number of bathrooms in the property (may include half baths as decimals).
        sqft (int): The total living area of the property in square feet.
        lot_size (int): The lot size of the property in square feet.
        year_built (int): The year the property was originally constructed.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if not city_state_zip or not isinstance(city_state_zip, str):
            raise ValueError("City, state, and ZIP must be a non-empty string")
        result = api.get_property_details(address, city_state_zip)
        if not result:
            raise ValueError(f"Property not found at {address}, {city_state_zip}")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_comparables(zpid: str, count: int = 5) -> dict:
    """
    Retrieve a list of comparable properties for a given property to assist with market analysis.

    Args:
        zpid (str): The unique Zillow Property ID for which to find comparable properties.
        count (int): [Optional] The number of comparable properties to return (maximum 25, defaults to 5).

    Returns:
        comparables (list): A list of comparable properties with basic details.
    """
    try:
        if not zpid or not isinstance(zpid, str):
            raise ValueError("ZPID must be a non-empty string")
        if zpid not in api.properties:
            raise ValueError(f"Property with ZPID {zpid} not found")
        if count > 25:
            count = 25
        return api.get_comparables(zpid, count)
    except Exception as e:
        raise e

@mcp.tool()
def search_properties(city: str, state: str, min_price: Optional[int] = None, max_price: Optional[int] = None) -> dict:
    """
    Search for properties in a specific location with optional price range filters.

    Args:
        city (str): The city name to search for properties (e.g., 'Seattle').
        state (str): The two-letter state abbreviation (e.g., 'WA').
        min_price (int): [Optional] The minimum price filter in USD.
        max_price (int): [Optional] The maximum price filter in USD.

    Returns:
        results (list): A list of properties matching the search criteria.
        total_count (int): The total number of properties found matching the search criteria.
    """
    try:
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        if not state or not isinstance(state, str):
            raise ValueError("State must be a non-empty string")
        return api.search_properties(city, state, min_price, max_price)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
