from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Station(BaseModel):
    """Represents a railway station."""
    station_code: str = Field(..., description="The unique station code used in the China Railway system")
    station_name: str = Field(..., description="The official Chinese name of the railway station")
    address: str = Field(default="", description="The geographical location or physical address of the railway station")
    phone: str = Field(default="", description="The contact telephone number for the railway station")

class SeatAvailability(BaseModel):
    """Represents seat availability for different classes."""
    business_class: int = Field(..., ge=0, description="Number of available business class seats")
    first_class: int = Field(..., ge=0, description="Number of available first class seats")
    second_class: int = Field(..., ge=0, description="Number of available second class seats")

class Train(BaseModel):
    """Represents a train service."""
    train_no: str = Field(..., description="The unique train number identifier")
    departure_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Scheduled departure time in HH:MM format")
    arrival_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Scheduled arrival time in HH:MM format")
    duration: str = Field(..., description="Total travel time for this train journey")
    seat_availability: SeatAvailability = Field(..., description="Current ticket availability for different seat classes")

class RouteStation(BaseModel):
    """Represents a station along a train route."""
    station_name: str = Field(..., description="The official Chinese name of the railway station")
    arrival_time: str = Field(default="", description="Scheduled arrival time in HH:MM format")
    departure_time: str = Field(default="", description="Scheduled departure time in HH:MM format")
    stop_duration: str = Field(default="", description="Length of time the train stops at this station")

class ChinaRailwayScenario(BaseModel):
    """Main scenario model for China Railway system."""
    stations: Dict[str, Station] = Field(default={}, description="All railway stations indexed by station code")
    city_stations: Dict[str, List[str]] = Field(default={}, description="Mapping of city names to station codes")
    trains: Dict[str, List[Train]] = Field(default={}, description="Available trains indexed by date_from_to key")
    train_routes: Dict[str, List[RouteStation]] = Field(default={}, description="Train routes indexed by date_from_to_trainno key")
    station_details_map: Dict[str, Dict[str, Any]] = Field(default={
        "BJP": {"station_name": "北京", "address": "北京市西城区莲花池东路", "phone": "010-12306"},
        "BXP": {"station_name": "北京西", "address": "北京市丰台区莲花池东路", "phone": "010-51826273"},
        "VNP": {"station_name": "北京南", "address": "北京市丰台区永外大街", "phone": "010-51867182"},
        "AOH": {"station_name": "上海", "address": "上海市静安区秣陵路", "phone": "021-12306"},
        "SHH": {"station_name": "上海虹桥", "address": "上海市闵行区申虹路", "phone": "021-12306"},
        "GZQ": {"station_name": "广州", "address": "广州市越秀区环市西路", "phone": "020-12306"},
        "IZQ": {"station_name": "广州南", "address": "广州市番禺区石壁街道", "phone": "020-39267222"},
        "SZQ": {"station_name": "深圳", "address": "深圳市罗湖区和平路", "phone": "0755-12306"},
        "IOQ": {"station_name": "深圳北", "address": "深圳市龙华区民治街道", "phone": "0755-12306"},
        "NJH": {"station_name": "南京", "address": "南京市玄武区龙蟠路", "phone": "025-12306"},
        "NKH": {"station_name": "南京南", "address": "南京市雨花台区玉兰路", "phone": "025-12306"},
        "HZH": {"station_name": "杭州", "address": "杭州市上城区环城东路", "phone": "0571-12306"},
        "HGH": {"station_name": "杭州东", "address": "杭州市江干区天城路", "phone": "0571-12306"},
        "TJP": {"station_name": "天津", "address": "天津市河北区新纬路", "phone": "022-12306"},
        "TIP": {"station_name": "天津西", "address": "天津市红桥区西青道", "phone": "022-12306"},
        "CQW": {"station_name": "重庆", "address": "重庆市渝中区菜园坝", "phone": "023-12306"},
        "CXW": {"station_name": "重庆北", "address": "重庆市渝北区龙头寺", "phone": "023-12306"},
        "CDW": {"station_name": "成都", "address": "成都市金牛区荷花池", "phone": "028-12306"},
        "ICW": {"station_name": "成都东", "address": "成都市成华区保和街道", "phone": "028-12306"},
        "WHN": {"station_name": "武汉", "address": "武汉市武昌区中山路", "phone": "027-12306"}
    }, description="Station details lookup map")

