from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
import random
import time

# Section 1: Schema
class Location(BaseModel):
    """Represents a geographic location with latitude and longitude."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

class Place(BaseModel):
    """Represents a Point of Interest (POI) place."""
    name: str = Field(..., description="Name of the POI place")
    address: str = Field(..., description="Full address of the POI place")
    location: Location = Field(..., description="Geographic coordinates of the POI location")
    distance: int = Field(..., ge=0, description="Distance from search center in meters")

class RouteInfo(BaseModel):
    """Represents route information between two locations."""
    distance: int = Field(..., ge=0, description="Total route distance in meters")
    duration: int = Field(..., ge=0, description="Estimated travel duration in seconds")
    transfers: Optional[int] = Field(None, ge=0, description="Number of transit transfers required")
    route: List[Dict[str, Any]] = Field(default=[], description="List of coordinate points forming the route path")

class AddressInfo(BaseModel):
    """Represents reverse geocoding address information."""
    address: str = Field(..., description="Full formatted address")
    province: str = Field(..., description="Province or state name")
    city: str = Field(..., description="City name")
    district: str = Field(..., description="District or county name")
    street: str = Field(..., description="Street name and number")

class TaxiProduct(BaseModel):
    """Represents a taxi/ride-hailing product with pricing."""
    product_category: str = Field(..., description="Vehicle category identifier")
    price: float = Field(..., ge=0, description="Estimated fare for this vehicle type")
    estimated_duration: int = Field(..., ge=0, description="Estimated trip duration in seconds")

class TaxiEstimate(BaseModel):
    """Represents taxi fare estimate response."""
    estimate_trace_id: str = Field(..., description="Unique trace identifier for estimate session")
    products: List[TaxiProduct] = Field(..., description="List of available vehicle types with pricing")

class OrderInfo(BaseModel):
    """Represents taxi order information."""
    order_id: str = Field(..., description="Unique identifier for the ride-hailing order")
    status: str = Field(..., description="Current status of the order")
    driver_name: Optional[str] = Field(None, description="Name of the assigned driver")
    driver_phone: Optional[str] = Field(None, description="Contact phone number of the assigned driver")
    license_plate: Optional[str] = Field(None, description="License plate number of the driver's vehicle")
    estimated_arrival: Optional[int] = Field(None, ge=0, description="Estimated time for driver arrival in seconds")

class DriverLocation(BaseModel):
    """Represents driver location tracking information."""
    order_id: str = Field(..., description="Unique identifier for the ride-hailing order")
    driver_lat: str = Field(..., description="Current latitude coordinate of the driver's location")
    driver_lng: str = Field(..., description="Current longitude coordinate of the driver's location")
    updated_at: str = Field(..., description="Timestamp of the last location update in ISO 8601 format")

class CancelInfo(BaseModel):
    """Represents order cancellation information."""
    order_id: str = Field(..., description="Unique identifier for the cancelled ride-hailing order")
    cancelled_at: str = Field(..., description="Timestamp when the order was cancelled in ISO 8601 format")
    refund_status: str = Field(..., description="Status of any refund processing for the cancelled order")

class DeepLink(BaseModel):
    """Represents generated deep link information."""
    deep_link: str = Field(..., description="Generated deep link URL to open the ride-hailing app")
    from_location: str = Field(..., description="Origin location coordinates embedded in the link")
    to_location: str = Field(..., description="Destination location coordinates embedded in the link")

class DidiScenario(BaseModel):
    """Main scenario model for Didi ride-hailing and map services."""
    current_location: Location = Field(default=Location(latitude=39.9042, longitude=116.4074), description="Current device location")
    orders: Dict[str, OrderInfo] = Field(default={}, description="Active taxi orders")
    estimates: Dict[str, TaxiEstimate] = Field(default={}, description="Stored taxi estimates")
    places_database: Dict[str, List[Place]] = Field(default={
        "restaurant": [
            Place(name="Golden Dragon Restaurant", address="123 Main St, Beijing", location=Location(latitude=39.9042, longitude=116.4074), distance=500),
            Place(name="Sichuan Cuisine House", address="456 Park Ave, Beijing", location=Location(latitude=39.9142, longitude=116.4174), distance=1200),
            Place(name="Italian Bistro", address="789 Center St, Beijing", location=Location(latitude=39.8942, longitude=116.3974), distance=800),
            Place(name="Japanese Sushi Bar", address="321 East Rd, Beijing", location=Location(latitude=39.9242, longitude=116.4274), distance=1500),
            Place(name="French Cafe", address="654 West Ave, Beijing", location=Location(latitude=39.8842, longitude=116.3874), distance=2000)
        ],
        "hotel": [
            Place(name="Grand Hotel Beijing", address="1 Palace Rd, Beijing", location=Location(latitude=39.9142, longitude=116.3974), distance=1000),
            Place(name="Business Inn", address="2 Commerce St, Beijing", location=Location(latitude=39.8942, longitude=116.4174), distance=800),
            Place(name="Airport Hotel", address="3 Airport Blvd, Beijing", location=Location(latitude=39.9542, longitude=116.4574), distance=3000),
            Place(name="City Center Hotel", address="4 Central Ave, Beijing", location=Location(latitude=39.9042, longitude=116.4074), distance=200),
            Place(name="Budget Lodge", address="5 Budget St, Beijing", location=Location(latitude=39.8842, longitude=116.4274), distance=2500)
        ],
        "gas station": [
            Place(name="Shell Gas Station", address="100 Fuel Rd, Beijing", location=Location(latitude=39.9242, longitude=116.3874), distance=1800),
            Place(name="PetroChina Station", address="200 Oil Ave, Beijing", location=Location(latitude=39.8742, longitude=116.4374), distance=2200),
            Place(name="Sinopec Gas", address="300 Petroleum St, Beijing", location=Location(latitude=39.9442, longitude=116.3674), distance=2800),
            Place(name="BP Service Station", address="400 Gas Blvd, Beijing", location=Location(latitude=39.8642, longitude=116.4474), distance=3200),
            Place(name="ExxonMobil", address="500 Energy Rd, Beijing", location=Location(latitude=39.9542, longitude=116.3574), distance=3500)
        ]
    }, description="Database of POI places by category")
    address_database: Dict[str, AddressInfo] = Field(default={
        "39.9042,116.4074": AddressInfo(address="Tiananmen Square, Beijing", province="Beijing", city="Beijing", district="Dongcheng", street="Tiananmen Square"),
        "39.9142,116.3974": AddressInfo(address="Forbidden City, Beijing", province="Beijing", city="Beijing", district="Dongcheng", street="4 Jingshan Front St"),
        "39.8942,116.4174": AddressInfo(address="Temple of Heaven, Beijing", province="Beijing", city="Beijing", district="Dongcheng", street="1 Tiantan Rd"),
        "39.9242,116.3874": AddressInfo(address="Beihai Park, Beijing", province="Beijing", city="Beijing", district="Xicheng", street="1 Wenjin St"),
        "39.8842,116.4274": AddressInfo(address="Beijing South Station", province="Beijing", city="Beijing", district="Fengtai", street="12 South Station Rd")
    }, description="Database of addresses by coordinate key")
    route_database: Dict[str, RouteInfo] = Field(default={
        "driving_39.9042,116.4074_39.9142,116.3974": RouteInfo(distance=2000, duration=480, route=[{"lat": 39.9042, "lng": 116.4074}, {"lat": 39.9092, "lng": 116.4024}, {"lat": 39.9142, "lng": 116.3974}]),
        "transit_39.9042,116.4074_39.9142,116.3974": RouteInfo(distance=2200, duration=900, transfers=1, route=[{"type": "subway", "line": "Line 1", "stops": 3}, {"type": "walk", "distance": 200}]),
        "walking_39.9042,116.4074_39.9142,116.3974": RouteInfo(distance=1800, duration=1200, route=[{"lat": 39.9042, "lng": 116.4074}, {"lat": 39.9092, "lng": 116.4024}, {"lat": 39.9142, "lng": 116.3974}]),
        "bicycling_39.9042,116.4074_39.9142,116.3974": RouteInfo(distance=1900, duration=600, route=[{"lat": 39.9042, "lng": 116.4074}, {"lat": 39.9092, "lng": 116.4024}, {"lat": 39.9142, "lng": 116.3974}])
    }, description="Database of pre-calculated routes")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducible results")
    current_time: str = Field(default="2024-01-01T00:00:00", pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Location, Place, RouteInfo, AddressInfo, TaxiProduct, TaxiEstimate, OrderInfo, DriverLocation, CancelInfo, DeepLink, DidiScenario]

# Section 2: Class
class DidiAPI:
    def __init__(self):
        """Initialize Didi API with empty state."""
        self.current_location: Location = Location(latitude=0, longitude=0)
        self.orders: Dict[str, OrderInfo] = {}
        self.estimates: Dict[str, TaxiEstimate] = {}
        self.places_database: Dict[str, List[Place]] = {}
        self.address_database: Dict[str, AddressInfo] = {}
        self.route_database: Dict[str, RouteInfo] = {}
        self.random_seed: Optional[int] = None
        self.current_time: str = "2024-01-01T00:00:00"

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = DidiScenario(**scenario)
        self.current_location = model.current_location
        self.orders = model.orders
        self.estimates = model.estimates
        self.places_database = model.places_database
        self.address_database = model.address_database
        self.route_database = model.route_database
        self.random_seed = model.random_seed
        self.current_time = model.current_time
        if self.random_seed is not None:
            random.seed(self.random_seed)

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "current_location": self.current_location.dict(),
            "orders": {k: v.dict() for k, v in self.orders.items()},
            "estimates": {k: v.dict() for k, v in self.estimates.items()},
            "places_database": {k: [place.dict() for place in places] for k, places in self.places_database.items()},
            "address_database": {k: v.dict() for k, v in self.address_database.items()},
            "route_database": {k: v.dict() for k, v in self.route_database.items()},
            "random_seed": self.random_seed,
            "current_time": self.current_time
        }

    def get_current_location(self) -> dict:
        """Retrieve the current device location coordinates."""
        return {"location": self.current_location.dict()}

    def maps_direction(self, mode: str, origin_location: dict, destination_location: dict, city: Optional[str] = None) -> dict:
        """Plan a route between origin and destination coordinates."""
        origin = Location(**origin_location)
        dest = Location(**destination_location)
        
        # Create route key
        route_key = f"{mode}_{origin.latitude},{origin.longitude}_{dest.latitude},{dest.longitude}"
        
        # Check if route exists in database
        if route_key in self.route_database:
            return self.route_database[route_key].dict()
        
        # Generate new route if not found
        distance = int(((dest.latitude - origin.latitude)**2 + (dest.longitude - origin.longitude)**2)**0.5 * 111000)
        
        # Mode-specific duration calculation
        if mode == "driving":
            duration = int(distance / 8.33)  # ~30 km/h average
        elif mode == "transit":
            duration = int(distance / 5.56)  # ~20 km/h average
            if city:
                return {"distance": distance, "duration": duration, "transfers": 1, "route": [{"type": "subway", "line": "Line 1", "stops": 3}, {"type": "bus", "line": "Bus 101", "stops": 2}]}
            return {"distance": distance, "duration": duration, "transfers": 1, "route": [{"type": "subway", "line": "Line 1", "stops": 3}]}
        elif mode == "walking":
            duration = int(distance / 1.39)  # ~5 km/h average
        elif mode == "bicycling":
            duration = int(distance / 4.17)  # ~15 km/h average
        else:
            duration = int(distance / 5.56)
        
        # Simple route with intermediate points
        route = [
            {"lat": origin.latitude, "lng": origin.longitude},
            {"lat": (origin.latitude + dest.latitude) / 2, "lng": (origin.longitude + dest.longitude) / 2},
            {"lat": dest.latitude, "lng": dest.longitude}
        ]
        
        return {"distance": distance, "duration": duration, "route": route}

    def maps_place_around(self, keywords: str, location: dict, max_distance: Optional[str] = None) -> dict:
        """Search for POI places around a specified location."""
        center = Location(**location)
        max_dist = int(max_distance) if max_distance else 5000
        
        # Find matching places
        matching_places = []
        for category, places in self.places_database.items():
            if keywords.lower() in category.lower() or any(keyword in place.name.lower() for place in places for keyword in keywords.lower().split()):
                for place in places:
                    if place.distance <= max_dist:
                        matching_places.append(place)
        
        # If no exact matches, return some default places
        if not matching_places and keywords.lower() in ["restaurant", "food", "dining"]:
            matching_places = self.places_database.get("restaurant", [])[:3]
        elif not matching_places and keywords.lower() in ["hotel", "lodging"]:
            matching_places = self.places_database.get("hotel", [])[:3]
        elif not matching_places and keywords.lower() in ["gas", "fuel", "station"]:
            matching_places = self.places_database.get("gas station", [])[:3]
        
        return {"places": [place.dict() for place in matching_places]}

    def maps_regeocode(self, location: dict) -> dict:
        """Convert coordinates to human-readable address information."""
        loc = Location(**location)
        coord_key = f"{loc.latitude},{loc.longitude}"
        
        # Check if address exists in database
        if coord_key in self.address_database:
            return self.address_database[coord_key].dict()
        
        # Generate generic address if not found
        return {
            "address": f"{loc.latitude}, {loc.longitude}",
            "province": "Beijing",
            "city": "Beijing",
            "district": "Unknown District",
            "street": f"Street near {loc.latitude}, {loc.longitude}"
        }

    def taxi_estimate(self, origin_location: dict, destination_location: dict) -> dict:
        """Get available ride-hailing vehicle types and fare estimates for a trip between origin and destination."""
        origin = Location(**origin_location)
        dest = Location(**destination_location)
        
        # Calculate distance
        distance = int(((dest.latitude - origin.latitude)**2 + (dest.longitude - origin.longitude)**2)**0.5 * 111000)
        
        # Generate estimate trace ID using current_time
        time_hash = hash(self.current_time) % 100000
        estimate_trace_id = f"EST_{time_hash}_{random.randint(1000, 9999)}"
        
        # Create products with different pricing
        products = [
            TaxiProduct(product_category="economy", price=distance * 0.002 + 8, estimated_duration=int(distance / 8.33)),
            TaxiProduct(product_category="comfort", price=distance * 0.003 + 12, estimated_duration=int(distance / 8.33)),
            TaxiProduct(product_category="business", price=distance * 0.005 + 20, estimated_duration=int(distance / 8.33)),
            TaxiProduct(product_category="luxury", price=distance * 0.008 + 35, estimated_duration=int(distance / 8.33))
        ]
        
        estimate = TaxiEstimate(estimate_trace_id=estimate_trace_id, products=products)
        self.estimates[estimate_trace_id] = estimate
        
        return estimate.dict()

    def taxi_create_order(self, estimate_trace_id: str, product_category: str, caller_car_phone: Optional[str] = None) -> dict:
        """Create a ride-hailing order directly via API."""
        if estimate_trace_id not in self.estimates:
            raise ValueError(f"Estimate trace ID {estimate_trace_id} not found")
        
        # Generate order ID using current_time
        time_hash = hash(self.current_time) % 100000
        order_id = f"ORDER_{time_hash}_{random.randint(1000, 9999)}"
        
        # Find selected product
        estimate = self.estimates[estimate_trace_id]
        selected_product = None
        for product in estimate.products:
            if product.product_category == product_category:
                selected_product = product
                break
        
        if not selected_product:
            raise ValueError(f"Product category {product_category} not found in estimate")
        
        # Create order
        order = OrderInfo(
            order_id=order_id,
            status="pending",
            estimated_arrival=random.randint(300, 900)
        )
        
        self.orders[order_id] = order
        
        return {
            "order_id": order_id,
            "status": "pending",
            "estimated_arrival": order.estimated_arrival,
            "created_at": self.current_time
        }

    def taxi_query_order(self, order_id: Optional[str] = None) -> dict:
        """Query ride-hailing order status and information."""
        if order_id:
            if order_id not in self.orders:
                raise ValueError(f"Order {order_id} not found")
            order = self.orders[order_id]
        else:
            # Return first unfinished order
            unfinished_orders = [o for o in self.orders.values() if o.status not in ["completed", "cancelled"]]
            if not unfinished_orders:
                raise ValueError("No unfinished orders found")
            order = unfinished_orders[0]
        
        # Simulate driver assignment if pending
        if order.status == "pending" and random.random() < 0.7:
            order.status = "accepted"
            order.driver_name = f"Driver {random.randint(100, 999)}"
            order.driver_phone = f"138{random.randint(10000000, 99999999)}"
            order.license_plate = f"京A{random.randint(10000, 99999)}"
        
        return order.dict()

    def taxi_cancel_order(self, order_id: str, reason: Optional[str] = None) -> dict:
        """Cancel an existing ride-hailing order."""
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self.orders[order_id]
        if order.status in ["completed", "cancelled"]:
            raise ValueError(f"Order {order_id} is already {order.status}")
        
        order.status = "cancelled"
        
        return {
            "order_id": order_id,
            "cancelled_at": self.current_time,
            "refund_status": "processing" if reason != "不需要了" else "refunded"
        }

    def taxi_get_driver_location(self, order_id: str) -> dict:
        """Get real-time driver location coordinates for an active order."""
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self.orders[order_id]
        # Allow driver location tracking for all statuses except pending and cancelled
        if order.status in ["pending", "cancelled"]:
            raise ValueError(f"Driver location not available for order status: {order.status}")
        
        # Simulate driver movement
        base_lat = 39.9042
        base_lng = 116.4074
        driver_lat = base_lat + random.uniform(-0.01, 0.01)
        driver_lng = base_lng + random.uniform(-0.01, 0.01)
        
        return {
            "order_id": order_id,
            "driver_lat": str(driver_lat),
            "driver_lng": str(driver_lng),
            "updated_at": self.current_time
        }

    def taxi_generate_ride_app_link(self, origin_location: dict, destination_location: dict, product_category: Optional[str] = None) -> dict:
        """Generate a deep link to open the mobile app with pre-filled locations."""
        origin = Location(**origin_location)
        dest = Location(**destination_location)
        
        from_loc = f"{origin.latitude},{origin.longitude}"
        to_loc = f"{dest.latitude},{dest.longitude}"
        
        # Generate deep link
        deep_link = f"didirider://ride?from={from_loc}&to={to_loc}"
        if product_category:
            deep_link += f"&product={product_category}"
        
        return {
            "deep_link": deep_link,
            "from_location": from_loc,
            "to_location": to_loc
        }

# Section 3: MCP Tools
mcp = FastMCP(name="Didi")
api = DidiAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the Didi API.
    
    Args:
        scenario (dict): Scenario dictionary matching DidiScenario schema.
    
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
    """Save current Didi state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_current_location() -> dict:
    """Retrieve the current device location coordinates for use in map and ride-hailing operations.
    
    Returns:
        location (dict): Geographic coordinates of the location.
    """
    try:
        return api.get_current_location()
    except Exception as e:
        raise e

