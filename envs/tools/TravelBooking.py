from pydantic import BaseModel, Field
from typing import Dict, List, Optional, cast
from mcp.server.fastmcp import FastMCP
import uuid
import random
import hashlib

# Section 1: Schema
class RegisteredUser(BaseModel):
    """Represents a registered user account."""
    client_id: str = Field(..., description="Client application ID")
    client_secret: str = Field(..., description="Client application secret")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")

class Session(BaseModel):
    """Represents an authenticated user session."""
    access_token: str = Field(..., description="Access token for API calls")
    client_id: str = Field(..., description="Client application ID")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., ge=0, description="Token expiration time in seconds")
    scope: str = Field(..., description="Granted permissions scope")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Token creation timestamp")

class Flight(BaseModel):
    """Represents a flight option."""
    flight_id: str = Field(..., description="Unique flight identifier")
    departure_airport: str = Field(..., pattern=r"^[A-Z]{3}$", description="Departure airport IATA code")
    arrival_airport: str = Field(..., pattern=r"^[A-Z]{3}$", description="Arrival airport IATA code")
    departure_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Departure time in HH:MM format")
    arrival_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Arrival time in HH:MM format")
    travel_class: str = Field(..., description="Travel class: economy, business, or first")
    cost: float = Field(..., ge=0, description="Flight price in USD")
    available_seats: int = Field(..., ge=0, description="Number of available seats")

class CreditCard(BaseModel):
    """Represents a registered credit card."""
    card_id: str = Field(..., description="Unique card identifier")
    card_number: str = Field(..., description="Last 4 digits of card number")
    cardholder_name: str = Field(..., description="Cardholder name")
    expiration_date: str = Field(..., pattern=r"^\d{2}/\d{4}$", description="Expiration date in MM/YYYY format")
    balance: float = Field(..., ge=0, description="Available balance in USD")

class Booking(BaseModel):
    """Represents a flight booking."""
    booking_id: str = Field(..., description="Unique booking identifier")
    transaction_id: str = Field(..., description="Payment transaction ID")
    booking_status: str = Field(..., description="Booking status: confirmed, cancelled, or pending")
    cost: float = Field(..., ge=0, description="Total booking cost in USD")
    departure_airport: str = Field(..., pattern=r"^[A-Z]{3}$", description="Departure airport IATA code")
    arrival_airport: str = Field(..., pattern=r"^[A-Z]{3}$", description="Arrival airport IATA code")
    travel_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Travel date in YYYY-MM-DD format")
    travel_class: str = Field(..., description="Travel class")
    booking_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Booking creation timestamp")
    traveler_first_name: str = Field(..., description="Traveler's first name")
    traveler_last_name: str = Field(..., description="Traveler's last name")

