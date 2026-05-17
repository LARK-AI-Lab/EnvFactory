from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP

# ---------- Section 1: Schema ----------
class TirePressure(BaseModel):
    """Represents tire pressure readings."""
    front_left: float = Field(..., ge=0, description="Front left tire pressure in PSI")
    front_right: float = Field(..., ge=0, description="Front right tire pressure in PSI")
    rear_left: float = Field(..., ge=0, description="Rear left tire pressure in PSI")
    rear_right: float = Field(..., ge=0, description="Rear right tire pressure in PSI")

class DoorStatus(BaseModel):
    """Represents door lock status."""
    driver: str = Field(..., pattern="^(locked|unlocked)$", description="Driver door status")
    passenger: str = Field(..., pattern="^(locked|unlocked)$", description="Passenger door status")
    rear_left: str = Field(..., pattern="^(locked|unlocked)$", description="Rear left door status")
    rear_right: str = Field(..., pattern="^(locked|unlocked)$", description="Rear right door status")

class ClimateStatus(BaseModel):
    """Represents climate control settings."""
    temperature: float = Field(..., description="Temperature setting in Celsius")
    fan_speed: int = Field(..., ge=0, le=100, description="Fan speed 0-100")
    mode: str = Field(..., pattern="^(auto|cool|heat|defrost)$", description="Operating mode")
    humidity_level: float = Field(..., ge=0, le=100, description="Humidity percentage")

class VehicleScenario(BaseModel):
    """Main scenario model for vehicle control system."""
    engine_state: str = Field(default="stopped", pattern="^(running|stopped)$", description="Engine operational state")
    fuel_level: float = Field(default=25.0, ge=0, le=50, description="Fuel level in gallons")
    battery_voltage: float = Field(default=12.0, ge=0, description="Battery voltage in volts")
    door_status: DoorStatus = Field(default_factory=lambda: DoorStatus(driver="unlocked", passenger="unlocked", rear_left="unlocked", rear_right="unlocked"), description="Door lock status")
    climate_status: ClimateStatus = Field(default_factory=lambda: ClimateStatus(temperature=22.0, fan_speed=50, mode="auto", humidity_level=45.0), description="Climate control settings")
    headlight_status: str = Field(default="off", pattern="^(on|off|auto)$", description="Headlight status")
    parking_brake_status: str = Field(default="released", pattern="^(engaged|released)$", description="Parking brake status")
    parking_brake_force: float = Field(default=0.0, ge=0, description="Parking brake force in Newtons")
    slope_angle: float = Field(default=0.0, description="Surface slope angle in degrees")
    brake_pedal_status: str = Field(default="released", pattern="^(pressed|released)$", description="Brake pedal status")
    brake_pedal_force: float = Field(default=0.0, ge=0, description="Brake pedal force in Newtons")
    cruise_status: str = Field(default="inactive", pattern="^(active|inactive)$", description="Cruise control status")
    current_speed: float = Field(default=0.0, ge=0, description="Current speed in km/h")
    distance_to_next_vehicle: float = Field(default=100.0, ge=0, description="Distance to next vehicle in meters")
    tire_pressure: TirePressure = Field(default_factory=lambda: TirePressure(front_left=32.0, front_right=32.0, rear_left=32.0, rear_right=32.0), description="Tire pressure readings")
    navigation_destination: str = Field(default="", description="Navigation destination address")
    navigation_active: bool = Field(default=False, description="Navigation active status")
    outside_temperature: float = Field(default=20.0, description="Outside temperature in Celsius")
    cityZipMap: Dict[str, str] = Field(default={
        "New York": "10001", "Los Angeles": "90001", "Chicago": "60601", "Houston": "77001",
        "Phoenix": "85001", "Philadelphia": "19101", "San Antonio": "78201", "San Diego": "92101",
        "Dallas": "75201", "San Jose": "95101", "Austin": "78701", "Jacksonville": "32201",
        "Fort Worth": "76101", "Columbus": "43201", "Charlotte": "28201", "San Francisco": "94101",
        "Indianapolis": "46201", "Seattle": "98101", "Denver": "80201", "Washington": "20001"
    }, description="City to zipcode mapping")
    distanceMap: Dict[str, Dict[str, float]] = Field(default={
        "10001": {"90001": 4500, "60601": 1200, "77001": 1800, "85001": 3500, "19101": 150},
        "90001": {"10001": 4500, "60601": 2800, "77001": 2200, "85001": 600, "19101": 4300},
        "60601": {"10001": 1200, "90001": 2800, "77001": 1500, "85001": 2300, "19101": 1100},
        "77001": {"10001": 1800, "90001": 2200, "60601": 1500, "85001": 1700, "19101": 1900},
        "85001": {"10001": 3500, "90001": 600, "60601": 2300, "77001": 1700, "19101": 3400}
    }, description="Inter-city distance mapping in kilometers")
    shopLocationsMap: Dict[str, str] = Field(default={
        "10001": "123 Main St, New York, NY", "90001": "456 Sunset Blvd, Los Angeles, CA",
        "60601": "789 Lake Shore Dr, Chicago, IL", "77001": "321 Space Center Blvd, Houston, TX",
        "85001": "654 Camelback Rd, Phoenix, AZ", "19101": "987 Liberty Bell Dr, Philadelphia, PA",
        "78201": "147 River Walk, San Antonio, TX", "92101": "258 Harbor Dr, San Diego, CA",
        "75201": "369 Downtown Plz, Dallas, TX", "95101": "741 Silicon Valley Blvd, San Jose, CA"
    }, description="Tire shop locations by zipcode")

Scenario_Schema = [TirePressure, DoorStatus, ClimateStatus, VehicleScenario]