@mcp.tool()
def maps_direction(mode: str, origin_location: dict, destination_location: dict, city: Optional[str] = None) -> dict:
    """Plan a route between origin and destination coordinates based on the specified travel mode.
    
    Args:
        mode (str): Travel mode for route planning. Must be one of: 'bicycling', 'driving', 'transit', 'walking'.
        origin_location (dict): Geographic coordinates of the origin location.
        destination_location (dict): Geographic coordinates of the destination location.
        city (str): [Optional] City name for the route query. Required when mode is 'transit'.
    
    Returns:
        distance (int): Total route distance in meters.
        duration (int): Estimated travel duration in seconds.
        transfers (int): [Optional] Number of transit transfers required. Only present when mode is 'transit'.
        route (list): List of coordinate points forming the route path.
    """
    try:
        if not mode or not isinstance(mode, str):
            raise ValueError("Mode must be a non-empty string")
        if mode not in ["bicycling", "driving", "transit", "walking"]:
            raise ValueError("Mode must be one of: 'bicycling', 'driving', 'transit', 'walking'")
        if not origin_location or not isinstance(origin_location, dict):
            raise ValueError("Origin location must be a non-empty dictionary")
        if not destination_location or not isinstance(destination_location, dict):
            raise ValueError("Destination location must be a non-empty dictionary")
        return api.maps_direction(mode, origin_location, destination_location, city)
    except Exception as e:
        raise e

