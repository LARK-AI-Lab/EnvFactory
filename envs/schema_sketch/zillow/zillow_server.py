# Data Source: https://www.zillow.com/howto/api/APIOverview.htm
# Server: Zillow
# Category: real_estate

def get_zestimate(address: str, city_state_zip: str) -> dict:
    """
    Get Zestimate home valuation for a property.
    
    Args:
        address (str): Property street address
        city_state_zip (str): City, state and ZIP code
        
    Returns:
        dict: {
            "zestimate": float,
            "value_range_low": float,
            "value_range_high": float,
            "last_updated": str
        }
    """
    pass

def get_property_details(address: str, city_state_zip: str) -> dict:
    """
    Get detailed property information.
    
    Args:
        address (str): Property street address
        city_state_zip (str): City, state and ZIP code
        
    Returns:
        dict: {
            "zpid": str,
            "street": str,
            "city": str,
            "state": str,
            "zipcode": str,
            "bedrooms": int,
            "bathrooms": float,
            "sqft": int,
            "lot_size": int,
            "year_built": int
        }
    """
    pass

def get_comparables(zpid: str, count: int = 5) -> dict:
    """
    Get comparable properties for a given ZPID.
    
    Args:
        zpid (str): Zillow Property ID
        count (int): [Optional] Number of comparables (max 25)
        
    Returns:
        dict: {
            "comparables": [
                {
                    "zpid": str,
                    "address": str,
                    "price": float,
                    "bedrooms": int,
                    "bathrooms": float
                }
            ]
        }
    """
    pass

def search_properties(city: str, state: str, min_price: int = None, max_price: int = None) -> dict:
    """
    Search for properties by location and price range.
    
    Args:
        city (str): City name
        state (str): State abbreviation
        min_price (int): [Optional] Minimum price filter
        max_price (int): [Optional] Maximum price filter
        
    Returns:
        dict: {
            "results": [
                {
                    "zpid": str,
                    "address": str,
                    "price": float
                }
            ],
            "total_count": int
        }
    """
    pass