# ---------- Section 2: VehicleControl ----------
class VehicleControl:
    def __init__(self):
        """Initialize vehicle control with empty state."""
        self.engine_state: str = ""
        self.fuel_level: float = 0.0
        self.battery_voltage: float = 0.0
        self.door_status: DoorStatus = None
        self.climate_status: ClimateStatus = None
        self.headlight_status: str = ""
        self.parking_brake_status: str = ""
        self.parking_brake_force: float = 0.0
        self.slope_angle: float = 0.0
        self.brake_pedal_status: str = ""
        self.brake_pedal_force: float = 0.0
        self.cruise_status: str = ""
        self.current_speed: float = 0.0
        self.distance_to_next_vehicle: float = 0.0
        self.tire_pressure: TirePressure = None
        self.navigation_destination: str = ""
        self.navigation_active: bool = False
        self.outside_temperature: float = 0.0
        self.cityZipMap: Dict[str, str] = {}
        self.distanceMap: Dict[str, Dict[str, float]] = {}
        self.shopLocationsMap: Dict[str, str] = {}

    def load_scenario(self, scenario: dict) -> None:
        """
        Load scenario data into the vehicle control instance.
        
        Args:
            scenario (dict): Scenario dictionary matching VehicleScenario schema.
        
        Returns:
            None
        """
        model = VehicleScenario(**scenario)
        self.engine_state = model.engine_state
        self.fuel_level = model.fuel_level
        self.battery_voltage = model.battery_voltage
        self.door_status = model.door_status
        self.climate_status = model.climate_status
        self.headlight_status = model.headlight_status
        self.parking_brake_status = model.parking_brake_status
        self.parking_brake_force = model.parking_brake_force
        self.slope_angle = model.slope_angle
        self.brake_pedal_status = model.brake_pedal_status
        self.brake_pedal_force = model.brake_pedal_force
        self.cruise_status = model.cruise_status
        self.current_speed = model.current_speed
        self.distance_to_next_vehicle = model.distance_to_next_vehicle
        self.tire_pressure = model.tire_pressure
        self.navigation_destination = model.navigation_destination
        self.navigation_active = model.navigation_active
        self.outside_temperature = model.outside_temperature
        self.cityZipMap = model.cityZipMap
        self.distanceMap = model.distanceMap
        self.shopLocationsMap = model.shopLocationsMap

    def save_scenario(self) -> dict:
        """
        Save current state as scenario dictionary.
        
        Returns:
            dict: Dictionary containing all current state variables.
        """
        return {
            "engine_state": self.engine_state,
            "fuel_level": self.fuel_level,
            "battery_voltage": self.battery_voltage,
            "door_status": self.door_status.model_dump() if self.door_status else None,
            "climate_status": self.climate_status.model_dump() if self.climate_status else None,
            "headlight_status": self.headlight_status,
            "parking_brake_status": self.parking_brake_status,
            "parking_brake_force": self.parking_brake_force,
            "slope_angle": self.slope_angle,
            "brake_pedal_status": self.brake_pedal_status,
            "brake_pedal_force": self.brake_pedal_force,
            "cruise_status": self.cruise_status,
            "current_speed": self.current_speed,
            "distance_to_next_vehicle": self.distance_to_next_vehicle,
            "tire_pressure": self.tire_pressure.model_dump() if self.tire_pressure else None,
            "navigation_destination": self.navigation_destination,
            "navigation_active": self.navigation_active,
            "outside_temperature": self.outside_temperature,
            "cityZipMap": self.cityZipMap,
            "distanceMap": self.distanceMap,
            "shopLocationsMap": self.shopLocationsMap
        }

    def get_engine_status(self) -> dict:
        """
        Retrieve the current operational status of the vehicle engine, including running state, fuel level, and battery voltage.
        
        Returns:
            engine_state (str): The current operational state of the vehicle engine.
            fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
            battery_voltage (float): The current electrical voltage of the vehicle battery, measured in volts.
        """
        return {
            "engine_state": self.engine_state,
            "fuel_level": self.fuel_level,
            "battery_voltage": self.battery_voltage
        }

    def start_engine(self) -> dict:
        """
        Start the vehicle engine. This operation requires all doors to be locked and the brake pedal to be fully pressed as safety prerequisites.
        
        Returns:
            engine_state (str): The current operational state of the vehicle engine.
            fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
            battery_voltage (float): The current electrical voltage of the vehicle battery, measured in volts.
            error (str): Error message if prerequisites (locked doors and pressed brake pedal) are not met.
        """
        result = {
            "engine_state": self.engine_state,
            "fuel_level": self.fuel_level,
            "battery_voltage": self.battery_voltage
        }
        
        if self.door_status and all(status == "locked" for status in self.door_status.model_dump().values()):
            if self.brake_pedal_status == "pressed":
                self.engine_state = "running"
            else:
                self.engine_state = "stopped"
                result["error"] = "Brake pedal must be fully pressed to start the engine"
        else:
            self.engine_state = "stopped"
            result["error"] = "All doors must be locked to start the engine"
        
        result["engine_state"] = self.engine_state
        return result

    def stop_engine(self) -> dict:
        """
        Stop the vehicle engine and transition it to a stopped state.
        
        Returns:
            engine_state (str): The current operational state of the vehicle engine.
            fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
            battery_voltage (float): The current electrical voltage of the vehicle battery, measured in volts.
        """
        self.engine_state = "stopped"
        return {
            "engine_state": self.engine_state,
            "fuel_level": self.fuel_level,
            "battery_voltage": self.battery_voltage
        }

    def get_fuel_level(self) -> dict:
        """
        Retrieve the current fuel level in the vehicle tank.
        
        Returns:
            fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons (range: 0-50).
        """
        return {"fuel_level": self.fuel_level}

    def fill_fuel_tank(self, fuel_amount: float) -> dict:
        """
        Add a specified amount of fuel to the vehicle tank. The tank has a maximum capacity of 50 gallons.
        
        Args:
            fuel_amount (float): The amount of fuel to add to the tank, measured in gallons. Must be positive and the total fuel level must not exceed 50 gallons.
        
        Returns:
            fuel_level (float): The current amount of fuel in the vehicle tank after filling, measured in gallons.
            error (str): Error message if the fuel amount is invalid or would exceed the 50-gallon tank capacity.
        """
        new_level = self.fuel_level + fuel_amount
        if new_level > 50:
            return {
                "fuel_level": self.fuel_level,
                "error": "Fuel amount would exceed tank capacity of 50 gallons"
            }
        self.fuel_level = new_level
        return {"fuel_level": self.fuel_level}

    def estimate_drive_feasibility(self, distance: float, unit: str = "miles") -> dict:
        """
        Estimate whether the vehicle has sufficient fuel to complete a specified distance based on current fuel level and fuel efficiency.
        
        Args:
            distance (float): The distance to travel for which feasibility is being estimated.
            unit [Optional] (str): The unit of measurement for the distance. Defaults to 'miles' if not specified.
        
        Returns:
            can_drive (bool): Indicates whether the vehicle has sufficient fuel to complete the specified distance.
            current_fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
            estimated_range (float): The estimated maximum distance the vehicle can travel with current fuel, measured in the specified unit.
        """
        mpg = 25.0
        distance_miles = distance * 0.621371 if unit == "km" else distance
        estimated_range_miles = self.fuel_level * mpg
        estimated_range = estimated_range_miles * 1.60934 if unit == "km" else estimated_range_miles
        can_drive = estimated_range_miles >= distance_miles
        return {
            "can_drive": can_drive,
            "current_fuel_level": self.fuel_level,
            "estimated_range": estimated_range
        }

    def get_door_status(self, door_position: Optional[str] = None) -> dict:
        """
        Retrieve the lock status of vehicle doors, either for a specific door or all doors.
        
        Args:
            door_position [Optional] (str): The specific door position to query. If not provided, returns status for all doors.
        
        Returns:
            door_status (dict): A mapping of door positions to their current lock status (locked or unlocked).
            remaining_unlocked_doors (int): The count of doors that are currently in an unlocked state.
        """
        if not self.door_status:
            return {"door_status": {}, "remaining_unlocked_doors": 0}
        
        door_dict = self.door_status.model_dump()
        if door_position:
            if door_position in door_dict:
                return {
                    "door_status": {door_position: door_dict[door_position]},
                    "remaining_unlocked_doors": sum(1 for v in door_dict.values() if v == "unlocked")
                }
            else:
                return {"door_status": {}, "remaining_unlocked_doors": sum(1 for v in door_dict.values() if v == "unlocked")}
        
        remaining_unlocked = sum(1 for v in door_dict.values() if v == "unlocked")
        return {
            "door_status": door_dict,
            "remaining_unlocked_doors": remaining_unlocked
        }

    def lock_doors(self, door_positions: List[str]) -> dict:
        """
        Lock one or more vehicle doors at specified positions.
        
        Args:
            door_positions (List[str]): List of door positions to lock. Valid positions are driver, passenger, rear_left, and rear_right.
        
        Returns:
            lock_status (str): Confirmation that the specified doors have been locked.
            door_status (dict): A mapping of door positions to their updated lock status after the operation.
            remaining_unlocked_doors (int): The count of doors that are currently in an unlocked state.
        """
        if not self.door_status:
            self.door_status = DoorStatus(driver="unlocked", passenger="unlocked", rear_left="unlocked", rear_right="unlocked")
        
        door_dict = self.door_status.model_dump()
        for pos in door_positions:
            if pos in door_dict:
                door_dict[pos] = "locked"
        
        self.door_status = DoorStatus(**door_dict)
        remaining_unlocked = sum(1 for v in door_dict.values() if v == "unlocked")
        return {
            "lock_status": "locked",
            "door_status": door_dict,
            "remaining_unlocked_doors": remaining_unlocked
        }

    def unlock_doors(self, door_positions: List[str]) -> dict:
        """
        Unlock one or more vehicle doors at specified positions.
        
        Args:
            door_positions (List[str]): List of door positions to unlock. Valid positions are driver, passenger, rear_left, and rear_right.
        
        Returns:
            lock_status (str): Confirmation that the specified doors have been unlocked.
            door_status (dict): A mapping of door positions to their updated lock status after the operation.
            remaining_unlocked_doors (int): The count of doors that are currently in an unlocked state.
        """
        if not self.door_status:
            self.door_status = DoorStatus(driver="unlocked", passenger="unlocked", rear_left="unlocked", rear_right="unlocked")
        
        door_dict = self.door_status.model_dump()
        for pos in door_positions:
            if pos in door_dict:
                door_dict[pos] = "unlocked"
        
        self.door_status = DoorStatus(**door_dict)
        remaining_unlocked = sum(1 for v in door_dict.values() if v == "unlocked")
        return {
            "lock_status": "unlocked",
            "door_status": door_dict,
            "remaining_unlocked_doors": remaining_unlocked
        }

    def get_climate_status(self) -> dict:
        """
        Retrieve the current climate control settings and environmental status inside the vehicle.
        
        Returns:
            temperature (float): The current target temperature setting for the climate control system, measured in Celsius.
            fan_speed (int): The current fan speed setting, ranging from 0 (off) to 100 (maximum).
            mode (str): The current operational mode of the climate control system.
            humidity_level (float): The current humidity level inside the vehicle cabin, expressed as a percentage.
        """
        if not self.climate_status:
            return {"temperature": 0.0, "fan_speed": 0, "mode": "auto", "humidity_level": 0.0}
        
        return {
            "temperature": self.climate_status.temperature,
            "fan_speed": self.climate_status.fan_speed,
            "mode": self.climate_status.mode,
            "humidity_level": self.climate_status.humidity_level
        }

    def set_climate_control(self, temperature: float, unit: str = "celsius", fan_speed: Optional[int] = None, mode: Optional[str] = None) -> dict:
        """
        Adjust the climate control settings of the vehicle, including temperature, fan speed, and operational mode.
        
        Args:
            temperature (float): The target temperature to set for the climate control system.
            unit [Optional] (str): The unit of measurement for the temperature. Defaults to 'celsius' if not specified.
            fan_speed [Optional] (int): The fan speed to set, ranging from 0 (off) to 100 (maximum). If not provided, the current setting is maintained.
            mode [Optional] (str): The operational mode to set for the climate control system. If not provided, the current mode is maintained.
        
        Returns:
            current_temperature (float): The current target temperature setting for the climate control system, measured in Celsius.
            climate_mode (str): The current operational mode of the climate control system.
            fan_speed (int): The current fan speed setting, ranging from 0 (off) to 100 (maximum).
            humidity_level (float): The current humidity level inside the vehicle cabin, expressed as a percentage.
        """
        temp_celsius = temperature if unit == "celsius" else (temperature - 32) * 5 / 9
        
        if not self.climate_status:
            self.climate_status = ClimateStatus(temperature=22.0, fan_speed=50, mode="auto", humidity_level=45.0)
        
        current_fan_speed = fan_speed if fan_speed is not None else self.climate_status.fan_speed
        current_mode = mode if mode is not None else self.climate_status.mode
        
        self.climate_status = ClimateStatus(
            temperature=temp_celsius,
            fan_speed=current_fan_speed,
            mode=current_mode,
            humidity_level=self.climate_status.humidity_level
        )
        
        return {
            "current_temperature": self.climate_status.temperature,
            "climate_mode": self.climate_status.mode,
            "fan_speed": self.climate_status.fan_speed,
            "humidity_level": self.climate_status.humidity_level
        }

    def get_outside_temperature(self) -> dict:
        """
        Retrieve the current outside ambient temperature from the weather service.
        
        Returns:
            outside_temperature (float): The current ambient temperature outside the vehicle, measured in Celsius.
        """
        return {"outside_temperature": self.outside_temperature}

    def get_headlight_status(self) -> dict:
        """
        Retrieve the current operational status of the vehicle headlights.
        
        Returns:
            headlight_status (str): The current operational mode of the vehicle headlights.
        """
        return {"headlight_status": self.headlight_status}

    def set_headlights(self, mode: str) -> dict:
        """
        Set the operational mode of the vehicle headlights.
        
        Args:
            mode (str): The operational mode to set for the vehicle headlights. Options are on (always on), off (always off), or auto (automatic based on ambient light).
        
        Returns:
            headlight_status (str): The current operational mode of the vehicle headlights.
        """
        self.headlight_status = mode
        return {"headlight_status": self.headlight_status}

    def get_brake_status(self) -> dict:
        """
        Retrieve the current status of both the parking brake and brake pedal, including engagement state and applied force.
        
        Returns:
            parking_brake_status (str): The current engagement state of the parking brake.
            parking_brake_force (float): The current force applied by the parking brake, measured in Newtons.
            slope_angle (float): The current angle of the vehicle's slope or incline, measured in degrees.
            brake_pedal_status (str): The current state of the brake pedal indicating whether it is pressed or released.
            brake_pedal_force (float): The current force applied to the brake pedal, measured in Newtons.
        """
        return {
            "parking_brake_status": self.parking_brake_status,
            "parking_brake_force": self.parking_brake_force,
            "slope_angle": self.slope_angle,
            "brake_pedal_status": self.brake_pedal_status,
            "brake_pedal_force": self.brake_pedal_force
        }

    def set_parking_brake(self, action: str) -> dict:
        """
        Engage or release the parking brake.
        
        Args:
            action (str): The action to perform on the parking brake. Use 'engage' to activate or 'release' to deactivate.
        
        Returns:
            parking_brake_status (str): The current engagement state of the parking brake.
            parking_brake_force (float): The current force applied by the parking brake, measured in Newtons.
            slope_angle (float): The current angle of the vehicle's slope or incline, measured in degrees.
        """
        if action == "engage":
            self.parking_brake_status = "engaged"
            self.parking_brake_force = 5000.0
        else:
            self.parking_brake_status = "released"
            self.parking_brake_force = 0.0
        
        return {
            "parking_brake_status": self.parking_brake_status,
            "parking_brake_force": self.parking_brake_force,
            "slope_angle": self.slope_angle
        }

    def press_brake_pedal(self, pedal_position: float) -> dict:
        """
        Press the brake pedal to a specified position. The pedal will remain at this position until explicitly released.
        
        Args:
            pedal_position (float): The position to press the brake pedal to, ranging from 0 (not pressed) to 1 (fully pressed).
        
        Returns:
            brake_pedal_status (str): The current state of the brake pedal indicating whether it is pressed or released.
            brake_pedal_force (float): The current force applied to the brake pedal, measured in Newtons.
            error (str): Error message if the pedal position is invalid (not between 0 and 1).
        """
        if pedal_position < 0 or pedal_position > 1:
            return {
                "brake_pedal_status": self.brake_pedal_status,
                "brake_pedal_force": self.brake_pedal_force,
                "error": "Pedal position must be between 0 and 1"
            }
        
        self.brake_pedal_status = "pressed"
        self.brake_pedal_force = pedal_position * 3000.0
        
        return {
            "brake_pedal_status": self.brake_pedal_status,
            "brake_pedal_force": self.brake_pedal_force
        }

    def release_brake_pedal(self) -> dict:
        """
        Release the brake pedal completely, returning it to the unpressed position.
        
        Returns:
            brake_pedal_status (str): The current state of the brake pedal indicating whether it is pressed or released.
            brake_pedal_force (float): The current force applied to the brake pedal, measured in Newtons. Should be 0.0 when released.
        """
        self.brake_pedal_status = "released"
        self.brake_pedal_force = 0.0
        return {
            "brake_pedal_status": self.brake_pedal_status,
            "brake_pedal_force": self.brake_pedal_force
        }

    def get_cruise_status(self) -> dict:
        """
        Retrieve the current status of the cruise control system, including activation state and target speed.
        
        Returns:
            cruise_status (str): The current activation state of the cruise control system.
            current_speed (float): The current speed of the vehicle, measured in kilometers per hour (km/h).
            distance_to_next_vehicle (float): The distance to the next vehicle ahead, measured in meters.
        """
        return {
            "cruise_status": self.cruise_status,
            "current_speed": self.current_speed,
            "distance_to_next_vehicle": self.distance_to_next_vehicle
        }

    def set_cruise_control(self, speed: float, activate: bool, distance_to_next_vehicle: Optional[float] = None) -> dict:
        """
        Activate or deactivate cruise control with a specified target speed. The engine must be running to activate cruise control.
        
        Args:
            speed (float): The target speed to set for cruise control, measured in kilometers per hour (km/h). Must be between 0 and 120 and a multiple of 5 when activating.
            activate (bool): Set to true to activate cruise control, or false to deactivate it.
            distance_to_next_vehicle [Optional] (float): The distance to maintain from the next vehicle ahead, measured in meters. Required when activating cruise control.
        
        Returns:
            cruise_status (str): The current activation state of the cruise control system.
            current_speed (float): The current speed of the vehicle, measured in kilometers per hour (km/h).
            distance_to_next_vehicle (float): The distance to the next vehicle ahead, measured in meters.
            error (str): Error message if the engine is stopped or the speed is invalid (not between 0-120 or not a multiple of 5).
        """
        result = {
            "cruise_status": self.cruise_status,
            "current_speed": self.current_speed,
            "distance_to_next_vehicle": self.distance_to_next_vehicle
        }
        
        if activate:
            if self.engine_state != "running":
                result["error"] = "Engine must be running to activate cruise control"
                return result
            if speed < 0 or speed > 120:
                result["error"] = "Speed must be between 0 and 120 km/h"
                return result
            if speed % 5 != 0:
                result["error"] = "Speed must be a multiple of 5 when activating cruise control"
                return result
            if distance_to_next_vehicle is None:
                result["error"] = "Distance to next vehicle is required when activating cruise control"
                return result
            
            self.cruise_status = "active"
            self.current_speed = speed
            self.distance_to_next_vehicle = distance_to_next_vehicle
        else:
            self.cruise_status = "inactive"
        
        result["cruise_status"] = self.cruise_status
        result["current_speed"] = self.current_speed
        result["distance_to_next_vehicle"] = self.distance_to_next_vehicle
        return result

    def get_current_speed(self) -> dict:
        """
        Retrieve the current speed of the vehicle.
        
        Returns:
            current_speed (float): The current speed of the vehicle in kilometers per hour.
        """
        return {"current_speed": self.current_speed}

    def get_tire_pressure(self, tire_position: Optional[str] = None) -> dict:
        """
        Retrieve the tire pressure for a specific tire or all tires, along with health status.
        
        Args:
            tire_position [Optional] (str): The specific tire position to query. If not provided, returns pressure for all tires.
        
        Returns:
            tire_pressure (dict): A mapping of tire positions to their current pressure values, measured in PSI.
            healthy_tire_pressure (bool): Indicates whether all tires are within the healthy pressure range (30-35 PSI average).
        """
        if not self.tire_pressure:
            return {"tire_pressure": {}, "healthy_tire_pressure": False}
        
        tire_dict = self.tire_pressure.model_dump()
        if tire_position:
            if tire_position in tire_dict:
                pressure = tire_dict[tire_position]
                healthy = 30 <= pressure <= 35
                return {
                    "tire_pressure": {tire_position: pressure},
                    "healthy_tire_pressure": healthy
                }
            else:
                return {"tire_pressure": {}, "healthy_tire_pressure": False}
        
        avg_pressure = sum(tire_dict.values()) / len(tire_dict) if tire_dict else 0
        healthy = 30 <= avg_pressure <= 35
        return {
            "tire_pressure": tire_dict,
            "healthy_tire_pressure": healthy
        }

    def check_tire_pressure(self) -> dict:
        """
        Check the pressure of all tires and determine if maintenance is needed based on healthy pressure ranges.
        
        Returns:
            front_left_tire_pressure (float): The current pressure of the front left tire, measured in PSI.
            front_right_tire_pressure (float): The current pressure of the front right tire, measured in PSI.
            rear_left_tire_pressure (float): The current pressure of the rear left tire, measured in PSI.
            rear_right_tire_pressure (float): The current pressure of the rear right tire, measured in PSI.
            healthy_tire_pressure (bool): Indicates whether all tires are within the healthy pressure range (30-35 PSI average).
        """
        if not self.tire_pressure:
            return {
                "front_left_tire_pressure": 0.0,
                "front_right_tire_pressure": 0.0,
                "rear_left_tire_pressure": 0.0,
                "rear_right_tire_pressure": 0.0,
                "healthy_tire_pressure": False
            }
        
        tire_dict = self.tire_pressure.model_dump()
        pressures = [
            tire_dict.get("front_left", 0.0),
            tire_dict.get("front_right", 0.0),
            tire_dict.get("rear_left", 0.0),
            tire_dict.get("rear_right", 0.0)
        ]
        healthy = all(30 <= p <= 35 for p in pressures)
        
        return {
            "front_left_tire_pressure": pressures[0],
            "front_right_tire_pressure": pressures[1],
            "rear_left_tire_pressure": pressures[2],
            "rear_right_tire_pressure": pressures[3],
            "healthy_tire_pressure": healthy
        }

    def find_nearest_tire_shop(self) -> dict:
        """
        Locate the nearest tire shop for maintenance or repair services.
        
        Returns:
            shop_location (str): The address of the nearest tire shop available for maintenance services.
        """
        if not self.cityZipMap:
            return {"shop_location": "No tire shop found"}
        
        first_zipcode = list(self.cityZipMap.values())[0] if self.cityZipMap else None
        if first_zipcode and first_zipcode in self.shopLocationsMap:
            return {"shop_location": self.shopLocationsMap[first_zipcode]}
        
        return {"shop_location": "No tire shop found"}

    def get_navigation_status(self) -> dict:
        """
        Retrieve the current navigation destination and activation status.
        
        Returns:
            destination (str): The current destination address set in the navigation system.
            navigation_status (str): Indicates whether the navigation system is currently active and providing directions.
        """
        status = "active" if self.navigation_active else "inactive"
        return {
            "destination": self.navigation_destination,
            "navigation_status": status
        }

    def set_navigation_destination(self, destination: str) -> dict:
        """
        Set a destination address for the navigation system and activate navigation guidance.
        
        Args:
            destination (str): The destination address to navigate to, in the format 'street, city, state' or similar standard address format.
        
        Returns:
            destination (str): The current destination address set in the navigation system.
            navigation_status (str): Indicates whether the navigation system is currently active and providing directions.
        """
        self.navigation_destination = destination
        self.navigation_active = True
        return {
            "destination": self.navigation_destination,
            "navigation_status": "active"
        }

    def convert_liter_to_gallon(self, liters: float) -> dict:
        """
        Convert a volume measurement from liters to gallons.
        
        Args:
            liters (float): The volume in liters to convert to gallons.
        
        Returns:
            gallons (float): The converted volume measurement in gallons.
        """
        gallons = liters * 0.264172
        return {"gallons": gallons}

    def convert_gallon_to_liter(self, gallons: float) -> dict:
        """
        Convert a volume measurement from gallons to liters.
        
        Args:
            gallons (float): The volume in gallons to convert to liters.
        
        Returns:
            liters (float): The converted volume measurement in liters.
        """
        liters = gallons * 3.78541
        return {"liters": liters}

    def get_city_zipcode(self, city_name: str) -> dict:
        """
        Retrieve the zipcode for a specified city name. Returns '00000' if the city is not found in the database.
        
        Args:
            city_name (str): The name of the city for which to retrieve the zipcode.
        
        Returns:
            city_zipcode (str): The zipcode of the specified city.
        """
        zipcode = self.cityZipMap.get(city_name, "00000")
        return {"city_zipcode": zipcode}

    def estimate_distance_between_cities(self, city_a_zipcode: str, city_b_zipcode: str) -> dict:
        """
        Estimate the driving distance between two cities using their zipcodes, including intermediary cities along the route.
        
        Args:
            city_a_zipcode (str): The zipcode of the first city.
            city_b_zipcode (str): The zipcode of the second city.
        
        Returns:
            distance (float): The estimated driving distance between the two cities, measured in kilometers.
            intermediary_cities (List[str]): Optional list of cities along the route between the two specified cities.
            error (str): Error message if the distance is not found in the database for the specified zipcodes.
        """
        distance = self.distanceMap.get(city_a_zipcode, {}).get(city_b_zipcode, 0.0)
        if distance == 0.0:
            return {
                "distance": 0.0,
                "intermediary_cities": [],
                "error": f"Distance not found between zipcodes {city_a_zipcode} and {city_b_zipcode}"
            }
        return {
            "distance": distance,
            "intermediary_cities": []
        }