@mcp.tool()
def maps_place_around(keywords: str, location: dict, max_distance: Optional[str] = None) -> dict:
    """Search for POI (Point of Interest) places around a specified location based on keywords.
    
    Args:
        keywords (str): Search keywords to filter POI results.
        location (dict): Geographic coordinates of the center location for the search.
        max_distance (str): [Optional] Maximum search radius from the center location in meters.
    
    Returns:
        places (list): List of POI places matching the search criteria.
    """
    try:
        if not keywords or not isinstance(keywords, str):
            raise ValueError("Keywords must be a non-empty string")
        if not location or not isinstance(location, dict):
            raise ValueError("Location must be a non-empty dictionary")
        return api.maps_place_around(keywords, location, max_distance)
    except Exception as e:
        raise e

@mcp.tool()
def maps_regeocode(location: dict) -> dict:
    """Convert longitude and latitude coordinates to human-readable address information (reverse geocoding).
    
    Args:
        location (dict): Geographic coordinates to convert to address information.
    
    Returns:
        address (str): Full formatted address corresponding to the coordinates.
        province (str): Province or state name.
        city (str): City name.
        district (str): District or county name.
        street (str): Street name and number.
    """
    try:
        if not location or not isinstance(location, dict):
            raise ValueError("Location must be a non-empty dictionary")
        return api.maps_regeocode(location)
    except Exception as e:
        raise e

