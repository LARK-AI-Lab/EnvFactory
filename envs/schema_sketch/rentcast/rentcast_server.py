# Data Source: https://developers.rentcast.io/reference/introduction
# Server: RentCast
# Category: real_estate


def get_property_by_address(address: str) -> dict:
    """
    Get property details by address.
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "id": str,
            "address": str,
            "city": str,
            "state": str,
            "zipcode": str,
            "bedrooms": int,
            "bathrooms": float,
            "sqft": int,
            "year_built": int,
            "property_type": str,
            "owner_name": str
        }
    """
    pass


def get_property_valuation(address: str) -> dict:
    """
    Get automated property valuation (AVM).
    
    Args:
        address (str): Full property address
        
    Returns:
        dict: {
            "estimated_value": float,
            "value_range_low": float,
            "value_range_high": float,
            "confidence_score": float,
            "valuation_date": str
        }
    """
    pass


def search_sale_listings(city: str, state: str, min_price: int = None, max_price: int = None) -> dict:
    """
    Search active sale listings.
    
    Args:
        city (str): City name
        state (str): State abbreviation
        min_price (int): [Optional] Minimum listing price
        max_price (int): [Optional] Maximum listing price
        
    Returns:
        dict: {
            "listings": [
                {
                    "id": str,
                    "address": str,
                    "list_price": float,
                    "bedrooms": int,
                    "bathrooms": float,
                    "sqft": int,
                    "days_on_market": int
                }
            ]
        }
    """
    pass


def search_rental_listings(city: str, state: str, min_rent: int = None, max_rent: int = None) -> dict:
    """
    Search long-term rental listings.
    
    Args:
        city (str): City name
        state (str): State abbreviation
        min_rent (int): [Optional] Minimum monthly rent
        max_rent (int): [Optional] Maximum monthly rent
        
    Returns:
        dict: {
            "listings": [
                {
                    "id": str,
                    "address": str,
                    "monthly_rent": float,
                    "bedrooms": int,
                    "bathrooms": float,
                    "available_date": str
                }
            ]
        }
    """
    pass


def get_market_data(zip_code: str) -> dict:
    """
    Get real estate market trends for a ZIP code.
    
    Args:
        zip_code (str): ZIP code
        
    Returns:
        dict: {
            "average_sale_price": float,
            "average_rent": float,
            "price_per_sqft": float,
            "inventory_count": int,
            "days_on_market_avg": int
        }
    """
    pass
