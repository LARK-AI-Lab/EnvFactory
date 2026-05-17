# Data Source: https://resideline.com/resideline-api
# Server: Resideline
# Category: real_estate

def get_property_details(address: str) -> dict:
    """
    Get basic property information.
    
    Args:
        address (str): Full property address including city, state, ZIP
        
    Returns:
        dict: {
            "address": str,
            "latitude": float,
            "longitude": float,
            "bedrooms": int,
            "bathrooms": int,
            "sqft": int,
            "year_built": str,
            "property_type": str,
            "images": list
        }
    """
    pass

def get_property_report(address: str) -> dict:
    """
    Get full property valuation report with comparables.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "estimated_value": float,
            "value_range_low": float,
            "value_range_high": float,
            "confidence_score": float,
            "comparables": [
                {
                    "address": str,
                    "sale_price": float,
                    "sale_date": str,
                    "similarity_score": float
                }
            ]
        }
    """
    pass

def get_rental_analysis(address: str) -> dict:
    """
    Get rental market analysis for a property.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "estimated_monthly_rent": float,
            "rent_range_low": float,
            "rent_range_high": float,
            "rental_comps": [
                {
                    "address": str,
                    "monthly_rent": float,
                    "distance_miles": float
                }
            ]
        }
    """
    pass

def get_quick_valuation(address: str) -> dict:
    """
    Get quick property valuation estimate.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "estimated_value": float,
            "valuation_date": str,
            "price_per_sqft": float
        }
    """
    pass

def get_short_term_rental_analysis(address: str) -> dict:
    """
    Get short-term rental (Airbnb) analysis for a property.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "estimated_nightly_rate": float,
            "estimated_monthly_revenue": float,
            "occupancy_rate": float,
            "seasonal_trends": dict
        }
    """
    pass
