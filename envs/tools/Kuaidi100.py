from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import re
from datetime import datetime, timedelta

# Section 1: Schema
class TrackingEvent(BaseModel):
    """Represents a single tracking event."""
    time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Event timestamp in format yyyy-MM-dd HH:mm:ss")
    context: str = Field(..., description="Event description")

class TrackingData(BaseModel):
    """Represents complete tracking information."""
    kuaidi_num: str = Field(..., description="Package tracking number")
    kuaidi_company: str = Field(..., description="Courier company code")
    data: List[TrackingEvent] = Field(default=[], description="List of tracking events")

class DeliveryEstimate(BaseModel):
    """Represents delivery time estimate."""
    arrivalTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Estimated arrival time")
    remaining_transit_time: int = Field(..., ge=0, description="Remaining transit time in hours")

class PriceEstimate(BaseModel):
    """Represents shipping cost estimate."""
    price: float = Field(..., ge=0, description="Estimated shipping cost")
    currency: str = Field(default="CNY", description="Currency code")
    estimated_days: int = Field(..., ge=0, description="Estimated delivery days")

class Kuaidi100Scenario(BaseModel):
    """Main scenario model for Kuaidi100 logistics service."""
    tracking_records: Dict[str, TrackingData] = Field(default={}, description="Active tracking records by tracking number")
    company_zones: Dict[str, int] = Field(default={
        "shunfeng": 1, "jd": 2, "debangkuaidi": 3, "yuantong": 4, "zhongtong": 5,
        "shentong": 6, "yunda": 7, "ems": 8
    }, description="Courier company zone mapping")
    base_rates: Dict[str, float] = Field(default={
        "shunfeng": 12.0, "jd": 10.0, "debangkuaidi": 8.0, "yuantong": 6.0, "zhongtong": 5.0,
        "shentong": 6.0, "yunda": 5.0, "ems": 15.0
    }, description="Base shipping rates per kg in CNY")
    zone_multipliers: Dict[str, float] = Field(default={
        "1-1": 1.0, "1-2": 1.2, "1-3": 1.5, "1-4": 1.8, "1-5": 2.0,
        "2-1": 1.2, "2-2": 1.0, "2-3": 1.3, "2-4": 1.6, "2-5": 1.9,
        "3-1": 1.5, "3-2": 1.3, "3-3": 1.0, "3-4": 1.4, "3-5": 1.7,
        "4-1": 1.8, "4-2": 1.6, "4-3": 1.4, "4-4": 1.0, "4-5": 1.3,
        "5-1": 2.0, "5-2": 1.9, "5-3": 1.7, "5-4": 1.3, "5-5": 1.0
    }, description="Zone-based price multipliers")
    service_speeds: Dict[str, int] = Field(default={
        "标准快递": 48, "经济快递": 72, "特快专递": 24
    }, description="Service type delivery speeds in hours")
    zone_distances: Dict[str, int] = Field(default={
        "1-1": 500, "1-2": 800, "1-3": 1200, "1-4": 1800, "1-5": 2500,
        "2-1": 800, "2-2": 400, "2-3": 900, "2-4": 1400, "2-5": 2000,
        "3-1": 1200, "3-2": 900, "3-3": 600, "3-4": 1000, "3-5": 1600,
        "4-1": 1800, "4-2": 1400, "4-3": 1000, "4-4": 700, "4-5": 1200,
        "5-1": 2500, "5-2": 2000, "5-3": 1600, "5-4": 1200, "5-5": 800
    }, description="Zone distances in kilometers")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [TrackingEvent, TrackingData, DeliveryEstimate, PriceEstimate, Kuaidi100Scenario]