class TravelBookingScenario(BaseModel):
    """Main scenario model for travel booking system."""
    registered_users: Dict[str, RegisteredUser] = Field(default={}, description="Registered user accounts")
    authenticated_users: Dict[str, Session] = Field(default={}, description="Currently authenticated users")
    available_flights: Dict[str, List[Flight]] = Field(default={}, description="Available flights by route key")
    airport_city_map: Dict[str, str] = Field(default={
        "Rivermist": "RVM", "Stonebrook": "STB", "Maplecrest": "MPC", "Silverpine": "SVP", "Shadowridge": "SHR",
        "London": "LHR", "Paris": "CDG", "Sunset Valley": "SVV", "Oakendale": "OKD", "Willowbend": "WLB",
        "Crescent Hollow": "CHW", "Autumnville": "ATV", "Pinehaven": "PHV", "Greenfield": "GNF",
        "San Francisco": "SFO", "Los Angeles": "LAX", "New York": "JFK", "Chicago": "ORD", "Boston": "BOS",
        "Beijing": "PEK", "Hong Kong": "HKG", "Rome": "FCO", "Tokyo": "NRT"
    }, description="City to airport code mapping")
    credit_cards: Dict[str, CreditCard] = Field(default={}, description="Registered credit cards")
    bookings: Dict[str, Booking] = Field(default={}, description="Flight bookings")
    budget_limits: Dict[str, float] = Field(default={}, description="User budget limits in USD")
    total_spent: Dict[str, float] = Field(default={}, description="Total amount spent by user in USD")
    exchange_rates: Dict[str, float] = Field(default={
        "USD": 1.0, "RMB": 7.2, "EUR": 0.85, "JPY": 110.0, "GBP": 0.73, "CAD": 1.25, "AUD": 1.35,
        "INR": 74.0, "RUB": 74.0, "BRL": 5.2, "MXN": 20.0
    }, description="Currency exchange rates to USD")
    insurance_quotes: Dict[str, Dict[str, dict]] = Field(default={}, description="Insurance quotes by booking and type")
    insurance_policies: Dict[str, dict] = Field(default={}, description="Purchased insurance policies")
    support_tickets: List[dict] = Field(default=[], description="Customer support tickets")
    current_time: str = Field(default="2024-01-01T00:00:00", pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")
    random_seed: Optional[int] = Field(default=42, description="Random seed for reproducible scenarios")

Scenario_Schema = [RegisteredUser, Session, Flight, CreditCard, Booking, TravelBookingScenario]

# Section 2: Class
class TravelBookingAPI:
    def __init__(self):
        """Initialize travel booking API with empty state."""
        self.registered_users: Dict[str, RegisteredUser] = {}
        self.authenticated_users: Dict[str, Session] = {}
        self.available_flights: Dict[str, List[Flight]] = {}
        self.airport_city_map: Dict[str, str] = {}
        self.credit_cards: Dict[str, CreditCard] = {}
        self.bookings: Dict[str, Booking] = {}
        self.budget_limits: Dict[str, float] = {}
        self.total_spent: Dict[str, float] = {}
        self.exchange_rates: Dict[str, float] = {}
        self.insurance_quotes: Dict[str, Dict[str, dict]] = {}
        self.insurance_policies: Dict[str, dict] = {}
        self.support_tickets: List[dict] = []
        self.current_time: str = "2024-01-01T00:00:00"
        self.random_seed: Optional[int] = 42
        self.uuid_counter: int = 0
    
    def _generate_deterministic_uuid(self) -> str:
        """Generate deterministic UUID based on random_seed and counter."""
        # Use seed and counter to generate deterministic UUID
        seed = cast(int, self.random_seed)
        # Combine seed and counter as string, then hash
        combined_str = f"{seed}_{self.uuid_counter}"
        combined_bytes = combined_str.encode('utf-8')
        hash_obj = hashlib.md5(combined_bytes)
        hash_hex = hash_obj.hexdigest()
        
        # Format as UUID
        uuid_str = f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
        self.uuid_counter += 1
        return uuid_str
    
    def _generate_deterministic_random_int(self, min_val: int, max_val: int) -> int:
        """Generate deterministic random integer based on random_seed."""
        # Use counter to generate deterministic random number
        seed = cast(int, self.random_seed)
        random.seed(seed + self.uuid_counter)
        result = random.randint(min_val, max_val)
        self.uuid_counter += 1
        return result

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = TravelBookingScenario(**scenario)
        self.registered_users = model.registered_users
        self.authenticated_users = model.authenticated_users
        self.available_flights = model.available_flights
        self.airport_city_map = model.airport_city_map
        self.credit_cards = model.credit_cards
        self.bookings = model.bookings
        self.budget_limits = model.budget_limits
        self.total_spent = model.total_spent
        self.exchange_rates = model.exchange_rates
        self.insurance_quotes = model.insurance_quotes
        self.insurance_policies = model.insurance_policies
        self.support_tickets = model.support_tickets
        self.current_time = model.current_time
        self.random_seed = model.random_seed
        self.uuid_counter = 0
        random.seed(self.random_seed)

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "registered_users": {cid: user.dict() for cid, user in self.registered_users.items()},
            "authenticated_users": {uid: user.dict() for uid, user in self.authenticated_users.items()},
            "available_flights": {route: [flight.dict() for flight in flights] for route, flights in self.available_flights.items()},
            "airport_city_map": self.airport_city_map,
            "credit_cards": {cid: card.dict() for cid, card in self.credit_cards.items()},
            "bookings": {bid: booking.dict() for bid, booking in self.bookings.items()},
            "budget_limits": self.budget_limits,
            "total_spent": self.total_spent,
            "exchange_rates": self.exchange_rates,
            "insurance_quotes": self.insurance_quotes,
            "insurance_policies": self.insurance_policies,
            "support_tickets": self.support_tickets,
            "current_time": self.current_time,
            "random_seed": self.random_seed
        }

    def authenticate(self, client_id: str, client_secret: str, grant_type: str, first_name: str, last_name: str) -> dict:
        """Authenticate user and return access token. Only verifies existing registered users."""
        # Check if user is registered
        if client_id not in self.registered_users:
            raise ValueError(f"User with client_id '{client_id}' is not registered")
        
        registered_user = self.registered_users[client_id]
        
        # Verify client_secret
        if registered_user.client_secret != client_secret:
            raise ValueError("Invalid client_secret")
        
        # Verify user information matches
        if registered_user.first_name != first_name or registered_user.last_name != last_name:
            raise ValueError("User information does not match registered account")
        
        # Generate access token for authenticated user
        access_token = self._generate_deterministic_uuid()
        session = Session(
            access_token=access_token,
            client_id=client_id,
            token_type="Bearer",
            expires_in=3600,
            scope=grant_type,
            created_at=self.current_time
        )
        self.authenticated_users[access_token] = session
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": grant_type
        }

    def check_login_status(self) -> dict:
        """Check if user is currently logged in with valid token."""
        return {"is_logged_in": len(self.authenticated_users) > 0}

    def list_airports(self) -> dict:
        """List all available airport codes."""
        return {"airport_codes": list(set(self.airport_city_map.values()))}

    def get_airport_by_city(self, city_name: str) -> dict:
        """Get airport code for given city name."""
        if city_name in self.airport_city_map:
            return {"airport_code": self.airport_city_map[city_name], "city_name": city_name}
        return {"airport_code": "N/A", "city_name": city_name}

    def search_flights(self, departure_airport: str, arrival_airport: str, travel_date: str, travel_class: Optional[str] = None, max_results: Optional[int] = None) -> dict:
        """Search for flights between airports on specific date."""
        route_key = f"{departure_airport}-{arrival_airport}"
        if route_key not in self.available_flights:
            return {"flights": []}
        
        flights = self.available_flights[route_key]
        if travel_class:
            flights = [f for f in flights if f.travel_class == travel_class]
        
        if travel_date:
            flights = [f for f in flights if f.departure_airport == departure_airport and f.arrival_airport == arrival_airport]
        
        if max_results:
            flights = flights[:max_results]
        
        return {"flights": [f.dict() for f in flights]}

    def register_credit_card(self, access_token: str, card_number: str, expiration_date: str, cardholder_name: str, cvv: int) -> dict:
        """Register a new credit card."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        
        card_id = self._generate_deterministic_uuid()
        last_4 = card_number[-4:] if len(card_number) >= 4 else card_number
        card = CreditCard(
            card_id=card_id,
            card_number=last_4,
            cardholder_name=cardholder_name,
            expiration_date=expiration_date,
            balance=self._generate_deterministic_random_int(1000, 10000)
        )
        self.credit_cards[card_id] = card
        return {
            "card_id": card_id,
            "card_number": last_4,
            "registration_status": "success"
        }

    def get_credit_card_balance(self, access_token: str, card_id: str) -> dict:
        """Get balance of registered credit card."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        if card_id not in self.credit_cards:
            raise ValueError("Card not found")
        
        card = self.credit_cards[card_id]
        return {
            "card_id": card_id,
            "balance": card.balance,
            "currency": "USD"
        }

    def list_credit_cards(self, access_token: str) -> dict:
        """List all registered credit cards."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        
        user_cards = {k: v for k, v in self.credit_cards.items()}
        return {"credit_cards": [card.dict() for card in user_cards.values()]}

    def book_flight(self, access_token: str, card_id: str, departure_airport: str, arrival_airport: str, travel_date: str, travel_class: str, traveler_first_name: Optional[str] = None, traveler_last_name: Optional[str] = None) -> dict:
        """Book a flight using registered credit card."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        if card_id not in self.credit_cards:
            raise ValueError("Card not found")
        
        session = self.authenticated_users[access_token]
        registered_user = self.registered_users[session.client_id]
        card = self.credit_cards[card_id]
        
        route_key = f"{departure_airport}-{arrival_airport}"
        if route_key not in self.available_flights:
            raise ValueError("No flights available for this route")
        
        available_flights = [f for f in self.available_flights[route_key] if f.travel_class == travel_class]
        if not available_flights:
            raise ValueError("No flights available in this class")
        
        flight = available_flights[0]
        if flight.cost > card.balance:
            raise ValueError("Insufficient card balance")
        
        booking_id = self._generate_deterministic_uuid()
        transaction_id = self._generate_deterministic_uuid()
        
        if not traveler_first_name:
            traveler_first_name = registered_user.first_name
        if not traveler_last_name:
            traveler_last_name = registered_user.last_name
        
        booking = Booking(
            booking_id=booking_id,
            transaction_id=transaction_id,
            booking_status="confirmed",
            cost=flight.cost,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            travel_date=travel_date,
            travel_class=travel_class,
            booking_date=self.current_time,
            traveler_first_name=traveler_first_name,
            traveler_last_name=traveler_last_name
        )
        
        self.bookings[booking_id] = booking
        card.balance -= flight.cost
        self.total_spent[access_token] = self.total_spent.get(access_token, 0) + flight.cost
        
        return {
            "booking_id": booking_id,
            "transaction_id": transaction_id,
            "booking_status": True,
            "cost": flight.cost,
            "departure_airport": departure_airport,
            "arrival_airport": arrival_airport,
            "travel_date": travel_date,
            "travel_class": travel_class
        }

    def get_booking_invoice(self, access_token: str, booking_id: str) -> dict:
        """Get invoice details for specific booking."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        if booking_id not in self.bookings:
            raise ValueError("Booking not found")
        
        booking = self.bookings[booking_id]
        return {
            "booking_id": booking_id,
            "invoice_number": f"INV-{booking_id[:8]}",
            "travel_date": booking.travel_date,
            "departure_airport": booking.departure_airport,
            "arrival_airport": booking.arrival_airport,
            "travel_class": booking.travel_class,
            "cost": booking.cost,
            "transaction_id": booking.transaction_id,
            "booking_date": booking.booking_date,
            "payment_status": "paid"
        }

    def cancel_booking(self, access_token: str, booking_id: str) -> dict:
        """Cancel existing flight booking."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        if booking_id not in self.bookings:
            raise ValueError("Booking not found")
        
        booking = self.bookings[booking_id]
        if booking.booking_status == "cancelled":
            raise ValueError("Booking already cancelled")
        
        booking.booking_status = "cancelled"
        refund_transaction_id = self._generate_deterministic_uuid()
        
        return {
            "cancellation_status": True,
            "refund_amount": booking.cost,
            "refund_transaction_id": refund_transaction_id,
            "cancellation_date": self.current_time[:10]  # Extract date part
        }

    def list_bookings(self, access_token: str, start_date: Optional[str] = None, end_date: Optional[str] = None, status: Optional[str] = None) -> dict:
        """List all bookings for authenticated user."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        
        user_bookings = list(self.bookings.values())
        
        if status:
            user_bookings = [b for b in user_bookings if b.booking_status == status]
        
        return {"bookings": [b.dict() for b in user_bookings]}

    def get_insurance_quote(self, access_token: str, booking_id: str, insurance_type: str) -> dict:
        """Get insurance quote for booking."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        if booking_id not in self.bookings:
            raise ValueError("Booking not found")
        
        booking = self.bookings[booking_id]
        if booking.booking_status != "confirmed":
            raise ValueError("Booking must be confirmed for insurance")
        
        quote_key = f"{booking_id}-{insurance_type}"
        cost = booking.cost * 0.05 if insurance_type == "basic" else booking.cost * 0.08 if insurance_type == "premium" else booking.cost * 0.12
        
        coverage = {
            "basic": {"medical": "$10,000", "trip_cancel": "$1,000", "baggage": "$500"},
            "premium": {"medical": "$50,000", "trip_cancel": "$5,000", "baggage": "$2,000"},
            "comprehensive": {"medical": "$100,000", "trip_cancel": "$10,000", "baggage": "$5,000"}
        }
        
        quote = {
            "insurance_type": insurance_type,
            "insurance_cost": cost,
            "coverage_details": coverage[insurance_type]
        }
        
        if booking_id not in self.insurance_quotes:
            self.insurance_quotes[booking_id] = {}
        self.insurance_quotes[booking_id][insurance_type] = quote
        
        return quote

    def purchase_insurance(self, access_token: str, booking_id: str, insurance_type: str, card_id: str) -> dict:
        """Purchase travel insurance for booking."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        if booking_id not in self.bookings:
            raise ValueError("Booking not found")
        if card_id not in self.credit_cards:
            raise ValueError("Card not found")
        
        booking = self.bookings[booking_id]
        card = self.credit_cards[card_id]
        
        if booking_id not in self.insurance_quotes or insurance_type not in self.insurance_quotes[booking_id]:
            raise ValueError("No quote available for this insurance type")
        
        quote = self.insurance_quotes[booking_id][insurance_type]
        insurance_cost = quote["insurance_cost"]
        
        if insurance_cost > card.balance:
            raise ValueError("Insufficient card balance")
        
        insurance_id = self._generate_deterministic_uuid()
        policy = {
            "insurance_id": insurance_id,
            "insurance_type": insurance_type,
            "insurance_cost": insurance_cost,
            "coverage_details": quote["coverage_details"]
        }
        
        self.insurance_policies[insurance_id] = policy
        card.balance -= insurance_cost
        
        return policy

    def set_budget_limit(self, access_token: str, budget_limit: float) -> dict:
        """Set budget limit for user."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        
        self.budget_limits[access_token] = budget_limit
        return {
            "budget_limit": budget_limit,
            "currency": "USD",
            "status": "success"
        }

    def get_budget_info(self, access_token: str) -> dict:
        """Get budget information for user."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        
        budget_limit = self.budget_limits.get(access_token)
        total_spent = self.total_spent.get(access_token, 0)
        
        result = {
            "total_spent": total_spent,
            "currency": "USD"
        }
        
        if budget_limit is not None:
            result["budget_limit"] = budget_limit
            result["remaining_budget"] = budget_limit - total_spent
        
        return result

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> dict:
        """Convert currency using exchange rates."""
        if from_currency not in self.exchange_rates or to_currency not in self.exchange_rates:
            raise ValueError("Unsupported currency")
        
        usd_amount = amount / self.exchange_rates[from_currency]
        converted_amount = usd_amount * self.exchange_rates[to_currency]
        exchange_rate = self.exchange_rates[to_currency] / self.exchange_rates[from_currency]
        
        return {
            "converted_amount": round(converted_amount, 2),
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": round(exchange_rate, 4),
            "conversion_date": self.current_time[:10]  # Extract date part
        }

    def contact_support(self, access_token: str, message: str, booking_id: Optional[str] = None, subject: Optional[str] = None) -> dict:
        """Contact customer support."""
        if access_token not in self.authenticated_users:
            raise ValueError("Invalid access token")
        
        ticket_id = self._generate_deterministic_uuid()
        ticket = {
            "support_ticket_id": ticket_id,
            "subject": subject or "General Inquiry",
            "message": message,
            "booking_id": booking_id,
            "created_at": self.current_time
        }
        
        self.support_tickets.append(ticket)
        
        return {
            "support_ticket_id": ticket_id,
            "status": "created",
            "estimated_response_time": "24-48 hours",
            "message": "Support ticket created successfully"
        }

# Section 3: MCP Tools
mcp = FastMCP(name="TravelBookingAPI")
api = TravelBookingAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the travel booking API.
    
    Args:
        scenario (dict): Scenario dictionary matching TravelBookingScenario schema.
    
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
    """Save current travel booking state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def authenticate(client_id: str, client_secret: str, grant_type: str, first_name: str, last_name: str) -> dict:
    """Authenticate user with the travel booking API.
    
    Args:
        client_id (str): Client application ID for API access.
        client_secret (str): Client application secret for secure authentication.
        grant_type (str): Level of access permissions (read_write, read, or write).
        first_name (str): User's first name.
        last_name (str): User's last name.
    
    Returns:
        access_token (str): Access token for subsequent API calls.
        token_type (str): Token type, typically 'Bearer'.
        expires_in (int): Token expiration time in seconds.
        scope (str): Granted permissions scope.
    """
    try:
        if not all([client_id, client_secret, grant_type, first_name, last_name]):
            raise ValueError("All authentication parameters are required")
        return api.authenticate(client_id, client_secret, grant_type, first_name, last_name)
    except Exception as e:
        raise e

