# Server: CryptoPrice
from typing import Literal, Optional, List
def get_crypto_price(
    symbol: str, 
    exchanges: Optional[List[str]] = None
) -> dict:
    """
    Get current price and 24h statistics for a specific cryptocurrency.
    
    Args:
        symbol (str): Cryptocurrency symbol (e.g., "BTC", "ETH")
        exchanges (list[str]): [Optional] List of exchange names to get prices from (e.g., ["binance", "coinbase", "kraken"])
        
    Returns:
        dict: {
            "price_usd": float,
            "change_24h_percent": float,
            "volume_24h": float,
            "market_cap": float,
            "market_rank": int,
            "exchanges_prices": dict  # Prices from specific exchanges, format: {"exchange_name": {"price": float, "volume": float}}
        }
    """
    pass

def get_market_analysis(
    symbol: str,
    exchanges: Optional[List[str]] = None
) -> dict:
    """
    Provide detailed market analysis including exchange data and VWAP.
    
    Args:
        symbol (str): Cryptocurrency symbol (e.g., "BTC", "ETH")
        exchanges (list[str]): [Optional] List of exchange names to get prices from (e.g., ["binance", "coinbase", "kraken"])
        
    Returns:
        dict: {
            "top_exchanges": list[dict],  # Top 5 exchanges by volume
            "price_variations": dict,     # Variations across different exchanges
            "volume_distribution": dict,  # Distribution analysis by exchange/pair
            "vwap": float,                # Volume Weighted Average Price
            "exchanges_prices": dict      # Prices from specific exchanges, format: {"exchange_name": {"price": float, "volume": float}}
        }
    """
    pass

def get_historical_analysis(
    symbol: str, 
    interval: Literal["5m", "15m", "30m", "1h", "4h", "1d"] = "1d", 
    days: int = 7
) -> dict:
    """
    Analyze historical price data, trends, and volatility.
    
    Args:
        symbol (str): Cryptocurrency symbol (e.g., "BTC", "ETH")
        interval (Literal["5m", "15m", "30m", "1h", "4h", "1d"]): [Optional] Time interval between data points. Options: "5m", "15m", "30m", "1h", "4h", "1d". Default: "1d"
        days (int): [Optional] Number of days of historical data to analyze (max 30)
        
    Returns:
        dict: {
            "price_trends": list[float],
            "volatility_metrics": dict,
            "high_price": float,
            "low_price": float,
            "analysis_summary": str
        }
    """
    pass