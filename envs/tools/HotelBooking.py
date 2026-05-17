from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Destination(BaseModel):
    """Represents a travel destination."""
    destination_id: str = Field(..., description="Unique identifier of the destination")
    city_name: str = Field(..., description="Name of the city")
    country: str = Field(..., description="Country where the city is located")
    location: Dict[str, Any] = Field(default={}, description="Additional location information")

class Hotel(BaseModel):
    """Represents a hotel listing."""
    hotel_id: str = Field(..., description="Unique identifier of the hotel")
    hotel_name: str = Field(..., description="Name of the hotel")
    star_rating: int = Field(..., ge=1, le=5, description="Star rating of the hotel (1-5)")
    checkin_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Check-in date in ISO 8601 format")
    checkout_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Check-out date in ISO 8601 format")
    price_per_night: float = Field(..., ge=0, description="Price per night in hotel's local currency")
    total_price: float = Field(..., ge=0, description="Total price for entire stay")

class RoomType(BaseModel):
    """Represents a hotel room type."""
    room_type_id: str = Field(..., description="Unique identifier of the room type")
    room_name: str = Field(..., description="Name of the room type")
    price: float = Field(..., ge=0, description="Price per night for this room type")

class GuestInfo(BaseModel):
    """Represents guest information for booking."""
    name: str = Field(..., description="Full name of the guest")
    phone: str = Field(..., description="Contact phone number")
    id_number: str = Field(..., description="Government-issued ID number")

class Booking(BaseModel):
    """Represents a hotel booking."""
    booking_id: str = Field(..., description="Unique identifier of the booking")
    hotel_id: str = Field(..., description="Hotel ID for the booking")
    hotel_name: str = Field(..., description="Name of the booked hotel")
    checkin_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Check-in date")
    checkout_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Check-out date")
    total_price: float = Field(..., ge=0, description="Total price paid")
    booking_status: str = Field(default="confirmed", description="Current status of the booking")

class HotelDetails(BaseModel):
    """Represents detailed hotel information."""
    hotel_name: str = Field(..., description="Name of the hotel")
    address: str = Field(..., description="Full street address")
    description: str = Field(..., description="Descriptive overview of the hotel")
    room_types: List[RoomType] = Field(default=[], description="List of available room types")

class HotelBookingScenario(BaseModel):
    """Main scenario model for hotel booking system."""
    destinations: Dict[str, Destination] = Field(default={}, description="Available destinations")
    hotels: Dict[str, Hotel] = Field(default={}, description="Available hotels")
    hotel_details_map: Dict[str, HotelDetails] = Field(default={}, description="Detailed hotel information")
    bookings: Dict[str, Booking] = Field(default={}, description="Active bookings")
    booking_counter: int = Field(default=1000, description="Counter for generating booking IDs")

Scenario_Schema = [Destination, Hotel, RoomType, GuestInfo, Booking, HotelDetails, HotelBookingScenario]

# Section 2: Class
class HotelBookingAPI:
    def __init__(self):
        """Initialize hotel booking API with empty state."""
        self.destinations: Dict[str, Destination] = {}
        self.hotels: Dict[str, Hotel] = {}
        self.hotel_details_map: Dict[str, HotelDetails] = {}
        self.bookings: Dict[str, Booking] = {}
        self.booking_counter: int = 1000

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = HotelBookingScenario(**scenario)
        self.destinations = model.destinations
        self.hotels = model.hotels
        self.hotel_details_map = model.hotel_details_map
        self.bookings = model.bookings
        self.booking_counter = model.booking_counter

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "destinations": {k: v.model_dump() for k, v in self.destinations.items()},
            "hotels": {k: v.model_dump() for k, v in self.hotels.items()},
            "hotel_details_map": {k: v.model_dump() for k, v in self.hotel_details_map.items()},
            "bookings": {k: v.model_dump() for k, v in self.bookings.items()},
            "booking_counter": self.booking_counter
        }

    def search_destinations(self, city: str) -> dict:
        """Search for destinations by city name."""
        matching_destinations = []
        for dest in self.destinations.values():
            if city.lower() in dest.city_name.lower():
                matching_destinations.append(dest.model_dump())
        return {"destinations": matching_destinations}

    def get_hotels(self, destination_id: str, checkin_date: str, checkout_date: str, adults: int = 2, kids: int = 0, limit: int = 20) -> dict:
        """Retrieve available hotels for specified dates."""
        available_hotels = []
        count = 0
        for hotel in self.hotels.values():
            if count >= limit:
                break
            if hotel.checkin_date == checkin_date and hotel.checkout_date == checkout_date:
                available_hotels.append(hotel.model_dump())
                count += 1
        return {"hotels": available_hotels}

    def get_hotel_details(self, hotel_id: str) -> dict:
        """Retrieve detailed information about a specific hotel."""
        if hotel_id in self.hotel_details_map:
            return {"hotel_details": self.hotel_details_map[hotel_id].model_dump()}
        return {"hotel_details": {}}

    def book_hotel(self, hotel_id: str, checkin_date: str, checkout_date: str, room_type_id: str, adults: int, guest_info: List[dict]) -> dict:
        """Create a hotel reservation."""
        if hotel_id not in self.hotels:
            return {"booking_confirmation": {}}
        
        hotel = self.hotels[hotel_id]
        booking_id = f"BK{self.booking_counter}"
        self.booking_counter += 1
        
        booking = Booking(
            booking_id=booking_id,
            hotel_id=hotel_id,
            hotel_name=hotel.hotel_name,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            total_price=hotel.total_price
        )
        
        self.bookings[booking_id] = booking
        
        return {
            "booking_confirmation": {
                "booking_id": booking_id,
                "hotel_name": hotel.hotel_name,
                "checkin_date": checkin_date,
                "checkout_date": checkout_date,
                "total_price": hotel.total_price,
                "booking_status": "confirmed"
            }
        }

    def cancel_booking(self, booking_id: str) -> None:
        """Cancel an existing hotel booking."""
        if booking_id in self.bookings:
            del self.bookings[booking_id]

