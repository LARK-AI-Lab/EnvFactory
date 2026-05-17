# Server: Didi

def get_current_location() -> str:
    """
    Get the current location coordinates.
    
    Returns:
        str: Location coordinates in format: latitude,longitude
    """
    pass

def maps_direction(mode: str, origin_location: str, destination_location: str, city: str = None) -> dict:
    """
    Plan route between origin and destination coordinates based on travel mode.
    
    Args:
        mode (str): Travel mode, one of: "bicycling", "driving", "transit", "walking"
        origin_location (str): Origin location coordinates in format: latitude,longitude
        destination_location (str): Destination location coordinates in format: latitude,longitude
        city (str): [Optional] City name for query, required when mode is "transit"
        
    Returns:
        dict: {
            "distance": int,
            "duration": int,
            "transfers": int (only for transit mode),
            "route": list of coordinate points or transit segments
        }
    """
    pass

def maps_place_around(keywords: str, location: str, max_distance: str = None) -> list:
    """
    Search for POI places around a location coordinate based on keywords.
    
    Args:
        keywords (str): Search keywords
        location (str): Location coordinates in format: latitude,longitude 
        max_distance (str): [Optional] Search radius in meters
        
    Returns:
        list: Each POI contains {
            "name": str,
            "address": str,
            "location": str (latitude,longitude),
            "distance": int
        }
    """
    pass

def maps_regeocode(location: str) -> dict:
    """
    Convert longitude and latitude coordinates to address information.
    
    Args:
        location (str): Location coordinates in format: latitude,longitude
        
    Returns:
        dict: {
            "address": str,
            "province": str,
            "city": str,
            "district": str,
            "street": str
        }
    """
    pass


def taxi_estimate(origin_location: str, destination_location: str) -> dict:
    """
    Get available ride-hailing vehicle types and fare estimates for a trip.
    
    Args:
        origin_location (str): Origin location coordinates in format: latitude,longitude, must be obtained from map-related tools, cannot be assumed
        destination_location (str): Destination location coordinates in format: latitude,longitude, must be obtained from map-related tools, cannot be assumed
        
    Returns:
        dict: {
            "estimate_trace_id": str,
            "products": list of dicts with product_category, price, estimated_duration
        }
    """
    pass

def taxi_create_order(estimate_trace_id: str, product_category: str, caller_car_phone: str = None) -> dict:
    """
    Create a ride-hailing order directly via API without opening any application interface.
    
    Args:
        estimate_trace_id (str): Estimate trace ID obtained from estimate results
        product_category (str): Vehicle category identifier from estimate results, use comma-separated for multiple categories without spaces
        caller_car_phone (str): [Optional] Caller's phone number, pass if available
        
    Returns:
        dict: {
            "order_id": str,
            "status": str,
            "estimated_arrival": int,
            "created_at": str (ISO 8601)
        }
    """
    pass

def taxi_query_order(order_id: str = None) -> dict:
    """
    Query ride-hailing order status and information, such as driver contact, license plate, estimated arrival time.
    
    Args:
        order_id (str): [Optional] Order ID obtained from order creation results, pass if available, otherwise queries unfinished orders for current account
        
    Returns:
        dict: {
            "order_id": str,
            "status": str,
            "driver_name": str,
            "driver_phone": str,
            "license_plate": str,
            "estimated_arrival": int
        }
    """
    pass

def taxi_cancel_order(order_id: str, reason: str = None) -> dict:
    """
    Cancel a ride-hailing order.
    
    Args:
        order_id (str): Order ID obtained from order creation or query results
        reason (str): [Optional] Cancellation reason, e.g., "不需要了", "等待时间太长", "临时有事"
        
    Returns:
        dict: {
            "order_id": str,
            "cancelled_at": str (ISO 8601),
            "refund_status": str
        }
    """
    pass

def taxi_get_driver_location(order_id: str) -> dict:
    """
    Get real-time driver location coordinates for a ride-hailing order.
    
    Args:
        order_id (str): Ride-hailing order ID
        
    Returns:
        dict: {
            "order_id": str,
            "driver_lat": str,
            "driver_lng": str,
            "updated_at": str (ISO 8601)
        }
    """
    pass

def taxi_generate_ride_app_link(origin_location: str, destination_location: str, product_category: str = None) -> dict:
    """
    Generate deep link to open mobile app or mini-program based on origin, destination and vehicle type.
    
    Args:
        origin_location (str): Origin location coordinates in format: latitude,longitude
        destination_location (str): Destination location coordinates in format: latitude,longitude
        product_category (str): [Optional] Vehicle category identifier list from estimate results, supports multiple categories, only pass when user explicitly specifies certain categories, format: comma-separated
        
    Returns:
        dict: {
            "deep_link": str,
            "from_location": str (latitude,longitude),
            "to_location": str (latitude,longitude)
        }
    """
    pass