@mcp.tool()
def check_login_status() -> dict:
    """Check if user is currently logged in with valid token.
    
    Returns:
        is_logged_in (bool): Whether user is authenticated with valid token.
    """
    try:
        return api.check_login_status()
    except Exception as e:
        raise e

@mcp.tool()
def list_airports() -> dict:
    """List all available airports with IATA codes.
    
    Returns:
        airport_codes (list): List of 3-letter IATA airport codes.
    """
    try:
        return api.list_airports()
    except Exception as e:
        raise e

@mcp.tool()
def get_airport_by_city(city_name: str) -> dict:
    """Get airport IATA code for given city name.
    
    Args:
        city_name (str): Name of the city to find airport for.
    
    Returns:
        airport_code (str): 3-letter IATA code of nearest airport.
        city_name (str): Confirmed city name that was queried.
    """
    try:
        if not city_name or not isinstance(city_name, str):
            raise ValueError("City name must be a non-empty string")
        return api.get_airport_by_city(city_name)
    except Exception as e:
        raise e

@mcp.tool()
def search_flights(departure_airport: str, arrival_airport: str, travel_date: str, travel_class: Optional[str] = None, max_results: Optional[int] = None) -> dict:
    """Search for available flights between airports on specific date.
    
    Args:
        departure_airport (str): 3-letter IATA code of departure airport.
        arrival_airport (str): 3-letter IATA code of arrival airport.
        travel_date (str): Travel date in YYYY-MM-DD format.
        travel_class (str): [Optional] Filter by travel class (economy, business, first).
        max_results (int): [Optional] Maximum number of flight options to return.
    
    Returns:
        flights (list): List of available flight options matching criteria.
    """
    try:
        if not all([departure_airport, arrival_airport, travel_date]):
            raise ValueError("Departure airport, arrival airport, and travel date are required")
        return api.search_flights(departure_airport, arrival_airport, travel_date, travel_class, max_results)
    except Exception as e:
        raise e

