# Server: HotelBooking

def search_destinations(city: str) -> list:
    """
    Search for destinations by city name.
    
    Args:
        city (str): The city name to search for (e.g., "Paris", "New York").
        
    Returns:
        list: A list of matching destinations, each destination is a dict containing destination_id (str), city_name (str), country (str), location information.
    """
    pass

def get_hotels(destination_id: str, checkin_date: str, checkout_date: str, adults: int = 2, kids: int = 0, limit: int = 20) -> list:
    """
    Get hotels available at a destination for specified dates.
    
    Args:
        destination_id (str): The destination ID from search_destinations
        checkin_date (str): Check-in date in format YYYY-MM-DD. Must be a valid future date.
        checkout_date (str): Check-out date in format YYYY-MM-DD. Must be after checkin_date.
        adults (int): [Optional] Number of adults, defaults to 2.
        kids (int): [Optional] Number of kids, defaults to 0.
        limit (int): [Optional] Maximum number of hotels to return, defaults to 20.
        
    Returns:
        list: A list of available hotels, each hotel is a dict containing hotel_id (str), hotel_name (str), star_rating (int), checkin_date (str), checkout_date (str), price_per_night (float), total_price (float).
    """
    pass

def book_hotel(hotel_id: str, checkin_date: str, checkout_date: str, room_type_id: str, adults: int, guest_info: list, kids: int = 0) -> dict:
    """
    Book a hotel room.
    
    Args:
        hotel_id (str): The hotel ID from get_hotels
        checkin_date (str): Check-in date in format YYYY-MM-DD. Must match dates used in get_hotels.
        checkout_date (str): Check-out date in format YYYY-MM-DD. Must match dates used in get_hotels.
        room_type_id (str): The room type ID from get_hotel_details room_types list
        adults (int): Number of adults
        guest_info (list): List of guest information dicts, each dict should contain name (str), phone (str), id_number (str) for identity verification. Required for all guests.
        kids (int): [Optional] Number of kids, defaults to 0.
        
    Returns:
        dict: A dictionary containing booking confirmation including booking_id (str), hotel_name (str), checkin_date (str), checkout_date (str), total_price (float), booking_status (str).
    """
    pass

def get_hotel_details(hotel_id: str) -> dict:
    """
    Get detailed information about a specific hotel.
    
    Args:
        hotel_id (str): The hotel ID from get_hotels
        
    Returns:
        dict: A dictionary containing detailed hotel information including hotel_name (str), address (str), description (str), room_types (list of dicts, each with room_type_id (str), room_name (str), price (float)).
    """
    pass

def cancel_booking(booking_id: str) -> None:
    """
    Cancel a hotel booking.
    
    Args:
        booking_id (str): The booking ID from book_hotel. Subject to hotel cancellation policy and deadlines.

    Returns:
        None
    """
    pass