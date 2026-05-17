from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class StockPrice(BaseModel):
    """Represents current stock price data."""
    symbol: str = Field(..., description="Stock symbol")
    current_price: str = Field(..., description="Current market price as formatted string")

class HistoricalPrice(BaseModel):
    """Represents historical OHLC price data."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date in YYYY-MM-DD format")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

class DividendData(BaseModel):
    """Represents dividend payment data."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Ex-dividend date")
    amount: float = Field(..., ge=0, description="Dividend amount per share")

class EarningsData(BaseModel):
    """Represents earnings announcement data."""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Earnings date")
    type: str = Field(..., description="Earnings type: quarterly or annual")
    actualEPS: Optional[float] = Field(None, description="Actual earnings per share")
    estimatedEPS: Optional[float] = Field(None, description="Estimated earnings per share")
    surprise: Optional[float] = Field(None, description="Difference between actual and estimated EPS")

class NewsArticle(BaseModel):
    """Represents a news article."""
    title: str = Field(..., description="News headline")
    link: str = Field(..., description="URL to full article")
    publisher: str = Field(..., description="News source name")
    publishDate: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Publication date")
    summary: str = Field(..., description="Article summary")

class AnalystRecommendation(BaseModel):
    """Represents analyst recommendation data."""
    firm: str = Field(..., description="Financial research firm")
    rating: str = Field(..., description="Analyst rating")
    priceTarget: Optional[float] = Field(None, description="Price target")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Recommendation date")

class OptionContract(BaseModel):
    """Represents an options contract."""
    strike: float = Field(..., description="Strike price")
    bid: float = Field(..., description="Bid price")
    ask: float = Field(..., description="Ask price")
    volume: int = Field(..., ge=0, description="Trading volume")
    openInterest: int = Field(..., ge=0, description="Open interest")
    impliedVolatility: float = Field(..., description="Implied volatility")

class YahooFinanceScenario(BaseModel):
    """Main scenario model for Yahoo Finance API."""
    stock_prices: Dict[str, StockPrice] = Field(default={}, description="Current stock prices")
    historical_prices: Dict[str, Dict[str, HistoricalPrice]] = Field(default={}, description="Historical price data by symbol")
    dividends: Dict[str, Dict[str, DividendData]] = Field(default={}, description="Dividend data by symbol")
    income_statements: Dict[str, Dict[str, Dict[str, Any]]] = Field(default={}, description="Income statement data by symbol")
    cashflow_statements: Dict[str, Dict[str, Dict[str, Any]]] = Field(default={}, description="Cash flow data by symbol")
    earnings_dates: Dict[str, List[EarningsData]] = Field(default={}, description="Earnings dates by symbol")
    news_articles: Dict[str, List[NewsArticle]] = Field(default={}, description="News articles by symbol")
    recommendations: Dict[str, List[AnalystRecommendation]] = Field(default={}, description="Analyst recommendations by symbol")
    option_expirations: Dict[str, List[str]] = Field(default={}, description="Option expiration dates by symbol")
    option_chains: Dict[str, Dict[str, Dict[str, List[OptionContract]]]] = Field(default={}, description="Option chains by symbol and expiration")
    market_data: Dict[str, Any] = Field(default={
        "market_hours": {"open": "09:30", "close": "16:00"},
        "market_status": "open",
        "reference_symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "NFLX", "AMD", "INTC"],
        "sectors": {
            "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
            "Consumer Discretionary": ["AMZN", "TSLA", "NFLX"],
            "Financials": ["JPM", "BAC", "WFC"],
            "Healthcare": ["JNJ", "PFE", "UNH"],
            "Energy": ["XOM", "CVX", "COP"]
        }
    }, description="Market reference data")

Scenario_Schema = [StockPrice, HistoricalPrice, DividendData, EarningsData, NewsArticle, AnalystRecommendation, OptionContract, YahooFinanceScenario]