@mcp.tool()
def register_credit_card(access_token: str, card_number: str, expiration_date: str, cardholder_name: str, cvv: int) -> dict:
    """Register a credit card for payment processing.
    
    Args:
        access_token (str): Valid access token from authenticate.
        card_number (str): Credit card number (13-19 digits).
        expiration_date (str): Expiration date in MM/YYYY format.
        cardholder_name (str): Name on the credit card.
        cvv (int): Card verification number (3-4 digits).
    
    Returns:
        card_id (str): Credit card ID for payment operations.
        card_number (str): Last 4 digits of registered card.
        registration_status (str): Success status of registration.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        if not all([card_number, expiration_date, cardholder_name]):
            raise ValueError("All card details are required")
        return api.register_credit_card(access_token, card_number, expiration_date, cardholder_name, cvv)
    except Exception as e:
        raise e

@mcp.tool()
def get_credit_card_balance(access_token: str, card_id: str) -> dict:
    """Get current balance of registered credit card.
    
    Args:
        access_token (str): Valid access token from authenticate.
        card_id (str): Credit card ID from register_credit_card or list_credit_cards.
    
    Returns:
        card_id (str): Credit card ID.
        balance (float): Available balance in USD.
        currency (str): Currency code (typically 'USD').
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        if not card_id or not isinstance(card_id, str):
            raise ValueError("Card ID must be a non-empty string")
        return api.get_credit_card_balance(access_token, card_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_credit_cards(access_token: str) -> dict:
    """List all registered credit cards for authenticated user.
    
    Args:
        access_token (str): Valid access token from authenticate.
    
    Returns:
        credit_cards (list): List of registered credit cards with details.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        return api.list_credit_cards(access_token)
    except Exception as e:
        raise e

@mcp.tool()
def book_flight(access_token: str, card_id: str, departure_airport: str, arrival_airport: str, travel_date: str, travel_class: str, traveler_first_name: Optional[str] = None, traveler_last_name: Optional[str] = None) -> dict:
    """Book a flight using registered credit card.
    
    Args:
        access_token (str): Valid access token from authenticate.
        card_id (str): Credit card ID for payment.
        departure_airport (str): 3-letter IATA code of departure airport.
        arrival_airport (str): 3-letter IATA code of arrival airport.
        travel_date (str): Travel date in YYYY-MM-DD format.
        travel_class (str): Travel class (economy, business, or first).
        traveler_first_name (str): [Optional] Traveler's first name.
        traveler_last_name (str): [Optional] Traveler's last name.
    
    Returns:
        booking_id (str): Unique booking identifier.
        transaction_id (str): Payment transaction ID.
        booking_status (bool): Whether booking was successful.
        cost (float): Total booking cost in USD.
        departure_airport (str): Departure airport code.
        arrival_airport (str): Arrival airport code.
        travel_date (str): Travel date.
        travel_class (str): Travel class.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        required_fields = [card_id, departure_airport, arrival_airport, travel_date, travel_class]
        if not all(required_fields):
            raise ValueError("All required booking fields must be provided")
        return api.book_flight(access_token, card_id, departure_airport, arrival_airport, travel_date, travel_class, traveler_first_name, traveler_last_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_booking_invoice(access_token: str, booking_id: str) -> dict:
    """Retrieve invoice details for specific booking.
    
    Args:
        access_token (str): Valid access token from authenticate.
        booking_id (str): Booking ID from book_flight.
    
    Returns:
        booking_id (str): Booking ID.
        invoice_number (str): Unique invoice number.
        travel_date (str): Travel date.
        departure_airport (str): Departure airport code.
        arrival_airport (str): Arrival airport code.
        travel_class (str): Travel class.
        cost (float): Total booking cost.
        transaction_id (str): Payment transaction ID.
        booking_date (str): Booking creation date.
        payment_status (str): Payment status.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        if not booking_id or not isinstance(booking_id, str):
            raise ValueError("Booking ID must be a non-empty string")
        return api.get_booking_invoice(access_token, booking_id)
    except Exception as e:
        raise e

@mcp.tool()
def cancel_booking(access_token: str, booking_id: str) -> dict:
    """Cancel existing flight booking.
    
    Args:
        access_token (str): Valid access token from authenticate.
        booking_id (str): Booking ID to cancel.
    
    Returns:
        cancellation_status (bool): Whether cancellation was successful.
        refund_amount (float): Amount refunded in USD.
        refund_transaction_id (str): Refund transaction ID.
        cancellation_date (str): Date of cancellation.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        if not booking_id or not isinstance(booking_id, str):
            raise ValueError("Booking ID must be a non-empty string")
        return api.cancel_booking(access_token, booking_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_bookings(access_token: str, start_date: Optional[str] = None, end_date: Optional[str] = None, status: Optional[str] = None) -> dict:
    """List all bookings for authenticated user with optional filters.
    
    Args:
        access_token (str): Valid access token from authenticate.
        start_date (str): [Optional] Filter bookings from this date (YYYY-MM-DD).
        end_date (str): [Optional] Filter bookings up to this date (YYYY-MM-DD).
        status (str): [Optional] Filter by booking status (confirmed, cancelled, pending).
    
    Returns:
        bookings (list): List of bookings matching filter criteria.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        return api.list_bookings(access_token, start_date, end_date, status)
    except Exception as e:
        raise e

@mcp.tool()
def get_insurance_quote(access_token: str, booking_id: str, insurance_type: str) -> dict:
    """Get travel insurance quote for booking.
    
    Args:
        access_token (str): Valid access token from authenticate.
        booking_id (str): Confirmed booking ID.
        insurance_type (str): Type of insurance (basic, premium, comprehensive).
    
    Returns:
        insurance_type (str): Type of insurance quoted.
        insurance_cost (float): Estimated insurance cost in USD.
        coverage_details (dict): Coverage details and benefits.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        if not booking_id or not isinstance(booking_id, str):
            raise ValueError("Booking ID must be a non-empty string")
        if not insurance_type or not isinstance(insurance_type, str):
            raise ValueError("Insurance type must be a non-empty string")
        return api.get_insurance_quote(access_token, booking_id, insurance_type)
    except Exception as e:
        raise e

@mcp.tool()
def purchase_insurance(access_token: str, booking_id: str, insurance_type: str, card_id: str) -> dict:
    """Purchase travel insurance for booking.
    
    Args:
        access_token (str): Valid access token from authenticate.
        booking_id (str): Confirmed booking ID.
        insurance_type (str): Type of insurance to purchase.
        card_id (str): Credit card ID for payment.
    
    Returns:
        insurance_id (str): Unique insurance policy identifier.
        insurance_status (bool): Whether purchase was successful.
        insurance_cost (float): Amount charged for insurance.
        coverage_details (dict): Policy coverage details.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        required_fields = [booking_id, insurance_type, card_id]
        if not all(required_fields):
            raise ValueError("All required insurance fields must be provided")
        return api.purchase_insurance(access_token, booking_id, insurance_type, card_id)
    except Exception as e:
        raise e

@mcp.tool()
def set_budget_limit(access_token: str, budget_limit: float) -> dict:
    """Set budget limit for travel expenses.
    
    Args:
        access_token (str): Valid access token from authenticate.
        budget_limit (float): Budget limit in USD (must be positive).
    
    Returns:
        budget_limit (float): Budget limit that was set.
        currency (str): Currency code (typically 'USD').
        status (str): Success status of setting budget limit.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        if not isinstance(budget_limit, (int, float)) or budget_limit <= 0:
            raise ValueError("Budget limit must be a positive number")
        return api.set_budget_limit(access_token, budget_limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_budget_info(access_token: str) -> dict:
    """Get current budget limit and spending information.
    
    Args:
        access_token (str): Valid access token from authenticate.
    
    Returns:
        budget_limit (float): [Optional] Current budget limit if set.
        total_spent (float): Total amount spent on bookings.
        remaining_budget (float): [Optional] Remaining budget if limit set.
        currency (str): Currency code (typically 'USD').
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        return api.get_budget_info(access_token)
    except Exception as e:
        raise e

@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert currency using current exchange rates.
    
    Args:
        amount (float): Amount to convert (must be positive).
        from_currency (str): Source currency code.
        to_currency (str): Target currency code.
    
    Returns:
        converted_amount (float): Converted value in target currency.
        from_currency (str): Source currency code.
        to_currency (str): Target currency code.
        exchange_rate (float): Exchange rate used.
        conversion_date (str): Date of exchange rate.
    """
    try:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount must be a positive number")
        if not from_currency or not to_currency:
            raise ValueError("Currency codes must be non-empty strings")
        return api.convert_currency(amount, from_currency, to_currency)
    except Exception as e:
        raise e

@mcp.tool()
def contact_support(access_token: str, message: str, booking_id: Optional[str] = None, subject: Optional[str] = None) -> dict:
    """Contact customer support for assistance.
    
    Args:
        access_token (str): Valid access token from authenticate.
        message (str): Message describing the issue or question.
        booking_id (str): [Optional] Booking ID if related to specific booking.
        subject (str): [Optional] Subject line for the inquiry.
    
    Returns:
        support_ticket_id (str): Unique ticket identifier.
        status (str): Confirmation that ticket was created.
        estimated_response_time (str): Expected response timeframe.
        message (str): Confirmation message.
    """
    try:
        if not access_token or not isinstance(access_token, str):
            raise ValueError("Access token must be a non-empty string")
        if not message or not isinstance(message, str):
            raise ValueError("Message must be a non-empty string")
        return api.contact_support(access_token, message, booking_id, subject)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()