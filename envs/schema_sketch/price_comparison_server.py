# Server: PriceComparison

def get_pid_pos_details(name: str) -> dict:
    """
    Get PID and POS information for a product by name.
    
    Args:
        name (str): Product name to search for
        
    Returns:
        dict: {
            "pid": str,
            "pos": int,
            "name": str
        }
    """
    pass

def compare_price(pid: str, pos: int, max_retailers: int = 10) -> dict:
    """
    Fetch price comparison details for a product across different retailers.
    
    Args:
        pid (str): Product identifier
        pos (int): Product position identifier
        max_retailers (int): Maximum number of retailers to compare (default: 10)
        
    Returns:
        dict: {
            "pid": str,
            "pos": int,
            "retailers": list of dicts with store_name, price, availability
        }
    """
    pass

def price_trend(pid: str, pos: int) -> dict:
    """
    Fetch predicted price trend data for a product to track future price changes.
    
    Args:
        pid (str): Product identifier
        pos (int): Product position identifier
        
    Returns:
        dict: {
            "pid": str,
            "pos": int,
            "price_data": list of dicts with date, predicted_price, trend
        }
    """
    pass

def get_price_history(pid: str, pos: int, retailers: list = None) -> dict:
    """
    Get historical price data for a product to track past price changes.
    
    Args:
        pid (str): Product identifier
        pos (int): Product position identifier
        retailers (list, optional): List of retailer names to filter by. If None, returns data for all retailers.
        
    Returns:
        dict: {
            "pid": str,
            "pos": int,
            "price_history": list of dicts with date, price, retailer
        }
    """
    pass

def get_discount_info(pid: str, pos: int, retailer: str, time_period: str) -> dict:
    """
    Get discount information for a product at a specific retailer within a time period.
    
    Args:
        pid (str): Product identifier
        pos (int): Product position identifier
        retailer (str): Retailer name
        time_period (str): Time period to query, one of "current", "past", "upcoming"
        
    Returns:
        dict: {
            "pid": str,
            "pos": int,
            "retailer": str,
            "discounts": list of dicts with discount_percentage, start_date, end_date, original_price, discounted_price
        }
    """
    pass

