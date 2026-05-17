from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class MarketInfo(BaseModel):
    """Represents a geographic market in the AirDNA database."""
    market_id: str = Field(..., description="Unique identifier of the market in the AirDNA database")
    market_name: str = Field(..., description="Display name of the market (e.g., 'Downtown Austin')")
    market_type: str = Field(..., description="Classification of the market (e.g., 'city', 'neighborhood', 'metro')")
    state: str = Field(..., description="Two-letter US state abbreviation where the market is located")

class RentalEstimate(BaseModel):
    """Represents a rental revenue estimate for a property."""
    address: str = Field(..., description="The full street address of the property")
    estimated_revenue: float = Field(..., ge=0, description="Projected annual rental revenue in USD")
    average_daily_rate: float = Field(..., ge=0, description="Average Daily Rate in USD")
    occupancy_rate: float = Field(..., ge=0, le=100, description="Projected occupancy percentage")
    confidence_score: float = Field(..., ge=0, le=1, description="Statistical confidence metric")

class MarketData(BaseModel):
    """Represents aggregate market analytics for a geographic area."""
    city: str = Field(..., description="City name")
    state: str = Field(..., description="Two-letter US state abbreviation")
    market_score: int = Field(..., ge=0, description="AirDNA's proprietary market attractiveness score")
    average_adr: float = Field(..., ge=0, description="Market-wide Average Daily Rate in USD")
    average_occupancy: float = Field(..., ge=0, le=100, description="Market-wide average occupancy percentage")
    active_listings: int = Field(..., ge=0, description="Total count of active short-term rental listings")
    revpar: float = Field(..., ge=0, description="Revenue Per Available Room in USD")

class ListingData(BaseModel):
    """Represents historical performance metrics for an Airbnb property."""
    property_id: str = Field(..., description="Unique identifier of the Airbnb property listing")
    revenue_ltm: float = Field(..., ge=0, description="Total rental revenue over last 12 months in USD")
    occupancy_ltm: float = Field(..., ge=0, le=100, description="Occupancy percentage over last 12 months")
    adr_ltm: float = Field(..., ge=0, description="Average Daily Rate over last 12 months in USD")
    number_of_reviews: int = Field(..., ge=0, description="Total count of guest reviews")
    rating: float = Field(..., ge=0, le=5, description="Average guest review rating")

