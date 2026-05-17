# Server: TravelBooking

def authenticate(client_id: str, client_secret: str, grant_type: str, first_name: str, last_name: str) -> dict:
    """
    Authenticate user with the travel booking API and obtain access token.
    
    Args:
        client_id (str): The client application ID supplied by App Management
        client_secret (str): The client application secret supplied by App Management
        grant_type (str): The grant type of the authentication request. [Enum]: ["read_write", "read", "write"]
        first_name (str): The first name of the user
        last_name (str): The last name of the user
        
    Returns:
        dict: A dictionary containing access_token (str) to be used in Authorization header, token_type (str) typically "Bearer", expires_in (int) seconds until token expires, scope (str) the granted scope.
    """
    pass

def check_login_status() -> dict:
    """
    Check if the user is currently logged in and token is valid.
    
    Returns:
        dict: A dictionary containing is_logged_in (bool) indicating login status.
    """
    pass

def list_airports() -> list:
    """
    List all available airports with their IATA codes.
    
    Returns:
        list: A list of airport codes (str) in IATA format (e.g., "SFO", "LAX", "JFK").
    """
    pass

def get_airport_by_city(city_name: str) -> dict:
    """
    Get the nearest airport IATA code for a given city name.
    
    Args:
        city_name (str): The name of the city. [Enum]: ["Rivermist", "Stonebrook", "Maplecrest", "Silverpine", "Shadowridge", "London", "Paris", "Sunset Valley", "Oakendale", "Willowbend", "Crescent Hollow", "Autumnville", "Pinehaven", "Greenfield", "San Francisco", "Los Angeles", "New York", "Chicago", "Boston", "Beijing", "Hong Kong", "Rome", "Tokyo"]
        
    Returns:
        dict: A dictionary containing airport_code (str) the IATA code of the nearest airport, city_name (str) the input city name.
    """
    pass


def search_flights(departure_airport: str, arrival_airport: str, travel_date: str, travel_class: str = None, max_results: int = 5) -> list:
    """
    Search for available flights between two airports on a specific date.
    
    Args:
        departure_airport (str): The 3-letter IATA code of the departure airport. Can be obtained from list_airports or get_airport_by_city.
        arrival_airport (str): The 3-letter IATA code of the arrival airport. Can be obtained from list_airports or get_airport_by_city.
        travel_date (str): The date of travel in format YYYY-MM-DD (e.g., "2024-12-25")
        travel_class (str): [Optional] Filter by travel class. [Enum]: ["economy", "business", "first"]. If not provided, returns all classes.
        max_results (int): [Optional] Maximum number of flight options to return. Defaults to 5.
        
    Returns:
        list: A list of flight options, each containing flight_id (str), departure_airport (str), arrival_airport (str), departure_time (str), arrival_time (str), travel_class (str), cost (float) in USD, available_seats (int).
    """
    pass

def register_credit_card(access_token: str, card_number: str, expiration_date: str, cardholder_name: str, cvv: int) -> dict:
    """
    Register a credit card for payment in the travel booking system.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        card_number (str): The credit card number (typically 13-19 digits)
        expiration_date (str): The expiration date in format MM/YYYY (e.g., "12/2025")
        cardholder_name (str): The name of the cardholder as it appears on the card
        cvv (int): The card verification number (3-4 digits)
        
    Returns:
        dict: A dictionary containing card_id (str) the unique identifier for the registered card, card_number (str) last 4 digits for confirmation, registration_status (str) indicating success.
    """
    pass

def get_credit_card_balance(access_token: str, card_id: str) -> dict:
    """
    Get the current balance of a registered credit card.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        card_id (str): The credit card ID obtained from register_credit_card or list_credit_cards.
        
    Returns:
        dict: A dictionary containing card_id (str), balance (float) the current balance in USD, currency (str) typically "USD".
    """
    pass

def list_credit_cards(access_token: str) -> list:
    """
    List all registered credit cards for the authenticated user.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        
    Returns:
        list: A list of credit cards, each containing card_id (str), card_number (str) last 4 digits, cardholder_name (str), expiration_date (str), balance (float) in USD.
    """
    pass

def book_flight(access_token: str, card_id: str, departure_airport: str, arrival_airport: str, travel_date: str, travel_class: str, traveler_first_name: str = None, traveler_last_name: str = None) -> dict:
    """
    Book a flight using a registered credit card. Requires valid authentication and sufficient card balance.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        card_id (str): The credit card ID obtained from register_credit_card or list_credit_cards.
        departure_airport (str): The 3-letter IATA code of the departure airport. Can be obtained from list_airports or get_airport_by_city.
        arrival_airport (str): The 3-letter IATA code of the arrival airport. Can be obtained from list_airports or get_airport_by_city.
        travel_date (str): The date of travel in format YYYY-MM-DD (e.g., "2024-12-25")
        travel_class (str): The class of travel. [Enum]: ["economy", "business", "first"]
        traveler_first_name (str): [Optional] The first name of the traveler. If not provided, uses authenticated user's first name.
        traveler_last_name (str): [Optional] The last name of the traveler. If not provided, uses authenticated user's last name.
        
    Returns:
        dict: A dictionary containing booking_id (str) the unique booking identifier, transaction_id (str) the payment transaction ID, booking_status (bool) indicating success, cost (float) the amount charged in USD, departure_airport (str), arrival_airport (str), travel_date (str), travel_class (str).
    """
    pass