# Section 2: Class
class Kuaidi100API:
    def __init__(self):
        """Initialize Kuaidi100 API with empty state."""
        self.tracking_records: Dict[str, TrackingData] = {}
        self.company_zones: Dict[str, int] = {}
        self.base_rates: Dict[str, float] = {}
        self.zone_multipliers: Dict[str, float] = {}
        self.service_speeds: Dict[str, int] = {}
        self.zone_distances: Dict[str, int] = {}
        self.current_time: str = ""
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = Kuaidi100Scenario(**scenario)
        self.tracking_records = model.tracking_records
        self.company_zones = model.company_zones
        self.base_rates = model.base_rates
        self.zone_multipliers = model.zone_multipliers
        self.service_speeds = model.service_speeds
        self.zone_distances = model.zone_distances
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "tracking_records": {num: data.model_dump() for num, data in self.tracking_records.items()},
            "company_zones": self.company_zones,
            "base_rates": self.base_rates,
            "zone_multipliers": self.zone_multipliers,
            "service_speeds": self.service_speeds,
            "zone_distances": self.zone_distances,
            "current_time": self.current_time
        }

    def _extract_zone(self, address: str) -> int:
        """Extract zone from address (simplified logic)."""
        if any(city in address for city in ["北京", "天津", "河北", "山西", "内蒙古"]):
            return 1
        elif any(city in address for city in ["上海", "江苏", "浙江", "安徽", "山东"]):
            return 2
        elif any(city in address for city in ["广东", "广西", "海南", "福建", "江西"]):
            return 3
        elif any(city in address for city in ["四川", "重庆", "贵州", "云南", "西藏"]):
            return 4
        else:
            return 5

    def query_trace(self, kuaidi_num: str, phone: Optional[str] = None) -> dict:
        """Query logistics tracking information for a package."""
        if kuaidi_num not in self.tracking_records:
            return {"kuaidi_num": kuaidi_num, "kuaidi_company": "unknown", "data": []}
        
        tracking_data = self.tracking_records[kuaidi_num]
        return {
            "kuaidi_num": tracking_data.kuaidi_num,
            "kuaidi_company": tracking_data.kuaidi_company,
            "data": [{"time": event.time, "context": event.context} for event in tracking_data.data]
        }

    def estimate_time(self, from_addr: str, kuaidi_company: str, to_addr: str, 
                     exp_type: str = "标准快递", order_time: Optional[str] = None, 
                     logistic: Optional[str] = None) -> dict:
        """Estimate delivery time based on various factors."""
        from_zone = self._extract_zone(from_addr)
        to_zone = self._extract_zone(to_addr)
        zone_key = f"{min(from_zone, to_zone)}-{max(from_zone, to_zone)}"
        
        base_hours = self.service_speeds.get(exp_type, 48)
        distance = self.zone_distances.get(zone_key, 1000)
        
        # Adjust for distance
        distance_multiplier = max(1.0, distance / 1000)
        total_hours = int(base_hours * distance_multiplier)
        
        # Use order_time or current time as base
        if order_time:
            base_time = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
        else:
            base_time = datetime.strptime(self.current_time.replace("T", " ")[:19], "%Y-%m-%d %H:%M:%S")
        
        arrival_time = base_time + timedelta(hours=total_hours)
        
        return {
            "arrivalTime": arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            "remaining_transit_time": total_hours
        }

    def estimate_price(self, kuaidi_company: str, from_addr: str, to_addr: str, 
                      weight: str = "1.0") -> dict:
        """Estimate shipping cost based on various factors."""
        from_zone = self._extract_zone(from_addr)
        to_zone = self._extract_zone(to_addr)
        zone_key = f"{min(from_zone, to_zone)}-{max(from_zone, to_zone)}"
        
        base_rate = self.base_rates.get(kuaidi_company, 10.0)
        multiplier = self.zone_multipliers.get(zone_key, 1.5)
        
        try:
            weight_kg = float(weight)
        except ValueError:
            weight_kg = 1.0
        
        price = base_rate * weight_kg * multiplier
        
        # Estimate days based on zones
        if from_zone == to_zone:
            days = 1
        elif abs(from_zone - to_zone) <= 2:
            days = 2
        else:
            days = 3
        
        return {
            "price": round(price, 2),
            "currency": "CNY",
            "estimated_days": days
        }

# Section 3: MCP Tools
mcp = FastMCP(name="Kuaidi100")
api = Kuaidi100API()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Kuaidi100 API.
    
    Args:
        scenario (dict): Scenario dictionary matching Kuaidi100Scenario schema.
    
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
    Save current Kuaidi100 state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def query_trace(kuaidi_num: str, phone: Optional[str] = None) -> dict:
    """
    Query logistics tracking information for a package.
    
    Args:
        kuaidi_num (str): The tracking number of the package to query.
        phone (str) [Optional]: The recipient's phone number for SF Express verification.
    
    Returns:
        kuaidi_num (str): The tracking number of the queried package.
        kuaidi_company (str): The courier company code.
        data (list): List of tracking events with time and context.
    """
    try:
        if not kuaidi_num or not isinstance(kuaidi_num, str):
            raise ValueError("Tracking number must be a non-empty string")
        return api.query_trace(kuaidi_num, phone)
    except Exception as e:
        raise e

@mcp.tool()
def estimate_time(from_addr: str, kuaidi_company: str, to_addr: str, 
                 exp_type: str = "标准快递", order_time: Optional[str] = None, 
                 logistic: Optional[str] = None) -> dict:
    """
    Estimate delivery time based on courier company, addresses, and service type.
    
    Args:
        from_addr (str): Origin address with 3 administrative levels.
        kuaidi_company (str): Courier company code in lowercase.
        to_addr (str): Destination address with 3 administrative levels.
        exp_type (str) [Optional]: Service type - 标准快递, 经济快递, or 特快专递.
        order_time (str) [Optional]: Order time in format yyyy-MM-dd HH:mm:ss.
        logistic (str) [Optional]: Historical tracking data JSON array string.
    
    Returns:
        arrivalTime (str): Estimated arrival date and time.
        remaining_transit_time (int): Remaining transit time in hours.
    """
    try:
        if not from_addr or not isinstance(from_addr, str):
            raise ValueError("From address must be a non-empty string")
        if not kuaidi_company or not isinstance(kuaidi_company, str):
            raise ValueError("Courier company must be a non-empty string")
        if not to_addr or not isinstance(to_addr, str):
            raise ValueError("To address must be a non-empty string")
        if exp_type not in ["标准快递", "经济快递", "特快专递"]:
            raise ValueError("Invalid service type")
        return api.estimate_time(from_addr, kuaidi_company, to_addr, exp_type, order_time, logistic)
    except Exception as e:
        raise e

@mcp.tool()
def estimate_price(kuaidi_company: str, from_addr: str, to_addr: str, 
                  weight: str = "1.0") -> dict:
    """
    Estimate shipping cost based on courier company, addresses, and weight.
    
    Args:
        kuaidi_company (str): Courier company code in lowercase.
        from_addr (str): Origin address with 3 administrative levels.
        to_addr (str): Destination address with 3 administrative levels.
        weight (str) [Optional]: Package weight in kilograms, defaults to 1.0kg.
    
    Returns:
        price (float): Estimated shipping cost.
        currency (str): Currency code (CNY).
        estimated_days (int): Estimated delivery days.
    """
    try:
        if not kuaidi_company or not isinstance(kuaidi_company, str):
            raise ValueError("Courier company must be a non-empty string")
        if not from_addr or not isinstance(from_addr, str):
            raise ValueError("From address must be a non-empty string")
        if not to_addr or not isinstance(to_addr, str):
            raise ValueError("To address must be a non-empty string")
        return api.estimate_price(kuaidi_company, from_addr, to_addr, weight)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()