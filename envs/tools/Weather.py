from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class WindData(BaseModel):
    """Wind metrics including speed and direction."""
    speed: float = Field(..., ge=0, description="Wind speed in km/h")
    direction: int = Field(..., ge=0, le=360, description="Wind direction in degrees")

class PrecipitationData(BaseModel):
    """Precipitation chances and amounts."""
    chance: float = Field(..., ge=0, le=100, description="Precipitation probability percentage")
    amount: float = Field(..., ge=0, description="Expected precipitation amount in mm")

class WeatherAlert(BaseModel):
    """Weather alert information."""
    severity: str = Field(..., description="Alert severity level")
    urgency: str = Field(..., description="Urgency classification")
    event: str = Field(..., description="Weather event description")
    instructions: str = Field(..., description="Safety instructions")
    areas: List[str] = Field(default_factory=list, description="Affected areas")
    active: bool = Field(default=True, description="Whether alert is currently active")

class HistoricalRecord(BaseModel):
    """Historical weather observation."""
    temperature: float = Field(..., description="Recorded temperature in Celsius")
    conditions: str = Field(..., description="Weather conditions summary")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    pressure: float = Field(..., ge=0, description="Atmospheric pressure in hPa")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="ISO 8601 date")

class SavedLocation(BaseModel):
    """Saved location with coordinates."""
    alias: str = Field(..., description="Unique identifier for the location")
    name: str = Field(..., description="Display name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    timezone: str = Field(default="UTC", description="Timezone identifier")

class CurrentWeather(BaseModel):
    """Current weather conditions."""
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    wind: WindData = Field(..., description="Wind metrics")
    pressure: float = Field(..., ge=0, description="Atmospheric pressure in hPa")
    latitude: float = Field(..., ge=-90, le=90, description="Location latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Location longitude")

class ForecastData(BaseModel):
    """Weather forecast data."""
    temperature: float = Field(..., description="Forecasted temperature in Celsius")
    precipitation: PrecipitationData = Field(..., description="Precipitation data")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    weather_conditions: str = Field(..., description="Weather summary")
    timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="ISO 8601 timestamp")
    latitude: float = Field(..., ge=-90, le=90, description="Location latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Location longitude")
    days: int = Field(..., ge=1, description="Number of forecast days")

