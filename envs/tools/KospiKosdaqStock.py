from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import re

# Section 1: Schema
class OHLCVRecord(BaseModel):
    """Represents a single day's OHLCV data."""
    date: str = Field(..., pattern=r"^\d{8}$", description="The trading date in YYYYMMDD format.")
    open: float = Field(..., ge=0, description="The opening price of the stock for the trading day.")
    high: float = Field(..., ge=0, description="The highest price of the stock during the trading day.")
    low: float = Field(..., ge=0, description="The lowest price of the stock during the trading day.")
    close: float = Field(..., ge=0, description="The closing price of the stock for the trading day.")
    volume: int = Field(..., ge=0, description="The total number of shares traded during the trading day.")

class MarketCapRecord(BaseModel):
    """Represents a single day's market capitalization data."""
    date: str = Field(..., pattern=r"^\d{8}$", description="The trading date in YYYYMMDD format.")
    market_cap: float = Field(..., ge=0, description="The total market capitalization of the stock.")

class FundamentalRecord(BaseModel):
    """Represents a single day's fundamental indicator data."""
    date: str = Field(..., pattern=r"^\d{8}$", description="The trading date in YYYYMMDD format.")
    per: float = Field(..., description="Price-to-Earnings Ratio measuring the stock price relative to earnings per share.")
    pbr: float = Field(..., description="Price-to-Book Ratio measuring the stock price relative to book value per share.")
    dividend_yield: float = Field(..., ge=0, description="The annual dividend payment expressed as a percentage of the stock price.")

class TradingVolumeRecord(BaseModel):
    """Represents a single day's trading volume breakdown by investor type."""
    date: str = Field(..., pattern=r"^\d{8}$", description="The trading date in YYYYMMDD format.")
    individual: int = Field(..., description="Trading volume attributed to individual retail investors.")
    institutional: int = Field(..., description="Trading volume attributed to institutional investors.")
    foreign: int = Field(..., description="Trading volume attributed to foreign investors.")

class StockInfo(BaseModel):
    """Represents basic stock information."""
    ticker: str = Field(..., pattern=r"^\d{6}$", description="The 6-digit stock ticker symbol.")
    name: str = Field(..., description="The company name.")
    market: str = Field(..., description="The market where the stock is listed (KOSPI or KOSDAQ).")

class KospiKosdaqScenario(BaseModel):
    """Main scenario model for Korean stock market data."""
    stocks: Dict[str, StockInfo] = Field(default={}, description="Registered stocks information by ticker.")
    ohlcv_data: Dict[str, List[Dict[str, Any]]] = Field(default={}, description="OHLCV data by ticker.")
    ohlcv_adjusted_data: Dict[str, List[Dict[str, Any]]] = Field(default={}, description="Adjusted OHLCV data by ticker.")
    market_cap_data: Dict[str, List[Dict[str, Any]]] = Field(default={}, description="Market capitalization data by ticker.")
    fundamental_data: Dict[str, List[Dict[str, Any]]] = Field(default={}, description="Fundamental indicator data by ticker.")
    trading_volume_data: Dict[str, List[Dict[str, Any]]] = Field(default={}, description="Trading volume by investor type data by ticker.")
    tickerNameMap: Dict[str, str] = Field(default={
        "005930": "Samsung Electronics",
        "000660": "SK Hynix",
        "035420": "NAVER",
        "035720": "Kakao",
        "051910": "LG Chem",
        "006400": "Samsung SDI",
        "068270": "Celltrion",
        "005380": "Hyundai Motor",
        "000270": "Kia",
        "105560": "KB Financial Group",
        "055550": "Shinhan Financial Group",
        "012330": "Hyundai Mobis",
        "066570": "LG Electronics",
        "003550": "LG",
        "028260": "Samsung C&T",
        "207940": "Samsung Biologics",
        "096770": "SK Innovation",
        "034730": "SK",
        "017670": "SK Telecom",
        "030200": "KT"
    }, description="Mapping of ticker symbols to company names.")
    tickerMarketMap: Dict[str, str] = Field(default={
        "005930": "KOSPI",
        "000660": "KOSPI",
        "035420": "KOSPI",
        "035720": "KOSPI",
        "051910": "KOSPI",
        "006400": "KOSPI",
        "068270": "KOSPI",
        "005380": "KOSPI",
        "000270": "KOSPI",
        "105560": "KOSPI",
        "055550": "KOSPI",
        "012330": "KOSPI",
        "066570": "KOSPI",
        "003550": "KOSPI",
        "028260": "KOSPI",
        "207940": "KOSPI",
        "096770": "KOSPI",
        "034730": "KOSPI",
        "017670": "KOSPI",
        "030200": "KOSPI"
    }, description="Mapping of ticker symbols to market type.")

Scenario_Schema = [OHLCVRecord, MarketCapRecord, FundamentalRecord, TradingVolumeRecord, StockInfo, KospiKosdaqScenario]

