
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema

class Park(BaseModel):
    """Represents a national park."""
    parkCode: str = Field(..., description="Unique park identifier")
    fullName: str = Field(..., description="Complete official name of the park")
    states: str = Field(default="", description="Comma-separated state codes")
    description: str = Field(default="", description="Short narrative overview")
    activities: List[Any] = Field(default=[], description="List of activities")

class Alert(BaseModel):
    """Represents a park alert."""
    id: str = Field(..., description="Unique alert identifier")
    parkCode: str = Field(..., description="Park identifier")
    title: str = Field(default="", description="Alert headline")
    description: str = Field(default="", description="Alert details")
    category: str = Field(default="", description="Alert category")
    lastIndexedDate: str = Field(default="", description="Last updated timestamp")

class Campground(BaseModel):
    """Represents a campground."""
    id: str = Field(..., description="Unique campground identifier")
    name: str = Field(..., description="Official campground name")
    parkCode: str = Field(..., description="Park identifier")
    description: str = Field(default="", description="Campground overview")
    amenities: Dict[str, Any] = Field(default={}, description="Available amenities")
    fees: List[Any] = Field(default=[], description="Camping fees")
    reservationUrl: str = Field(default="", description="Reservation URL")

class VisitorCenter(BaseModel):
    """Represents a visitor center."""
    id: str = Field(..., description="Unique visitor center identifier")
    name: str = Field(..., description="Official visitor center name")
    parkCode: str = Field(..., description="Park identifier")
    description: str = Field(default="", description="Services and exhibits overview")
    operatingHours: List[Any] = Field(default=[], description="Operating hours")
    contacts: Dict[str, Any] = Field(default={}, description="Contact information")
    addresses: List[Any] = Field(default=[], description="Physical addresses")

class ParkDetails(BaseModel):
    """Represents detailed park information."""
    parkCode: str = Field(..., description="Unique park identifier")
    fullName: str = Field(..., description="Complete official name")
    description: str = Field(default="", description="Detailed overview")
    directionsInfo: str = Field(default="", description="Driving directions")
    operatingHours: List[Any] = Field(default=[], description="Operating hours")
    entranceFees: List[Any] = Field(default=[], description="Entrance fees")
    contacts: Dict[str, Any] = Field(default={}, description="Contact information")
    addresses: List[Any] = Field(default=[], description="Physical addresses")

class NationalParksScenario(BaseModel):
    """Main scenario model for National Parks data."""
    parks: Dict[str, Any] = Field(default={}, description="Park data keyed by parkCode")
    alerts: List[Any] = Field(default=[], description="Park alerts")
    campgrounds: List[Any] = Field(default=[], description="Campground listings")
    visitor_centers: List[Any] = Field(default=[], description="Visitor center listings")
    activitiesMap: Dict[str, Any] = Field(default={
        "hiking": {"id": "BFF8C027-7C8F-400B-B55D-5414C3AA8BB8", "name": "Hiking"},
        "camping": {"id": "A59947B7-3376-49B4-AD02-C0423E08C5F7", "name": "Camping"},
        "fishing": {"id": "AE42B46C-E4B7-4889-A122-08FE180371AE", "name": "Fishing"},
        "swimming": {"id": "587BB2D3-EC35-41B2-B3F7-A39E2B088AEE", "name": "Swimming"},
        "birdwatching": {"id": "0B685688-3405-4E2A-ABBA-E3069492EC50", "name": "Birdwatching"},
        "climbing": {"id": "7CE6E935-F839-4FEC-A63E-052B1DEF39D2", "name": "Rock Climbing"},
        "cycling": {"id": "4D224BCA-C127-408B-AC75-A51563C42411", "name": "Biking"},
        "kayaking": {"id": "4A58AF13-E8FB-4530-B41A-97DF0B0C77B7", "name": "Kayaking"},
        "photography": {"id": "C8F98B28-3C10-41AE-AA99-092B3B398C43", "name": "Photography"},
        "stargazing": {"id": "B33DC9B6-0B7D-4322-BAD7-A13A34C584A3", "name": "Stargazing"},
        "snowshoeing": {"id": "F9B1D433-6B86-4804-AED7-B50A519A3B7C", "name": "Snowshoeing"},
        "horseback": {"id": "1DFACD97-1B9C-4F5A-80F2-05593604799E", "name": "Horseback Riding"},
        "rafting": {"id": "F353A9ED-4A08-456E-8DEC-E61974D0FEB6", "name": "Whitewater Rafting"},
        "snorkeling": {"id": "5FF5B286-E9C3-430E-B612-3380D8138600", "name": "Snorkeling"},
        "skiing": {"id": "D37A0003-8317-4F04-8FB0-4CF0A272E195", "name": "Downhill Skiing"},
    }, description="Activities reference map")
    stateParksMap: Dict[str, Any] = Field(default={
        "CA": ["yose", "sequ", "jotr", "redw", "pinn"],
        "UT": ["zion", "brca", "cany", "arch", "care"],
        "AZ": ["grca", "pefo", "sacu", "tuzi", "chir"],
        "CO": ["romo", "blca", "grsa", "meve", "cure"],
        "WY": ["yell", "grte", "fobu", "thro", "bica"],
        "MT": ["glac", "biho", "litt", "grko", "noca"],
        "WA": ["olym", "noca", "mora", "laro", "whis"],
        "OR": ["crla", "john", "nebe", "lewi", "timu"],
        "FL": ["ever", "bisc", "drto", "cana", "timu"],
        "TX": ["bibe", "gumo", "saan", "paal", "lyjo"],
        "AK": ["dena", "katm", "glba", "kefj", "lacl"],
        "HI": ["havo", "hale", "kala", "puhe", "puko"],
        "VA": ["shen", "colo", "apco", "mana", "rich"],
        "NC": ["grsm", "blue", "caha", "fora", "carl"],
        "SD": ["badl", "wica", "moru", "jeca", "mnrr"],
    }, description="State to park codes mapping")