# ---------- Section 3: MCP Tools ----------
mcp = FastMCP(name="VehicleControl")
api = VehicleControl()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the vehicle control instance.
    
    Args:
        scenario (dict): Scenario dictionary matching VehicleScenario schema.
    
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
    Save current vehicle state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_engine_status() -> dict:
    """
    Retrieve the current operational status of the vehicle engine, including running state, fuel level, and battery voltage.
    
    Returns:
        engine_state (str): The current operational state of the vehicle engine.
        fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
        battery_voltage (float): The current electrical voltage of the vehicle battery, measured in volts.
    """
    try:
        return api.get_engine_status()
    except Exception as e:
        raise e

@mcp.tool()
def start_engine() -> dict:
    """
    Start the vehicle engine. This operation requires all doors to be locked and the brake pedal to be fully pressed as safety prerequisites.
    
    Returns:
        engine_state (str): The current operational state of the vehicle engine.
        fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
        battery_voltage (float): The current electrical voltage of the vehicle battery, measured in volts.
        error (str): Error message if prerequisites (locked doors and pressed brake pedal) are not met.
    """
    try:
        return api.start_engine()
    except Exception as e:
        raise e

@mcp.tool()
def stop_engine() -> dict:
    """
    Stop the vehicle engine and transition it to a stopped state.
    
    Returns:
        engine_state (str): The current operational state of the vehicle engine.
        fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
        battery_voltage (float): The current electrical voltage of the vehicle battery, measured in volts.
    """
    try:
        return api.stop_engine()
    except Exception as e:
        raise e