# Section 3: MCP Tools
mcp = FastMCP(name="HotelBooking")
api = HotelBookingAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the hotel booking API.
    
    Args:
        scenario (dict): Scenario dictionary matching HotelBookingScenario schema.
    
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
    Save current hotel booking state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_destinations(city: str) -> dict:
    """
    Search for travel destinations by city name.
    
    Args:
        city (str): The city name to search for.
    
    Returns:
        destinations (list): List of matching destinations with ID, city name, country, and location info.
    """
    try:
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        return api.search_destinations(city)
    except Exception as e:
        raise e

@mcp.tool()
def get_hotels(destination_id: str, checkin_date: str, checkout_date: str, adults: int = 2, kids: int = 0, limit: int = 20) -> dict:
    """
    Retrieve available hotels at a destination for specific dates.
    
    Args:
        destination_id (str): Destination ID from search_destinations.
        checkin_date (str): Check-in date in ISO 8601 format (YYYY-MM-DD).
        checkout_date (str): Check-out date in ISO 8601 format (YYYY-MM-DD).
        adults (int): [Optional] Number of adults, defaults to 2.
        kids (int): [Optional] Number of kids, defaults to 0.
        limit (int): [Optional] Maximum hotels to return, defaults to 20.
    
    Returns:
        hotels (list): List of available hotels with ID, name, rating, dates, and pricing.
    """
    try:
        if not destination_id or not isinstance(destination_id, str):
            raise ValueError("Destination ID must be a non-empty string")
        if not checkin_date or not isinstance(checkin_date, str):
            raise ValueError("Check-in date must be a non-empty string")
        if not checkout_date or not isinstance(checkout_date, str):
            raise ValueError("Check-out date must be a non-empty string")
        if not isinstance(adults, int) or adults <= 0:
            raise ValueError("Adults must be a positive integer")
        if not isinstance(kids, int) or kids < 0:
            raise ValueError("Kids must be a non-negative integer")
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer")
        return api.get_hotels(destination_id, checkin_date, checkout_date, adults, kids, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_hotel_details(hotel_id: str) -> dict:
    """
    Retrieve comprehensive information about a specific hotel.
    
    Args:
        hotel_id (str): Hotel ID from get_hotels.
    
    Returns:
        hotel_details (dict): Detailed hotel info including name, address, description, and room types.
    """
    try:
        if not hotel_id or not isinstance(hotel_id, str):
            raise ValueError("Hotel ID must be a non-empty string")
        return api.get_hotel_details(hotel_id)
    except Exception as e:
        raise e

@mcp.tool()
def book_hotel(hotel_id: str, checkin_date: str, checkout_date: str, room_type_id: str, adults: int, guest_info: List[dict]) -> dict:
    """
    Create a hotel room reservation for specified guests and dates.
    
    Args:
        hotel_id (str): Hotel ID from get_hotels.
        checkin_date (str): Check-in date in ISO 8601 format.
        checkout_date (str): Check-out date in ISO 8601 format.
        room_type_id (str): Room type ID from get_hotel_details.
        adults (int): Number of adults staying.
        guest_info (list): List of guest info dicts with name, phone, and id_number.
    
    Returns:
        booking_confirmation (dict): Confirmed booking details with ID, hotel name, dates, price, and status.
    """
    try:
        if not hotel_id or not isinstance(hotel_id, str):
            raise ValueError("Hotel ID must be a non-empty string")
        if not checkin_date or not isinstance(checkin_date, str):
            raise ValueError("Check-in date must be a non-empty string")
        if not checkout_date or not isinstance(checkout_date, str):
            raise ValueError("Check-out date must be a non-empty string")
        if not room_type_id or not isinstance(room_type_id, str):
            raise ValueError("Room type ID must be a non-empty string")
        if not isinstance(adults, int) or adults <= 0:
            raise ValueError("Adults must be a positive integer")
        if not guest_info or not isinstance(guest_info, list) or len(guest_info) == 0:
            raise ValueError("Guest info must be a non-empty list")
        return api.book_hotel(hotel_id, checkin_date, checkout_date, room_type_id, adults, guest_info)
    except Exception as e:
        raise e

@mcp.tool()
def cancel_booking(booking_id: str) -> dict:
    """
    Cancel an existing hotel booking.
    
    Args:
        booking_id (str): Booking ID from book_hotel.
    
    Returns:
        empty_dict (dict): Empty dictionary on success.
    """
    try:
        if not booking_id or not isinstance(booking_id, str):
            raise ValueError("Booking ID must be a non-empty string")
        api.cancel_booking(booking_id)
        return {}
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()