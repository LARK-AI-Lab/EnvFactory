# Server: TradingBot

def login(username: str, password: str) -> dict:
    """
    Authenticate user and establish session for trading operations.
    
    Args:
        username (str): The username for authentication
        password (str): The password for authentication
        
    Returns:
        dict: A dictionary containing status (str) indicating login success or failure, session_token (str) [Optional] session token if login successful.
    """
    pass

def logout() -> dict:
    """
    Log out the currently authenticated user and invalidate session.
    
    Returns:
        dict: A dictionary containing status (str) indicating logout success or failure.
    """
    pass

def check_login_status() -> dict:
    """
    Check if a user is currently authenticated and session is valid.
    
    Returns:
        dict: A dictionary containing is_authenticated (bool) indicating current authentication status.
    """
    pass


def get_market_status() -> dict:
    """
    Get the current market status (Open or Closed) based on trading hours.
    
    Returns:
        dict: A dictionary containing status (str) [Enum]: ["Open", "Closed"], current_time (str) in HH:MM AM/PM format.
    """
    pass

def get_account_info() -> dict:
    """
    Get account information including balance and account details. Requires authentication.
    
    Returns:
        dict: A dictionary containing account_id (int), balance (float) current account balance, binding_card (int) [Optional] card number associated with account, currency (str) typically "USD".
    """
    pass

def make_transaction(transaction_type: str, amount: float) -> dict:
    """
    Make a deposit or withdrawal transaction. Requires authentication and market must be open for withdrawals.
    
    Args:
        transaction_type (str): The type of transaction. [Enum]: ["deposit", "withdrawal"]
        amount (float): The amount to deposit or withdraw. Must be positive.
        
    Returns:
        dict: A dictionary containing status (str) indicating transaction success or failure, new_balance (float) updated account balance, timestamp (str) transaction timestamp in YYYY-MM-DD HH:MM:SS format.
    """
    pass

def get_transaction_history(start_date: str = None, end_date: str = None) -> list:
    """
    Get transaction history within a specified date range. Requires authentication.
    
    Args:
        start_date (str): [Optional] Start date for filtering transactions in format YYYY-MM-DD. If not provided, shows all transactions.
        end_date (str): [Optional] End date for filtering transactions in format YYYY-MM-DD. If not provided, shows all transactions.
        
    Returns:
        list: A list of transactions, each containing transaction_id (str), type (str) [Enum]: ["deposit", "withdrawal"], amount (float), timestamp (str) in YYYY-MM-DD HH:MM:SS format.
    """
    pass

def get_stock_symbol(company_name: str) -> dict:
    """
    Get the stock symbol for a given company name.
    
    Args:
        company_name (str): The name of the company. [Enum]: ["Apple", "Google", "Tesla", "Microsoft", "Nvidia", "Amazon", "Zeta Corp", "Alpha Tech", "Omega Industries", "Quasar Ltd.", "Neptune Systems", "Synex Solutions"]
        
    Returns:
        dict: A dictionary containing symbol (str) the stock symbol, company_name (str) the input company name.
    """
    pass

def get_stock_info(symbol: str) -> dict:
    """
    Get detailed information about a stock including price, volume, and moving averages.
    
    Args:
        symbol (str): The stock symbol (e.g., "AAPL", "GOOG", "TSLA"). Can be obtained from get_stock_symbol or get_available_stocks.
        
    Returns:
        dict: A dictionary containing symbol (str), price (float) current stock price, percent_change (float) percentage change in price, volume (float) trading volume, ma_5 (float) 5-day moving average, ma_20 (float) 20-day moving average.
    """
    pass

def get_available_stocks(sector: str) -> list:
    """
    Get a list of stock symbols available in a specific sector.
    
    Args:
        sector (str): The sector to retrieve stocks from. [Enum]: ["Technology", "Automobile", "Finance", "Healthcare", "Energy"]
        
    Returns:
        list: A list of stock symbols (str) available in the specified sector. Can be used with get_stock_info to get detailed information.
    """
    pass

def filter_stocks_by_price(symbols: list, min_price: float, max_price: float) -> list:
    """
    Filter a list of stocks based on price range.
    
    Args:
        symbols (list): List of stock symbols to filter. Can be obtained from get_available_stocks.
        min_price (float): Minimum stock price for filtering
        max_price (float): Maximum stock price for filtering
        
    Returns:
        list: A filtered list of stock symbols (str) within the specified price range. Can be used with get_stock_info for detailed information.
    """
    pass

