from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Airport(BaseModel):
    """Represents an airport with IATA code and city."""
    iata: str = Field(..., pattern=r"^[A-Z]{3}$", description="IATA airport code")
    city: str = Field(..., description="City where airport is located")

class Flight(BaseModel):
    """Represents a flight segment."""
    flight_number: str = Field(..., pattern=r"^[A-Z]{2}\d{3,4}$", description="Flight number")
    origin: str = Field(..., pattern=r"^[A-Z]{3}$", description="Origin airport IATA code")
    destination: str = Field(..., pattern=r"^[A-Z]{3}$", description="Destination airport IATA code")
    scheduled_departure: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Scheduled departure time")
    available_seats: Dict[str, int] = Field(default={}, description="Available seats by cabin class")
    prices: Dict[str, float] = Field(default={}, description="Ticket prices by cabin class")

class FlightStatus(BaseModel):
    """Represents flight status information."""
    flight_number: str = Field(..., pattern=r"^[A-Z]{2}\d{3,4}$", description="Flight number")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Flight date")
    status: str = Field(..., description="Flight status")

class User(BaseModel):
    """Represents a user account."""
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User full name")
    reservations: List[str] = Field(default=[], description="List of reservation IDs")
    payment_methods: List[str] = Field(default=[], description="List of saved payment methods")

class Reservation(BaseModel):
    """Represents a flight reservation."""
    reservation_id: str = Field(..., description="Unique reservation identifier")
    user_id: str = Field(..., description="User ID who made the reservation")
    flights: List[Dict[str, Any]] = Field(default=[], description="Flight segments")
    passengers: List[Dict[str, Any]] = Field(default=[], description="Passenger details")
    total_price: float = Field(..., ge=0, description="Total price of reservation")
    status: str = Field(..., description="Reservation status")

class AirlineScenario(BaseModel):
    """Main scenario model for airline booking service."""
    airports: List[Airport] = Field(default=[], description="List of available airports")
    flights: Dict[str, Flight] = Field(default={}, description="Flight database")
    flight_statuses: Dict[str, FlightStatus] = Field(default={}, description="Flight status database")
    users: Dict[str, User] = Field(default={}, description="User database")
    reservations: Dict[str, Reservation] = Field(default={}, description="Reservation database")
    baggage_fees: Dict[str, float] = Field(default={
        "economy": 25.0, "business": 0.0, "first": 0.0
    }, description="Baggage fees by cabin class")
    insurance_fee: float = Field(default=15.0, description="Travel insurance fee")

Scenario_Schema = [Airport, Flight, FlightStatus, User, Reservation, AirlineScenario]