class CityLocation(BaseModel):
    """City location information."""
    city: str = Field(..., description="City name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    population: int = Field(..., ge=0, description="Population count")
    country: str = Field(..., description="Country name")

class WeatherScenario(BaseModel):
    """Main scenario model for weather service."""
    current_weather: Dict[str, CurrentWeather] = Field(default={}, description="Current weather by coordinate key")
    forecasts: Dict[str, ForecastData] = Field(default={}, description="Forecasts by coordinate key")
    alerts: Dict[str, List[WeatherAlert]] = Field(default={}, description="Alerts by coordinate key")
    historical_records: Dict[str, List[HistoricalRecord]] = Field(default={}, description="Historical data by coordinate key")
    saved_locations: Dict[str, SavedLocation] = Field(default={}, description="Saved locations by alias")
    city_database: Dict[str, CityLocation] = Field(default_factory=lambda: {
        "Paris": CityLocation(city="Paris", latitude=48.8566, longitude=2.3522, population=2161000, country="France"),
        "New York": CityLocation(city="New York", latitude=40.7128, longitude=-74.0060, population=8336817, country="United States"),
        "Tokyo": CityLocation(city="Tokyo", latitude=35.6762, longitude=139.6503, population=13960000, country="Japan"),
        "London": CityLocation(city="London", latitude=51.5074, longitude=-0.1278, population=8982000, country="United Kingdom"),
        "Sydney": CityLocation(city="Sydney", latitude=-33.8688, longitude=151.2093, population=5312000, country="Australia"),
        "Berlin": CityLocation(city="Berlin", latitude=52.5200, longitude=13.4050, population=3645000, country="Germany"),
        "Mumbai": CityLocation(city="Mumbai", latitude=19.0760, longitude=72.8777, population=20411000, country="India"),
        "Dubai": CityLocation(city="Dubai", latitude=25.2048, longitude=55.2708, population=3331000, country="United Arab Emirates"),
        "Singapore": CityLocation(city="Singapore", latitude=1.3521, longitude=103.8198, population=5686000, country="Singapore"),
        "Toronto": CityLocation(city="Toronto", latitude=43.6532, longitude=-79.3832, population=2731000, country="Canada"),
        "Moscow": CityLocation(city="Moscow", latitude=55.7558, longitude=37.6173, population=12506000, country="Russia"),
        "Beijing": CityLocation(city="Beijing", latitude=39.9042, longitude=116.4074, population=21540000, country="China"),
        "Los Angeles": CityLocation(city="Los Angeles", latitude=34.0522, longitude=-118.2437, population=3979000, country="United States"),
        "Rome": CityLocation(city="Rome", latitude=41.9028, longitude=12.4964, population=2873000, country="Italy"),
        "Madrid": CityLocation(city="Madrid", latitude=40.4168, longitude=-3.7038, population=3223000, country="Spain"),
        "Amsterdam": CityLocation(city="Amsterdam", latitude=52.3676, longitude=4.9041, population=872680, country="Netherlands"),
        "Seoul": CityLocation(city="Seoul", latitude=37.5665, longitude=126.9780, population=9776000, country="South Korea"),
        "Bangkok": CityLocation(city="Bangkok", latitude=13.7563, longitude=100.5018, population=10539000, country="Thailand"),
        "Istanbul": CityLocation(city="Istanbul", latitude=41.0082, longitude=28.9784, population=15462000, country="Turkey"),
        "Mexico City": CityLocation(city="Mexico City", latitude=19.4326, longitude=-99.1332, population=21581000, country="Mexico")
    }, description="City location database")

Scenario_Schema = [WindData, PrecipitationData, WeatherAlert, HistoricalRecord, SavedLocation, CurrentWeather, ForecastData, CityLocation, WeatherScenario]

# Section 2: Class
class WeatherAPI:
    def __init__(self):
        """Initialize weather API with empty state."""
        self.current_weather: Dict[str, CurrentWeather] = {}
        self.forecasts: Dict[str, ForecastData] = {}
        self.alerts: Dict[str, List[WeatherAlert]] = {}
        self.historical_records: Dict[str, List[HistoricalRecord]] = {}
        self.saved_locations: Dict[str, SavedLocation] = {}
        self.city_database: Dict[str, CityLocation] = {}
        
    def _get_coord_key(self, latitude: float, longitude: float) -> str:
        """Generate coordinate key for lookups."""
        return f"{latitude:.4f},{longitude:.4f}"
    
    def _normalize_coord_keys(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize coordinate keys in a dictionary to match the standard format."""
        normalized = {}
        for key, value in data_dict.items():
            # Parse the coordinate key
            try:
                parts = key.split(',')
                if len(parts) == 2:
                    lat = float(parts[0])
                    lon = float(parts[1])
                    # Regenerate key with standard format
                    normalized_key = self._get_coord_key(lat, lon)
                    normalized[normalized_key] = value
                else:
                    # Not a coordinate key, keep as is
                    normalized[key] = value
            except (ValueError, AttributeError):
                # Not a coordinate key, keep as is
                normalized[key] = value
        return normalized
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = WeatherScenario(**scenario)
        
        # Normalize coordinate keys for all coordinate-based dictionaries
        self.current_weather = self._normalize_coord_keys(model.current_weather)
        self.forecasts = self._normalize_coord_keys(model.forecasts)
        self.alerts = self._normalize_coord_keys(model.alerts)
        self.historical_records = self._normalize_coord_keys(model.historical_records)
        
        # These don't use coordinate keys, so no normalization needed
        self.saved_locations = model.saved_locations
        self.city_database = model.city_database

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "current_weather": {k: v.model_dump() for k, v in self.current_weather.items()},
            "forecasts": {k: v.model_dump() for k, v in self.forecasts.items()},
            "alerts": {k: [alert.model_dump() for alert in alerts] for k, alerts in self.alerts.items()},
            "historical_records": {k: [rec.model_dump() for rec in recs] for k, recs in self.historical_records.items()},
            "saved_locations": {k: v.model_dump() for k, v in self.saved_locations.items()},
            "city_database": {k: v.model_dump() for k, v in self.city_database.items()}
        }

    def get_current_weather(self, latitude: float, longitude: float) -> dict:
        """Fetch real-time weather conditions for coordinates."""
        key = self._get_coord_key(latitude, longitude)
        weather = self.current_weather.get(key)
        
        if not weather:
            return {}
        
        return {
            "temperature": weather.temperature,
            "humidity": weather.humidity,
            "wind": {
                "speed": weather.wind.speed,
                "direction": weather.wind.direction
            },
            "pressure": weather.pressure
        }

    def get_forecast(self, latitude: float, longitude: float, days: int = 3) -> dict:
        """Retrieve multi-day weather forecast for coordinates."""
        key = self._get_coord_key(latitude, longitude)
        forecast = self.forecasts.get(key)
        
        if not forecast:
            return {}
        
        return {
            "temperature": forecast.temperature,
            "precipitation": {
                "chance": forecast.precipitation.chance,
                "amount": forecast.precipitation.amount
            },
            "wind_speed": forecast.wind_speed,
            "humidity": forecast.humidity,
            "weather_conditions": forecast.weather_conditions,
            "timestamp": forecast.timestamp
        }

    def search_location(self, city: str) -> dict:
        """Resolve city name to geographic coordinates."""
        location = self.city_database.get(city)
        
        if not location:
            return {}
        
        return {
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "population": location.population,
            "country": location.country
        }

    def get_alerts(self, latitude: float, longitude: float, active_only: bool = True) -> dict:
        """Retrieve weather alerts for coordinates."""
        key = self._get_coord_key(latitude, longitude)
        all_alerts = self.alerts.get(key, [])
        
        if active_only:
            filtered_alerts = [alert for alert in all_alerts if alert.active]
        else:
            filtered_alerts = all_alerts
        
        return {
            "alerts": [
                {
                    "severity": alert.severity,
                    "urgency": alert.urgency,
                    "event": alert.event,
                    "instructions": alert.instructions,
                    "areas": alert.areas
                }
                for alert in filtered_alerts
            ]
        }

    def get_historical_weather(self, latitude: float, longitude: float, start_date: str, end_date: str, limit: int = 10) -> dict:
        """Observe past weather conditions for coordinates."""
        key = self._get_coord_key(latitude, longitude)
        all_records = self.historical_records.get(key, [])
        
        filtered_records = [
            rec for rec in all_records
            if start_date <= rec.date <= end_date
        ]
        
        limited_records = filtered_records[:limit]
        
        return {
            "records": [
                {
                    "temperature": rec.temperature,
                    "conditions": rec.conditions,
                    "wind_speed": rec.wind_speed,
                    "humidity": rec.humidity,
                    "pressure": rec.pressure,
                    "date": rec.date
                }
                for rec in limited_records
            ]
        }

    def save_location(self, alias: str, latitude: float, longitude: float, name: str) -> None:
        """Store geographic coordinate under custom alias."""
        location = SavedLocation(
            alias=alias,
            name=name,
            latitude=latitude,
            longitude=longitude
        )
        self.saved_locations[alias] = location

    def list_saved_locations(self) -> dict:
        """Enumerate all saved location aliases."""
        return {
            "locations": [
                {
                    "alias": loc.alias,
                    "name": loc.name,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude
                }
                for loc in self.saved_locations.values()
            ]
        }

    def get_saved_location(self, alias: str) -> dict:
        """Retrieve details of saved location by alias."""
        location = self.saved_locations.get(alias)
        
        if not location:
            return {}
        
        return {
            "alias": location.alias,
            "name": location.name,
            "timezone": location.timezone,
            "latitude": location.latitude,
            "longitude": location.longitude
        }

    def remove_saved_location(self, alias: str) -> dict:
        """Delete saved location by alias."""
        if alias in self.saved_locations:
            del self.saved_locations[alias]
        
        return {
            "confirmation": f"Location '{alias}' has been removed",
            "remaining_count": len(self.saved_locations)
        }

# Section 3: MCP Tools
mcp = FastMCP(name="Weather")
api = WeatherAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the weather API.
    
    Args:
        scenario (dict): Scenario dictionary matching WeatherScenario schema.
    
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
    Save current weather state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_current_weather(latitude: float, longitude: float) -> dict:
    """
    Fetch real-time weather conditions for any coordinate on Earth.
    
    Args:
        latitude (float): The latitude of the location in decimal degrees, ranging from -90 to 90.
        longitude (float): The longitude of the location in decimal degrees, ranging from -180 to 180.
    
    Returns:
        temperature (float): Current temperature in degrees Celsius.
        humidity (float): Current relative humidity percentage.
        wind (dict): Current wind metrics including speed and direction.
        pressure (float): Atmospheric pressure in hPa.
    """
    try:
        result = api.get_current_weather(latitude, longitude)
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_forecast(latitude: float, longitude: float, days: int = 3) -> dict:
    """
    Retrieve a multi-day weather forecast for any coordinate on Earth.
    
    Args:
        latitude (float): The latitude of the location in decimal degrees, ranging from -90 to 90.
        longitude (float): The longitude of the location in decimal degrees, ranging from -180 to 180.
        days (int): [Optional] Number of forecast days to return (default 3).
    
    Returns:
        temperature (float): Forecasted temperature in degrees Celsius.
        precipitation (dict): Chances and amounts of precipitation for each forecast day.
        wind_speed (float): Forecasted wind speed in km/h.
        humidity (float): Forecasted relative humidity percentage.
        weather_conditions (str): Descriptive summary of expected weather (e.g., sunny, cloudy).
        timestamp (str): ISO 8601 timestamp when the forecast data was generated.
    """
    try:
        result = api.get_forecast(latitude, longitude, days)
        return result
    except Exception as e:
        raise e

@mcp.tool()
def search_location(city: str) -> dict:
    """
    Resolve a city name into geographic coordinates and metadata.
    
    Args:
        city (str): City name to search for (e.g., 'Paris' or 'New York').
    
    Returns:
        location (dict): Geographic coordinates of the searched city.
        population (int): Population count of the matched city.
        country (str): Country in which the city is located.
    """
    try:
        if not city or not isinstance(city, str):
            raise ValueError("City must be a non-empty string")
        result = api.search_location(city)
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_alerts(latitude: float, longitude: float, active_only: bool = True) -> dict:
    """
    Retrieve active or all weather alerts for a specific coordinate.
    
    Args:
        latitude (float): The latitude of the location in decimal degrees, ranging from -90 to 90.
        longitude (float): The longitude of the location in decimal degrees, ranging from -180 to 180.
        active_only (bool): [Optional] When true, return only currently active alerts; when false, include past alerts as well.
    
    Returns:
        alerts (list): List of weather alerts applicable to the requested coordinates.
    """
    try:
        result = api.get_alerts(latitude, longitude, active_only)
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_historical_weather(latitude: float, longitude: float, start_date: str, end_date: str, limit: int = 10) -> dict:
    """
    Observe past weather conditions for a coordinate within a date range.
    
    Args:
        latitude (float): The latitude of the location in decimal degrees, ranging from -90 to 90.
        longitude (float): The longitude of the location in decimal degrees, ranging from -180 to 180.
        start_date (str): Start date for historical data in ISO 8601 format (YYYY-MM-DD).
        end_date (str): End date for historical data in ISO 8601 format (YYYY-MM-DD).
        limit (int): [Optional] Maximum number of historical records to return (default 10).
    
    Returns:
        records (list): Chronological list of historical weather observations.
    """
    try:
        if not start_date or not isinstance(start_date, str):
            raise ValueError("Start date must be a non-empty string")
        if not end_date or not isinstance(end_date, str):
            raise ValueError("End date must be a non-empty string")
        result = api.get_historical_weather(latitude, longitude, start_date, end_date, limit)
        return result
    except Exception as e:
        raise e

@mcp.tool()
def save_location(alias: str, latitude: float, longitude: float, name: str) -> str:
    """
    Store a geographic coordinate under a custom alias for quick future access.
    
    Args:
        alias (str): Short unique identifier you will use to recall this location.
        latitude (float): The latitude of the location in decimal degrees, ranging from -90 to 90.
        longitude (float): The longitude of the location in decimal degrees, ranging from -180 to 180.
        name (str): Human-readable display name for the saved location.
    
    Returns:
        success_message (str): Success message.
    """
    try:
        if not alias or not isinstance(alias, str):
            raise ValueError("Alias must be a non-empty string")
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        result = api.save_location(alias, latitude, longitude, name)
        if result is None:
            return "Successfully saved location"
        return result
    except Exception as e:
        raise e

@mcp.tool()
def list_saved_locations() -> dict:
    """
    Enumerate all previously saved location aliases with their coordinates.
    
    Returns:
        locations (list): List of all saved locations with aliases and coordinates.
    """
    try:
        return api.list_saved_locations()
    except Exception as e:
        raise e

@mcp.tool()
def get_saved_location(alias: str) -> dict:
    """
    Retrieve details of a single saved location by its alias.
    
    Args:
        alias (str): The alias of the location to retrieve.
    
    Returns:
        alias (str): User-defined alias for the saved location.
        name (str): Display name of the saved location.
        timezone (str): Timezone identifier for the saved location.
        latitude (float): Latitude of the saved location.
        longitude (float): Longitude of the saved location.
    """
    try:
        if not alias or not isinstance(alias, str):
            raise ValueError("Alias must be a non-empty string")
        if alias not in api.saved_locations:
            raise ValueError(f"Location with alias '{alias}' not found")
        return api.get_saved_location(alias)
    except Exception as e:
        raise e

@mcp.tool()
def remove_saved_location(alias: str) -> dict:
    """
    Delete a saved location using its alias.
    
    Args:
        alias (str): The alias of the location to delete.
    
    Returns:
        confirmation (str): Message confirming successful removal of the saved location.
        remaining_count (int): Number of locations still saved after this deletion.
    """
    try:
        if not alias or not isinstance(alias, str):
            raise ValueError("Alias must be a non-empty string")
        return api.remove_saved_location(alias)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()