def place_order(order_type: str, symbol: str, price: float, quantity: int) -> dict:
    """
    Place a buy or sell order for a stock. Requires authentication and market must be open.
    
    Args:
        order_type (str): The type of order. [Enum]: ["Buy", "Sell"]
        symbol (str): The stock symbol to trade. Can be obtained from get_stock_symbol or get_available_stocks.
        price (float): The price per share at which to place the order. Must be positive.
        quantity (int): The number of shares to trade. Must be positive.
        
    Returns:
        dict: A dictionary containing order_id (int) unique order identifier, order_type (str), symbol (str), price (float), quantity (int), status (str) [Enum]: ["Pending", "Open", "Completed", "Cancelled"], timestamp (str) order placement time.
    """
    pass

def get_order_details(order_id: int) -> dict:
    """
    Get detailed information about a specific order. Requires authentication.
    
    Args:
        order_id (int): The order ID obtained from place_order or get_order_history.
        
    Returns:
        dict: A dictionary containing order_id (int), order_type (str) [Enum]: ["Buy", "Sell"], symbol (str), price (float), quantity (int), status (str) [Enum]: ["Open", "Pending", "Completed", "Cancelled"], timestamp (str) order placement time, execution_price (float) [Optional] actual execution price if completed.
    """
    pass

def cancel_order(order_id: int) -> dict:
    """
    Cancel a pending or open order. Requires authentication. Cannot cancel completed orders.
    
    Args:
        order_id (int): The order ID obtained from place_order or get_order_history.
        
    Returns:
        dict: A dictionary containing order_id (int), status (str) [Enum]: ["Cancelled", "Error"], message (str) [Optional] error message if cancellation failed.
    """
    pass

def get_order_history(status: str = None, symbol: str = None) -> list:
    """
    Get order history with optional filtering by status or symbol. Requires authentication.
    
    Args:
        status (str): [Optional] Filter orders by status. [Enum]: ["Open", "Pending", "Completed", "Cancelled"]. If not provided, returns all orders.
        symbol (str): [Optional] Filter orders by stock symbol. If not provided, returns orders for all symbols.
        
    Returns:
        list: A list of order summaries, each containing order_id (int), order_type (str), symbol (str), price (float), quantity (int), status (str), timestamp (str). Order IDs can be used with get_order_details for full information.
    """
    pass

def get_watchlist() -> list:
    """
    Get the list of stocks currently in the watchlist. Requires authentication.
    
    Returns:
        list: A list of stock symbols (str) in the watchlist. Can be used with get_stock_info to get current prices and information.
    """
    pass

def add_to_watchlist(symbol: str) -> dict:
    """
    Add a stock to the watchlist. Requires authentication.
    
    Args:
        symbol (str): The stock symbol to add. Can be obtained from get_stock_symbol or get_available_stocks.
        
    Returns:
        dict: A dictionary containing status (str) indicating success or failure, symbol (str) the added symbol, watchlist (list) updated list of symbols in watchlist.
    """
    pass

def remove_from_watchlist(symbol: str) -> dict:
    """
    Remove a stock from the watchlist. Requires authentication.
    
    Args:
        symbol (str): The stock symbol to remove. Can be obtained from get_watchlist.
        
    Returns:
        dict: A dictionary containing status (str) indicating success or failure, symbol (str) the removed symbol, watchlist (list) updated list of symbols in watchlist.
    """
    pass

def notify_price_change(symbols: list, threshold: float) -> dict:
    """
    Check if stocks in the provided list have significant price changes exceeding the threshold.
    
    Args:
        symbols (list): List of stock symbols to monitor. Can be obtained from get_watchlist or get_available_stocks.
        threshold (float): Percentage change threshold to trigger notification. Must be positive.
        
    Returns:
        dict: A dictionary containing notification (str) message about price changes, changed_stocks (list) [Optional] list of symbols with significant changes, details (list) [Optional] list of dicts containing symbol (str), current_price (float), percent_change (float) for each changed stock.
    """
    pass

def update_stock_price(symbol: str, new_price: float) -> dict:
    """
    Update the price of a stock. This is typically used for testing or simulation purposes.
    
    Args:
        symbol (str): The stock symbol to update. Can be obtained from get_stock_symbol or get_available_stocks.
        new_price (float): The new price for the stock. Must be positive.
        
    Returns:
        dict: A dictionary containing symbol (str), old_price (float) previous price, new_price (float) updated price, percent_change (float) calculated percentage change.
    """
    pass