class RateRecommendation(BaseModel):
    """Represents a daily pricing recommendation."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date in ISO 8601 format (YYYY-MM-DD)")
    recommended_rate: float = Field(..., ge=0, description="Suggested optimal nightly rate in USD")
    demand_level: str = Field(..., description="Categorical indicator of expected demand (low, medium, high, peak)")

class SmartRates(BaseModel):
    """Represents dynamic pricing recommendations for a date range."""
    airbnb_property_id: str = Field(..., description="Unique identifier of the Airbnb property listing")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date in ISO 8601 format")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date in ISO 8601 format")
    recommendations: List[RateRecommendation] = Field(default=[], description="List of daily pricing recommendations")

class AirDNAScenario(BaseModel):
    """Main scenario model for AirDNA short-term rental analytics platform."""
    markets: Dict[str, MarketInfo] = Field(default={}, description="Available markets by market_id")
    rental_estimates: Dict[str, RentalEstimate] = Field(default={}, description="Rental estimates by address key")
    market_data_map: Dict[str, MarketData] = Field(default={}, description="Market data by city_state key")
    listing_data_map: Dict[str, ListingData] = Field(default={}, description="Listing data by property_id")
    smart_rates_map: Dict[str, SmartRates] = Field(default={}, description="Smart rates by property_id")
    # Reference data - US state tax rates and regulations (example reference data)
    state_regulations: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "CA": {"max_rental_days": 180, "transient_occupancy_tax": 0.14, "permit_required": True},
        "NY": {"max_rental_days": 365, "transient_occupancy_tax": 0.145, "permit_required": True},
        "TX": {"max_rental_days": 365, "transient_occupancy_tax": 0.09, "permit_required": False},
        "FL": {"max_rental_days": 365, "transient_occupancy_tax": 0.13, "permit_required": True},
        "CO": {"max_rental_days": 365, "transient_occupancy_tax": 0.108, "permit_required": True},
        "AZ": {"max_rental_days": 365, "transient_occupancy_tax": 0.125, "permit_required": False},
        "WA": {"max_rental_days": 365, "transient_occupancy_tax": 0.152, "permit_required": True},
        "NV": {"max_rental_days": 365, "transient_occupancy_tax": 0.135, "permit_required": True},
        "TN": {"max_rental_days": 365, "transient_occupancy_tax": 0.09, "permit_required": False},
        "OR": {"max_rental_days": 90, "transient_occupancy_tax": 0.115, "permit_required": True}
    }, description="State-specific short-term rental regulations")

Scenario_Schema = [MarketInfo, RentalEstimate, MarketData, ListingData, RateRecommendation, SmartRates, AirDNAScenario]

# Section 2: Class
class AirDNAAPI:
    def __init__(self):
        """Initialize AirDNA API with empty state."""
        self.markets: Dict[str, MarketInfo] = {}
        self.rental_estimates: Dict[str, RentalEstimate] = {}
        self.market_data_map: Dict[str, MarketData] = {}
        self.listing_data_map: Dict[str, ListingData] = {}
        self.smart_rates_map: Dict[str, SmartRates] = {}
        self.state_regulations: Dict[str, Dict[str, Any]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = AirDNAScenario(**scenario)
        self.markets = model.markets
        self.rental_estimates = model.rental_estimates
        self.market_data_map = model.market_data_map
        self.listing_data_map = model.listing_data_map
        self.smart_rates_map = model.smart_rates_map
        self.state_regulations = model.state_regulations

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "markets": {k: v.model_dump() for k, v in self.markets.items()},
            "rental_estimates": {k: v.model_dump() for k, v in self.rental_estimates.items()},
            "market_data_map": {k: v.model_dump() for k, v in self.market_data_map.items()},
            "listing_data_map": {k: v.model_dump() for k, v in self.listing_data_map.items()},
            "smart_rates_map": {k: v.model_dump() for k, v in self.smart_rates_map.items()},
            "state_regulations": self.state_regulations
        }

    def _get_address_key(self, address: str) -> str:
        """Generate a normalized key from address."""
        return address.lower().strip().replace(" ", "_")

    def _get_city_state_key(self, city: str, state: str) -> str:
        """Generate a key from city and state."""
        return f"{city.lower().strip()}_{state.lower().strip()}"

    def get_rental_estimate(self, address: str, bedrooms: int, bathrooms: int) -> dict:
        """Calculate projected short-term rental revenue estimates for a property."""
        key = self._get_address_key(address)
        
        if key in self.rental_estimates:
            estimate = self.rental_estimates[key]
            return {
                "estimated_revenue": estimate.estimated_revenue,
                "average_daily_rate": estimate.average_daily_rate,
                "occupancy_rate": estimate.occupancy_rate,
                "confidence_score": estimate.confidence_score
            }
        
        # Generate estimate based on bedrooms/bathrooms if not in scenario
        base_rate = 100.0 + (bedrooms * 50.0) + (bathrooms * 30.0)
        occupancy = 65.0 + (bedrooms * 5.0)
        
        return {
            "estimated_revenue": round(base_rate * occupancy * 3.65, 2),  # Annual revenue estimate
            "average_daily_rate": round(base_rate, 2),
            "occupancy_rate": round(min(occupancy, 95.0), 2),
            "confidence_score": 0.75
        }

    def get_market_data(self, city: str, state: str) -> dict:
        """Retrieve aggregate short-term rental market analytics for a geographic area."""
        key = self._get_city_state_key(city, state)
        
        if key in self.market_data_map:
            data = self.market_data_map[key]
            return {
                "market_score": data.market_score,
                "average_adr": data.average_adr,
                "average_occupancy": data.average_occupancy,
                "active_listings": data.active_listings,
                "revpar": data.revpar
            }
        
        return {
            "market_score": 0,
            "average_adr": 0.0,
            "average_occupancy": 0.0,
            "active_listings": 0,
            "revpar": 0.0
        }

    def get_listing_data(self, airbnb_property_id: str) -> dict:
        """Fetch historical performance metrics for a specific Airbnb property listing."""
        if airbnb_property_id in self.listing_data_map:
            data = self.listing_data_map[airbnb_property_id]
            return {
                "property_id": data.property_id,
                "revenue_ltm": data.revenue_ltm,
                "occupancy_ltm": data.occupancy_ltm,
                "adr_ltm": data.adr_ltm,
                "number_of_reviews": data.number_of_reviews,
                "rating": data.rating
            }
        
        return {
            "property_id": airbnb_property_id,
            "revenue_ltm": 0.0,
            "occupancy_ltm": 0.0,
            "adr_ltm": 0.0,
            "number_of_reviews": 0,
            "rating": 0.0
        }

    def get_smart_rates(self, airbnb_property_id: str, start_date: str, end_date: str) -> dict:
        """Generate dynamic pricing recommendations for a date range."""
        if airbnb_property_id in self.smart_rates_map:
            data = self.smart_rates_map[airbnb_property_id]
            # Filter recommendations within the requested date range
            filtered = [
                rec for rec in data.recommendations 
                if start_date <= rec.date <= end_date
            ]
            return {
                "recommendations": [
                    {
                        "date": rec.date,
                        "recommended_rate": rec.recommended_rate,
                        "demand_level": rec.demand_level
                    }
                    for rec in filtered
                ]
            }
        
        return {"recommendations": []}

    def search_markets(self, query: str) -> dict:
        """Search the AirDNA database for available markets and geographic regions."""
        matching_markets = []
        query_lower = query.lower()
        
        for market in self.markets.values():
            if (query_lower in market.market_name.lower() or 
                query_lower in market.state.lower() or
                query_lower in market.market_type.lower()):
                matching_markets.append({
                    "market_id": market.market_id,
                    "market_name": market.market_name,
                    "market_type": market.market_type,
                    "state": market.state
                })
        
        return {"markets": matching_markets}

# Section 3: MCP Tools
mcp = FastMCP(name="AirDNA")
api = AirDNAAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the AirDNA API.
    
    Args:
        scenario (dict): Scenario dictionary matching AirDNAScenario schema.
    
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
    Save current AirDNA state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_rental_estimate(address: str, bedrooms: int, bathrooms: int) -> dict:
    """
    Calculate projected short-term rental revenue estimates for a specific property.
    
    Args:
        address (str): The full street address of the property (e.g., '123 Main St, Austin, TX 78701').
        bedrooms (int): The number of bedrooms in the property.
        bathrooms (int): The number of bathrooms in the property.
    
    Returns:
        estimated_revenue (float): The projected annual rental revenue in USD.
        average_daily_rate (float): Average Daily Rate - the projected average rental price per booked night in USD.
        occupancy_rate (float): The projected percentage of available nights that will be booked (0-100).
        confidence_score (float): A statistical confidence metric (0-1) indicating reliability.
    """
    try:
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")
        if not isinstance(bedrooms, int) or bedrooms < 0:
            raise ValueError("Bedrooms must be a non-negative integer")
        if not isinstance(bathrooms, int) or bathrooms < 0:
            raise ValueError("Bathrooms must be a non-negative integer")
        return api.get_rental_estimate(address, bedrooms, bathrooms)
    except Exception as e:
        raise e

@mcp.tool()
def get_market_data(city: str, state: str) -> dict:
    """
    Retrieve aggregate short-term rental market analytics for a specified geographic area.
    
    Args:
        city (str): The city name to analyze (e.g., 'Austin').
        state (str): The two-letter US state abbreviation (e.g., 'CA', 'NY').
    
    Returns:
        market_score (int): AirDNA's proprietary market attractiveness score.
        average_adr (float): Market-wide Average Daily Rate in USD.
        average_occupancy (float): Market-wide average occupancy percentage (0-100).
        active_listings (int): Total count of active short-term rental listings.
        revpar (float): Revenue Per Available Room in USD.
    """
    try:
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        if not state or not isinstance(state, str):
            raise ValueError("State must be a non-empty string")
        return api.get_market_data(city, state)
    except Exception as e:
        raise e

@mcp.tool()
def get_listing_data(airbnb_property_id: str) -> dict:
    """
    Fetch historical performance metrics for a specific Airbnb property listing.
    
    Args:
        airbnb_property_id (str): The unique identifier of the Airbnb property listing.
    
    Returns:
        property_id (str): The unique identifier of the Airbnb property listing.
        revenue_ltm (float): Total rental revenue generated over the last 12 months in USD.
        occupancy_ltm (float): Occupancy percentage over the last 12 months (0-100).
        adr_ltm (float): Average Daily Rate over the last 12 months in USD.
        number_of_reviews (int): Total count of guest reviews for the property.
        rating (float): Average guest review rating (typically 0-5 scale).
    """
    try:
        if not airbnb_property_id or not isinstance(airbnb_property_id, str):
            raise ValueError("Airbnb property ID must be a non-empty string")
        return api.get_listing_data(airbnb_property_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_smart_rates(airbnb_property_id: str, start_date: str, end_date: str) -> dict:
    """
    Generate dynamic pricing recommendations and demand forecasts for optimizing nightly rates.
    
    Args:
        airbnb_property_id (str): The unique identifier of the Airbnb property listing.
        start_date (str): The start date for pricing recommendations in ISO 8601 format (YYYY-MM-DD).
        end_date (str): The end date for pricing recommendations in ISO 8601 format (YYYY-MM-DD).
    
    Returns:
        recommendations (list): A chronological list of daily pricing recommendations with date, rate, and demand level.
    """
    try:
        if not airbnb_property_id or not isinstance(airbnb_property_id, str):
            raise ValueError("Airbnb property ID must be a non-empty string")
        if not start_date or not isinstance(start_date, str):
            raise ValueError("Start date must be a non-empty string")
        if not end_date or not isinstance(end_date, str):
            raise ValueError("End date must be a non-empty string")
        return api.get_smart_rates(airbnb_property_id, start_date, end_date)
    except Exception as e:
        raise e

@mcp.tool()
def search_markets(query: str) -> dict:
    """
    Search the AirDNA database for available markets and geographic regions.
    
    Args:
        query (str): Search query string for finding markets (e.g., city name, neighborhood, or region).
    
    Returns:
        markets (list): List of markets matching the search query with market_id, name, type, and state.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_markets(query)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
