# Server: Weather

def get_forecast(latitude: float, longitude: float, days: int = 3) -> dict:
    """
    Get current weather conditions for a location specified by coordinates anywhere in the world. Provides precise weather data for exact geographic coordinates.
    
    Args:
        latitude (float): The latitude of the location in decimal degrees.
        longitude (float): The longitude of the location in decimal degrees.
        days (int): Number of days to forecast. default is 3.
        
    Returns:
        dict:
        - temperature (float): The temperature in Celsius.
        - precipitation chances and amounts
        - wind speed
        - humidity
        - weather conditions
        - timestamp (str): The timestamp of the weather data.
    """
    pass

def get_current_weather(latitude: float, longitude: float) -> dict:
    """
    Get current weather conditions for a location specified by coordinates anywhere in the world. Provides precise weather data for exact geographic coordinates.
    
    Args:
        latitude (float): The latitude of the location in decimal degrees.
        longitude (float): The longitude of the location in decimal degrees.
        
    Returns:
        dict:
        - Current temperature, humidity, wind, pressure
    """
    pass

def search_location(city: str) -> dict:
    """
    Search for a location by city name.
    
    Args:
        city (str): The city name to search for.
    
    Returns:
        dict:
        - location (dict): The location dictionary containing latitude (float) and longitude (float).
        - population (int): The population of the location.
        - country (str): The country of the location.
    """
    pass

def get_alerts(latitude: float, longitude: float, active_only: bool = True) -> dict:
    """
    Get weather alerts for a location specified by coordinates anywhere in the world. 
    
    Args:
        latitude (float): The latitude of the location in decimal degrees.
        longitude (float): The longitude of the location in decimal degrees.
        active_only (bool): Whether to only return active alerts. default is True.

    Returns:
        dict:
        - Alert type and severity (Extreme → Severe → Moderate → Minor)
        - Urgency type
        - Event description and instructions
        - Affected areas
    """
    pass

def get_historical_weather(latitude: float, longitude: float, start_date: str, end_date: str, limit: int = 10) -> dict:
    """
    Get historical weather data for a location specified by coordinates anywhere in the world.
    
    Args:
        latitude (float): The latitude of the location in decimal degrees.
        longitude (float): The longitude of the location in decimal degrees.
        start_date (str): The start date of the historical weather data.
        end_date (str): The end date of the historical weather data.
        limit (int): The number of historical weather data to return. default is 10.

    Return Includes: temperature, conditions, wind speed, humidity, pressure
    """
    pass

def save_location(alias: str, latitude: float, longitude: float, name: str) -> None:
    """
    Save a location with an alias for quick access.
    
    Args:
        alias (str): The alias for the location.
        latitude (float): The latitude of the location in decimal degrees.
        longitude (float): The longitude of the location in decimal degrees.
        name (str): Display name of the location.

    Returns: None
    """
    pass

def list_saved_locations() -> dict:
    """
    View all saved locations.

    Returns:
        dict: return a list of saved alias, names and locations containing latitude and longitude.
     
    """
    pass

def get_saved_location(alias: str) -> dict:
    """
    Get a saved location by alias.

    Args:
        alias (str): The alias of the location to get.

    Returns:
        dict: return the saved location containing alias, name, timezone, latitude and longitude,.
    """
    pass

def remove_saved_location(alias: str) -> None:
    """
    Remove a saved location.

    Args:
        alias (str): The alias of the location to delete.

    Returns: 
        Confirmation of removal
        Count of remaining saved locations
    """