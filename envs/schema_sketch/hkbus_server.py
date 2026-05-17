# Server: HKBus

def get_next_bus(route: str, stop_name: str, direction: str = None) -> dict:
    """
    Get the next arrival time for a specified bus route at a stop.
    
    Args:
        route (str): The bus route number (e.g., "1A", "6", "960")
        stop_name (str): The name of the bus stop
        direction (str): [Optional] The route direction (e.g., "to Tsim Sha Tsui", "to Central"), required if the route has multiple directions
        
    Returns:
        dict: A dictionary containing information about the next bus arrival time, including estimated arrival time, distance from stop.
    """
    pass

def find_buses_to_destination(destination: str, origin: str = None) -> list:
    """
    Find bus routes that go to a specified destination.
    
    Args:
        destination (str): The destination to search for (e.g., "Central", "Mong Kok", "Airport")
        origin (str): [Optional] The origin location name, if provided, searches for routes from origin to destination
        
    Returns:
        list: A list of bus routes that can reach the destination, each route contains route number, route name.
    """
    pass

def get_route_stops_info(route: str, direction: str = None) -> dict:
    """
    Get all stops along a specified bus route.
    
    Args:
        route (str): The bus route number (e.g., "1A", "6", "960")
        direction (str): [Optional] The route direction, required if the route has multiple directions
        
    Returns:
        dict: A dictionary containing information about all stops along the route, including stop list, stop order, stop names.
    """
    pass

def find_stop_by_name(stop_name: str) -> list:
    """
    Find bus stops matching a name or partial name.
    
    Args:
        stop_name (str): Full or partial name of the bus stop to search for
        
    Returns:
        list: A list of matching bus stops, each stop contains stop ID, stop name, location information.
    """
    pass

def get_all_routes_at_stop(stop_name: str) -> list:
    """
    Get all bus routes that pass through a specified bus stop.
    
    Args:
        stop_name (str): Name of the bus stop
        
    Returns:
        list: A list of all bus routes that pass through the stop, each route contains route number, route name, direction.
    """
    pass

def get_bus_eta(route: str, stop_name: str, direction: str = None, count: int = 3) -> list:
    """
    Get multiple estimated arrival times for a specified bus route at a stop.
    
    Args:
        route (str): The bus route number
        stop_name (str): The name of the bus stop
        direction (str): [Optional] The route direction
        count (int): [Optional] Number of bus arrivals to retrieve, defaults to 3
        
    Returns:
        list: A list containing multiple estimated arrival times, each entry includes estimated arrival time, distance.
    """
    pass

def search_route_by_stops(from_stop_name: str, to_stop_name: str) -> list:
    """
    Search for available bus routes by origin and destination stops.
    
    Args:
        from_stop_name (str): Name of the origin bus stop
        to_stop_name (str): Name of the destination bus stop
        
    Returns:
        list: A list of available bus routes from origin to destination, each route contains route number, transfer information.
    """
    pass

