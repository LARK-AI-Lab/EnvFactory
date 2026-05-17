# Server: Maps

def maps_geocode(city: str, country: str = None) -> dict:
    """
    Convert a city name to geographic coordinates (latitude and longitude) at city-level precision. This returns the center coordinates of the specified city, useful for city-level location operations.
    
    Args:
        city (str): The city name to geocode (e.g., "New York", "Beijing", "Tokyo", "London"). Must be a valid city name only, no street addresses or detailed locations. Minimum 2 characters.
        country (str): [Optional] ISO 3166-1 alpha-2 country code (e.g., "US", "CN", "GB", "JP") to disambiguate cities with the same name. If provided, results will be prioritized for the specified country.
        
    Returns:
        dict: A dictionary containing location(dict with latitude (float) and longitude (float)), formatted_address (str), place_id (str). 
    """
    pass

def maps_reverse_geocode(latitude: float, longitude: float) -> dict:
    """
    Convert geographic coordinates to a human-readable address. This is useful for converting precise location coordinates into address information.
    
    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.
        
    Returns:
        dict: A dictionary containing formatted_address (str), place_id (str),coordinates (dict with latitude (float) and longitude (float). 
    """
    pass

def maps_place_details(place_id: str) -> dict:
    """
    Get detailed information about a specific place. This provides comprehensive information including contact details, ratings, reviews, and business hours.
    
    Args:
        place_id (str): The unique identifier of the place.
        
    Returns:
        dict: A dictionary containing name (str), formatted_address (str), location (dict with latitude (float) and longitude (float)), place_id (str), phone_number (str), website (str), rating (float), phone_number (str).
    """
    pass

def maps_distance_matrix(origins: list[str], destinations: list[str], mode: str = "driving") -> dict:
    """
    Calculate distance and travel time between multiple origin and destination points. Returns a matrix of distances and durations for all origin-destination pairs.
    
    Args:
        origins (list[dict]): List of origin location dictionaries, each containing latitude (float) and longitude (float). Maximum 25 origins.
        destinations (list[dict]): List of destination location dictionaries, each containing latitude (float) and longitude (float). Maximum 25 destinations.       
    Returns:
        dict: A dictionary containing rows (list of dicts), each row contains elements (list of dicts), each element contains distance (dict with value (int in meters)). The matrix provides distance for each origin-destination pair.
    """
    pass

def maps_elevation(locations: list[dict]) -> list:
    """
    Get elevation data for specific geographic locations. Returns the elevation above sea level for each provided coordinate.
    
    Args:
        locations (list[dict]): List of location dictionaries, each containing latitude (float) and longitude (float) keys (e.g., [{"latitude": 40.7128, "longitude": -74.0060}, {"latitude": 35.6762, "longitude": 139.6503}]). Maximum 512 locations per request.
        
    Returns:
        list: A list of elevation data, each item is a dict containing location (dict with latitude (float) and longitude (float)), elevation (float in meters), resolution (float in meters, indicating the accuracy of the elevation data).
    """
    pass

def maps_directions(origin_location: str, destination_location: str, mode: str = "driving") -> dict:
    """
    Get detailed turn-by-turn directions between two locations. Returns step-by-step navigation instructions with distance and duration information.
    
    Args:
        origin_location (dict): The origin location dictionary containing latitude (float) and longitude (float).
        destination_location (dict): The destination location dictionary containing latitude (float) and longitude (float).
        mode (str): [Optional] Travel mode: "driving" (default), "bicycling", or "transit". Affects the route calculation and available options.
        
    Returns:
        dict: A dictionary containing routes (list of dicts), each route contains bounds (dict with northeast and southwest coordinates), legs (list of dicts), each leg contains distance (dict with value (int in meters)), duration (dict with value (int in seconds)), steps (list of dicts), each step contains distance (dict with value (int)), duration (dict with value (int)), start_location (dict with latitude (float) and longitude (float)), end_location (dict with latitude (float) and longitude (float)), travel_mode (str)). The steps provide turn-by-turn navigation instructions.
    """
    pass

