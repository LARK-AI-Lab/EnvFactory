# Server: YahooFinance

def get_current_stock_price(symbol: str) -> str:
    """
    Retrieve the current real-time stock price for a given stock symbol.
    
    This function fetches the latest market price (last traded price) for a stock symbol.
    The price reflects the most recent transaction executed on the exchange.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format. Examples: "AAPL" for Apple Inc., 
                     "GOOGL" for Alphabet Inc. Class A shares, "MSFT" for Microsoft Corporation.
        
    Returns:
        str: Current market price as a formatted string (e.g., "150.25" for $150.25)
    """
    pass

def get_stock_price_by_date(symbol: str, date: str) -> str:
    """
    Retrieve stock price data for a given stock symbol on a specific trading date.
    
    This function returns both the opening price (the first trade price of the day) and 
    closing price (the last trade price of the day) for the specified date. The opening 
    price indicates market sentiment at the start of trading, while the closing price is 
    commonly used as a reference point for daily price movements.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "MSFT", "AAPL")
        date (str): The trading date in YYYY-MM-DD format (e.g., "2024-01-15"). 
                   Must be a valid trading day (not weekends or market holidays).
        
    Returns:
        str: JSON string containing price data with the following structure:
             {"date": "YYYY-MM-DD", "open": float, "close": float}
             Example: '{"date": "2024-01-15", "open": 150.25, "close": 152.30}'
    """
    pass

def get_stock_price_date_range(symbol: str, start_date: str, end_date: str) -> str:
    """
    Retrieve historical stock closing prices for a given stock symbol over a specified date range.
    
    This function returns daily closing prices (the final trade price of each trading day) 
    for all trading days within the specified range. Closing prices are fundamental metrics 
    used in technical analysis and portfolio valuation.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "TSLA")
        start_date (str): The start date (inclusive) in YYYY-MM-DD format (e.g., "2024-01-01")
        end_date (str): The end date (inclusive) in YYYY-MM-DD format (e.g., "2024-12-31")
        
    Returns:
        str: JSON string containing a dictionary mapping dates to closing prices.
             Format: {"YYYY-MM-DD": float, ...}
             Example: '{"2024-01-15": 150.25, "2024-01-16": 152.30, ...}'
             Only includes trading days (excludes weekends and market holidays).
    """
    pass

def get_historical_stock_prices(
    symbol: str, 
    period: str = "1mo", 
    interval: str = "1d"
) -> str:
    """
    Retrieve historical stock price data for a given stock symbol with flexible period and interval options.
    
    This function provides comprehensive historical price data including open, high, low, close (OHLC) 
    prices and volume. The period parameter determines how far back to fetch data, while interval 
    controls the granularity of data points.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "GOOGL")
        period (str): [Optional] Time period for historical data. Options:
                     - "1d", "5d": Last 1 or 5 trading days
                     - "1mo", "3mo", "6mo": Last 1, 3, or 6 months
                     - "1y", "2y", "5y", "10y": Last 1, 2, 5, or 10 years
                     - "ytd": Year to date (from January 1st to today)
                     - "max": Maximum available historical data
                     Default: "1mo"
        interval (str): [Optional] Data sampling interval. Options:
                       - "1d": Daily data (one data point per trading day)
                       - "5d": Every 5 days
                       - "1wk": Weekly data (one data point per week)
                       - "1mo": Monthly data (one data point per month)
                       - "3mo": Quarterly data (one data point per quarter)
                       Default: "1d"
        
    Returns:
        str: JSON string containing an array of price data objects. Each object includes:
             {"date": "YYYY-MM-DD", "open": float, "high": float, "low": float, 
              "close": float, "volume": int}
             Example: '[{"date": "2024-01-15", "open": 150.25, "high": 152.00, 
                        "low": 149.50, "close": 151.75, "volume": 50000000}, ...]'
    """
    pass

