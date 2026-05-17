from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class IncomeStatement(BaseModel):
    """Represents an income statement entry."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Reporting date in YYYY-MM-DD format")
    revenue: float = Field(..., ge=0, description="Total revenue")
    net_income: float = Field(..., description="Net income")
    eps: float = Field(..., description="Earnings per share")

class BalanceSheet(BaseModel):
    """Represents a balance sheet entry."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Reporting date in YYYY-MM-DD format")
    total_assets: float = Field(..., ge=0, description="Total assets")
    total_liabilities: float = Field(..., ge=0, description="Total liabilities")
    shareholders_equity: float = Field(..., description="Shareholders' equity")

class CashFlowStatement(BaseModel):
    """Represents a cash flow statement entry."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Reporting date in YYYY-MM-DD format")
    operating_cash_flow: float = Field(..., description="Operating cash flow")
    investing_cash_flow: float = Field(..., description="Investing cash flow")
    financing_cash_flow: float = Field(..., description="Financing cash flow")
    net_change_in_cash: float = Field(..., description="Net change in cash")

class StockPrice(BaseModel):
    """Represents a stock price entry."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date in YYYY-MM-DD format")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="High price")
    low: float = Field(..., ge=0, description="Low price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

class CryptoPrice(BaseModel):
    """Represents a cryptocurrency price entry."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date in YYYY-MM-DD format")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="High price")
    low: float = Field(..., ge=0, description="Low price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: float = Field(..., ge=0, description="Trading volume")

class NewsArticle(BaseModel):
    """Represents a news article."""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    published_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Publication timestamp in ISO 8601 format")
    source: str = Field(..., description="News source")

class FinancialScenario(BaseModel):
    """Main scenario model for financial datasets."""
    income_statements: Dict[str, Dict[str, List[IncomeStatement]]] = Field(default={}, description="Income statements by symbol and period")
    balance_sheets: Dict[str, Dict[str, List[BalanceSheet]]] = Field(default={}, description="Balance sheets by symbol and period")
    cash_flow_statements: Dict[str, Dict[str, List[CashFlowStatement]]] = Field(default={}, description="Cash flow statements by symbol and period")
    stock_prices: Dict[str, StockPrice] = Field(default={}, description="Current stock prices")
    historical_stock_prices: Dict[str, List[StockPrice]] = Field(default={}, description="Historical stock prices")
    crypto_prices: Dict[str, CryptoPrice] = Field(default={}, description="Current crypto prices")
    historical_crypto_prices: Dict[str, List[CryptoPrice]] = Field(default={}, description="Historical crypto prices")
    company_news: Dict[str, List[NewsArticle]] = Field(default={}, description="Company news articles")
    available_stock_tickers: List[str] = Field(default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ", "WMT", "PG", "DIS", "HD", "MA", "PYPL", "NFLX", "ADBE", "CRM", "ACN"], description="Available stock tickers")
    available_crypto_tickers: List[str] = Field(default=["BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "USDC", "ADA", "DOGE", "TRX", "TON", "AVAX", "DOT", "LINK", "MATIC", "LTC", "ICP", "UNI", "ATOM", "ETC"], description="Available crypto tickers")

Scenario_Schema = [IncomeStatement, BalanceSheet, CashFlowStatement, StockPrice, CryptoPrice, NewsArticle, FinancialScenario]

# Section 2: Class
class FinancialDatasetsAPI:
    def __init__(self):
        """Initialize financial datasets API with empty state."""
        self.income_statements: Dict[str, Dict[str, List[IncomeStatement]]] = {}
        self.balance_sheets: Dict[str, Dict[str, List[BalanceSheet]]] = {}
        self.cash_flow_statements: Dict[str, Dict[str, List[CashFlowStatement]]] = {}
        self.stock_prices: Dict[str, StockPrice] = {}
        self.historical_stock_prices: Dict[str, List[StockPrice]] = {}
        self.crypto_prices: Dict[str, CryptoPrice] = {}
        self.historical_crypto_prices: Dict[str, List[CryptoPrice]] = {}
        self.company_news: Dict[str, List[NewsArticle]] = {}
        self.available_stock_tickers: List[str] = []
        self.available_crypto_tickers: List[str] = []

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = FinancialScenario(**scenario)
        self.income_statements = model.income_statements
        self.balance_sheets = model.balance_sheets
        self.cash_flow_statements = model.cash_flow_statements
        self.stock_prices = model.stock_prices
        self.historical_stock_prices = model.historical_stock_prices
        self.crypto_prices = model.crypto_prices
        self.historical_crypto_prices = model.historical_crypto_prices
        self.company_news = model.company_news
        self.available_stock_tickers = model.available_stock_tickers
        self.available_crypto_tickers = model.available_crypto_tickers

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "income_statements": self.income_statements,
            "balance_sheets": self.balance_sheets,
            "cash_flow_statements": self.cash_flow_statements,
            "stock_prices": self.stock_prices,
            "historical_stock_prices": self.historical_stock_prices,
            "crypto_prices": self.crypto_prices,
            "historical_crypto_prices": self.historical_crypto_prices,
            "company_news": self.company_news,
            "available_stock_tickers": self.available_stock_tickers,
            "available_crypto_tickers": self.available_crypto_tickers
        }

    def get_income_statements(self, symbol: str, period: str = "annual") -> dict:
        """Retrieve income statements for a company."""
        if symbol not in self.income_statements or period not in self.income_statements[symbol]:
            return {"symbol": symbol, "period": period, "statements": []}
        
        statements = [stmt.model_dump() for stmt in self.income_statements[symbol][period]]
        return {"symbol": symbol, "period": period, "statements": statements}

    def get_balance_sheets(self, symbol: str, period: str = "annual") -> dict:
        """Retrieve balance sheets for a company."""
        if symbol not in self.balance_sheets or period not in self.balance_sheets[symbol]:
            return {"symbol": symbol, "period": period, "statements": []}
        
        statements = [stmt.model_dump() for stmt in self.balance_sheets[symbol][period]]
        return {"symbol": symbol, "period": period, "statements": statements}

    def get_cash_flow_statements(self, symbol: str, period: str = "annual") -> dict:
        """Retrieve cash flow statements for a company."""
        if symbol not in self.cash_flow_statements or period not in self.cash_flow_statements[symbol]:
            return {"symbol": symbol, "period": period, "statements": []}
        
        statements = [stmt.model_dump() for stmt in self.cash_flow_statements[symbol][period]]
        return {"symbol": symbol, "period": period, "statements": statements}

    def get_current_stock_price(self, symbol: str) -> dict:
        """Retrieve current stock price."""
        if symbol not in self.stock_prices:
            return {"symbol": symbol, "price": 0.0, "currency": "USD", "timestamp": "2024-01-01T00:00:00", "change": 0.0, "change_percent": 0.0}
        
        price_data = self.stock_prices[symbol]
        return {
            "symbol": symbol,
            "price": price_data.close,
            "currency": "USD",
            "timestamp": f"{price_data.date}T00:00:00",
            "change": 0.0,
            "change_percent": 0.0
        }

    def get_historical_stock_prices(self, symbol: str, start_date: str = "", end_date: str = "", interval: str = "1d") -> dict:
        """Retrieve historical stock prices."""
        if symbol not in self.historical_stock_prices:
            return {"symbol": symbol, "prices": []}
        
        prices = [price.model_dump() for price in self.historical_stock_prices[symbol]]
        return {"symbol": symbol, "prices": prices}

    def get_company_news(self, symbol: str, limit: int = 10) -> dict:
        """Retrieve company news."""
        if symbol not in self.company_news:
            return {"symbol": symbol, "news": []}
        
        news = [article.model_dump() for article in self.company_news[symbol][:limit]]
        return {"symbol": symbol, "news": news}

    def get_available_stock_tickers(self) -> dict:
        """Retrieve available stock tickers."""
        return {"symbols": self.available_stock_tickers}

    def get_available_crypto_tickers(self) -> dict:
        """Retrieve available crypto tickers."""
        return {"tickers": self.available_crypto_tickers}

    def get_historical_crypto_prices(self, ticker: str, start_date: str = "", end_date: str = "", interval: str = "1d") -> dict:
        """Retrieve historical crypto prices."""
        if ticker not in self.historical_crypto_prices:
            return {"ticker": ticker, "prices": []}
        
        prices = [price.model_dump() for price in self.historical_crypto_prices[ticker]]
        return {"ticker": ticker, "prices": prices}

    def get_current_crypto_price(self, ticker: str) -> dict:
        """Retrieve current crypto price."""
        if ticker not in self.crypto_prices:
            return {"ticker": ticker, "price": 0.0, "currency": "USD", "timestamp": "2024-01-01T00:00:00", "change": 0.0, "change_percent": 0.0}
        
        price_data = self.crypto_prices[ticker]
        return {
            "ticker": ticker,
            "price": price_data.close,
            "currency": "USD",
            "timestamp": f"{price_data.date}T00:00:00",
            "change": 0.0,
            "change_percent": 0.0
        }

# Section 3: MCP Tools
mcp = FastMCP(name="FinancialDatasets")
api = FinancialDatasetsAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the financial datasets API.
    
    Args:
        scenario (dict): Scenario dictionary matching FinancialScenario schema.
    
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
    Save current financial datasets state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_income_statements(symbol: str, period: str = "annual") -> dict:
    """
    Retrieves income statements for a publicly traded company.
    
    Args:
        symbol (str): The stock ticker symbol of the company to retrieve data for.
        period (str): [Optional] The reporting period frequency: "annual" or "quarterly".
    
    Returns:
        symbol (str): The stock ticker symbol.
        period (str): The reporting period frequency.
        statements (list): List of income statement records.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_income_statements(symbol, period)
    except Exception as e:
        raise e

@mcp.tool()
def get_balance_sheets(symbol: str, period: str = "annual") -> dict:
    """
    Retrieves balance sheet data for a publicly traded company.
    
    Args:
        symbol (str): The stock ticker symbol of the company to retrieve data for.
        period (str): [Optional] The reporting period frequency: "annual" or "quarterly".
    
    Returns:
        symbol (str): The stock ticker symbol.
        period (str): The reporting period frequency.
        statements (list): List of balance sheet records.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_balance_sheets(symbol, period)
    except Exception as e:
        raise e

@mcp.tool()
def get_cash_flow_statements(symbol: str, period: str = "annual") -> dict:
    """
    Retrieves cash flow statements for a publicly traded company.
    
    Args:
        symbol (str): The stock ticker symbol of the company to retrieve data for.
        period (str): [Optional] The reporting period frequency: "annual" or "quarterly".
    
    Returns:
        symbol (str): The stock ticker symbol.
        period (str): The reporting period frequency.
        statements (list): List of cash flow statement records.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_cash_flow_statements(symbol, period)
    except Exception as e:
        raise e

@mcp.tool()
def get_current_stock_price(symbol: str) -> dict:
    """
    Retrieves the current real-time stock price and daily change information.
    
    Args:
        symbol (str): The stock ticker symbol of the company to retrieve data for.
    
    Returns:
        symbol (str): The stock ticker symbol.
        price (float): The current trading price.
        currency (str): The currency denomination.
        timestamp (str): The timestamp of the price quote.
        change (float): The absolute price change.
        change_percent (float): The percentage price change.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_current_stock_price(symbol)
    except Exception as e:
        raise e

@mcp.tool()
def get_historical_stock_prices(symbol: str, start_date: str = "", end_date: str = "", interval: str = "1d") -> dict:
    """
    Retrieves historical stock price data (OHLCV) over a specified date range.
    
    Args:
        symbol (str): The stock ticker symbol of the company to retrieve data for.
        start_date (str): [Optional] The start date in YYYY-MM-DD format.
        end_date (str): [Optional] The end date in YYYY-MM-DD format.
        interval (str): [Optional] The time interval: "1d", "1w", or "1m".
    
    Returns:
        symbol (str): The stock ticker symbol.
        prices (list): List of historical price records.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_historical_stock_prices(symbol, start_date, end_date, interval)
    except Exception as e:
        raise e

@mcp.tool()
def get_company_news(symbol: str, limit: int = 10) -> dict:
    """
    Retrieves recent news articles related to a publicly traded company.
    
    Args:
        symbol (str): The stock ticker symbol of the company to retrieve data for.
        limit (int): [Optional] The maximum number of news articles to return.
    
    Returns:
        symbol (str): The stock ticker symbol.
        news (list): List of news articles.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer")
        return api.get_company_news(symbol, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_available_stock_tickers() -> dict:
    """
    Retrieves a list of all available stock ticker symbols.
    
    Returns:
        symbols (list): List of available stock ticker symbols.
    """
    try:
        return api.get_available_stock_tickers()
    except Exception as e:
        raise e

@mcp.tool()
def get_available_crypto_tickers() -> dict:
    """
    Retrieves a list of all available cryptocurrency ticker symbols.
    
    Returns:
        tickers (list): List of available cryptocurrency ticker symbols.
    """
    try:
        return api.get_available_crypto_tickers()
    except Exception as e:
        raise e

@mcp.tool()
def get_historical_crypto_prices(ticker: str, start_date: str = "", end_date: str = "", interval: str = "1d") -> dict:
    """
    Retrieves historical price data (OHLCV) for a cryptocurrency over a specified date range.
    
    Args:
        ticker (str): The cryptocurrency ticker symbol to retrieve data for.
        start_date (str): [Optional] The start date in YYYY-MM-DD format.
        end_date (str): [Optional] The end date in YYYY-MM-DD format.
        interval (str): [Optional] The time interval: "1d", "1w", or "1m".
    
    Returns:
        ticker (str): The cryptocurrency ticker symbol.
        prices (list): List of historical price records.
    """
    try:
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
        return api.get_historical_crypto_prices(ticker, start_date, end_date, interval)
    except Exception as e:
        raise e

@mcp.tool()
def get_current_crypto_price(ticker: str) -> dict:
    """
    Retrieves the current real-time price and daily change information for a cryptocurrency.
    
    Args:
        ticker (str): The cryptocurrency ticker symbol to retrieve data for.
    
    Returns:
        ticker (str): The cryptocurrency ticker symbol.
        price (float): The current trading price.
        currency (str): The currency denomination.
        timestamp (str): The timestamp of the price quote.
        change (float): The absolute price change.
        change_percent (float): The percentage price change.
    """
    try:
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
        return api.get_current_crypto_price(ticker)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()