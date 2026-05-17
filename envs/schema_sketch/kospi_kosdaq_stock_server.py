# Server: KospiKosdaqStock

def get_stock_ohlcv(
    fromdate: str, 
    todate: str, 
    ticker: str, 
    adjusted: bool = True
) -> dict:
    """
    Retrieve OHLCV (Open/High/Low/Close/Volume) data for a specific stock.
    
    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate (str): End date for retrieval (YYYYMMDD)
        ticker (str): Stock ticker symbol
        adjusted (bool): [Optional] Whether to use adjusted prices (True: adjusted, False: unadjusted)
        
    Returns:
        dict: {
            "ticker": str,
            "data": list[dict] - Each record contains {
                "date": str (YYYYMMDD),
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": int
            }
        }
    """
    pass

def get_stock_market_cap(
    fromdate: str, 
    todate: str, 
    ticker: str
) -> dict:
    """
    Retrieve market capitalization data for a specific stock.
    
    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate (str): End date for retrieval (YYYYMMDD)
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: {
            "ticker": str,
            "data": list[dict] - Each record contains {
                "date": str (YYYYMMDD),
                "market_cap": float
            }
        }
    """
    pass

def get_stock_fundamental(
    fromdate: str, 
    todate: str, 
    ticker: str
) -> dict:
    """
    Retrieve fundamental data (PER/PBR/Dividend Yield) for a specific stock.
    
    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate (str): End date for retrieval (YYYYMMDD)
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: {
            "ticker": str,
            "data": list[dict] - Each record contains {
                "date": str (YYYYMMDD),
                "per": float,  # Price-to-Earnings Ratio
                "pbr": float,  # Price-to-Book Ratio
                "dividend_yield": float
            }
        }
    """
    pass

def get_stock_trading_volume(
    fromdate: str, 
    todate: str, 
    ticker: str
) -> dict:
    """
    Retrieve trading volume by investor type for a specific stock.
    
    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate (str): End date for retrieval (YYYYMMDD)
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: {
            "ticker": str,
            "data": list[dict] - Each record contains {
                "date": str (YYYYMMDD),
                "individual": int,  # Individual investor volume
                "institutional": int,  # Institutional investor volume
                "foreign": int  # Foreign investor volume
            }
        }
    """
    pass

