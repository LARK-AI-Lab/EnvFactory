# Server: VehicleControl

def get_engine_status() -> dict:
    """
    Get the current engine status.
    
    Returns:
        dict: A dictionary containing engine_state (str) [Enum]: ["running", "stopped"], fuel_level (float) in gallons, battery_voltage (float) in volts.
    """
    pass

def start_engine() -> dict:
    """
    Start the vehicle engine. Requires all doors to be locked and brake pedal to be fully pressed.
    
    Returns:
        dict: A dictionary containing engine_state (str) [Enum]: ["running", "stopped"], fuel_level (float) in gallons, battery_voltage (float) in volts. Returns error message if prerequisites are not met.
    """
    pass

def stop_engine() -> dict:
    """
    Stop the vehicle engine.
    
    Returns:
        dict: A dictionary containing engine_state (str) [Enum]: ["stopped"], fuel_level (float) in gallons, battery_voltage (float) in volts.
    """
    pass

def get_fuel_level() -> dict:
    """
    Get the current fuel level in the tank.
    
    Returns:
        dict: A dictionary containing fuel_level (float) in gallons (0-50).
    """
    pass

def fill_fuel_tank(fuel_amount: float) -> dict:
    """
    Fill the fuel tank with the specified amount of fuel. The tank capacity is 50 gallons.
    
    Args:
        fuel_amount (float): The amount of fuel to add in gallons. Must be positive and the total should not exceed 50 gallons.
        
    Returns:
        dict: A dictionary containing fuel_level (float) in gallons after filling. Returns error message if the amount is invalid or exceeds capacity.
    """
    pass

def estimate_drive_feasibility(distance: float, unit: str = "miles") -> dict:
    """
    Estimate whether the vehicle can drive the specified distance based on current fuel level.
    
    Args:
        distance (float): The distance to travel
        unit (str): [Optional] The unit of distance. [Enum]: ["miles", "kilometers"]. Defaults to "miles".
        
    Returns:
        dict: A dictionary containing can_drive (bool) indicating if the vehicle can complete the distance, current_fuel_level (float) in gallons, estimated_range (float) in the specified unit.
    """
    pass

def get_door_status(door_position: str = None) -> dict:
    """
    Get the status of vehicle doors.
    
    Args:
        door_position (str): [Optional] The specific door to query. [Enum]: ["driver", "passenger", "rear_left", "rear_right"]. If not provided, returns status of all doors.
        
    Returns:
        dict: A dictionary containing door_status (dict) with door positions as keys and lock status [Enum]: ["locked", "unlocked"] as values, remaining_unlocked_doors (int) count.
    """
    pass

def lock_doors(door_positions: list[str]) -> dict:
    """
    Lock one or more vehicle doors.
    
    Args:
        door_positions (list[str]): List of door positions to lock. [Enum]: ["driver", "passenger", "rear_left", "rear_right"]
        
    Returns:
        dict: A dictionary containing lock_status (str) [Enum]: ["locked"], door_status (dict) with updated status, remaining_unlocked_doors (int) count.
    """
    pass

def unlock_doors(door_positions: list[str]) -> dict:
    """
    Unlock one or more vehicle doors.
    
    Args:
        door_positions (list[str]): List of door positions to unlock. [Enum]: ["driver", "passenger", "rear_left", "rear_right"]
        
    Returns:
        dict: A dictionary containing lock_status (str) [Enum]: ["unlocked"], door_status (dict) with updated status, remaining_unlocked_doors (int) count.
    """
    pass

def get_climate_status() -> dict:
    """
    Get the current climate control settings and status.
    
    Returns:
        dict: A dictionary containing temperature (float) in Celsius, fan_speed (int) from 0-100, mode (str) [Enum]: ["auto", "cool", "heat", "defrost"], humidity_level (float) as percentage.
    """
    pass

def set_climate_control(temperature: float, unit: str = "celsius", fan_speed: int = None, mode: str = None) -> dict:
    """
    Adjust the climate control settings of the vehicle.
    
    Args:
        temperature (float): The target temperature to set
        unit (str): [Optional] The unit of temperature. [Enum]: ["celsius", "fahrenheit"]. Defaults to "celsius".
        fan_speed (int): [Optional] The fan speed to set from 0 to 100. If not provided, keeps current setting.
        mode (str): [Optional] The climate mode to set. [Enum]: ["auto", "cool", "heat", "defrost"]. If not provided, keeps current setting.
        
    Returns:
        dict: A dictionary containing current_temperature (float) in Celsius, climate_mode (str), fan_speed (int), humidity_level (float) as percentage.
    """
    pass

def get_outside_temperature() -> dict:
    """
    Get the current outside temperature from weather service.
    
    Returns:
        dict: A dictionary containing outside_temperature (float) in Celsius.
    """
    pass

def get_headlight_status() -> dict:
    """
    Get the current headlight status.
    
    Returns:
        dict: A dictionary containing headlight_status (str) [Enum]: ["on", "off", "auto"].
    """
    pass

def set_headlights(mode: str) -> dict:
    """
    Set the headlight mode.
    
    Args:
        mode (str): The headlight mode to set. [Enum]: ["on", "off", "auto"]
        
    Returns:
        dict: A dictionary containing headlight_status (str) [Enum]: ["on", "off", "auto"].
    """
    pass

def get_brake_status() -> dict:
    """
    Get the current status of both parking brake and brake pedal.
    
    Returns:
        dict: A dictionary containing parking_brake_status (str) [Enum]: ["engaged", "released"], parking_brake_force (float) in Newtons, slope_angle (float) in degrees, brake_pedal_status (str) [Enum]: ["pressed", "released"], brake_pedal_force (float) in Newtons.
    """
    pass