Scenario_Schema = [Park, Alert, Campground, VisitorCenter, ParkDetails, NationalParksScenario]


# Section 2: Class

class NationalParksAPI:
    def __init__(self):
        """Initialize National Parks API with empty state."""
        self.parks: Dict[str, Any] = {}
        self.alerts: List[Any] = []
        self.campgrounds: List[Any] = []
        self.visitor_centers: List[Any] = []
        self.activitiesMap: Dict[str, Any] = {}
        self.stateParksMap: Dict[str, Any] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = NationalParksScenario(**scenario)
        self.parks = model.parks
        self.alerts = model.alerts
        self.campgrounds = model.campgrounds
        self.visitor_centers = model.visitor_centers
        self.activitiesMap = model.activitiesMap
        self.stateParksMap = model.stateParksMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "parks": self.parks,
            "alerts": self.alerts,
            "campgrounds": self.campgrounds,
            "visitor_centers": self.visitor_centers,
            "activitiesMap": self.activitiesMap,
            "stateParksMap": self.stateParksMap,
        }

    def findParks(self, stateCode: Optional[str], q: Optional[str], limit: int, start: int, activities: Optional[str]) -> dict:
        """Search for parks by state code, text query, or activities."""
        results = list(self.parks.values())

        if stateCode:
            codes = [s.strip().upper() for s in stateCode.split(",")]
            results = [p for p in results if any(c in p.get("states", "").upper().split(",") for c in codes)]

        if q:
            q_lower = q.lower()
            results = [p for p in results if q_lower in p.get("fullName", "").lower() or q_lower in p.get("description", "").lower()]

        if activities:
            act_names = [a.strip().lower() for a in activities.split(",")]
            def park_has_activity(park):
                park_acts = [a.get("name", "").lower() for a in park.get("activities", [])]
                return any(a in park_acts for a in act_names)
            results = [p for p in results if park_has_activity(p)]

        total = len(results)
        paginated = results[start:start + limit]
        return {"total": total, "limit": limit, "start": start, "data": paginated}

    def getParkDetails(self, parkCode: str) -> dict:
        """Retrieve comprehensive details for a specific park."""
        return self.parks[parkCode]

    def getAlerts(self, parkCode: Optional[str], limit: int, start: int, q: Optional[str]) -> dict:
        """Fetch current alerts for parks."""
        results = list(self.alerts)

        if parkCode:
            codes = [c.strip().lower() for c in parkCode.split(",")]
            results = [a for a in results if a.get("parkCode", "").lower() in codes]

        if q:
            q_lower = q.lower()
            results = [a for a in results if q_lower in a.get("title", "").lower() or q_lower in a.get("description", "").lower()]

        total = len(results)
        return {"total": total, "data": results[start:start + limit]}

    def getCampgrounds(self, parkCode: Optional[str], limit: int, start: int, q: Optional[str]) -> dict:
        """Retrieve campground listings for parks."""
        results = list(self.campgrounds)

        if parkCode:
            codes = [c.strip().lower() for c in parkCode.split(",")]
            results = [c for c in results if c.get("parkCode", "").lower() in codes]

        if q:
            q_lower = q.lower()
            results = [c for c in results if q_lower in c.get("name", "").lower() or q_lower in c.get("description", "").lower()]

        total = len(results)
        return {"total": total, "data": results[start:start + limit]}

    def getVisitorCenters(self, parkCode: Optional[str], limit: int, start: int, q: Optional[str]) -> dict:
        """Obtain visitor center information for parks."""
        results = list(self.visitor_centers)

        if parkCode:
            codes = [c.strip().lower() for c in parkCode.split(",")]
            results = [v for v in results if v.get("parkCode", "").lower() in codes]

        if q:
            q_lower = q.lower()
            results = [v for v in results if q_lower in v.get("name", "").lower() or q_lower in v.get("description", "").lower()]

        total = len(results)
        return {"total": total, "data": results[start:start + limit]}


