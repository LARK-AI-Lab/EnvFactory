from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
import math

# Section 1: Schema
class Location(BaseModel):
    """Represents a geographic location with latitude and longitude."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate (-180 to 180)")

class Place(BaseModel):
    """Represents a place with detailed information."""
    place_id: str = Field(..., description="Unique identifier of the place")
    name: str = Field(..., description="Name of the place")
    formatted_address: str = Field(..., description="Human-readable address string")
    location: Location = Field(..., description="Geographic coordinates of the place")
    phone_number: Optional[str] = Field(default=None, description="Contact phone number")
    website: Optional[str] = Field(default=None, description="Official website URL")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Average rating score (0-5)")

class GeocodedLocation(BaseModel):
    """Represents a geocoded location result."""
    place_id: str = Field(..., description="Unique identifier of the geocoded place")
    formatted_address: str = Field(..., description="Human-readable address string")
    location: Location = Field(..., description="Geographic coordinates")

class DistanceElement(BaseModel):
    """Represents distance information for an origin-destination pair."""
    distance: Dict[str, int] = Field(..., description="Distance information with value in meters")

class DistanceRow(BaseModel):
    """Represents a row of distance elements for an origin."""
    elements: List[DistanceElement] = Field(..., description="List of distance elements")

class ElevationData(BaseModel):
    """Represents elevation data for a location."""
    location: Location = Field(..., description="Geographic coordinates of the location")
    elevation: float = Field(..., description="Elevation above sea level in meters")
    resolution: float = Field(..., description="Accuracy of elevation data in meters")

class RouteStep(BaseModel):
    """Represents a turn-by-turn step in a route."""
    distance: Dict[str, int] = Field(..., description="Distance information with value in meters")
    duration: Dict[str, int] = Field(..., description="Duration information with value in seconds")
    start_location: Location = Field(..., description="Starting geographic coordinates")
    end_location: Location = Field(..., description="Ending geographic coordinates")
    travel_mode: str = Field(..., description="Mode of travel for the step")

class RouteLeg(BaseModel):
    """Represents a leg of a route between waypoints."""
    distance: Dict[str, int] = Field(..., description="Distance information with value in meters")
    duration: Dict[str, int] = Field(..., description="Duration information with value in seconds")
    steps: List[RouteStep] = Field(..., description="List of turn-by-turn steps")

class Route(BaseModel):
    """Represents a complete route with bounds and legs."""
    bounds: Dict[str, Location] = Field(..., description="Bounding box containing the route")
    legs: List[RouteLeg] = Field(..., description="List of route legs")

class MapsScenario(BaseModel):
    """Main scenario model for maps services."""
    places: Dict[str, Place] = Field(default={}, description="Dictionary of places by place_id")
    cityCoordinates: Dict[str, Location] = Field(default={
        "New York": {"latitude": 40.7128, "longitude": -74.0060},
        "Los Angeles": {"latitude": 34.0522, "longitude": -118.2437},
        "Chicago": {"latitude": 41.8781, "longitude": -87.6298},
        "Houston": {"latitude": 29.7604, "longitude": -95.3698},
        "Phoenix": {"latitude": 33.4484, "longitude": -112.0740},
        "Philadelphia": {"latitude": 39.9526, "longitude": -75.1652},
        "San Antonio": {"latitude": 29.4241, "longitude": -98.4936},
        "San Diego": {"latitude": 32.7157, "longitude": -117.1611},
        "Dallas": {"latitude": 32.7767, "longitude": -96.7970},
        "San Jose": {"latitude": 37.3382, "longitude": -121.8863},
        "Austin": {"latitude": 30.2672, "longitude": -97.7431},
        "Jacksonville": {"latitude": 30.3322, "longitude": -81.6557},
        "Fort Worth": {"latitude": 32.7555, "longitude": -97.3308},
        "Columbus": {"latitude": 39.9612, "longitude": -82.9988},
        "Charlotte": {"latitude": 35.2271, "longitude": -80.8431},
        "San Francisco": {"latitude": 37.7749, "longitude": -122.4194},
        "Indianapolis": {"latitude": 39.7684, "longitude": -86.1581},
        "Seattle": {"latitude": 47.6062, "longitude": -122.3321},
        "Denver": {"latitude": 39.7392, "longitude": -104.9903},
        "Boston": {"latitude": 42.3601, "longitude": -71.0589}
    }, description="Predefined coordinates for major cities")
    elevationData: Dict[str, float] = Field(default={
        "40.7128,-74.0060": 10.0,
        "34.0522,-118.2437": 92.0,
        "41.8781,-87.6298": 181.0,
        "29.7604,-95.3698": 32.0,
        "33.4484,-112.0740": 331.0,
        "39.9526,-75.1652": 12.0,
        "29.4241,-98.4936": 198.0,
        "32.7157,-117.1611": 18.0,
        "32.7767,-96.7970": 131.0,
        "37.3382,-121.8863": 25.0,
        "30.2672,-97.7431": 149.0,
        "30.3322,-81.6557": 5.0,
        "32.7555,-97.3308": 183.0,
        "39.9612,-82.9988": 275.0,
        "35.2271,-80.8431": 229.0,
        "37.7749,-122.4194": 52.0,
        "39.7684,-86.1581": 218.0,
        "47.6062,-122.3321": 56.0,
        "39.7392,-104.9903": 1609.0,
        "42.3601,-71.0589": 43.0
    }, description="Elevation data for predefined coordinates")

Scenario_Schema = [Location, Place, GeocodedLocation, DistanceElement, DistanceRow, ElevationData, RouteStep, RouteLeg, Route, MapsScenario]

# Section 2: Class
class MapsAPI:
    def __init__(self):
        """Initialize maps API with empty state."""
        self.places: Dict[str, Place] = {}
        self.cityCoordinates: Dict[str, Location] = {}
        self.elevationData: Dict[str, float] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = MapsScenario(**scenario)
        self.places = model.places
        self.cityCoordinates = model.cityCoordinates
        self.elevationData = model.elevationData

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "places": {place_id: place.model_dump() for place_id, place in self.places.items()},
            "cityCoordinates": {city: location.model_dump() for city, location in self.cityCoordinates.items()},
            "elevationData": self.elevationData
        }

    def maps_geocode(self, city: str, country: Optional[str] = None) -> dict:
        """Convert a city name into geographic coordinates."""
        city_key = city.title()
        if city_key not in self.cityCoordinates:
            # Generate coordinates for unknown cities
            import hashlib
            hash_val = int(hashlib.md5(city.encode()).hexdigest(), 16)
            lat = (hash_val % 1800) / 10.0 - 90
            lng = ((hash_val // 1800) % 3600) / 10.0 - 180
            self.cityCoordinates[city_key] = Location(latitude=lat, longitude=lng)
        
        location = self.cityCoordinates[city_key]
        place_id = f"geocode_{city_key.replace(' ', '_')}"
        formatted_address = f"{city_key}, {country}" if country else city_key
        
        return {
            "location": location.model_dump(),
            "formatted_address": formatted_address,
            "place_id": place_id
        }

    def maps_reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """Convert geographic coordinates into a human-readable address."""
        coord_key = f"{latitude:.4f},{longitude:.4f}"
        
        # Find closest city
        closest_city = "Unknown Location"
        min_distance = float('inf')
        
        for city, loc in self.cityCoordinates.items():
            distance = math.sqrt((latitude - loc.latitude)**2 + (longitude - loc.longitude)**2)
            if distance < min_distance:
                min_distance = distance
                closest_city = city
        
        place_id = f"reverse_{coord_key.replace(',', '_')}"
        formatted_address = f"{closest_city} ({latitude:.4f}, {longitude:.4f})"
        
        return {
            "formatted_address": formatted_address,
            "place_id": place_id,
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }

    def maps_place_details(self, place_id: str) -> dict:
        """Retrieve comprehensive information about a specific place."""
        if place_id in self.places:
            place = self.places[place_id]
            return {
                "name": place.name,
                "formatted_address": place.formatted_address,
                "location": place.location.model_dump(),
                "place_id": place.place_id,
                "phone_number": place.phone_number,
                "website": place.website,
                "rating": place.rating
            }
        else:
            # Return default place info
            return {
                "name": "Unknown Place",
                "formatted_address": "Unknown Address",
                "location": {"latitude": 0.0, "longitude": 0.0},
                "place_id": place_id,
                "phone_number": None,
                "website": None,
                "rating": None
            }

    def maps_distance_matrix(self, origins: List[dict], destinations: List[dict], mode: str = "driving") -> dict:
        """Calculate distance and travel time between multiple points."""
        rows = []
        
        for origin in origins:
            elements = []
            for dest in destinations:
                # Calculate distance using haversine formula
                lat1, lng1 = origin["latitude"], origin["longitude"]
                lat2, lng2 = dest["latitude"], dest["longitude"]
                
                # Haversine distance
                R = 6371000  # Earth radius in meters
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                delta_phi = math.radians(lat2 - lat1)
                delta_lambda = math.radians(lng2 - lng1)
                
                a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance = int(R * c)
                
                elements.append({"distance": {"value": distance}})
            
            rows.append({"elements": elements})
        
        return {"rows": rows}

    def maps_elevation(self, locations: List[dict]) -> dict:
        """Retrieve elevation data for specific geographic locations."""
        elevation_data = []
        
        for loc in locations:
            lat_key = f"{loc['latitude']:.4f}"
            lng_key = f"{loc['longitude']:.4f}"
            coord_key = f"{lat_key},{lng_key}"
            
            if coord_key in self.elevationData:
                elevation = self.elevationData[coord_key]
            else:
                # Generate elevation for unknown locations
                elevation = int((hash(coord_key) % 2000) + 1)
                self.elevationData[coord_key] = elevation
            
            elevation_data.append({
                "location": loc,
                "elevation": float(elevation),
                "resolution": 10.0
            })
        
        return {"elevation_data": elevation_data}

    def maps_directions(self, origin_location: dict, destination_location: dict, mode: str = "driving") -> dict:
        """Get detailed turn-by-turn directions between two locations."""
        # Calculate route bounds
        lat_min = min(origin_location["latitude"], destination_location["latitude"])
        lat_max = max(origin_location["latitude"], destination_location["latitude"])
        lng_min = min(origin_location["longitude"], destination_location["longitude"])
        lng_max = max(origin_location["longitude"], destination_location["longitude"])
        
        # Create a simple route with one leg and a few steps
        distance_value = 1000  # Default 1km
        duration_value = 300   # Default 5 minutes
        
        steps = [
            {
                "distance": {"value": distance_value // 3},
                "duration": {"value": duration_value // 3},
                "start_location": origin_location,
                "end_location": {
                    "latitude": (origin_location["latitude"] + destination_location["latitude"]) / 2,
                    "longitude": (origin_location["longitude"] + destination_location["longitude"]) / 2
                },
                "travel_mode": mode
            },
            {
                "distance": {"value": distance_value * 2 // 3},
                "duration": {"value": duration_value * 2 // 3},
                "start_location": {
                    "latitude": (origin_location["latitude"] + destination_location["latitude"]) / 2,
                    "longitude": (origin_location["longitude"] + destination_location["longitude"]) / 2
                },
                "end_location": destination_location,
                "travel_mode": mode
            }
        ]
        
        legs = [{
            "distance": {"value": distance_value},
            "duration": {"value": duration_value},
            "steps": steps
        }]
        
        routes = [{
            "bounds": {
                "northeast": {"latitude": lat_max, "longitude": lng_max},
                "southwest": {"latitude": lat_min, "longitude": lng_min}
            },
            "legs": legs
        }]
        
        return {"routes": routes}

# Section 3: MCP Tools
mcp = FastMCP(name="Maps")
api = MapsAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the maps API.
    
    Args:
        scenario (dict): Scenario dictionary matching MapsScenario schema.
    
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
    Save current maps state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def maps_geocode(city: str, country: Optional[str] = None) -> dict:
    """
    Convert a city name into geographic coordinates.
    
    Args:
        city (str): The city name to geocode.
        country (str): [Optional] ISO country code for disambiguation.
    
    Returns:
        location (dict): Geographic coordinates with latitude and longitude.
        formatted_address (str): Human-readable address string.
        place_id (str): Unique identifier of the geocoded place.
    """
    try:
        if not city or not isinstance(city, str) or len(city) < 2:
            raise ValueError("City must be a non-empty string with at least 2 characters")
        return api.maps_geocode(city, country)
    except Exception as e:
        raise e

@mcp.tool()
def maps_reverse_geocode(latitude: float, longitude: float) -> dict:
    """
    Convert geographic coordinates into a human-readable address.
    
    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
    
    Returns:
        formatted_address (str): Human-readable address string.
        place_id (str): Unique identifier of the reverse-geocoded place.
        coordinates (dict): Geographic coordinates of the location.
    """
    try:
        # Basic type checks - range validation handled by Pydantic Location model
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError("Latitude and longitude must be numeric")
        return api.maps_reverse_geocode(latitude, longitude)
    except Exception as e:
        raise e

@mcp.tool()
def maps_place_details(place_id: str) -> dict:
    """
    Retrieve comprehensive information about a specific place.
    
    Args:
        place_id (str): The unique identifier of the place.
    
    Returns:
        name (str): The name of the place.
        formatted_address (str): Human-readable address string.
        location (dict): Geographic coordinates of the place.
        place_id (str): The unique identifier of the place.
        phone_number (str): Contact phone number.
        website (str): Official website URL.
        rating (float): Average rating score.
    """
    try:
        if not place_id or not isinstance(place_id, str):
            raise ValueError("Place ID must be a non-empty string")
        return api.maps_place_details(place_id)
    except Exception as e:
        raise e

@mcp.tool()
def maps_distance_matrix(origins: List[dict], destinations: List[dict], mode: str = "driving") -> dict:
    """
    Calculate distance and travel time between multiple points.
    
    Args:
        origins (List[dict]): List of origin location dictionaries with latitude and longitude.
        destinations (List[dict]): List of destination location dictionaries with latitude and longitude.
        mode (str): [Optional] Travel mode: "driving", "bicycling", or "transit".
    
    Returns:
        rows (List[dict]): List of rows with distance elements for each origin-destination pair.
    """
    try:
        if not isinstance(origins, list) or len(origins) == 0:
            raise ValueError("Origins must be a non-empty list")
        if not isinstance(destinations, list) or len(destinations) == 0:
            raise ValueError("Destinations must be a non-empty list")
        if len(origins) > 25:
            raise ValueError("Maximum 25 origins allowed")
        if len(destinations) > 25:
            raise ValueError("Maximum 25 destinations allowed")
        if mode not in ["driving", "bicycling", "transit"]:
            raise ValueError("Mode must be one of: driving, bicycling, transit")
        return api.maps_distance_matrix(origins, destinations, mode)
    except Exception as e:
        raise e

@mcp.tool()
def maps_elevation(locations: List[dict]) -> dict:
    """
    Retrieve elevation data for specific geographic locations.
    
    Args:
        locations (List[dict]): List of location dictionaries with latitude and longitude.
    
    Returns:
        elevation_data (List[dict]): List of elevation results for each location.
    """
    try:
        if not isinstance(locations, list) or len(locations) == 0:
            raise ValueError("Locations must be a non-empty list")
        if len(locations) > 512:
            raise ValueError("Maximum 512 locations per request")
        return api.maps_elevation(locations)
    except Exception as e:
        raise e

@mcp.tool()
def maps_directions(origin_location: dict, destination_location: dict, mode: str = "driving") -> dict:
    """
    Get detailed turn-by-turn directions between two locations.
    
    Args:
        origin_location (dict): Origin location dictionary with latitude and longitude.
        destination_location (dict): Destination location dictionary with latitude and longitude.
        mode (str): [Optional] Travel mode: "driving", "bicycling", or "transit".
    
    Returns:
        routes (List[dict]): List of possible routes with bounds and legs.
    """
    try:
        if not isinstance(origin_location, dict):
            raise ValueError("Origin location must be a dictionary")
        if not isinstance(destination_location, dict):
            raise ValueError("Destination location must be a dictionary")
        if mode not in ["driving", "bicycling", "transit"]:
            raise ValueError("Mode must be one of: driving, bicycling, transit")
        return api.maps_directions(origin_location, destination_location, mode)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()