@mcp.tool()
def get_fuel_level() -> dict:
    """
    Retrieve the current fuel level in the vehicle tank.
    
    Returns:
        fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons (range: 0-50).
    """
    try:
        return api.get_fuel_level()
    except Exception as e:
        raise e

@mcp.tool()
def fill_fuel_tank(fuel_amount: float) -> dict:
    """
    Add a specified amount of fuel to the vehicle tank. The tank has a maximum capacity of 50 gallons.
    
    Args:
        fuel_amount (float): The amount of fuel to add to the tank, measured in gallons. Must be positive and the total fuel level must not exceed 50 gallons.
    
    Returns:
        fuel_level (float): The current amount of fuel in the vehicle tank after filling, measured in gallons.
        error (str): Error message if the fuel amount is invalid or would exceed the 50-gallon tank capacity.
    """
    try:
        if not isinstance(fuel_amount, (int, float)):
            raise ValueError("Fuel amount must be a number")
        if fuel_amount <= 0:
            raise ValueError("Fuel amount must be positive")
        return api.fill_fuel_tank(fuel_amount)
    except Exception as e:
        raise e

@mcp.tool()
def estimate_drive_feasibility(distance: float, unit: Optional[str] = None) -> dict:
    """
    Estimate whether the vehicle has sufficient fuel to complete a specified distance based on current fuel level and fuel efficiency.
    
    Args:
        distance (float): The distance to travel for which feasibility is being estimated.
        unit [Optional] (str): The unit of measurement for the distance. Defaults to 'miles' if not specified.
    
    Returns:
        can_drive (bool): Indicates whether the vehicle has sufficient fuel to complete the specified distance.
        current_fuel_level (float): The current amount of fuel in the vehicle tank, measured in gallons.
        estimated_range (float): The estimated maximum distance the vehicle can travel with current fuel, measured in the specified unit.
    """
    try:
        if not isinstance(distance, (int, float)):
            raise ValueError("Distance must be a number")
        if distance < 0:
            raise ValueError("Distance must be non-negative")
        unit = unit if unit is not None else "miles"
        return api.estimate_drive_feasibility(distance, unit)
    except Exception as e:
        raise e