@mcp.tool()
def taxi_estimate(origin_location: dict, destination_location: dict) -> dict:
    """Get available ride-hailing vehicle types and fare estimates for a trip between origin and destination.
    
    Args:
        origin_location (dict): Geographic coordinates of the origin location.
        destination_location (dict): Geographic coordinates of the destination location.
    
    Returns:
        estimate_trace_id (str): Unique trace identifier for this estimate session.
        products (list): List of available vehicle types with pricing information.
    """
    try:
        if not origin_location or not isinstance(origin_location, dict):
            raise ValueError("Origin location must be a non-empty dictionary")
        if not destination_location or not isinstance(destination_location, dict):
            raise ValueError("Destination location must be a non-empty dictionary")
        return api.taxi_estimate(origin_location, destination_location)
    except Exception as e:
        raise e

@mcp.tool()
def taxi_create_order(estimate_trace_id: str, product_category: str, caller_car_phone: Optional[str] = None) -> dict:
    """Create a ride-hailing order directly via API without opening any application interface.
    
    Args:
        estimate_trace_id (str): Unique trace identifier obtained from the taxi_estimate results.
        product_category (str): Vehicle category identifier from estimate results.
        caller_car_phone (str): [Optional] Caller's phone number for driver contact.
    
    Returns:
        order_id (str): Unique identifier for the created ride-hailing order.
        status (str): Current status of the order.
        estimated_arrival (int): Estimated time for driver arrival in seconds.
        created_at (str): Timestamp when the order was created in ISO 8601 format.
    """
    try:
        if not estimate_trace_id or not isinstance(estimate_trace_id, str):
            raise ValueError("Estimate trace ID must be a non-empty string")
        if not product_category or not isinstance(product_category, str):
            raise ValueError("Product category must be a non-empty string")
        return api.taxi_create_order(estimate_trace_id, product_category, caller_car_phone)
    except Exception as e:
        raise e