def get_booking_invoice(access_token: str, booking_id: str) -> dict:
    """
    Retrieve the invoice details for a specific booking.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        booking_id (str): The booking ID obtained from book_flight.
        
    Returns:
        dict: A dictionary containing booking_id (str), invoice_number (str), travel_date (str), departure_airport (str), arrival_airport (str), travel_class (str), cost (float) in USD, transaction_id (str), booking_date (str) when booking was made, payment_status (str).
    """
    pass

def cancel_booking(access_token: str, booking_id: str) -> dict:
    """
    Cancel an existing flight booking. Refund will be processed to the original payment method.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        booking_id (str): The booking ID obtained from book_flight or get_booking_invoice.
        
    Returns:
        dict: A dictionary containing cancellation_status (bool) indicating success, refund_amount (float) the amount refunded in USD, refund_transaction_id (str) [Optional] the refund transaction ID, cancellation_date (str) when cancellation was processed.
    """
    pass

def list_bookings(access_token: str, start_date: str = None, end_date: str = None, status: str = None) -> list:
    """
    List all bookings for the authenticated user with optional filtering.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        start_date (str): [Optional] Filter bookings from this date onwards in format YYYY-MM-DD. If not provided, shows all bookings.
        end_date (str): [Optional] Filter bookings up to this date in format YYYY-MM-DD. If not provided, shows all bookings.
        status (str): [Optional] Filter by booking status. [Enum]: ["confirmed", "cancelled", "pending"]. If not provided, returns all statuses.
        
    Returns:
        list: A list of bookings, each containing booking_id (str), travel_date (str), departure_airport (str), arrival_airport (str), travel_class (str), cost (float) in USD, booking_status (str), booking_date (str).
    """
    pass

def get_insurance_quote(access_token: str, booking_id: str, insurance_type: str) -> dict:
    """
    Get a price quote for travel insurance before purchasing. This allows users to check the cost and coverage details before making a purchase decision.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        booking_id (str): The booking ID obtained from book_flight. The booking must be confirmed.
        insurance_type (str): The type of insurance to get a quote for. [Enum]: ["basic", "premium", "comprehensive"]
        
    Returns:
        dict: A dictionary containing insurance_type (str) the requested insurance type, insurance_cost (float) the estimated cost in USD, coverage_details (dict) details of what is covered.
    """
    pass

def purchase_insurance(access_token: str, booking_id: str, insurance_type: str, card_id: str) -> dict:
    """
    Purchase travel insurance for an existing booking. Users should call get_insurance_quote first to check the price before purchasing.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        booking_id (str): The booking ID obtained from book_flight. The booking must be confirmed.
        insurance_type (str): The type of insurance to purchase. [Enum]: ["basic", "premium", "comprehensive"]
        card_id (str): The credit card ID obtained from register_credit_card or list_credit_cards to use for payment.
        
    Returns:
        dict: A dictionary containing insurance_id (str) the unique insurance identifier, insurance_status (bool) indicating success, insurance_cost (float) the amount charged in USD, coverage_details (dict) details of what is covered.
    """
    pass

def set_budget_limit(access_token: str, budget_limit: float) -> dict:
    """
    Set a budget limit for travel expenses. Bookings exceeding this limit will be restricted.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        budget_limit (float): The budget limit to set in USD. Must be a positive number.
        
    Returns:
        dict: A dictionary containing budget_limit (float) the set budget limit in USD, currency (str) typically "USD", status (str) indicating success.
    """
    pass

def get_budget_info(access_token: str) -> dict:
    """
    Get the current budget limit and spending information for the authenticated user.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        
    Returns:
        dict: A dictionary containing budget_limit (float) [Optional] the current budget limit in USD if set, total_spent (float) total amount spent in USD, remaining_budget (float) [Optional] remaining budget if limit is set, currency (str) typically "USD".
    """
    pass

def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert an amount from one currency to another using current exchange rates.
    
    Args:
        amount (float): The amount to convert. Must be positive.
        from_currency (str): The source currency code. [Enum]: ["USD", "RMB", "EUR", "JPY", "GBP", "CAD", "AUD", "INR", "RUB", "BRL", "MXN"]
        to_currency (str): The target currency code. [Enum]: ["USD", "RMB", "EUR", "JPY", "GBP", "CAD", "AUD", "INR", "RUB", "BRL", "MXN"]
        
    Returns:
        dict: A dictionary containing converted_amount (float) the converted value, from_currency (str), to_currency (str), exchange_rate (float) the rate used for conversion, conversion_date (str) when the rate was obtained.
    """
    pass

def contact_support(access_token: str, message: str, booking_id: str = None, subject: str = None) -> dict:
    """
    Contact customer support for assistance with bookings or general inquiries.
    
    Args:
        access_token (str): The access token obtained from authenticate. Must be valid and not expired.
        booking_id (str): [Optional] The booking ID if inquiry is related to a specific booking. Can be obtained from book_flight or list_bookings.
        subject (str): [Optional] The subject of the inquiry. If not provided, a default subject will be used.
        message (str): The message content describing the issue or question.
        
    Returns:
        dict: A dictionary containing support_ticket_id (str) the unique ticket identifier, status (str) indicating ticket was created, estimated_response_time (str) [Optional] expected response time, message (str) confirmation message.
    """
    pass