@mcp.tool()
def get_door_status(door_position: Optional[str] = None) -> dict:
    """
    Retrieve the lock status of vehicle doors, either for a specific door or all doors.
    
    Args:
        door_position [Optional] (str): The specific door position to query. If not provided, returns status for all doors.
    
    Returns:
        door_status (dict): A mapping of door positions to their current lock status (locked or unlocked).
        remaining_unlocked_doors (int): The count of doors that are currently in an unlocked state.
    """
    try:
        if door_position is not None and not isinstance(door_position, str):
            raise ValueError("Door position must be a string")
        return api.get_door_status(door_position)
    except Exception as e:
        raise e

@mcp.tool()
def lock_doors(door_positions: List[str]) -> dict:
    """
    Lock one or more vehicle doors at specified positions.
    
    Args:
        door_positions (List[str]): List of door positions to lock. Valid positions are driver, passenger, rear_left, and rear_right.
    
    Returns:
        lock_status (str): Confirmation that the specified doors have been locked.
        door_status (dict): A mapping of door positions to their updated lock status after the operation.
        remaining_unlocked_doors (int): The count of doors that are currently in an unlocked state.
    """
    try:
        if not isinstance(door_positions, list):
            raise ValueError("Door positions must be a list")
        if not door_positions:
            raise ValueError("Door positions list cannot be empty")
        return api.lock_doors(door_positions)
    except Exception as e:
        raise e