# Section 2: Class
class YahooFinanceAPI:
    def __init__(self):
        """Initialize Yahoo Finance API with empty state."""
        self.stock_prices: Dict[str, StockPrice] = {}
        self.historical_prices: Dict[str, Dict[str, HistoricalPrice]] = {}
        self.dividends: Dict[str, Dict[str, DividendData]] = {}
        self.income_statements: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.cashflow_statements: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.earnings_dates: Dict[str, List[EarningsData]] = {}
        self.news_articles: Dict[str, List[NewsArticle]] = {}
        self.recommendations: Dict[str, List[AnalystRecommendation]] = {}
        self.option_expirations: Dict[str, List[str]] = {}
        self.option_chains: Dict[str, Dict[str, Dict[str, List[OptionContract]]]] = {}
        self.market_data: Dict[str, Any] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = YahooFinanceScenario(**scenario)
        self.stock_prices = model.stock_prices
        self.historical_prices = model.historical_prices
        self.dividends = model.dividends
        self.income_statements = model.income_statements
        self.cashflow_statements = model.cashflow_statements
        self.earnings_dates = model.earnings_dates
        self.news_articles = model.news_articles
        self.recommendations = model.recommendations
        self.option_expirations = model.option_expirations
        self.option_chains = model.option_chains
        self.market_data = model.market_data

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "stock_prices": {k: v.model_dump() for k, v in self.stock_prices.items()},
            "historical_prices": {symbol: {date: price.model_dump() for date, price in data.items()} for symbol, data in self.historical_prices.items()},
            "dividends": {symbol: {date: div.model_dump() for date, div in data.items()} for symbol, data in self.dividends.items()},
            "income_statements": self.income_statements,
            "cashflow_statements": self.cashflow_statements,
            "earnings_dates": {symbol: [e.model_dump() for e in data] for symbol, data in self.earnings_dates.items()},
            "news_articles": {symbol: [n.model_dump() for n in data] for symbol, data in self.news_articles.items()},
            "recommendations": {symbol: [r.model_dump() for r in data] for symbol, data in self.recommendations.items()},
            "option_expirations": self.option_expirations,
            "option_chains": self.option_chains,
            "market_data": self.market_data
        }

    def get_current_stock_price(self, symbol: str) -> dict:
        """Retrieve current stock price."""
        if symbol not in self.stock_prices:
            raise ValueError(f"Price data not found for symbol {symbol}")
        return {"current_price": self.stock_prices[symbol].current_price}

    def get_stock_price_by_date(self, symbol: str, date: str) -> dict:
        """Retrieve stock price by date."""
        if symbol not in self.historical_prices or date not in self.historical_prices[symbol]:
            raise ValueError(f"Price data not found for {symbol} on {date}")
        price_data = self.historical_prices[symbol][date]
        return {
            "date": date,
            "open": price_data.open,
            "close": price_data.close
        }

    def get_stock_price_date_range(self, symbol: str, start_date: str, end_date: str) -> dict:
        """Retrieve stock prices for date range."""
        if symbol not in self.historical_prices:
            raise ValueError(f"Historical price data not found for symbol {symbol}")
        
        closing_prices = {}
        for date, price_data in self.historical_prices[symbol].items():
            if start_date <= date <= end_date:
                closing_prices[date] = price_data.close
        
        return {"closing_prices": closing_prices}

    def get_historical_stock_prices(self, symbol: str, period: str = "1mo", interval: str = "1d") -> dict:
        """Retrieve historical OHLC stock prices."""
        if symbol not in self.historical_prices:
            raise ValueError(f"Historical price data not found for symbol {symbol}")
        
        price_history = []
        for date, price_data in sorted(self.historical_prices[symbol].items()):
            price_history.append({
                "date": date,
                "open": price_data.open,
                "high": price_data.high,
                "low": price_data.low,
                "close": price_data.close,
                "volume": price_data.volume
            })
        
        return {"price_history": price_history}

    def get_dividends(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        """Retrieve dividend payment history."""
        if symbol not in self.dividends:
            return {"dividends": {}}
        
        dividends = {}
        for date, div_data in self.dividends[symbol].items():
            if (start_date is None or date >= start_date) and (end_date is None or date <= end_date):
                dividends[date] = div_data.amount
        
        return {"dividends": dividends}

    def get_income_statement(self, symbol: str, freq: str = "yearly") -> dict:
        """Retrieve income statement data."""
        if symbol not in self.income_statements:
            raise ValueError(f"Income statement data not found for symbol {symbol}")
        return {"income_statements": self.income_statements[symbol]}

    def get_cashflow(self, symbol: str, freq: str = "yearly") -> dict:
        """Retrieve cash flow statement data."""
        if symbol not in self.cashflow_statements:
            raise ValueError(f"Cash flow statement data not found for symbol {symbol}")
        return {"cashflow_statements": self.cashflow_statements[symbol]}

    def get_earning_dates(self, symbol: str, limit: int = 12) -> dict:
        """Retrieve earnings announcement dates."""
        if symbol not in self.earnings_dates:
            raise ValueError(f"Earnings data not found for symbol {symbol}")
        
        earnings = self.earnings_dates[symbol][:limit]
        return {"earnings_dates": [e.model_dump() for e in earnings]}

    def get_news(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 50) -> dict:
        """Retrieve news articles."""
        if symbol not in self.news_articles:
            return {"news_articles": []}
        
        articles = []
        for article in self.news_articles[symbol]:
            if (start_date is None or article.publishDate >= start_date) and (end_date is None or article.publishDate <= end_date):
                articles.append(article.model_dump())
                if len(articles) >= limit:
                    break
        
        return {"news_articles": articles}

    def get_recommendations(self, symbol: str) -> dict:
        """Retrieve analyst recommendations."""
        if symbol not in self.recommendations:
            raise ValueError(f"Recommendations data not found for symbol {symbol}")
        return {"recommendations": [r.model_dump() for r in self.recommendations[symbol]]}

    def get_option_expiration_dates(self, symbol: str) -> dict:
        """Retrieve option expiration dates."""
        if symbol not in self.option_expirations:
            raise ValueError(f"Option expiration data not found for symbol {symbol}")
        return {"expiration_dates": self.option_expirations[symbol]}

    def get_option_chain(self, symbol: str, expiration_date: str) -> dict:
        """Retrieve option chain data."""
        if symbol not in self.option_chains or expiration_date not in self.option_chains[symbol]:
            raise ValueError(f"Option chain data not found for {symbol} on {expiration_date}")
        
        chain_data = self.option_chains[symbol][expiration_date]
        return {
            "underlyingPrice": chain_data.get("underlyingPrice", 0),
            "calls": [c.model_dump() for c in chain_data.get("calls", [])],
            "puts": [p.model_dump() for p in chain_data.get("puts", [])]
        }

# Section 3: MCP Tools
mcp = FastMCP(name="YahooFinance")
api = YahooFinanceAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Yahoo Finance API.
    
    Args:
        scenario (dict): Scenario dictionary matching YahooFinanceScenario schema.
    
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
    Save current Yahoo Finance state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_current_stock_price(symbol: str) -> dict:
    """
    Retrieve the current real-time market price for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
    
    Returns:
        current_price (str): Current market price as formatted string.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_current_stock_price(symbol)
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_price_by_date(symbol: str, date: str) -> dict:
    """
    Retrieve opening and closing stock prices for a given symbol on a specific date.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        date (str): Trading date in YYYY-MM-DD format.
    
    Returns:
        date (str): Trading date.
        open (float): Opening price.
        close (float): Closing price.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not date or not isinstance(date, str):
            raise ValueError("Date must be a non-empty string")
        return api.get_stock_price_by_date(symbol, date)
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_price_date_range(symbol: str, start_date: str, end_date: str) -> dict:
    """
    Retrieve historical daily closing prices for a given stock symbol over a date range.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
    
    Returns:
        closing_prices (dict): Dictionary mapping dates to closing prices.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not start_date or not isinstance(start_date, str):
            raise ValueError("Start date must be a non-empty string")
        if not end_date or not isinstance(end_date, str):
            raise ValueError("End date must be a non-empty string")
        return api.get_stock_price_date_range(symbol, start_date, end_date)
    except Exception as e:
        raise e

@mcp.tool()
def get_historical_stock_prices(symbol: str, period: str = "1mo", interval: str = "1d") -> dict:
    """
    Retrieve comprehensive historical OHLC price data and volume for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        period (str): [Optional] Time period for historical data. Default: '1mo'.
        interval (str): [Optional] Data sampling interval. Default: '1d'.
    
    Returns:
        price_history (list): Array of historical price data objects.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_historical_stock_prices(symbol, period, interval)
    except Exception as e:
        raise e

@mcp.tool()
def get_dividends(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Retrieve dividend payment history for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        start_date (str): [Optional] Start date in YYYY-MM-DD format.
        end_date (str): [Optional] End date in YYYY-MM-DD format.
    
    Returns:
        dividends (dict): Dictionary mapping dividend dates to amounts.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_dividends(symbol, start_date, end_date)
    except Exception as e:
        raise e

@mcp.tool()
def get_income_statement(symbol: str, freq: str = "yearly") -> dict:
    """
    Retrieve the income statement for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        freq (str): [Optional] Reporting frequency. Default: 'yearly'.
    
    Returns:
        income_statements (dict): Income statement data organized by reporting period.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_income_statement(symbol, freq)
    except Exception as e:
        raise e

@mcp.tool()
def get_cashflow(symbol: str, freq: str = "yearly") -> dict:
    """
    Retrieve the cash flow statement for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        freq (str): [Optional] Reporting frequency. Default: 'yearly'.
    
    Returns:
        cashflow_statements (dict): Cash flow statement data organized by reporting period.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_cashflow(symbol, freq)
    except Exception as e:
        raise e

@mcp.tool()
def get_earning_dates(symbol: str, limit: int = 12) -> dict:
    """
    Retrieve historical and upcoming earnings announcement dates for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        limit (int): [Optional] Maximum number of earnings dates. Default: 12.
    
    Returns:
        earnings_dates (list): Array of earnings announcement records.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_earning_dates(symbol, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_news(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 50) -> dict:
    """
    Retrieve news articles related to a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        start_date (str): [Optional] Start date in YYYY-MM-DD format.
        end_date (str): [Optional] End date in YYYY-MM-DD format.
        limit (int): [Optional] Maximum number of articles. Default: 50.
    
    Returns:
        news_articles (list): Array of news items sorted by relevance.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_news(symbol, start_date, end_date, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_recommendations(symbol: str) -> dict:
    """
    Retrieve analyst recommendations for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
    
    Returns:
        recommendations (list): Array of analyst recommendation records.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_recommendations(symbol)
    except Exception as e:
        raise e

@mcp.tool()
def get_option_expiration_dates(symbol: str) -> dict:
    """
    Retrieve all available options expiration dates for a given stock symbol.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
    
    Returns:
        expiration_dates (list): Array of available expiration dates.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return api.get_option_expiration_dates(symbol)
    except Exception as e:
        raise e

@mcp.tool()
def get_option_chain(symbol: str, expiration_date: str) -> dict:
    """
    Retrieve the complete options chain for a specific expiration date.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format.
        expiration_date (str): Options expiration date in YYYY-MM-DD format.
    
    Returns:
        underlyingPrice (float): Current price of underlying stock.
        calls (list): Array of call option contracts.
        puts (list): Array of put option contracts.
    """
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not expiration_date or not isinstance(expiration_date, str):
            raise ValueError("Expiration date must be a non-empty string")
        return api.get_option_chain(symbol, expiration_date)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()