# Section 2: Class
class KospiKosdaqStockAPI:
    # Date format pattern for YYYYMMDD validation
    DATE_PATTERN = re.compile(r"^\d{8}$")
    
    def __init__(self):
        """Initialize Korean stock market API with empty state."""
        self.stocks: Dict[str, StockInfo] = {}
        self.ohlcv_data: Dict[str, List[Dict[str, Any]]] = {}
        self.ohlcv_adjusted_data: Dict[str, List[Dict[str, Any]]] = {}
        self.market_cap_data: Dict[str, List[Dict[str, Any]]] = {}
        self.fundamental_data: Dict[str, List[Dict[str, Any]]] = {}
        self.trading_volume_data: Dict[str, List[Dict[str, Any]]] = {}
        self.tickerNameMap: Dict[str, str] = {}
        self.tickerMarketMap: Dict[str, str] = {}

    def _validate_date_format(self, date_str: str, context: str) -> None:
        """Validate that a date string matches YYYYMMDD format."""
        if not self.DATE_PATTERN.match(date_str):
            raise ValueError(f"Invalid date format in {context}: '{date_str}'. Expected YYYYMMDD format (8 digits, no hyphens).")

    def _validate_data_records_dates(self, data_dict: Dict[str, List[Dict[str, Any]]], data_type: str) -> None:
        """Validate date formats in all records of a data dictionary."""
        for ticker, records in data_dict.items():
            for idx, record in enumerate(records):
                if "date" in record:
                    date_value = record["date"]
                    if not isinstance(date_value, str):
                        raise ValueError(f"Invalid date type in {data_type} for ticker {ticker}, record {idx}: expected string, got {type(date_value).__name__}")
                    self._validate_date_format(date_value, f"{data_type} for ticker {ticker}, record {idx}")

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance with validation."""
        # First, validate the basic structure using Pydantic
        model = KospiKosdaqScenario(**scenario)
        
        # Validate date formats in all data records before loading
        # This ensures dates are in YYYYMMDD format (8 digits, no hyphens)
        self._validate_data_records_dates(model.ohlcv_data, "ohlcv_data")
        self._validate_data_records_dates(model.ohlcv_adjusted_data, "ohlcv_adjusted_data")
        self._validate_data_records_dates(model.market_cap_data, "market_cap_data")
        self._validate_data_records_dates(model.fundamental_data, "fundamental_data")
        self._validate_data_records_dates(model.trading_volume_data, "trading_volume_data")
        
        # All validations passed, now load the data
        self.stocks = {ticker: StockInfo(**stock) if isinstance(stock, dict) else stock 
                       for ticker, stock in model.stocks.items()}
        self.ohlcv_data = model.ohlcv_data
        self.ohlcv_adjusted_data = model.ohlcv_adjusted_data
        self.market_cap_data = model.market_cap_data
        self.fundamental_data = model.fundamental_data
        self.trading_volume_data = model.trading_volume_data
        self.tickerNameMap = model.tickerNameMap
        self.tickerMarketMap = model.tickerMarketMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "stocks": {ticker: stock.model_dump() for ticker, stock in self.stocks.items()},
            "ohlcv_data": self.ohlcv_data,
            "ohlcv_adjusted_data": self.ohlcv_adjusted_data,
            "market_cap_data": self.market_cap_data,
            "fundamental_data": self.fundamental_data,
            "trading_volume_data": self.trading_volume_data,
            "tickerNameMap": self.tickerNameMap,
            "tickerMarketMap": self.tickerMarketMap
        }

    def _filter_by_date_range(self, data: List[Dict[str, Any]], fromdate: str, todate: str) -> List[Dict[str, Any]]:
        """Filter data records by date range."""
        return [record for record in data if fromdate <= record.get("date", "") <= todate]

    def get_stock_ohlcv(self, fromdate: str, todate: str, ticker: str, adjusted: Optional[bool] = False) -> dict:
        """Retrieve OHLCV price data for a specific stock over a date range."""
        if adjusted:
            data_source = self.ohlcv_adjusted_data.get(ticker, [])
        else:
            data_source = self.ohlcv_data.get(ticker, [])
        
        filtered_data = self._filter_by_date_range(data_source, fromdate, todate)
        
        return {
            "ticker": ticker,
            "data": filtered_data
        }

    def get_stock_market_cap(self, fromdate: str, todate: str, ticker: str) -> dict:
        """Retrieve market capitalization data for a specific stock over a date range."""
        data_source = self.market_cap_data.get(ticker, [])
        filtered_data = self._filter_by_date_range(data_source, fromdate, todate)
        
        return {
            "ticker": ticker,
            "data": filtered_data
        }

    def get_stock_fundamental(self, fromdate: str, todate: str, ticker: str) -> dict:
        """Retrieve fundamental valuation indicators for a specific stock over a date range."""
        data_source = self.fundamental_data.get(ticker, [])
        filtered_data = self._filter_by_date_range(data_source, fromdate, todate)
        
        return {
            "ticker": ticker,
            "data": filtered_data
        }

    def get_stock_trading_volume(self, fromdate: str, todate: str, ticker: str) -> dict:
        """Retrieve trading volume breakdown by investor type for a specific stock over a date range."""
        data_source = self.trading_volume_data.get(ticker, [])
        filtered_data = self._filter_by_date_range(data_source, fromdate, todate)
        
        return {
            "ticker": ticker,
            "data": filtered_data
        }

# Section 3: MCP Tools
mcp = FastMCP(name="KospiKosdaqStock")
api = KospiKosdaqStockAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Korean stock market API.
    
    Args:
        scenario (dict): Scenario dictionary matching KospiKosdaqScenario schema.
    
    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Korean stock market state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_ohlcv(fromdate: str, todate: str, ticker: str, adjusted: Optional[bool] = False) -> dict:
    """
    Retrieve OHLCV (Open/High/Low/Close/Volume) price data for a specific stock over a date range.
    
    Args:
        fromdate (str): Start date for the data retrieval period in YYYYMMDD format.
        todate (str): End date for the data retrieval period in YYYYMMDD format.
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
        adjusted (bool): [Optional] Whether to return adjusted prices accounting for stock splits and dividends. True for adjusted prices, False for unadjusted raw prices.
    
    Returns:
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
        data (list): List of daily OHLCV records for the requested date range.
    """
    try:
        if not fromdate or not isinstance(fromdate, str):
            raise ValueError("fromdate must be a non-empty string")
        if not todate or not isinstance(todate, str):
            raise ValueError("todate must be a non-empty string")
        if not ticker or not isinstance(ticker, str):
            raise ValueError("ticker must be a non-empty string")
        if fromdate > todate:
            raise ValueError("fromdate must be less than or equal to todate")
        return api.get_stock_ohlcv(fromdate, todate, ticker, adjusted)
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_market_cap(fromdate: str, todate: str, ticker: str) -> dict:
    """
    Retrieve market capitalization data for a specific stock over a date range.
    
    Args:
        fromdate (str): Start date for the data retrieval period in YYYYMMDD format.
        todate (str): End date for the data retrieval period in YYYYMMDD format.
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
    
    Returns:
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
        data (list): List of daily market capitalization records for the requested date range.
    """
    try:
        if not fromdate or not isinstance(fromdate, str):
            raise ValueError("fromdate must be a non-empty string")
        if not todate or not isinstance(todate, str):
            raise ValueError("todate must be a non-empty string")
        if not ticker or not isinstance(ticker, str):
            raise ValueError("ticker must be a non-empty string")
        if fromdate > todate:
            raise ValueError("fromdate must be less than or equal to todate")
        return api.get_stock_market_cap(fromdate, todate, ticker)
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_fundamental(fromdate: str, todate: str, ticker: str) -> dict:
    """
    Retrieve fundamental valuation indicators (PER, PBR, Dividend Yield) for a specific stock over a date range.
    
    Args:
        fromdate (str): Start date for the data retrieval period in YYYYMMDD format.
        todate (str): End date for the data retrieval period in YYYYMMDD format.
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
    
    Returns:
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
        data (list): List of daily fundamental indicator records for the requested date range.
    """
    try:
        if not fromdate or not isinstance(fromdate, str):
            raise ValueError("fromdate must be a non-empty string")
        if not todate or not isinstance(todate, str):
            raise ValueError("todate must be a non-empty string")
        if not ticker or not isinstance(ticker, str):
            raise ValueError("ticker must be a non-empty string")
        if fromdate > todate:
            raise ValueError("fromdate must be less than or equal to todate")
        return api.get_stock_fundamental(fromdate, todate, ticker)
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_trading_volume(fromdate: str, todate: str, ticker: str) -> dict:
    """
    Retrieve trading volume breakdown by investor type (individual, institutional, foreign) for a specific stock over a date range.
    
    Args:
        fromdate (str): Start date for the data retrieval period in YYYYMMDD format.
        todate (str): End date for the data retrieval period in YYYYMMDD format.
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
    
    Returns:
        ticker (str): The stock ticker symbol identifying the security on KOSPI or KOSDAQ.
        data (list): List of daily trading volume records segmented by investor type for the requested date range.
    """
    try:
        if not fromdate or not isinstance(fromdate, str):
            raise ValueError("fromdate must be a non-empty string")
        if not todate or not isinstance(todate, str):
            raise ValueError("todate must be a non-empty string")
        if not ticker or not isinstance(ticker, str):
            raise ValueError("ticker must be a non-empty string")
        if fromdate > todate:
            raise ValueError("fromdate must be less than or equal to todate")
        return api.get_stock_trading_volume(fromdate, todate, ticker)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()