@mcp.tool()
def taxi_query_order(order_id: Optional[str] = None) -> dict:
    """Query ride-hailing order status and information including driver contact, license plate, and estimated arrival time.
    
    Args:
        order_id (str): [Optional] Unique identifier for the ride-hailing order. If not provided, queries unfinished orders for the current account.
    
    Returns:
        order_id (str): Unique identifier for the ride-hailing order.
        status (str): Current status of the order.
        driver_name (str): [Optional] Name of the assigned driver.
        driver_phone (str): [Optional] Contact phone number of the assigned driver.
        license_plate (str): [Optional] License plate number of the driver's vehicle.
        estimated_arrival (int): [Optional] Estimated time for driver arrival in seconds.
    """
    try:
        return api.taxi_query_order(order_id)
    except Exception as e:
        raise e

@mcp.tool()
def taxi_cancel_order(order_id: str, reason: Optional[str] = None) -> dict:
    """Cancel an existing ride-hailing order.
    
    Args:
        order_id (str): Unique identifier for the ride-hailing order to cancel.
        reason (str): [Optional] Reason for cancellation.
    
    Returns:
        order_id (str): Unique identifier for the cancelled ride-hailing order.
        cancelled_at (str): Timestamp when the order was cancelled in ISO 8601 format.
        refund_status (str): Status of any refund processing for the cancelled order.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        return api.taxi_cancel_order(order_id, reason)
    except Exception as e:
        raise e

@mcp.tool()
def taxi_get_driver_location(order_id: str) -> dict:
    """Get real-time driver location coordinates for an active ride-hailing order.
    
    Args:
        order_id (str): Unique identifier for the ride-hailing order to track driver location.
    
    Returns:
        order_id (str): Unique identifier for the ride-hailing order.
        driver_lat (str): Current latitude coordinate of the driver's location.
        driver_lng (str): Current longitude coordinate of the driver's location.
        updated_at (str): Timestamp of the last location update in ISO 8601 format.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("Order ID must be a non-empty string")
        return api.taxi_get_driver_location(order_id)
    except Exception as e:
        raise e

@mcp.tool()
def taxi_generate_ride_app_link(origin_location: dict, destination_location: dict, product_category: Optional[str] = None) -> dict:
    """Generate a deep link to open the mobile app or mini-program with pre-filled origin, destination, and vehicle type.
    
    Args:
        origin_location (dict): Geographic coordinates of the origin location.
        destination_location (dict): Geographic coordinates of the destination location.
        product_category (str): [Optional] Vehicle category identifier list from estimate results.
    
    Returns:
        deep_link (str): Generated deep link URL to open the ride-hailing app or mini-program.
        from_location (str): Origin location coordinates embedded in the link in format: latitude,longitude.
        to_location (str): Destination location coordinates embedded in the link in format: latitude,longitude.
    """
    try:
        if not origin_location or not isinstance(origin_location, dict):
            raise ValueError("Origin location must be a non-empty dictionary")
        if not destination_location or not isinstance(destination_location, dict):
            raise ValueError("Destination location must be a non-empty dictionary")
        return api.taxi_generate_ride_app_link(origin_location, destination_location, product_category)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()