def get_dividends(symbol: str, start_date: str = None, end_date: str = None) -> str:
    """
    Retrieve dividend payment history for a given stock symbol, optionally filtered by date range.
    
    Dividends are periodic cash payments made by companies to shareholders from their profits. 
    This function returns historical dividend payments including the payment date (ex-dividend date) 
    and the dividend amount per share. Dividend data is essential for calculating total return 
    and yield analysis.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "KO")
        start_date (str): [Optional] Start date (inclusive) in YYYY-MM-DD format for filtering 
                         dividend history. If None, returns all available historical dividends.
        end_date (str): [Optional] End date (inclusive) in YYYY-MM-DD format for filtering 
                       dividend history. If None, returns dividends up to the most recent payment.
        
    Returns:
        str: JSON string containing a dictionary mapping dividend payment dates to amounts.
             Format: {"YYYY-MM-DD": float, ...}
             Example: '{"2024-03-15": 0.24, "2024-06-15": 0.24, "2024-09-15": 0.24, ...}'
             Values represent dividend amount per share in the stock's currency.
    """
    pass

def get_income_statement(symbol: str, freq: str = "yearly") -> str:
    """
    Retrieve the income statement (profit and loss statement) for a given stock symbol.
    
    An income statement is a financial report showing a company's revenues, expenses, and profits 
    over a specific period. It includes key metrics like total revenue, cost of goods sold (COGS), 
    operating income, net income, and earnings per share (EPS). This data is crucial for fundamental 
    analysis and assessing a company's profitability.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "MSFT")
        freq (str): [Optional] Reporting frequency. Options:
                   - "yearly": Annual financial statements (fiscal year)
                   - "quarterly": Quarterly financial statements (Q1, Q2, Q3, Q4)
                   - "trailing": Trailing twelve months (TTM) - most recent 12 months of data
                   Default: "yearly"
        
    Returns:
        str: JSON string containing income statement data with financial metrics organized by period.
             Includes fields such as: totalRevenue, costOfRevenue, grossProfit, operatingIncome, 
             netIncome, earningsPerShare, etc.
             Example: '{"2023": {"totalRevenue": 383285000000, "netIncome": 99803000000, ...}, ...}'
    """
    pass

def get_cashflow(symbol: str, freq: str = "yearly") -> str:
    """
    Retrieve the cash flow statement for a given stock symbol.
    
    A cash flow statement shows how cash moves in and out of a company through operating activities 
    (day-to-day business), investing activities (capital expenditures, acquisitions), and financing 
    activities (debt, equity transactions). It helps assess a company's liquidity, solvency, and 
    ability to generate cash. Free cash flow (FCF) is a key metric derived from this statement.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "AMZN")
        freq (str): [Optional] Reporting frequency. Options:
                   - "yearly": Annual cash flow statements (fiscal year)
                   - "quarterly": Quarterly cash flow statements (Q1, Q2, Q3, Q4)
                   - "trailing": Trailing twelve months (TTM) - most recent 12 months of data
                   Default: "yearly"
        
    Returns:
        str: JSON string containing cash flow statement data organized by period.
             Includes fields such as: operatingCashFlow, capitalExpenditure, freeCashFlow, 
             netBorrowings, etc.
             Example: '{"2023": {"operatingCashFlow": 110543000000, "freeCashFlow": 99584000000, ...}, ...}'
    """
    pass

def get_earning_dates(symbol: str, limit: int = 12) -> str:
    """
    Retrieve earnings announcement dates (both historical and upcoming) for a given stock symbol.
    
    Earnings dates mark when companies publicly release their quarterly or annual financial results. 
    These announcements often cause significant stock price movements. The function returns both 
    past earnings dates (with actual results) and future earnings dates (with analyst estimates).
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "TSLA")
        limit (int): [Optional] Maximum number of earnings dates to return (combines both past 
                    and upcoming dates). Default: 12
        
    Returns:
        str: JSON string containing an array of earnings date records. Each record includes:
             {"date": "YYYY-MM-DD", "type": "quarterly"|"annual", "actualEPS": float|null, 
              "estimatedEPS": float|null, "surprise": float|null}
             Example: '[{"date": "2024-01-25", "type": "quarterly", "actualEPS": 2.18, ...}, ...]'
             surprise indicates the difference between actual and estimated EPS.
    """
    pass