@mcp.tool()
def unlock_doors(door_positions: List[str]) -> dict:
    """
    Unlock one or more vehicle doors at specified positions.
    
    Args:
        door_positions (List[str]): List of door positions to unlock. Valid positions are driver, passenger, rear_left, and rear_right.
    
    Returns:
        lock_status (str): Confirmation that the specified doors have been unlocked.
        door_status (dict): A mapping of door positions to their updated lock status after the operation.
        remaining_unlocked_doors (int): The count of doors that are currently in an unlocked state.
    """
    try:
        if not isinstance(door_positions, list):
            raise ValueError("Door positions must be a list")
        if not door_positions:
            raise ValueError("Door positions list cannot be empty")
        return api.unlock_doors(door_positions)
    except Exception as e:
        raise e

@mcp.tool()
def get_climate_status() -> dict:
    """
    Retrieve the current climate control settings and environmental status inside the vehicle.
    
    Returns:
        temperature (float): The current target temperature setting for the climate control system, measured in Celsius.
        fan_speed (int): The current fan speed setting, ranging from 0 (off) to 100 (maximum).
        mode (str): The current operational mode of the climate control system.
        humidity_level (float): The current humidity level inside the vehicle cabin, expressed as a percentage.
    """
    try:
        return api.get_climate_status()
    except Exception as e:
        raise e

