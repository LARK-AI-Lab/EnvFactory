from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class ExchangePriceData(BaseModel):
    """Price data from a specific exchange."""
    exchange: str = Field(..., description="Exchange name")
    price: float = Field(..., ge=0, description="Price in USD")
    volume: float = Field(..., ge=0, description="24h trading volume")
    timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Timestamp in ISO 8601 format")

class CryptoData(BaseModel):
    """Cryptocurrency data."""
    symbol: str = Field(..., pattern=r"^[A-Z]{2,10}$", description="Cryptocurrency symbol")
    name: str = Field(..., min_length=1, description="Full name of the cryptocurrency")
    price_usd: float = Field(..., ge=0, description="Current price in USD")
    change_24h_percent: float = Field(..., description="24h price change percentage")
    volume_24h: float = Field(..., ge=0, description="24h trading volume")
    market_cap: float = Field(..., ge=0, description="Market capitalization")
    market_rank: int = Field(..., ge=1, description="Market cap ranking")

class MarketAnalysis(BaseModel):
    """Market analysis data."""
    symbol: str = Field(..., pattern=r"^[A-Z]{2,10}$", description="Cryptocurrency symbol")
    exchange: str = Field(..., description="Exchange name")
    price: float = Field(..., ge=0, description="Price on exchange")
    volume: float = Field(..., ge=0, description="Volume on exchange")
    timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Timestamp")

class HistoricalData(BaseModel):
    """Historical price data point."""
    timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Timestamp")
    price: float = Field(..., ge=0, description="Price at timestamp")
    volume: float = Field(..., ge=0, description="Volume at timestamp")

class CryptoScenario(BaseModel):
    """Main scenario model for cryptocurrency data."""
    crypto_data: Dict[str, CryptoData] = Field(default_factory=dict, description="Cryptocurrency data by symbol")
    market_analysis: Dict[str, List[MarketAnalysis]] = Field(default_factory=dict, description="Market analysis by symbol")
    historical_data: Dict[str, List[HistoricalData]] = Field(default_factory=dict, description="Historical data by symbol")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")

Scenario_Schema = [ExchangePriceData, CryptoData, MarketAnalysis, HistoricalData, CryptoScenario]

# Section 2: Class
class CryptoPriceAPI:
    def __init__(self):
        self.crypto_data: Dict[str, CryptoData] = {}
        self.market_analysis: Dict[str, List[MarketAnalysis]] = {}
        self.historical_data: Dict[str, List[HistoricalData]] = {}
        self.random_seed: Optional[int] = None

    def load_scenario(self, scenario: dict) -> None:
        model = CryptoScenario(**scenario)
        self.crypto_data = model.crypto_data
        self.market_analysis = model.market_analysis
        self.historical_data = model.historical_data
        self.random_seed = model.random_seed

    def save_scenario(self) -> dict:
        return {
            "crypto_data": {k: v.model_dump() for k, v in self.crypto_data.items()},
            "market_analysis": {k: [item.model_dump() for item in v] for k, v in self.market_analysis.items()},
            "historical_data": {k: [item.model_dump() for item in v] for k, v in self.historical_data.items()},
            "random_seed": self.random_seed
        }

    def get_crypto_price(self, symbol: str) -> dict:
        """Get current price data for a cryptocurrency."""
        if symbol not in self.crypto_data:
            raise ValueError(f"Cryptocurrency {symbol} not found in scenario data")
        return self.crypto_data[symbol].model_dump()

    def get_market_analysis(self, symbol: str) -> List[dict]:
        """Get market analysis for a cryptocurrency."""
        if symbol not in self.market_analysis:
            raise ValueError(f"Market analysis for {symbol} not found")
        return [item.model_dump() for item in self.market_analysis[symbol]]

    def get_historical_analysis(self, symbol: str, days: int = 30) -> List[dict]:
        """Get historical price analysis."""
        if symbol not in self.historical_data:
            raise ValueError(f"Historical data for {symbol} not found")
        data = self.historical_data[symbol]
        return [item.model_dump() for item in data[-days:]]

# Section 3: MCP Tools
mcp = FastMCP(name="CryptoPriceAPI")
api = CryptoPriceAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the API."""
    try:
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current state as scenario dictionary."""
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_crypto_price(symbol: str) -> dict:
    """Get current price data for a cryptocurrency.

    Args:
        symbol (str): Cryptocurrency symbol (e.g., BTC, ETH).

    Returns:
        Cryptocurrency price data.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_crypto_price(symbol.upper())
    except Exception as e:
        raise e

@mcp.tool()
def get_market_analysis(symbol: str) -> List[dict]:
    """Get market analysis for a cryptocurrency.

    Args:
        symbol (str): Cryptocurrency symbol.

    Returns:
        List of market analysis data points.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_market_analysis(symbol.upper())
    except Exception as e:
        raise e

@mcp.tool()
def get_historical_analysis(symbol: str, days: int = 30) -> List[dict]:
    """Get historical price analysis.

    Args:
        symbol (str): Cryptocurrency symbol.
        days (int): [Optional] Number of days of history. Default: 30.

    Returns:
        List of historical data points.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not isinstance(days, int) or days <= 0:
            raise ValueError("Days must be a positive integer")
        return api.get_historical_analysis(symbol.upper(), days)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
