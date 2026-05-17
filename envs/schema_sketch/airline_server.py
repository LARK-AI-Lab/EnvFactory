# Server: Airline

def list_airports() -> list:
    """
    List all available airports and their IATA codes.
    
    Returns:
        list: Each airport contains {
            "iata": str,
            "city": str
        }
    """
    pass

def search_flights(origin: str, destination: str, date: str) -> list:
    """
    Search for direct flights between two cities on a specific date.
    
    Args:
        origin (str): IATA code of the departure airport
        destination (str): IATA code of the arrival airport
        date (str): Date of the flight in YYYY-MM-DD format
        
    Returns:
        list: Each flight contains {
            "flight_number": str,
            "origin": str,
            "destination": str,
            "scheduled_departure": str,
            "available_seats": dict,
            "prices": dict
        }
    """
    pass

def get_flight_status(flight_number: str, date: str) -> dict:
    """
    Get the current status of a specific flight.
    
    Args:
        flight_number (str): Unique identifier for the flight
        date (str): Date of the flight in YYYY-MM-DD format
        
    Returns:
        dict: {
            "flight_number": str,
            "status": str,  # e.g., "available", "delayed"
            "date": str
        }
    """
    pass

def get_user_details(user_id: str) -> dict:
    """
    Get user profile and their reservation history.
    
    Args:
        user_id (str): Unique identifier for the customer
        
    Returns:
        dict: {
            "user_id": str,
            "name": str,
            "reservations": list,  # List of reservation_ids
            "payment_methods": list
        }
    """
    pass

def get_reservation_details(reservation_id: str) -> dict:
    """
    Get full details of a specific reservation.
    
    Args:
        reservation_id (str): Unique identifier for the flight booking
        
    Returns:
        dict: {
            "reservation_id": str,
            "user_id": str,
            "flights": list,
            "passengers": list,
            "total_price": float,
            "status": str
        }
    """
    pass

def book_reservation(
    user_id: str,
    origin: str,
    destination: str,
    flight_type: str,
    cabin: str,
    flights: list,
    passengers: list,
    payment_method: str,
    total_baggages: int,
    nonfree_baggages: int,
    insurance: bool
) -> dict:
    """
    Book a new flight reservation.
    
    Args:
        user_id (str): Unique identifier for the customer
        origin (str): IATA code of the departure airport
        destination (str): IATA code of the arrival airport
        flight_type (str): Type of travel (e.g., "one_way" or "round_trip")
        cabin (str): Service class for the travel (e.g., "economy" or "business")
        flights (list): Detailed list of flight segments for the booking
        passengers (list): Comprehensive list of passenger details
        payment_methods (list): List of payment methods used for the booking [Enum]: ["credit_card", "paypal", "alipay", "wechat_pay"]
        total_baggages (int): Total number of baggage pieces for all passengers
        nonfree_baggages (int): Number of baggage pieces that require additional payment
        insurance (bool): Whether to include travel insurance for the trip
        
    Returns:
        dict: {
            "reservation_id": str,
            "status": str,
            "total_price": float
        }
    """
    pass

def update_reservation_flights(
    reservation_id: str,
    cabin: str,
    flights: list,
    payment_method: str
) -> dict:
    """
    Update the flights or cabin class of an existing reservation.
    
    Args:
        reservation_id (str): Unique identifier for the flight booking
        cabin (str): Service class for the travel (e.g., "economy" or "business")
        flights (list): Entire new set of flight segments for the booking
        payment_method (str): Payment method used for the charge. [Enum]: ["credit_card", "paypal", "alipay", "wechat_pay"]
        
    Returns:
        dict: {
            "reservation_id": str,
            "status": str,
            "additional_charge": float
        }
    """
    pass

def update_reservation_passengers(reservation_id: str, passengers: list) -> dict:
    """
    Update passenger information for a reservation.
    
    Args:
        reservation_id (str): Unique identifier for the flight booking
        passengers (list): Updated list of passenger details for the booking
        
    Returns:
        dict: {
            "reservation_id": str,
            "status": str
        }
    """
    pass

def update_reservation_baggage(
    reservation_id: str,
    total_baggages: int,
    nonfree_baggages: int,
    payment_method: str
) -> dict:
    """
    Update baggage allowance for a reservation.
    
    Args:
        reservation_id (str): Unique identifier for the flight booking
        total_baggages (int): Updated total number of baggage pieces
        nonfree_baggages (int): Updated count of baggage pieces requiring payment
        payment_method (str): Payment method used for the charge. [Enum]: ["credit_card", "paypal", "alipay", "wechat_pay"]
        
    Returns:
        dict: {
            "reservation_id": str,
            "additional_charge": float
        }
    """
    pass

def cancel_reservation(reservation_id: str) -> dict:
    """
    Cancel an entire reservation and process refunds.
    
    Args:
        reservation_id (str): Unique identifier for the flight booking
        
    Returns:
        dict: {
            "reservation_id": str,
            "status": str,  # "cancelled"
            "refund_amount": float
        }
    """
    pass