@mcp.tool()
def set_climate_control(temperature: float, unit: Optional[str] = None, fan_speed: Optional[int] = None, mode: Optional[str] = None) -> dict:
    """
    Adjust the climate control settings of the vehicle, including temperature, fan speed, and operational mode.
    
    Args:
        temperature (float): The target temperature to set for the climate control system.
        unit [Optional] (str): The unit of measurement for the temperature. Defaults to 'celsius' if not specified.
        fan_speed [Optional] (int): The fan speed to set, ranging from 0 (off) to 100 (maximum). If not provided, the current setting is maintained.
        mode [Optional] (str): The operational mode to set for the climate control system. If not provided, the current mode is maintained.
    
    Returns:
        current_temperature (float): The current target temperature setting for the climate control system, measured in Celsius.
        climate_mode (str): The current operational mode of the climate control system.
        fan_speed (int): The current fan speed setting, ranging from 0 (off) to 100 (maximum).
        humidity_level (float): The current humidity level inside the vehicle cabin, expressed as a percentage.
    """
    try:
        if not isinstance(temperature, (int, float)):
            raise ValueError("Temperature must be a number")
        unit = unit if unit is not None else "celsius"
        if fan_speed is not None:
            if not isinstance(fan_speed, int):
                raise ValueError("Fan speed must be an integer")
            if fan_speed < 0 or fan_speed > 100:
                raise ValueError("Fan speed must be between 0 and 100")
        return api.set_climate_control(temperature, unit, fan_speed, mode)
    except Exception as e:
        raise e

@mcp.tool()
def get_outside_temperature() -> dict:
    """
    Retrieve the current outside ambient temperature from the weather service.
    
    Returns:
        outside_temperature (float): The current ambient temperature outside the vehicle, measured in Celsius.
    """
    try:
        return api.get_outside_temperature()
    except Exception as e:
        raise e

@mcp.tool()
def get_headlight_status() -> dict:
    """
    Retrieve the current operational status of the vehicle headlights.
    
    Returns:
        headlight_status (str): The current operational mode of the vehicle headlights.
    """
    try:
        return api.get_headlight_status()
    except Exception as e:
        raise e

@mcp.tool()
def set_headlights(mode: str) -> dict:
    """
    Set the operational mode of the vehicle headlights.
    
    Args:
        mode (str): The operational mode to set for the vehicle headlights. Options are on (always on), off (always off), or auto (automatic based on ambient light).
    
    Returns:
        headlight_status (str): The current operational mode of the vehicle headlights.
    """
    try:
        if not isinstance(mode, str):
            raise ValueError("Mode must be a string")
        if mode not in ["on", "off", "auto"]:
            raise ValueError("Mode must be 'on', 'off', or 'auto'")
        return api.set_headlights(mode)
    except Exception as e:
        raise e

@mcp.tool()
def get_brake_status() -> dict:
    """
    Retrieve the current status of both the parking brake and brake pedal, including engagement state and applied force.
    
    Returns:
        parking_brake_status (str): The current engagement state of the parking brake.
        parking_brake_force (float): The current force applied by the parking brake, measured in Newtons.
        slope_angle (float): The current angle of the vehicle's slope or incline, measured in degrees.
        brake_pedal_status (str): The current state of the brake pedal indicating whether it is pressed or released.
        brake_pedal_force (float): The current force applied to the brake pedal, measured in Newtons.
    """
    try:
        return api.get_brake_status()
    except Exception as e:
        raise e

@mcp.tool()
def set_parking_brake(action: str) -> dict:
    """
    Engage or release the parking brake.
    
    Args:
        action (str): The action to perform on the parking brake. Use 'engage' to activate or 'release' to deactivate.
    
    Returns:
        parking_brake_status (str): The current engagement state of the parking brake.
        parking_brake_force (float): The current force applied by the parking brake, measured in Newtons.
        slope_angle (float): The current angle of the vehicle's slope or incline, measured in degrees.
    """
    try:
        if not isinstance(action, str):
            raise ValueError("Action must be a string")
        if action not in ["engage", "release"]:
            raise ValueError("Action must be 'engage' or 'release'")
        return api.set_parking_brake(action)
    except Exception as e:
        raise e

@mcp.tool()
def press_brake_pedal(pedal_position: float) -> dict:
    """
    Press the brake pedal to a specified position. The pedal will remain at this position until explicitly released.
    
    Args:
        pedal_position (float): The position to press the brake pedal to, ranging from 0 (not pressed) to 1 (fully pressed).
    
    Returns:
        brake_pedal_status (str): The current state of the brake pedal indicating whether it is pressed or released.
        brake_pedal_force (float): The current force applied to the brake pedal, measured in Newtons.
        error (str): Error message if the pedal position is invalid (not between 0 and 1).
    """
    try:
        if not isinstance(pedal_position, (int, float)):
            raise ValueError("Pedal position must be a number")
        return api.press_brake_pedal(pedal_position)
    except Exception as e:
        raise e

@mcp.tool()
def release_brake_pedal() -> dict:
    """
    Release the brake pedal completely, returning it to the unpressed position.
    
    Returns:
        brake_pedal_status (str): The current state of the brake pedal indicating whether it is pressed or released.
        brake_pedal_force (float): The current force applied to the brake pedal, measured in Newtons. Should be 0.0 when released.
    """
    try:
        return api.release_brake_pedal()
    except Exception as e:
        raise e

@mcp.tool()
def get_cruise_status() -> dict:
    """
    Retrieve the current status of the cruise control system, including activation state and target speed.
    
    Returns:
        cruise_status (str): The current activation state of the cruise control system.
        current_speed (float): The current speed of the vehicle, measured in kilometers per hour (km/h).
        distance_to_next_vehicle (float): The distance to the next vehicle ahead, measured in meters.
    """
    try:
        return api.get_cruise_status()
    except Exception as e:
        raise e

@mcp.tool()
def set_cruise_control(speed: float, activate: bool, distance_to_next_vehicle: Optional[float] = None) -> dict:
    """
    Activate or deactivate cruise control with a specified target speed. The engine must be running to activate cruise control.
    
    Args:
        speed (float): The target speed to set for cruise control, measured in kilometers per hour (km/h). Must be between 0 and 120 and a multiple of 5 when activating.
        activate (bool): Set to true to activate cruise control, or false to deactivate it.
        distance_to_next_vehicle [Optional] (float): The distance to maintain from the next vehicle ahead, measured in meters. Required when activating cruise control.
    
    Returns:
        cruise_status (str): The current activation state of the cruise control system.
        current_speed (float): The current speed of the vehicle, measured in kilometers per hour (km/h).
        distance_to_next_vehicle (float): The distance to the next vehicle ahead, measured in meters.
        error (str): Error message if the engine is stopped or the speed is invalid (not between 0-120 or not a multiple of 5).
    """
    try:
        if not isinstance(speed, (int, float)):
            raise ValueError("Speed must be a number")
        if not isinstance(activate, bool):
            raise ValueError("Activate must be a boolean")
        return api.set_cruise_control(speed, activate, distance_to_next_vehicle)
    except Exception as e:
        raise e

