# Server: FinancialDatasets

def get_income_statements(symbol: str, period: str = None) -> dict:
    """
    Get income statements for a company.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., "AAPL", "MSFT")
        period (str): [Optional] Reporting period: "annual" or "quarterly"
        
    Returns:
        dict: {
            "symbol": str,
            "period": str,
            "statements": list[dict] - Each statement contains {
                "date": str (YYYY-MM-DD),
                "revenue": float,
                "net_income": float,
                "eps": float
            }
        }
    """
    pass

def get_balance_sheets(symbol: str, period: str = None) -> dict:
    """
    Get balance sheets for a company.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., "AAPL", "MSFT")
        period (str): [Optional] Reporting period: "annual" or "quarterly"
        
    Returns:
        dict: {
            "symbol": str,
            "period": str,
            "statements": list[dict] - Each statement contains {
                "date": str (YYYY-MM-DD),
                "total_assets": float,
                "total_liabilities": float,
                "shareholders_equity": float
            }
        }
    """
    pass

def get_cash_flow_statements(symbol: str, period: str = None) -> dict:
    """
    Get cash flow statements for a company.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., "AAPL", "MSFT")
        period (str): [Optional] Reporting period: "annual" or "quarterly"
        
    Returns:
        dict: {
            "symbol": str,
            "period": str,
            "statements": list[dict] - Each statement contains {
                "date": str (YYYY-MM-DD),
                "operating_cash_flow": float,
                "investing_cash_flow": float,
                "financing_cash_flow": float,
                "net_change_in_cash": float
            }
        }
    """
    pass

def get_current_stock_price(symbol: str) -> dict:
    """
    Get the current / latest price of a company.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., "AAPL", "MSFT")
        
    Returns:
        dict: {
            "symbol": str,
            "price": float,
            "currency": str,
            "timestamp": str (ISO 8601),
            "change": float,
            "change_percent": float
        }
    """
    pass

def get_historical_stock_prices(
    symbol: str, 
    start_date: str = None, 
    end_date: str = None,
    interval: str = None
) -> dict:
    """
    Gets historical stock prices for a company.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., "AAPL", "MSFT")
        start_date (str): [Optional] Start date in YYYY-MM-DD format
        end_date (str): [Optional] End date in YYYY-MM-DD format
        interval (str): [Optional] Data interval: "1d", "1w", "1m"
        
    Returns:
        dict: {
            "symbol": str,
            "prices": list[dict] - Each record contains {
                "date": str (YYYY-MM-DD),
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": int
            }
        }
    """
    pass

def get_company_news(symbol: str, limit: int = None) -> dict:
    """
    Get news for a company.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., "AAPL", "MSFT")
        limit (int): [Optional] Maximum number of news articles to return
        
    Returns:
        dict: {
            "symbol": str,
            "news": list[dict] - Each article contains {
                "title": str,
                "url": str,
                "published_at": str (ISO 8601),
                "source": str
            }
        }
    """
    pass

def get_available_stock_tickers() -> dict:
    """
    Gets all available stock tickers.
    
    Returns:
        dict: {
            "symbols": list[str] - List of available stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        }
    """
    pass

def get_available_crypto_tickers() -> dict:
    """
    Gets all available crypto tickers.
    
    Returns:
        dict: {
            "tickers": list[str] - List of available cryptocurrency ticker symbols (e.g., ["BTC", "ETH", "USDT"])
        }
    """
    pass

def get_historical_crypto_prices(
    ticker: str,
    start_date: str = None,
    end_date: str = None,
    interval: str = None
) -> dict:
    """
    Gets historical prices for a crypto currency.
    
    Args:
        ticker (str): Cryptocurrency ticker symbol (e.g., "BTC", "ETH")
        start_date (str): [Optional] Start date in YYYY-MM-DD format
        end_date (str): [Optional] End date in YYYY-MM-DD format
        interval (str): [Optional] Data interval: "1d", "1w", "1m"
        
    Returns:
        dict: {
            "ticker": str,
            "prices": list[dict] - Each record contains {
                "date": str (YYYY-MM-DD),
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float
            }
        }
    """
    pass

def get_current_crypto_price(ticker: str) -> dict:
    """
    Get the current / latest price of a crypto currency.
    
    Args:
        ticker (str): Cryptocurrency ticker symbol (e.g., "BTC", "ETH")
        
    Returns:
        dict: {
            "ticker": str,
            "price": float,
            "currency": str,
            "timestamp": str (ISO 8601),
            "change": float,
            "change_percent": float
        }
    """
    pass

