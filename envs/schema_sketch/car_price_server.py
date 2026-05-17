# Server: CarPrice

def get_car_brands(limit: int = 10) -> list:
    """
    Get all available car brands from FIPE API.
    
    Args:
        limit (int): [Optional] Maximum number of results to return, default is 10.
    
    Returns:
        list: Each brand contains {
            "brand_code": int,
            "brand_name": str
        }
    """
    pass

def search_car_price(brand_name: str) -> list:
    """
    Search for car models and prices by brand name.
    
    Args:
        brand_name (str): Car brand name to search for (e.g., "Toyota", "Honda", "Ford")
        
    Returns:
        list: Each vehicle contains {
            "model_name": str,
            "production_year": int,
            "fuel_type": str,
            "current_price": float,
            "fipe_code": str
        }
    """
    pass

def get_vehicles_by_type(vehicle_type: str) -> list:
    """
    Get vehicles by type.
    
    Args:
        vehicle_type (str): Type of vehicles ("carros"/"cars", "motos"/"motorcycles", "caminhoes"/"trucks")

    Returns:
        list: Each brand contains {
            "brand_code": int,
            "brand_name": str
        }
    """
    pass

