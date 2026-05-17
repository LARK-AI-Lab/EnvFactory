from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Brand(BaseModel):
    """Represents a car brand."""
    brand_code: int = Field(..., ge=1, description="The unique numeric identifier for the car brand in the FIPE system.")
    brand_name: str = Field(..., description="The display name of the car brand (e.g., 'Toyota', 'Honda', 'Ford').")

class Vehicle(BaseModel):
    """Represents a vehicle model with pricing information."""
    model_name: str = Field(..., description="The full model name of the vehicle.")
    production_year: int = Field(..., ge=1900, le=2100, description="The year the vehicle was manufactured.")
    fuel_type: str = Field(..., description="The type of fuel the vehicle uses (e.g., 'Gasoline', 'Diesel', 'Electric', 'Flex').")
    current_price: float = Field(..., ge=0, description="The current market price of the vehicle in Brazilian Reais (BRL) according to FIPE.")
    fipe_code: str = Field(..., description="The unique FIPE reference code for this specific vehicle configuration.")

class CarPriceScenario(BaseModel):
    """Main scenario model for car pricing information."""
    brands: Dict[str, Brand] = Field(default={}, description="Available car brands indexed by brand name")
    vehicles: Dict[str, List[Vehicle]] = Field(default={}, description="Vehicle models grouped by brand name")
    vehicle_types: Dict[str, List[Brand]] = Field(default={}, description="Available brands grouped by vehicle type")
    
Scenario_Schema = [Brand, Vehicle, CarPriceScenario]

# Section 2: Class
class CarPriceAPI:
    def __init__(self):
        """Initialize car price API with empty state."""
        self.brands: Dict[str, Brand] = {}
        self.vehicles: Dict[str, List[Vehicle]] = {}
        self.vehicle_types: Dict[str, List[Brand]] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """
        Load scenario data into the API instance.
        """
        model = CarPriceScenario(**scenario)
        self.brands = model.brands
        self.vehicles = model.vehicles
        self.vehicle_types = model.vehicle_types

    def save_scenario(self) -> dict:
        """
        Save current state as scenario dictionary.
        """
        return {
            "brands": {name: brand.model_dump() for name, brand in self.brands.items()},
            "vehicles": {brand: [vehicle.model_dump() for vehicle in vehicles] for brand, vehicles in self.vehicles.items()},
            "vehicle_types": {vtype: [brand.model_dump() for brand in brands] for vtype, brands in self.vehicle_types.items()}
        }

    def get_car_brands(self, limit: Optional[int] = None) -> dict:
        """
        Retrieve all available car brands with optional result limiting.
        """
        brands_list = list(self.brands.values())
        if limit is not None and limit > 0:
            brands_list = brands_list[:limit]
        return {"brands": [brand.model_dump() for brand in brands_list]}

    def search_car_price(self, brand_name: str) -> dict:
        """
        Search for car models and their current market prices by brand name.
        """
        if brand_name not in self.vehicles:
            return {"vehicles": []}
        return {"vehicles": [vehicle.model_dump() for vehicle in self.vehicles[brand_name]]}

    def get_vehicles_by_type(self, vehicle_type: str) -> dict:
        """
        Retrieve available vehicle brands filtered by vehicle type category.
        """
        normalized_type = self._normalize_vehicle_type(vehicle_type)
        # Check if the normalized type exists in vehicle_types
        if normalized_type not in self.vehicle_types:
            # Try the original type as well in case normalization didn't match
            if vehicle_type.lower() in self.vehicle_types:
                normalized_type = vehicle_type.lower()
            else:
                return {"brands": []}
        return {"brands": [brand.model_dump() for brand in self.vehicle_types[normalized_type]]}
    
    def _normalize_vehicle_type(self, vehicle_type: str) -> str:
        """Normalize vehicle type input to standard format."""
        type_mapping = {
            "cars": "cars", "carros": "cars",
            "motorcycles": "motorcycles", "motos": "motorcycles",
            "trucks": "trucks", "caminhoes": "trucks"
        }
        return type_mapping.get(vehicle_type.lower(), vehicle_type.lower())

# Section 3: MCP Tools
mcp = FastMCP(name="CarPrice")
api = CarPriceAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the car price API.
    
    Args:
        scenario (dict): Scenario dictionary matching CarPriceScenario schema.
    
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
    Save current car price state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_car_brands(limit: Optional[int] = None) -> dict:
    """
    Retrieve all available car brands from the FIPE API with optional result limiting.
    
    Args:
        limit (int) [Optional]: Maximum number of brand results to return. Defaults to 10 if not specified.
    
    Returns:
        brands (list): List of car brands available in the FIPE database.
    """
    try:
        # Basic parameter check only - range validation handled by Pydantic Brand model
        if limit is not None and not isinstance(limit, int):
            raise ValueError("Limit must be an integer")
        return api.get_car_brands(limit)
    except Exception as e:
        raise e

@mcp.tool()
def search_car_price(brand_name: str) -> dict:
    """
    Search for car models and their current market prices by brand name.
    
    Args:
        brand_name (str): The display name of the car brand to search for (e.g., 'Toyota', 'Honda', 'Ford').
    
    Returns:
        vehicles (list): List of vehicle models matching the specified brand with pricing information.
    """
    try:
        # Basic parameter checks only - business logic validation
        if not brand_name or not isinstance(brand_name, str):
            raise ValueError("Brand name must be a non-empty string")
        return api.search_car_price(brand_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_vehicles_by_type(vehicle_type: str) -> dict:
    """
    Retrieve available vehicle brands filtered by vehicle type category.
    
    Args:
        vehicle_type (str): The category of vehicles to retrieve. Accepts 'carros' or 'cars' for automobiles, 'motos' or 'motorcycles' for two-wheelers, 'caminhoes' or 'trucks' for commercial trucks.
    
    Returns:
        brands (list): List of brands available for the specified vehicle type in the FIPE database.
    """
    try:
        # Basic parameter checks only - business logic validation
        if not vehicle_type or not isinstance(vehicle_type, str):
            raise ValueError("Vehicle type must be a non-empty string")
        return api.get_vehicles_by_type(vehicle_type)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()