Scenario_Schema = [Station, SeatAvailability, Train, RouteStation, ChinaRailwayScenario]

# Section 2: Class
class ChinaRailwayAPI:
    def __init__(self):
        """Initialize China Railway API with empty state."""
        self.stations: Dict[str, Station] = {}
        self.city_stations: Dict[str, List[str]] = {}
        self.trains: Dict[str, List[Train]] = {}
        self.train_routes: Dict[str, List[RouteStation]] = {}
        self.station_details_map: Dict[str, Dict[str, Any]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = ChinaRailwayScenario(**scenario)
        self.stations = model.stations
        self.city_stations = model.city_stations
        self.trains = model.trains
        self.train_routes = model.train_routes
        self.station_details_map = model.station_details_map

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "stations": {code: station.model_dump() for code, station in self.stations.items()},
            "city_stations": self.city_stations,
            "trains": {key: [train.model_dump() for train in trains] for key, trains in self.trains.items()},
            "train_routes": {key: [station.model_dump() for station in stations] for key, stations in self.train_routes.items()},
            "station_details_map": self.station_details_map
        }

    def get_stations_code_in_city(self, city: str) -> dict:
        """Retrieve all railway stations within a specified city."""
        station_codes = self.city_stations.get(city, [])
        stations = []
        for code in station_codes:
            if code in self.stations:
                station = self.stations[code]
                stations.append({
                    "station_code": station.station_code,
                    "station_name": station.station_name
                })
        return {"stations": stations}

    def get_station_code_by_name(self, station_name: str) -> dict:
        """Look up the unique station code for a railway station by its name."""
        for code, station in self.stations.items():
            if station.station_name == station_name:
                return {"station_code": station.station_code}
        return {"station_code": ""}

    def get_station_by_code(self, station_code: str) -> dict:
        """Retrieve detailed information about a railway station using its code."""
        if station_code in self.station_details_map:
            details = self.station_details_map[station_code]
            return {
                "station_name": details.get("station_name", ""),
                "address": details.get("address", ""),
                "phone": details.get("phone", "")
            }
        
        if station_code in self.stations:
            station = self.stations[station_code]
            return {
                "station_name": station.station_name,
                "address": station.address,
                "phone": station.phone
            }
        
        return {"station_name": "", "address": "", "phone": ""}

    def get_tickets(self, date: str, from_station_code: str, to_station_code: str) -> dict:
        """Query available train tickets between two stations on a specific date."""
        key = f"{date}_{from_station_code}_{to_station_code}"
        trains = self.trains.get(key, [])
        trains_list = []
        for train in trains:
            trains_list.append({
                "train_no": train.train_no,
                "departure_time": train.departure_time,
                "arrival_time": train.arrival_time,
                "duration": train.duration,
                "seat_availability": {
                    "business_class": train.seat_availability.business_class,
                    "first_class": train.seat_availability.first_class,
                    "second_class": train.seat_availability.second_class
                }
            })
        return {"trains": trains_list}

    def get_train_route_stations(self, date: str, from_station_code: str, to_station_code: str, train_no: str) -> dict:
        """Retrieve the complete route information for a specific train."""
        key = f"{date}_{from_station_code}_{to_station_code}_{train_no}"
        route_stations = self.train_routes.get(key, [])
        stations_list = []
        for station in route_stations:
            stations_list.append({
                "station_name": station.station_name,
                "arrival_time": station.arrival_time,
                "departure_time": station.departure_time,
                "stop_duration": station.stop_duration
            })
        return {"route_stations": stations_list}

