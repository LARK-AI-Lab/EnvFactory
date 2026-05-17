# Data Source: https://api.developer.attomdata.com/docs
# Server: ATTOM
# Category: real_estate

def get_property_profile(address: str) -> dict:
    """
    Get basic property profile information.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "property_id": str,
            "fips": str,
            "apn": str,
            "address": str,
            "city": str,
            "state": str,
            "zip": str
        }
    """
    pass

def get_property_details(address: str) -> dict:
    """
    Get detailed property information including building characteristics.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "property_id": str,
            "address": str,
            "sqft": int,
            "lot_size": int,
            "bedrooms": int,
            "bathrooms": float,
            "year_built": int,
            "property_type": str,
            "stories": int,
            "garage_type": str
        }
    """
    pass

def get_property_valuation(address: str) -> dict:
    """
    Get AVM (Automated Valuation Model) for a property.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "estimated_value": float,
            "value_range_low": float,
            "value_range_high": float,
            "confidence_score": str,
            "valuation_date": str
        }
    """
    pass

def get_tax_assessment(address: str) -> dict:
    """
    Get tax assessment information for a property.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "assessed_value": float,
            "assessed_land_value": float,
            "assessed_improvement_value": float,
            "tax_amount": float,
            "tax_year": int,
            "assessment_year": int
        }
    """
    pass

def get_nearby_schools(address: str, radius: int = 5) -> dict:
    """
    Get schools near a property.
    
    Args:
        address (str): Full property address
        radius (int): [Optional] Search radius in miles (default 5)
        
    Returns:
        dict: {
            "schools": [
                {
                    "school_name": str,
                    "distance": float,
                    "school_type": str,
                    "grade_level": str,
                    "rating": float
                }
            ]
        }
    """
    pass