def set_parking_brake(action: str) -> dict:
    """
    Engage or release the parking brake.
    
    Args:
        action (str): The action to perform. [Enum]: ["engage", "release"]
        
    Returns:
        dict: A dictionary containing parking_brake_status (str) [Enum]: ["engaged", "released"], parking_brake_force (float) in Newtons, slope_angle (float) in degrees.
    """
    pass

def press_brake_pedal(pedal_position: float) -> dict:
    """
    Press the brake pedal to the specified position. The pedal will remain pressed until released.
    
    Args:
        pedal_position (float): Position of the brake pedal between 0 (not pressed) and 1 (fully pressed).
        
    Returns:
        dict: A dictionary containing brake_pedal_status (str) [Enum]: ["pressed", "released"], brake_pedal_force (float) in Newtons. Returns error if position is invalid.
    """
    pass

def release_brake_pedal() -> dict:
    """
    Release the brake pedal completely.
    
    Returns:
        dict: A dictionary containing brake_pedal_status (str) [Enum]: ["released"], brake_pedal_force (float) which should be 0.0.
    """
    pass

def get_cruise_status() -> dict:
    """
    Get the current cruise control status.
    
    Returns:
        dict: A dictionary containing cruise_status (str) [Enum]: ["active", "inactive"], current_speed (float) in km/h, distance_to_next_vehicle (float) in meters.
    """
    pass

def set_cruise_control(speed: float, activate: bool, distance_to_next_vehicle: float = None) -> dict:
    """
    Set or activate/deactivate cruise control. Engine must be running to activate cruise control.
    
    Args:
        speed (float): The target speed to set in km/h. Must be between 0 and 120 and a multiple of 5 when activating.
        activate (bool): True to activate cruise control, False to deactivate.
        distance_to_next_vehicle (float): [Optional] The distance to maintain from the next vehicle in meters. Required when activating, optional when deactivating.
        
    Returns:
        dict: A dictionary containing cruise_status (str) [Enum]: ["active", "inactive"], current_speed (float) in km/h, distance_to_next_vehicle (float) in meters. Returns error if engine is stopped or speed is invalid.
    """
    pass

def get_current_speed() -> dict:
    """
    Get the current speed of the vehicle.
    
    Returns:
        dict: A dictionary containing current_speed (float) in km/h.
    """
    pass

def get_tire_pressure(tire_position: str = None) -> dict:
    """
    Get the tire pressure for one or all tires.
    
    Args:
        tire_position (str): [Optional] The specific tire to query. [Enum]: ["front_left", "front_right", "rear_left", "rear_right"]. If not provided, returns pressure for all tires.
        
    Returns:
        dict: A dictionary containing tire_pressure (dict) with tire positions as keys and pressure values (float) in PSI as values, healthy_tire_pressure (bool) indicating if all tires are within healthy range (30-35 PSI average).
    """
    pass

def check_tire_pressure() -> dict:
    """
    Check tire pressure and determine if maintenance is needed.
    
    Returns:
        dict: A dictionary containing front_left_tire_pressure (float) in PSI, front_right_tire_pressure (float) in PSI, rear_left_tire_pressure (float) in PSI, rear_right_tire_pressure (float) in PSI, healthy_tire_pressure (bool) indicating if all tires are within healthy range.
    """
    pass

def find_nearest_tire_shop() -> dict:
    """
    Find the nearest tire shop location for maintenance.
    
    Returns:
        dict: A dictionary containing shop_location (str) with the address of the nearest tire shop.
    """
    pass

def get_navigation_status() -> dict:
    """
    Get the current navigation destination and status.
    
    Returns:
        dict: A dictionary containing destination (str) with the current navigation destination, navigation_status (str) indicating if navigation is active.
    """
    pass

def set_navigation_destination(destination: str) -> dict:
    """
    Set the navigation destination.
    
    Args:
        destination (str): The destination address in the format "street, city, state" or similar address format.
        
    Returns:
        dict: A dictionary containing destination (str) with the set destination, navigation_status (str) indicating navigation has been activated.
    """
    pass

def convert_liter_to_gallon(liters: float) -> dict:
    """
    Convert volume from liters to gallons.
    
    Args:
        liters (float): The volume in liters to convert.
        
    Returns:
        dict: A dictionary containing gallons (float) with the converted volume in gallons.
    """
    pass

def convert_gallon_to_liter(gallons: float) -> dict:
    """
    Convert volume from gallons to liters.
    
    Args:
        gallons (float): The volume in gallons to convert.
        
    Returns:
        dict: A dictionary containing liters (float) with the converted volume in liters.
    """
    pass

def get_city_zipcode(city_name: str) -> dict:
    """
    Get the zipcode for a given city name.
    
    Args:
        city_name (str): The name of the city.
        
    Returns:
        dict: A dictionary containing city_zipcode (str) with the zipcode of the city. Returns "00000" if city is not found.
    """
    pass

def estimate_distance_between_cities(city_a_zipcode: str, city_b_zipcode: str) -> dict:
    """
    Estimate the driving distance between two cities using their zipcodes.
    
    Args:
        city_a_zipcode (str): The zipcode of the first city. 
        city_b_zipcode (str): The zipcode of the second city. 
        
    Returns:
        dict: A dictionary containing distance (float) in kilometers, intermediary_cities (list[str]) [Optional] list of cities along the route. Returns error if distance is not found in database.
    """
    pass