# Section 3: MCP Tools
mcp = FastMCP(name="ChinaRailway")
api = ChinaRailwayAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the China Railway API.
    
    Args:
        scenario (dict): Scenario dictionary matching ChinaRailwayScenario schema.
    
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
    Save current China Railway state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_stations_code_in_city(city: str) -> dict:
    """
    Retrieves all railway stations within a specified Chinese city.
    
    Args:
        city (str): The Chinese name of the city to search for railway stations.
    
    Returns:
        stations (list): List of all railway stations located in the specified city, each containing:
            station_code (str): The unique station code used in the China Railway system.
            station_name (str): The official Chinese name of the railway station.
    """
    try:
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        return api.get_stations_code_in_city(city)
    except Exception as e:
        raise e

@mcp.tool()
def get_station_code_by_name(station_name: str) -> dict:
    """
    Looks up the unique station code for a railway station by its Chinese name.
    
    Args:
        station_name (str): The official Chinese name of the railway station to look up.
    
    Returns:
        station_code (str): The unique station code used in the China Railway system.
    """
    try:
        if not station_name or not isinstance(station_name, str):
            raise ValueError("Station name must be a non-empty string")
        return api.get_station_code_by_name(station_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_station_by_code(station_code: str) -> dict:
    """
    Retrieves detailed information about a railway station using its station code.
    
    Args:
        station_code (str): The unique station code used in the China Railway system.
    
    Returns:
        station_name (str): The official Chinese name of the railway station.
        address (str): The geographical location or physical address of the railway station.
        phone (str): The contact telephone number for the railway station.
    """
    try:
        if not station_code or not isinstance(station_code, str):
            raise ValueError("Station code must be a non-empty string")
        return api.get_station_by_code(station_code)
    except Exception as e:
        raise e

@mcp.tool()
def get_tickets(date: str, from_station_code: str, to_station_code: str) -> dict:
    """
    Queries available train tickets between two stations on a specific date.
    
    Args:
        date (str): The travel date for the ticket query in ISO 8601 format (yyyy-mm-dd).
        from_station_code (str): The unique station code for the departure station.
        to_station_code (str): The unique station code for the arrival station.
    
    Returns:
        trains (list): List of available train services, each containing:
            train_no (str): The unique train number identifier.
            departure_time (str): Scheduled departure time in HH:MM format.
            arrival_time (str): Scheduled arrival time in HH:MM format.
            duration (str): Total travel time for this train journey.
            seat_availability (dict): Current ticket availability containing:
                business_class (int): Number of available business class seats.
                first_class (int): Number of available first class seats.
                second_class (int): Number of available second class seats.
    """
    try:
        if not date or not isinstance(date, str):
            raise ValueError("Date must be a non-empty string")
        if not from_station_code or not isinstance(from_station_code, str):
            raise ValueError("From station code must be a non-empty string")
        if not to_station_code or not isinstance(to_station_code, str):
            raise ValueError("To station code must be a non-empty string")
        return api.get_tickets(date, from_station_code, to_station_code)
    except Exception as e:
        raise e

@mcp.tool()
def get_train_route_stations(date: str, from_station_code: str, to_station_code: str, train_no: str) -> dict:
    """
    Retrieves the complete route information for a specific train.
    
    Args:
        date (str): The travel date for the train route query in ISO 8601 format (yyyy-mm-dd).
        from_station_code (str): The unique station code for the departure station.
        to_station_code (str): The unique station code for the arrival station.
        train_no (str): The unique train number identifier.
    
    Returns:
        route_stations (list): Ordered list of all stations along the train's route, each containing:
            station_name (str): The official Chinese name of the railway station.
            arrival_time (str): Scheduled arrival time in HH:MM format.
            departure_time (str): Scheduled departure time in HH:MM format.
            stop_duration (str): Length of time the train stops at this station.
    """
    try:
        if not date or not isinstance(date, str):
            raise ValueError("Date must be a non-empty string")
        if not from_station_code or not isinstance(from_station_code, str):
            raise ValueError("From station code must be a non-empty string")
        if not to_station_code or not isinstance(to_station_code, str):
            raise ValueError("To station code must be a non-empty string")
        if not train_no or not isinstance(train_no, str):
            raise ValueError("Train number must be a non-empty string")
        return api.get_train_route_stations(date, from_station_code, to_station_code, train_no)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()