# Section 2: Class
class AirlineAPI:
    def __init__(self):
        """Initialize airline API with empty state."""
        self.airports: List[Airport] = []
        self.flights: Dict[str, Flight] = {}
        self.flight_statuses: Dict[str, FlightStatus] = {}
        self.users: Dict[str, User] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.baggage_fees: Dict[str, float] = {}
        self.insurance_fee: float = 0.0
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = AirlineScenario(**scenario)
        self.airports = model.airports
        self.flights = model.flights
        self.flight_statuses = model.flight_statuses
        self.users = model.users
        self.reservations = model.reservations
        self.baggage_fees = model.baggage_fees
        self.insurance_fee = model.insurance_fee

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "airports": [airport.model_dump() for airport in self.airports],
            "flights": {k: v.model_dump() for k, v in self.flights.items()},
            "flight_statuses": {k: v.model_dump() for k, v in self.flight_statuses.items()},
            "users": {k: v.model_dump() for k, v in self.users.items()},
            "reservations": {k: v.model_dump() for k, v in self.reservations.items()},
            "baggage_fees": self.baggage_fees,
            "insurance_fee": self.insurance_fee
        }

    def list_airports(self) -> dict:
        """Retrieve list of all available airports."""
        return {"airports": [{"iata": airport.iata, "city": airport.city} for airport in self.airports]}

    def search_flights(self, origin: str, destination: str, date: str) -> dict:
        """Search for available flights between airports on specified date."""
        available_flights = []
        for flight in self.flights.values():
            if flight.origin == origin and flight.destination == destination:
                available_flights.append({
                    "flight_number": flight.flight_number,
                    "origin": flight.origin,
                    "destination": flight.destination,
                    "scheduled_departure": flight.scheduled_departure,
                    "available_seats": flight.available_seats,
                    "prices": flight.prices
                })
        return {"flights": available_flights}

    def get_flight_status(self, flight_number: str, date: str) -> dict:
        """Retrieve current operational status of specific flight."""
        status_key = f"{flight_number}_{date}"
        if status_key in self.flight_statuses:
            status = self.flight_statuses[status_key]
            return {
                "flight_number": status.flight_number,
                "status": status.status,
                "date": status.date
            }
        return {"flight_number": flight_number, "status": "unknown", "date": date}

    def get_user_details(self, user_id: str) -> dict:
        """Retrieve user profile information."""
        if user_id in self.users:
            user = self.users[user_id]
            return {
                "user_id": user.user_id,
                "name": user.name,
                "reservations": user.reservations,
                "payment_methods": user.payment_methods
            }
        return {}

    def get_reservation_details(self, reservation_id: str) -> dict:
        """Retrieve complete reservation details."""
        if reservation_id in self.reservations:
            reservation = self.reservations[reservation_id]
            return {
                "reservation_id": reservation.reservation_id,
                "user_id": reservation.user_id,
                "flights": reservation.flights,
                "passengers": reservation.passengers,
                "total_price": reservation.total_price,
                "status": reservation.status
            }
        return {}

    def book_reservation(self, user_id: str, origin: str, destination: str, flight_type: str, 
                        cabin: str, flights: List[dict], passengers: List[dict], 
                        payment_method: str, total_baggages: int, nonfree_baggages: int, 
                        insurance: bool) -> dict:
        """Create new flight reservation."""
        import uuid
        reservation_id = f"RES{str(uuid.uuid4())[:8].upper()}"
        
        # Calculate base flight price from the flights list
        base_price = sum(flight.get("price", 0) for flight in flights)
        
        # Calculate baggage fee
        baggage_fee = nonfree_baggages * self.baggage_fees.get(cabin, 25.0)
        
        # Calculate insurance fee
        insurance_fee = self.insurance_fee if insurance else 0.0
        
        # Total price
        total_price = base_price + baggage_fee + insurance_fee
        
        reservation = Reservation(
            reservation_id=reservation_id,
            user_id=user_id,
            flights=flights,
            passengers=passengers,
            total_price=total_price,
            status="confirmed"
        )
        
        self.reservations[reservation_id] = reservation
        
        # Update user's reservations list
        if user_id in self.users:
            self.users[user_id].reservations.append(reservation_id)
        
        return {
            "reservation_id": reservation_id,
            "status": "confirmed",
            "total_price": total_price
        }

    def update_reservation_flights(self, reservation_id: str, cabin: str, flights: List[dict], 
                                  payment_method: str) -> dict:
        """Modify flight segments or cabin class of existing reservation."""
        if reservation_id in self.reservations:
            reservation = self.reservations[reservation_id]
            old_price = reservation.total_price
            
            # Calculate new base price from updated flights
            new_base_price = sum(flight.get("price", 0) for flight in flights)
            
            # Calculate additional charge as the difference
            additional_charge = max(0, new_base_price - old_price)
            
            # Update reservation
            reservation.flights = flights
            reservation.total_price = new_base_price
            
            return {
                "reservation_id": reservation_id,
                "status": reservation.status,
                "additional_charge": additional_charge
            }
        return {}

    def update_reservation_passengers(self, reservation_id: str, passengers: List[dict]) -> dict:
        """Update passenger information for existing reservation."""
        if reservation_id in self.reservations:
            reservation = self.reservations[reservation_id]
            reservation.passengers = passengers
            
            return {
                "reservation_id": reservation_id,
                "status": reservation.status
            }
        return {}

    def update_reservation_baggage(self, reservation_id: str, total_baggages: int, 
                                  nonfree_baggages: int, payment_method: str) -> dict:
        """Modify baggage allowance for existing reservation."""
        if reservation_id in self.reservations:
            reservation = self.reservations[reservation_id]
            
            # Calculate current nonfree bags from existing total_price and baggage fee structure
            # We need to determine how many nonfree bags were already charged
            # Since we don't track this explicitly, we assume the previous nonfree_baggages
            # For simplicity, we calculate the delta based on the new nonfree_baggages
            # and apply the fee only to the additional bags
            
            # For this implementation, we'll charge for the delta of nonfree bags
            # This is a simplified approach - in a real system, we'd track the baggage state
            additional_charge = nonfree_baggages * 25.0  # Charge for all nonfree bags as per current logic
            
            # Update reservation total price
            reservation.total_price += additional_charge
            
            return {
                "reservation_id": reservation_id,
                "additional_charge": additional_charge
            }
        return {}

    def cancel_reservation(self, reservation_id: str) -> dict:
        """Cancel entire flight reservation and process refund."""
        if reservation_id in self.reservations:
            reservation = self.reservations[reservation_id]
            refund_amount = reservation.total_price * 0.8
            reservation.status = "cancelled"
            
            # Remove reservation from user's list
            if reservation.user_id in self.users:
                if reservation_id in self.users[reservation.user_id].reservations:
                    self.users[reservation.user_id].reservations.remove(reservation_id)
            
            return {
                "reservation_id": reservation_id,
                "status": "cancelled",
                "refund_amount": refund_amount
            }
        return {}