@mcp.tool()
def get_current_speed() -> dict:
    """
    Retrieve the current speed of the vehicle.
    
    Returns:
        current_speed (float): The current speed of the vehicle in kilometers per hour.
    """
    try:
        return api.get_current_speed()
    except Exception as e:
        raise e

@mcp.tool()
def get_tire_pressure(tire_position: Optional[str] = None) -> dict:
    """
    Retrieve the tire pressure for a specific tire or all tires, along with health status.
    
    Args:
        tire_position [Optional] (str): The specific tire position to query. If not provided, returns pressure for all tires.
    
    Returns:
        tire_pressure (dict): A mapping of tire positions to their current pressure values, measured in PSI.
        healthy_tire_pressure (bool): Indicates whether all tires are within the healthy pressure range (30-35 PSI average).
    """
    try:
        if tire_position is not None and not isinstance(tire_position, str):
            raise ValueError("Tire position must be a string")
        return api.get_tire_pressure(tire_position)
    except Exception as e:
        raise e

@mcp.tool()
def check_tire_pressure() -> dict:
    """
    Check the pressure of all tires and determine if maintenance is needed based on healthy pressure ranges.
    
    Returns:
        front_left_tire_pressure (float): The current pressure of the front left tire, measured in PSI.
        front_right_tire_pressure (float): The current pressure of the front right tire, measured in PSI.
        rear_left_tire_pressure (float): The current pressure of the rear left tire, measured in PSI.
        rear_right_tire_pressure (float): The current pressure of the rear right tire, measured in PSI.
        healthy_tire_pressure (bool): Indicates whether all tires are within the healthy pressure range (30-35 PSI average).
    """
    try:
        return api.check_tire_pressure()
    except Exception as e:
        raise e

@mcp.tool()
def find_nearest_tire_shop() -> dict:
    """
    Locate the nearest tire shop for maintenance or repair services.
    
    Returns:
        shop_location (str): The address of the nearest tire shop available for maintenance services.
    """
    try:
        return api.find_nearest_tire_shop()
    except Exception as e:
        raise e

@mcp.tool()
def get_navigation_status() -> dict:
    """
    Retrieve the current navigation destination and activation status.
    
    Returns:
        destination (str): The current destination address set in the navigation system.
        navigation_status (str): Indicates whether the navigation system is currently active and providing directions.
    """
    try:
        return api.get_navigation_status()
    except Exception as e:
        raise e

@mcp.tool()
def set_navigation_destination(destination: str) -> dict:
    """
    Set a destination address for the navigation system and activate navigation guidance.
    
    Args:
        destination (str): The destination address to navigate to, in the format 'street, city, state' or similar standard address format.
    
    Returns:
        destination (str): The current destination address set in the navigation system.
        navigation_status (str): Indicates whether the navigation system is currently active and providing directions.
    """
    try:
        if not isinstance(destination, str):
            raise ValueError("Destination must be a string")
        if not destination:
            raise ValueError("Destination cannot be empty")
        return api.set_navigation_destination(destination)
    except Exception as e:
        raise e

@mcp.tool()
def convert_liter_to_gallon(liters: float) -> dict:
    """
    Convert a volume measurement from liters to gallons.
    
    Args:
        liters (float): The volume in liters to convert to gallons.
    
    Returns:
        gallons (float): The converted volume measurement in gallons.
    """
    try:
        if not isinstance(liters, (int, float)):
            raise ValueError("Liters must be a number")
        if liters < 0:
            raise ValueError("Liters must be non-negative")
        return api.convert_liter_to_gallon(liters)
    except Exception as e:
        raise e

@mcp.tool()
def convert_gallon_to_liter(gallons: float) -> dict:
    """
    Convert a volume measurement from gallons to liters.
    
    Args:
        gallons (float): The volume in gallons to convert to liters.
    
    Returns:
        liters (float): The converted volume measurement in liters.
    """
    try:
        if not isinstance(gallons, (int, float)):
            raise ValueError("Gallons must be a number")
        if gallons < 0:
            raise ValueError("Gallons must be non-negative")
        return api.convert_gallon_to_liter(gallons)
    except Exception as e:
        raise e

@mcp.tool()
def get_city_zipcode(city_name: str) -> dict:
    """
    Retrieve the zipcode for a specified city name. Returns '00000' if the city is not found in the database.
    
    Args:
        city_name (str): The name of the city for which to retrieve the zipcode.
    
    Returns:
        city_zipcode (str): The zipcode of the specified city.
    """
    try:
        if not isinstance(city_name, str):
            raise ValueError("City name must be a string")
        if not city_name:
            raise ValueError("City name cannot be empty")
        return api.get_city_zipcode(city_name)
    except Exception as e:
        raise e

@mcp.tool()
def estimate_distance_between_cities(city_a_zipcode: str, city_b_zipcode: str) -> dict:
    """
    Estimate the driving distance between two cities using their zipcodes, including intermediary cities along the route.
    
    Args:
        city_a_zipcode (str): The zipcode of the first city.
        city_b_zipcode (str): The zipcode of the second city.
    
    Returns:
        distance (float): The estimated driving distance between the two cities, measured in kilometers.
        intermediary_cities (List[str]): Optional list of cities along the route between the two specified cities.
        error (str): Error message if the distance is not found in the database for the specified zipcodes.
    """
    try:
        if not isinstance(city_a_zipcode, str):
            raise ValueError("City A zipcode must be a string")
        if not isinstance(city_b_zipcode, str):
            raise ValueError("City B zipcode must be a string")
        if not city_a_zipcode:
            raise ValueError("City A zipcode cannot be empty")
        if not city_b_zipcode:
            raise ValueError("City B zipcode cannot be empty")
        return api.estimate_distance_between_cities(city_a_zipcode, city_b_zipcode)
    except Exception as e:
        raise e

# ---------- Section 4: Entry Point ----------
if __name__ == "__main__":
    mcp.run()