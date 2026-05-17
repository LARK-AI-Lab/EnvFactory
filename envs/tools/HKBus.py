from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Location(BaseModel):
    """Geographic location coordinates."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

class BusStop(BaseModel):
    """Represents a bus stop."""
    stop_id: str = Field(..., description="Unique stop identifier")
    stop_name: str = Field(..., description="Name of the bus stop")
    location: Location = Field(..., description="Geographic coordinates")

class RouteInfo(BaseModel):
    """Bus route information."""
    route_number: str = Field(..., description="Route number identifier")
    route_name: str = Field(..., description="Descriptive route name")
    direction: Optional[str] = Field(default=None, description="Route direction")

class StopOnRoute(BaseModel):
    """Stop information along a route."""
    stop_order: int = Field(..., ge=1, description="Sequential position on route")
    stop_name: str = Field(..., description="Name of the stop")

class BusArrival(BaseModel):
    """Bus arrival information."""
    estimated_arrival_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="ISO 8601 timestamp")
    distance_from_stop: float = Field(..., ge=0, description="Distance in kilometers")

class TransferInfo(BaseModel):
    """Transfer information for routes."""
    is_direct: bool = Field(..., description="Whether route is direct")
    transfer_stops: List[str] = Field(default_factory=list, description="Transfer stop names")

class RouteWithTransfer(BaseModel):
    """Route with transfer information."""
    route_number: str = Field(..., description="Route number")
    transfer_information: TransferInfo = Field(..., description="Transfer details")

class HKBusScenario(BaseModel):
    """Main scenario model for Hong Kong bus system."""
    stops: Dict[str, BusStop] = Field(default_factory=dict, description="All bus stops by stop_id")
    routes: Dict[str, RouteInfo] = Field(default_factory=dict, description="All routes by route_number")
    route_stops: Dict[str, List[StopOnRoute]] = Field(default_factory=dict, description="Stops for each route, keyed by 'route_number:direction'")
    stop_routes: Dict[str, List[RouteInfo]] = Field(default_factory=dict, description="Routes serving each stop, keyed by stop_name")
    bus_arrivals: Dict[str, List[BusArrival]] = Field(default_factory=dict, description="Arrival times keyed by 'route:stop_name:direction'")
    route_connections: Dict[str, List[RouteWithTransfer]] = Field(default_factory=dict, description="Route connections keyed by 'from_stop:to_stop'")

Scenario_Schema = [Location, BusStop, RouteInfo, StopOnRoute, BusArrival, TransferInfo, RouteWithTransfer, HKBusScenario]

# Section 2: Class
class HKBusAPI:
    def __init__(self):
        """Initialize HK Bus API with empty state."""
        self.stops: Dict[str, BusStop] = {}
        self.routes: Dict[str, RouteInfo] = {}
        self.route_stops: Dict[str, List[StopOnRoute]] = {}
        self.stop_routes: Dict[str, List[RouteInfo]] = {}
        self.bus_arrivals: Dict[str, List[BusArrival]] = {}
        self.route_connections: Dict[str, List[RouteWithTransfer]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = HKBusScenario(**scenario)
        self.stops = model.stops
        self.routes = model.routes
        self.route_stops = model.route_stops
        self.stop_routes = model.stop_routes
        self.bus_arrivals = model.bus_arrivals
        self.route_connections = model.route_connections

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "stops": {stop_id: stop.model_dump() for stop_id, stop in self.stops.items()},
            "routes": {route_num: route.model_dump() for route_num, route in self.routes.items()},
            "route_stops": {key: [stop.model_dump() for stop in stops] for key, stops in self.route_stops.items()},
            "stop_routes": {stop_name: [route.model_dump() for route in routes] for stop_name, routes in self.stop_routes.items()},
            "bus_arrivals": {key: [arrival.model_dump() for arrival in arrivals] for key, arrivals in self.bus_arrivals.items()},
            "route_connections": {key: [route.model_dump() for route in routes] for key, routes in self.route_connections.items()}
        }

    def get_next_bus(self, route: str, stop_name: str, direction: Optional[str] = None) -> dict:
        """Retrieve the next estimated arrival time for a bus route at a stop."""
        key = f"{route}:{stop_name}:{direction if direction else ''}"
        arrivals = self.bus_arrivals.get(key, [])
        
        if not arrivals:
            return {}
        
        next_arrival = arrivals[0]
        return {
            "estimated_arrival_time": next_arrival.estimated_arrival_time,
            "distance_from_stop": next_arrival.distance_from_stop
        }

    def find_buses_to_destination(self, destination: str, origin: Optional[str] = None) -> dict:
        """Discover all bus routes serving a destination."""
        matching_routes = []
        
        for route_num, route_info in self.routes.items():
            route_name_lower = route_info.route_name.lower()
            destination_lower = destination.lower()
            
            if destination_lower in route_name_lower:
                if origin:
                    origin_lower = origin.lower()
                    if origin_lower in route_name_lower:
                        matching_routes.append({
                            "route_number": route_info.route_number,
                            "route_name": route_info.route_name
                        })
                else:
                    matching_routes.append({
                        "route_number": route_info.route_number,
                        "route_name": route_info.route_name
                    })
        
        return {"routes": matching_routes}

    def get_route_stops_info(self, route: str, direction: Optional[str] = None) -> dict:
        """Retrieve all stops along a bus route."""
        key = f"{route}:{direction if direction else ''}"
        stops = self.route_stops.get(key, [])
        
        return {
            "stops": [
                {
                    "stop_order": stop.stop_order,
                    "stop_name": stop.stop_name
                }
                for stop in stops
            ]
        }

    def find_stop_by_name(self, stop_name: str) -> dict:
        """Search for bus stops by name."""
        matching_stops = []
        stop_name_lower = stop_name.lower()
        
        for stop_id, stop in self.stops.items():
            if stop_name_lower in stop.stop_name.lower():
                matching_stops.append({
                    "stop_id": stop.stop_id,
                    "stop_name": stop.stop_name,
                    "location": {
                        "latitude": stop.location.latitude,
                        "longitude": stop.location.longitude
                    }
                })
        
        return {"stops": matching_stops}

    def get_all_routes_at_stop(self, stop_name: str) -> dict:
        """Retrieve all bus routes servicing a stop."""
        routes = self.stop_routes.get(stop_name, [])
        
        return {
            "routes": [
                {
                    "route_number": route.route_number,
                    "route_name": route.route_name,
                    "direction": route.direction if route.direction else ""
                }
                for route in routes
            ]
        }

    def get_bus_eta(self, route: str, stop_name: str, direction: Optional[str] = None, count: int = 3) -> dict:
        """Retrieve multiple estimated arrival times for a bus route."""
        key = f"{route}:{stop_name}:{direction if direction else ''}"
        arrivals = self.bus_arrivals.get(key, [])
        
        limited_arrivals = arrivals[:count]
        
        return {
            "arrivals": [
                {
                    "estimated_arrival_time": arrival.estimated_arrival_time,
                    "distance_from_stop": arrival.distance_from_stop
                }
                for arrival in limited_arrivals
            ]
        }

    def search_route_by_stops(self, from_stop_name: str, to_stop_name: str) -> dict:
        """Find bus routes connecting two stops."""
        key = f"{from_stop_name}:{to_stop_name}"
        routes = self.route_connections.get(key, [])
        
        return {
            "routes": [
                {
                    "route_number": route.route_number,
                    "transfer_information": {
                        "is_direct": route.transfer_information.is_direct,
                        "transfer_stops": route.transfer_information.transfer_stops
                    }
                }
                for route in routes
            ]
        }

# Section 3: MCP Tools
mcp = FastMCP(name="HKBus")
api = HKBusAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the HK Bus API.
    
    Args:
        scenario (dict): Scenario dictionary matching HKBusScenario schema.
    
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
    Save current HK Bus state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_next_bus(route: str, stop_name: str, direction: Optional[str] = None) -> dict:
    """
    Retrieve the next estimated arrival time for a specific bus route at a designated stop.
    
    Args:
        route (str): The bus route number identifier (e.g., '1A', '6', '960').
        stop_name (str): The name of the bus stop where the arrival time should be checked.
        direction (str) [Optional]: The route direction indicator (e.g., 'to Tsim Sha Tsui').
    
    Returns:
        estimated_arrival_time (str): The estimated time when the next bus will arrive.
        distance_from_stop (float): The current distance of the approaching bus from the stop.
    """
    try:
        if not route or not isinstance(route, str):
            raise ValueError("Route must be a non-empty string")
        if not stop_name or not isinstance(stop_name, str):
            raise ValueError("Stop name must be a non-empty string")
        
        result = api.get_next_bus(route, stop_name, direction)
        if not result:
            raise ValueError(f"No arrival information found for route {route} at stop {stop_name}")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def find_buses_to_destination(destination: str, origin: Optional[str] = None) -> dict:
    """
    Discover all bus routes that serve a specified destination.
    
    Args:
        destination (str): The destination location name to search for (e.g., 'Central', 'Mong Kok').
        origin (str) [Optional]: The origin location name for filtering routes.
    
    Returns:
        routes (list): Collection of bus routes with route_number and route_name.
    """
    try:
        if not destination or not isinstance(destination, str):
            raise ValueError("Destination must be a non-empty string")
        
        return api.find_buses_to_destination(destination, origin)
    except Exception as e:
        raise e

@mcp.tool()
def get_route_stops_info(route: str, direction: Optional[str] = None) -> dict:
    """
    Retrieve comprehensive information about all stops along a specified bus route.
    
    Args:
        route (str): The bus route number identifier (e.g., '1A', '6', '960').
        direction (str) [Optional]: The route direction indicator.
    
    Returns:
        stops (list): Ordered list of all bus stops with stop_order and stop_name.
    """
    try:
        if not route or not isinstance(route, str):
            raise ValueError("Route must be a non-empty string")
        
        return api.get_route_stops_info(route, direction)
    except Exception as e:
        raise e

@mcp.tool()
def find_stop_by_name(stop_name: str) -> dict:
    """
    Search for bus stops by full or partial name matching.
    
    Args:
        stop_name (str): Full or partial name of the bus stop to search for.
    
    Returns:
        stops (list): Collection of matching bus stops with stop_id, stop_name, and location.
    """
    try:
        if not stop_name or not isinstance(stop_name, str):
            raise ValueError("Stop name must be a non-empty string")
        
        return api.find_stop_by_name(stop_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_all_routes_at_stop(stop_name: str) -> dict:
    """
    Retrieve all bus routes that service a specified bus stop.
    
    Args:
        stop_name (str): The name of the bus stop for which to retrieve all servicing routes.
    
    Returns:
        routes (list): Collection of all bus routes with route_number, route_name, and direction.
    """
    try:
        if not stop_name or not isinstance(stop_name, str):
            raise ValueError("Stop name must be a non-empty string")
        
        return api.get_all_routes_at_stop(stop_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_bus_eta(route: str, stop_name: str, direction: Optional[str] = None, count: int = 3) -> dict:
    """
    Retrieve multiple estimated arrival times for a specified bus route at a stop.
    
    Args:
        route (str): The bus route number identifier (e.g., '1A', '6', '960').
        stop_name (str): The name of the bus stop where arrival times should be checked.
        direction (str) [Optional]: The route direction indicator.
        count (int) [Optional]: The number of upcoming bus arrivals to retrieve (defaults to 3).
    
    Returns:
        arrivals (list): Ordered list of upcoming bus arrivals with estimated_arrival_time and distance_from_stop.
    """
    try:
        if not route or not isinstance(route, str):
            raise ValueError("Route must be a non-empty string")
        if not stop_name or not isinstance(stop_name, str):
            raise ValueError("Stop name must be a non-empty string")
        
        return api.get_bus_eta(route, stop_name, direction, count)
    except Exception as e:
        raise e

@mcp.tool()
def search_route_by_stops(from_stop_name: str, to_stop_name: str) -> dict:
    """
    Find available bus routes connecting two specific stops.
    
    Args:
        from_stop_name (str): The name of the origin bus stop where the journey begins.
        to_stop_name (str): The name of the destination bus stop where the journey ends.
    
    Returns:
        routes (list): Collection of available bus routes with route_number and transfer_information.
    """
    try:
        if not from_stop_name or not isinstance(from_stop_name, str):
            raise ValueError("From stop name must be a non-empty string")
        if not to_stop_name or not isinstance(to_stop_name, str):
            raise ValueError("To stop name must be a non-empty string")
        
        return api.search_route_by_stops(from_stop_name, to_stop_name)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()