# Section 3: MCP Tools

mcp = FastMCP(name="NationalParks")
api = NationalParksAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the National Parks API.

    Args:
        scenario (dict): Scenario dictionary matching NationalParksScenario schema.

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
    Save current National Parks state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def findParks(
    stateCode: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 10,
    start: int = 0,
    activities: Optional[str] = None,
) -> dict:
    """
    Search for parks by state code, text query, or supported activities.

    Args:
        stateCode (str): [Optional] Comma-separated two-letter state codes (e.g., 'CA,UT').
        q (str): [Optional] Search term matching park names or descriptions.
        limit (int): [Optional] Maximum number of parks to return (default 10).
        start (int): [Optional] Result offset for pagination (default 0).
        activities (str): [Optional] Comma-separated activity names or IDs.

    Returns:
        total (int): Total number of parks matching the query.
        limit (int): Limit used for this response.
        start (int): Start offset used for this response.
        data (list): List of parks matching the search criteria.
    """
    try:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if start < 0:
            raise ValueError("start must be non-negative")
        return api.findParks(stateCode, q, limit, start, activities)
    except Exception as e:
        raise e

@mcp.tool()
def getParkDetails(parkCode: str) -> dict:
    """
    Retrieve comprehensive details for a specific park.

    Args:
        parkCode (str): The unique park identifier (e.g., 'yose', 'grca').

    Returns:
        parkCode (str): Unique park identifier.
        fullName (str): Complete official name of the park.
        description (str): Detailed narrative overview.
        directionsInfo (str): Human-readable driving directions.
        operatingHours (list): Seasonal or daily operating hours.
        entranceFees (list): Entrance fee structures.
        contacts (dict): Contact information.
        addresses (list): Physical and mailing addresses.
    """
    try:
        if not parkCode or not isinstance(parkCode, str):
            raise ValueError("parkCode must be a non-empty string")
        if parkCode not in api.parks:
            raise ValueError(f"Park '{parkCode}' not found")
        return api.getParkDetails(parkCode)
    except Exception as e:
        raise e

@mcp.tool()
def getAlerts(
    parkCode: Optional[str] = None,
    limit: int = 10,
    start: int = 0,
    q: Optional[str] = None,
) -> dict:
    """
    Fetch current alerts such as closures, hazards, or notices for parks.

    Args:
        parkCode (str): [Optional] Comma-separated park codes to filter alerts.
        limit (int): [Optional] Maximum number of alerts to return (default 10).
        start (int): [Optional] Result offset for pagination (default 0).
        q (str): [Optional] Search term matching alert titles or descriptions.

    Returns:
        total (int): Total number of alerts matching the query.
        data (list): List of alerts matching the query.
    """
    try:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if start < 0:
            raise ValueError("start must be non-negative")
        return api.getAlerts(parkCode, limit, start, q)
    except Exception as e:
        raise e

@mcp.tool()
def getCampgrounds(
    parkCode: Optional[str] = None,
    limit: int = 10,
    start: int = 0,
    q: Optional[str] = None,
) -> dict:
    """
    Retrieve campground listings and details for parks.

    Args:
        parkCode (str): [Optional] Comma-separated park codes to filter campgrounds.
        limit (int): [Optional] Maximum number of campgrounds to return (default 10).
        start (int): [Optional] Result offset for pagination (default 0).
        q (str): [Optional] Search term matching campground names or descriptions.

    Returns:
        total (int): Total number of campgrounds matching the query.
        data (list): List of campgrounds matching the query.
    """
    try:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if start < 0:
            raise ValueError("start must be non-negative")
        return api.getCampgrounds(parkCode, limit, start, q)
    except Exception as e:
        raise e

@mcp.tool()
def getVisitorCenters(
    parkCode: Optional[str] = None,
    limit: int = 10,
    start: int = 0,
    q: Optional[str] = None,
) -> dict:
    """
    Obtain visitor center information including hours and contact details.

    Args:
        parkCode (str): [Optional] Comma-separated park codes to filter visitor centers.
        limit (int): [Optional] Maximum number of visitor centers to return (default 10).
        start (int): [Optional] Result offset for pagination (default 0).
        q (str): [Optional] Search term matching visitor center names or descriptions.

    Returns:
        total (int): Total number of visitor centers matching the query.
        data (list): List of visitor centers matching the query.
    """
    try:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if start < 0:
            raise ValueError("start must be non-negative")
        return api.getVisitorCenters(parkCode, limit, start, q)
    except Exception as e:
        raise e


# Section 4: Entry Point

if __name__ == "__main__":
    mcp.run()