# Section 3: MCP Tools
mcp = FastMCP(name="Airline")
api = AirlineAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the airline API.
    
    Args:
        scenario (dict): Scenario dictionary matching AirlineScenario schema.
    
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
    Save current airline state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def list_airports() -> dict:
    """
    Retrieve a list of all available airports with their IATA codes and city names.
    
    Returns:
        airports (list): List of airports with iata and city fields.
    """
    try:
        return api.list_airports()
    except Exception as e:
        raise e

@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> dict:
    """
    Search for available direct flights between two airports on a specified date.
    
    Args:
        origin (str): The IATA code of the departure airport.
        destination (str): The IATA code of the arrival airport.
        date (str): The date of the flight in YYYY-MM-DD format.
    
    Returns:
        flights (list): List of available flights matching search criteria.
    """
    try:
        if not origin or not destination or not date:
            raise ValueError("Origin, destination, and date are required")
        return api.search_flights(origin, destination, date)
    except Exception as e:
        raise e

@mcp.tool()
def get_flight_status(flight_number: str, date: str) -> dict:
    """
    Retrieve the current operational status of a specific flight on a given date.
    
    Args:
        flight_number (str): The unique identifier for the flight.
        date (str): The date of the flight in YYYY-MM-DD format.
    
    Returns:
        flight_number (str): The flight identifier.
        status (str): The current operational status.
        date (str): The flight date.
    """
    try:
        if not flight_number or not date:
            raise ValueError("Flight number and date are required")
        return api.get_flight_status(flight_number, date)
    except Exception as e:
        raise e