def get_news(
    symbol: str, 
    start_date: str = None, 
    end_date: str = None,
    limit: int = 50
) -> str:
    """
    Retrieve news articles and press releases related to a given stock symbol, optionally filtered by date range.
    
    News articles can significantly impact stock prices. This function fetches relevant financial news, 
    company announcements, analyst reports, and market commentary. Filtering by date helps focus on 
    recent developments or specific time periods of interest.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "NVDA")
        start_date (str): [Optional] Start date (inclusive) in YYYY-MM-DD format for filtering news.
                         If None, returns the most recent news without a lower date bound.
        end_date (str): [Optional] End date (inclusive) in YYYY-MM-DD format for filtering news.
                       If None, returns news up to the current date.
        limit (int): [Optional] Maximum number of news articles to return. Default: 50
        
    Returns:
        str: JSON string containing an array of news items. Each item includes:
             {"title": str, "link": str, "publisher": str, "publishDate": "YYYY-MM-DD", 
              "summary": str}
             Example: '[{"title": "Apple Reports Record Q4 Earnings", "link": "https://...", 
                        "publisher": "Reuters", "publishDate": "2024-01-25", ...}, ...]'
             Articles are sorted by relevance and recency.
    """
    pass

def get_recommendations(symbol: str) -> str:
    """
    Retrieve analyst recommendations and price targets for a given stock symbol.
    
    Analyst recommendations are investment opinions issued by financial research firms and 
    investment banks. They typically include ratings (e.g., "Buy", "Hold", "Sell") and price 
    targets (expected future stock price). These recommendations influence investor sentiment 
    and can affect stock prices.
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "GOOGL")
        
    Returns:
        str: JSON string containing an array of recommendation records. Each record includes:
             {"firm": str, "rating": str, "priceTarget": float|null, "date": "YYYY-MM-DD"}
             Example: '[{"firm": "Goldman Sachs", "rating": "Buy", "priceTarget": 200.00, 
                        "date": "2024-01-15"}, ...]'
             Common ratings: "Strong Buy", "Buy", "Hold", "Underperform", "Sell".
    """
    pass

def get_option_expiration_dates(symbol: str) -> str:
    """
    Retrieve all available options expiration dates for a given stock symbol.
    
    Options are derivative contracts that give the holder the right (but not obligation) to buy 
    (call) or sell (put) a stock at a specific price (strike price) before or on the expiration 
    date. This function returns all dates when options contracts expire, typically occurring on 
    Fridays (weekly options) or the third Friday of each month (monthly options).
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "SPY")
        
    Returns:
        str: JSON string containing an array of expiration dates in YYYY-MM-DD format.
             Example: '["2024-01-19", "2024-01-26", "2024-02-02", "2024-02-16", ...]'
             Dates are sorted chronologically and include both weekly and monthly expirations.
    """
    pass

def get_option_chain(symbol: str, expiration_date: str) -> str:
    """
    Retrieve the complete options chain for a specific expiration date.
    
    An options chain displays all available call and put options for a stock at a given expiration 
    date, organized by strike prices. Call options give the right to buy the stock, while put 
    options give the right to sell. Each option shows its bid price (what buyers are willing to pay), 
    ask price (what sellers want), open interest (number of contracts), and implied volatility 
    (expected price movement).
    
    Args:
        symbol (str): Stock symbol (ticker) in Yahoo Finance format (e.g., "AAPL", "TSLA")
        expiration_date (str): Options expiration date in YYYY-MM-DD format. Must be a valid 
                               expiration date returned by get_option_expiration_dates().
        
    Returns:
        str: JSON string containing an object with the following structure:
             {"underlyingPrice": float, "calls": [...], "puts": [...]}
             Each call/put entry includes: {"strike": float, "bid": float, "ask": float, 
             "volume": int, "openInterest": int, "impliedVolatility": float}
             Example: '{"underlyingPrice": 150.25, "calls": [{"strike": 145, "bid": 6.50, ...}, ...], 
                        "puts": [{"strike": 145, "bid": 1.20, ...}, ...]}'
    """
    pass