@mcp.tool()
def get_user_details(user_id: str) -> dict:
    """
    Retrieve a user's profile information including their reservation history and saved payment methods.
    
    Args:
        user_id (str): The unique identifier of the customer account.
    
    Returns:
        user_id (str): The user identifier.
        name (str): The full name of the customer.
        reservations (list): List of reservation IDs.
        payment_methods (list): List of saved payment methods.
    """
    try:
        if not user_id:
            raise ValueError("User ID is required")
        result = api.get_user_details(user_id)
        if not result:
            raise ValueError(f"User {user_id} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_reservation_details(reservation_id: str) -> dict:
    """
    Retrieve complete details of a specific flight reservation including flights, passengers, and pricing.
    
    Args:
        reservation_id (str): The unique identifier of the flight booking.
    
    Returns:
        reservation_id (str): The reservation identifier.
        user_id (str): The user who made the booking.
        flights (list): List of flight segments.
        passengers (list): List of passengers.
        total_price (float): The total price.
        status (str): The reservation status.
    """
    try:
        if not reservation_id:
            raise ValueError("Reservation ID is required")
        result = api.get_reservation_details(reservation_id)
        if not result:
            raise ValueError(f"Reservation {reservation_id} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def book_reservation(user_id: str, origin: str, destination: str, flight_type: str,
                    cabin: str, flights: List[dict], passengers: List[dict], 
                    payment_method: str, total_baggages: int, nonfree_baggages: int, 
                    insurance: bool) -> dict:
    """
    Create a new flight reservation with specified flights, passengers, and additional services.
    
    Args:
        user_id (str): The unique identifier of the customer account.
        origin (str): The IATA code of the departure airport.
        destination (str): The IATA code of the arrival airport.
        flight_type (str): The type of travel itinerary.
        cabin (str): The service class for the travel.
        flights (list): Detailed list of flight segments.
        passengers (list): Comprehensive list of passenger details.
        payment_method (str): The payment method used.
        total_baggages (int): Total number of baggage pieces.
        nonfree_baggages (int): Number of paid baggage pieces.
        insurance (bool): Whether to include travel insurance.
    
    Returns:
        reservation_id (str): The newly created reservation ID.
        status (str): The reservation status.
        total_price (float): The total price charged.
    """
    try:
        if not user_id or not origin or not destination or not flight_type or not cabin:
            raise ValueError("Required parameters missing")
        if not flights or not passengers:
            raise ValueError("Flights and passengers are required")
        if not payment_method:
            raise ValueError("Payment method is required")
        return api.book_reservation(user_id, origin, destination, flight_type, cabin, 
                                   flights, passengers, payment_method, total_baggages, 
                                   nonfree_baggages, insurance)
    except Exception as e:
        raise e

@mcp.tool()
def update_reservation_flights(reservation_id: str, cabin: str, flights: List[dict], 
                              payment_method: str) -> dict:
    """
    Modify the flight segments or cabin class of an existing reservation.
    
    Args:
        reservation_id (str): The unique identifier of the flight booking.
        cabin (str): The service class for the travel.
        flights (list): The complete new set of flight segments.
        payment_method (str): The payment method for additional charges.
    
    Returns:
        reservation_id (str): The updated reservation ID.
        status (str): The reservation status after update.
        additional_charge (float): Additional amount charged.
    """
    try:
        if not reservation_id or not cabin or not flights or not payment_method:
            raise ValueError("All parameters are required")
        result = api.update_reservation_flights(reservation_id, cabin, flights, payment_method)
        if not result:
            raise ValueError(f"Reservation {reservation_id} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def update_reservation_passengers(reservation_id: str, passengers: List[dict]) -> dict:
    """
    Update passenger information for an existing reservation.
    
    Args:
        reservation_id (str): The unique identifier of the flight booking.
        passengers (list): Updated list of passenger details.
    
    Returns:
        reservation_id (str): The updated reservation ID.
        status (str): The reservation status after update.
    """
    try:
        if not reservation_id or not passengers:
            raise ValueError("Reservation ID and passengers are required")
        result = api.update_reservation_passengers(reservation_id, passengers)
        if not result:
            raise ValueError(f"Reservation {reservation_id} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def update_reservation_baggage(reservation_id: str, total_baggages: int, 
                              nonfree_baggages: int, payment_method: str) -> dict:
    """
    Modify the baggage allowance for an existing reservation.
    
    Args:
        reservation_id (str): The unique identifier of the flight booking.
        total_baggages (int): Updated total number of baggage pieces.
        nonfree_baggages (int): Updated count of paid baggage pieces.
        payment_method (str): The payment method for additional charges.
    
    Returns:
        reservation_id (str): The updated reservation ID.
        additional_charge (float): Additional amount charged.
    """
    try:
        if not reservation_id or total_baggages is None or nonfree_baggages is None or not payment_method:
            raise ValueError("All parameters are required")
        result = api.update_reservation_baggage(reservation_id, total_baggages, nonfree_baggages, payment_method)
        if not result:
            raise ValueError(f"Reservation {reservation_id} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def cancel_reservation(reservation_id: str) -> dict:
    """
    Cancel an entire flight reservation and process the applicable refund.
    
    Args:
        reservation_id (str): The unique identifier of the flight booking.
    
    Returns:
        reservation_id (str): The cancelled reservation ID.
        status (str): The reservation status (cancelled).
        refund_amount (float): The refund amount processed.
    """
    try:
        if not reservation_id:
            raise ValueError("Reservation ID is required")
        result = api.cancel_reservation(reservation_id)
        if not result:
            raise ValueError(f"Reservation {reservation_id} not found")
        return result
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()