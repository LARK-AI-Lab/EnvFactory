from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class User(BaseModel):
    """Represents a user account."""
    username: str = Field(..., description="Username credential")
    password: str = Field(..., description="Password credential")

class Account(BaseModel):
    """Represents a trading account."""
    account_id: int = Field(..., ge=1, description="Unique account identifier")
    balance: float = Field(..., ge=0, description="Available balance")
    currency: str = Field(default="USD", description="Account currency")
    binding_card: Optional[int] = Field(default=None, description="Linked card number")

class Stock(BaseModel):
    """Represents a stock."""
    symbol: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., gt=0, description="Current price per share")
    percent_change: float = Field(..., description="Percentage change in price")
    volume: int = Field(..., ge=0, description="Trading volume")
    ma_5: float = Field(..., description="5-day moving average")
    ma_20: float = Field(..., description="20-day moving average")

class Order(BaseModel):
    """Represents a trading order."""
    order_id: int = Field(..., ge=1, description="Unique order identifier")
    order_type: str = Field(..., description="Order type: Buy or Sell")
    symbol: str = Field(..., description="Stock symbol")
    price: float = Field(..., gt=0, description="Order price per share")
    quantity: int = Field(..., gt=0, description="Number of shares")
    status: str = Field(..., description="Order status")
    timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Order timestamp")
    execution_price: Optional[float] = Field(default=None, description="Execution price if completed")

class Transaction(BaseModel):
    """Represents a financial transaction."""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    type: str = Field(..., description="Transaction type: deposit or withdrawal")
    amount: float = Field(..., gt=0, description="Transaction amount")
    timestamp: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Transaction timestamp")

class TradingScenario(BaseModel):
    """Main scenario model for trading platform."""
    users: Dict[str, User] = Field(default={}, description="Registered users")
    accounts: Dict[int, Account] = Field(default={}, description="User accounts")
    current_user: Optional[str] = Field(default=None, description="Currently logged in user")
    session_token: Optional[str] = Field(default=None, description="Active session token")
    market_open: bool = Field(default=True, description="Market status")
    current_time: str = Field(default="09:30 AM", description="Current market time")
    stocks: Dict[str, Stock] = Field(default={
        "AAPL": Stock(symbol="AAPL", price=150.25, percent_change=1.2, volume=50000000, ma_5=149.5, ma_20=148.0),
        "GOOG": Stock(symbol="GOOG", price=2750.8, percent_change=-0.5, volume=1500000, ma_5=2760.0, ma_20=2745.0),
        "TSLA": Stock(symbol="TSLA", price=800.15, percent_change=2.8, volume=25000000, ma_5=790.0, ma_20=785.0),
        "MSFT": Stock(symbol="MSFT", price=305.6, percent_change=0.3, volume=20000000, ma_5=304.0, ma_20=302.5),
        "NVDA": Stock(symbol="NVDA", price=220.75, percent_change=-1.2, volume=18000000, ma_5=222.0, ma_20=218.0),
        "AMZN": Stock(symbol="AMZN", price=3200.4, percent_change=0.8, volume=3000000, ma_5=3180.0, ma_20=3150.0),
        "ZETA": Stock(symbol="ZETA", price=45.3, percent_change=3.5, volume=5000000, ma_5=44.0, ma_20=43.0),
        "ALPH": Stock(symbol="ALPH", price=120.9, percent_change=-2.1, volume=2000000, ma_5=123.0, ma_20=125.0),
        "OMEG": Stock(symbol="OMEG", price=78.45, percent_change=1.7, volume=1500000, ma_5=77.0, ma_20=76.0),
        "QUAS": Stock(symbol="QUAS", price=234.6, percent_change=0.9, volume=800000, ma_5=233.0, ma_20=230.0),
        "NEPT": Stock(symbol="NEPT", price=89.12, percent_change=-0.8, volume=1200000, ma_5=90.0, ma_20=91.0),
        "SYNX": Stock(symbol="SYNX", price=156.78, percent_change=2.3, volume=900000, ma_5=154.0, ma_20=152.0)
    }, description="Available stocks")
    company_symbols: Dict[str, str] = Field(default={
        "Apple": "AAPL", "Google": "GOOG", "Tesla": "TSLA", "Microsoft": "MSFT",
        "Nvidia": "NVDA", "Amazon": "AMZN", "Zeta Corp": "ZETA", "Alpha Tech": "ALPH",
        "Omega Industries": "OMEG", "Quasar Ltd.": "QUAS", "Neptune Systems": "NEPT", "Synex Solutions": "SYNX"
    }, description="Company to symbol mapping")
    sector_stocks: Dict[str, List[str]] = Field(default={
        "Technology": ["AAPL", "GOOG", "MSFT", "NVDA"],
        "Automobile": ["TSLA"],
        "Finance": [],
        "Healthcare": [],
        "Energy": []
    }, description="Stocks by sector")
    orders: Dict[int, Order] = Field(default={}, description="All orders")
    transactions: List[Transaction] = Field(default=[], description="Transaction history")
    watchlists: Dict[str, List[str]] = Field(default={}, description="User watchlists")
    next_order_id: int = Field(default=1, description="Next order ID")
    next_transaction_id: int = Field(default=1, description="Next transaction ID")
    current_time: str = Field(default="2024-01-01 00:00:00", pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Current timestamp in YYYY-MM-DD HH:mm:ss format")

Scenario_Schema = [User, Account, Stock, Order, Transaction, TradingScenario]

# Section 2: Class
class TradingBot:
    def __init__(self):
        """Initialize trading bot with empty state."""
        self.users: Dict[str, User] = {}
        self.accounts: Dict[int, Account] = {}
        self.current_user: Optional[str] = None
        self.session_token: Optional[str] = None
        self.market_open: bool = True
        self.current_time: str = "09:30 AM"
        self.stocks: Dict[str, Stock] = {}
        self.company_symbols: Dict[str, str] = {}
        self.sector_stocks: Dict[str, List[str]] = {}
        self.orders: Dict[int, Order] = {}
        self.transactions: List[Transaction] = []
        self.watchlists: Dict[str, List[str]] = {}
        self.next_order_id: int = 1
        self.next_transaction_id: int = 1
        self.current_time: str = "2024-01-01 00:00:00"

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the trading bot."""
        model = TradingScenario(**scenario)
        self.users = model.users
        self.accounts = model.accounts
        self.current_user = model.current_user
        self.session_token = model.session_token
        self.market_open = model.market_open
        self.current_time = model.current_time
        self.stocks = model.stocks
        self.company_symbols = model.company_symbols
        self.sector_stocks = model.sector_stocks
        self.orders = model.orders
        self.transactions = model.transactions
        self.watchlists = model.watchlists
        self.next_order_id = model.next_order_id
        self.next_transaction_id = model.next_transaction_id
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "users": {username: user.model_dump() for username, user in self.users.items()},
            "accounts": {account_id: account.model_dump() for account_id, account in self.accounts.items()},
            "current_user": self.current_user,
            "session_token": self.session_token,
            "market_open": self.market_open,
            "current_time": self.current_time,
            "stocks": {symbol: stock.model_dump() for symbol, stock in self.stocks.items()},
            "company_symbols": self.company_symbols,
            "sector_stocks": self.sector_stocks,
            "orders": {order_id: order.model_dump() for order_id, order in self.orders.items()},
            "transactions": [transaction.model_dump() for transaction in self.transactions],
            "watchlists": self.watchlists,
            "next_order_id": self.next_order_id,
            "next_transaction_id": self.next_transaction_id,
            "current_time": self.current_time
        }

    def login(self, username: str, password: str) -> dict:
        """Authenticate user and establish trading session."""
        if username in self.users and self.users[username].password == password:
            self.current_user = username
            # Generate session token using current_time
            time_hash = hash(self.current_time) % 100000
            self.session_token = f"token_{username}_{time_hash}"
            return {"status": "success", "session_token": self.session_token}
        return {"status": "failed"}

    def logout(self) -> dict:
        """Terminate current user session."""
        if self.current_user:
            self.current_user = None
            self.session_token = None
            return {"status": "success"}
        return {"status": "failed"}

    def check_login_status(self) -> dict:
        """Check if user session is active."""
        return {"is_authenticated": self.current_user is not None}

    def get_market_status(self) -> dict:
        """Retrieve current market status."""
        return {"status": "Open" if self.market_open else "Closed", "current_time": self.current_time}

    def get_account_info(self) -> dict:
        """Get account information for authenticated user."""
        if not self.current_user:
            return {}
        
        # Find account for current user - look for any account since scenarios use various IDs
        for account in self.accounts.values():
            return account.model_dump()
        return {}

    def make_transaction(self, transaction_type: str, amount: float) -> dict:
        """Execute deposit or withdrawal transaction."""
        if not self.current_user:
            return {"status": "failed", "new_balance": 0, "timestamp": ""}
        
        # Find any available account for the current user
        account = None
        for acc in self.accounts.values():
            account = acc
            break
            
        if not account:
            return {"status": "failed", "new_balance": 0, "timestamp": ""}
        
        if transaction_type == "withdrawal" and not self.market_open:
            return {"status": "failed", "new_balance": account.balance, "timestamp": ""}
        
        if transaction_type == "withdrawal" and account.balance < amount:
            return {"status": "failed", "new_balance": account.balance, "timestamp": ""}
        
        if transaction_type == "deposit":
            account.balance += amount
        else:
            account.balance -= amount
        
        transaction = Transaction(
            transaction_id=f"TXN{self.next_transaction_id:06d}",
            type=transaction_type,
            amount=amount,
            timestamp=self.current_time
        )
        self.transactions.append(transaction)
        self.next_transaction_id += 1
        
        return {"status": "success", "new_balance": account.balance, "timestamp": self.current_time}

    def get_transaction_history(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        """Get transaction history with optional date filtering."""
        if not self.current_user:
            return {"transactions": []}
        
        filtered_transactions = []
        for transaction in self.transactions:
            if start_date and transaction.timestamp < start_date:
                continue
            if end_date and transaction.timestamp > end_date + " 23:59:59":
                continue
            filtered_transactions.append(transaction.model_dump())
        
        return {"transactions": filtered_transactions}

    def get_stock_symbol(self, company_name: str) -> dict:
        """Get stock symbol for company name."""
        if company_name in self.company_symbols:
            return {"symbol": self.company_symbols[company_name], "company_name": company_name}
        return {"symbol": "", "company_name": company_name}

    def get_stock_info(self, symbol: str) -> dict:
        """Get comprehensive stock information."""
        if symbol in self.stocks:
            return self.stocks[symbol].model_dump()
        return {}

    def get_available_stocks(self, sector: str) -> dict:
        """Get available stocks in specified sector."""
        if sector in self.sector_stocks:
            return {"symbols": self.sector_stocks[sector]}
        return {"symbols": []}

    def filter_stocks_by_price(self, symbols: List[str], min_price: float, max_price: float) -> dict:
        """Filter stocks by price range."""
        filtered = []
        for symbol in symbols:
            if symbol in self.stocks and min_price <= self.stocks[symbol].price <= max_price:
                filtered.append(symbol)
        return {"filtered_symbols": filtered}

    def place_order(self, order_type: str, symbol: str, price: float, quantity: int) -> dict:
        """Place buy or sell order."""
        if not self.current_user or not self.market_open:
            return {}
        
        if symbol not in self.stocks:
            return {}
        
        # Find any available account for the current user
        account = None
        for acc in self.accounts.values():
            account = acc
            break
            
        if not account:
            return {}
        
        if order_type == "Buy" and account.balance < price * quantity:
            return {}
        
        order = Order(
            order_id=self.next_order_id,
            order_type=order_type,
            symbol=symbol,
            price=price,
            quantity=quantity,
            status="Pending",
            timestamp=self.current_time
        )
        
        self.orders[self.next_order_id] = order
        self.next_order_id += 1
        
        if order_type == "Buy":
            account.balance -= price * quantity
        
        return order.model_dump()

    def get_order_details(self, order_id: int) -> dict:
        """Get detailed order information."""
        if order_id in self.orders:
            return self.orders[order_id].model_dump()
        return {}

    def cancel_order(self, order_id: int) -> dict:
        """Cancel pending or open order."""
        if order_id not in self.orders:
            return {"order_id": order_id, "status": "Error", "message": "Order not found"}
        
        order = self.orders[order_id]
        if order.status in ["Completed", "Cancelled"]:
            return {"order_id": order_id, "status": "Error", "message": "Cannot cancel completed or cancelled order"}
        
        if order.status == "Pending":
            order.status = "Cancelled"
            if order.order_type == "Buy":
                # Find any available account to refund
                account = None
                for acc in self.accounts.values():
                    account = acc
                    break
                if account:
                    account.balance += order.price * order.quantity
            return {"order_id": order_id, "status": "Cancelled"}
        
        return {"order_id": order_id, "status": "Error", "message": "Cannot cancel order in current status"}

    def get_order_history(self, status: Optional[str] = None, symbol: Optional[str] = None) -> dict:
        """Get order history with optional filtering."""
        if not self.current_user:
            return {"orders": []}
        
        filtered_orders = []
        for order in self.orders.values():
            if status and order.status != status:
                continue
            if symbol and order.symbol != symbol:
                continue
            filtered_orders.append(order.model_dump())
        
        return {"orders": filtered_orders}

    def get_watchlist(self) -> dict:
        """Get user's watchlist."""
        if not self.current_user:
            return {"watchlist_symbols": []}
        
        if self.current_user not in self.watchlists:
            self.watchlists[self.current_user] = []
        
        return {"watchlist_symbols": self.watchlists[self.current_user]}

    def add_to_watchlist(self, symbol: str) -> dict:
        """Add stock to watchlist."""
        if not self.current_user or symbol not in self.stocks:
            return {"status": "failed", "symbol": symbol, "watchlist": []}
        
        if self.current_user not in self.watchlists:
            self.watchlists[self.current_user] = []
        
        if symbol not in self.watchlists[self.current_user]:
            self.watchlists[self.current_user].append(symbol)
        
        return {"status": "success", "symbol": symbol, "watchlist": self.watchlists[self.current_user]}

    def remove_from_watchlist(self, symbol: str) -> dict:
        """Remove stock from watchlist."""
        if not self.current_user:
            return {"status": "failed", "symbol": symbol, "watchlist": []}
        
        if self.current_user in self.watchlists and symbol in self.watchlists[self.current_user]:
            self.watchlists[self.current_user].remove(symbol)
            return {"status": "success", "symbol": symbol, "watchlist": self.watchlists[self.current_user]}
        
        return {"status": "failed", "symbol": symbol, "watchlist": self.watchlists.get(self.current_user, [])}

    def notify_price_change(self, symbols: List[str], threshold: float) -> dict:
        """Monitor stocks for significant price changes."""
        changed_stocks = []
        details = []
        
        for symbol in symbols:
            if symbol in self.stocks:
                stock = self.stocks[symbol]
                if abs(stock.percent_change) >= threshold:
                    changed_stocks.append(symbol)
                    details.append({
                        "symbol": symbol,
                        "current_price": stock.price,
                        "percent_change": stock.percent_change
                    })
        
        notification = f"Found {len(changed_stocks)} stocks with price changes exceeding {threshold}%"
        
        result = {"notification": notification}
        if changed_stocks:
            result["changed_stocks"] = changed_stocks
            result["details"] = details
        
        return result

    def update_stock_price(self, symbol: str, new_price: float) -> dict:
        """Update stock price manually."""
        if symbol not in self.stocks:
            return {}
        
        stock = self.stocks[symbol]
        old_price = stock.price
        percent_change = ((new_price - old_price) / old_price) * 100
        
        stock.price = new_price
        stock.percent_change = percent_change
        
        return {
            "symbol": symbol,
            "old_price": old_price,
            "new_price": new_price,
            "percent_change": percent_change
        }

# Section 3: MCP Tools
mcp = FastMCP(name="TradingBot")
bot = TradingBot()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the trading bot."""
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        bot.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current trading state as scenario dictionary."""
    try:
        return bot.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def login(username: str, password: str) -> dict:
    """Authenticate user and establish trading session."""
    try:
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        return bot.login(username, password)
    except Exception as e:
        raise e

@mcp.tool()
def logout() -> dict:
    """Terminate current user session."""
    try:
        return bot.logout()
    except Exception as e:
        raise e

@mcp.tool()
def check_login_status() -> dict:
    """Check if user session is active."""
    try:
        return bot.check_login_status()
    except Exception as e:
        raise e

@mcp.tool()
def get_market_status() -> dict:
    """Retrieve current market status."""
    try:
        return bot.get_market_status()
    except Exception as e:
        raise e

@mcp.tool()
def get_account_info() -> dict:
    """Get account information for authenticated user."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        result = bot.get_account_info()
        if not result:
            raise ValueError("No account found for current user")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def make_transaction(transaction_type: str, amount: float) -> dict:
    """Execute deposit or withdrawal transaction."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount must be a positive number")
        result = bot.make_transaction(transaction_type, amount)
        if result.get("status") == "failed":
            raise ValueError("Transaction failed - no account found or insufficient funds")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_transaction_history(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """Get transaction history with optional date filtering."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        return bot.get_transaction_history(start_date, end_date)
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_symbol(company_name: str) -> dict:
    """Get stock symbol for company name."""
    try:
        if not company_name or not isinstance(company_name, str):
            raise ValueError("Company name must be a non-empty string")
        return bot.get_stock_symbol(company_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_stock_info(symbol: str) -> dict:
    """Get comprehensive stock information."""
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        result = bot.get_stock_info(symbol)
        if not result:
            raise ValueError(f"Stock symbol {symbol} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_available_stocks(sector: str) -> dict:
    """Get available stocks in specified sector."""
    try:
        if not sector or not isinstance(sector, str):
            raise ValueError("Sector must be a non-empty string")
        return bot.get_available_stocks(sector)
    except Exception as e:
        raise e

@mcp.tool()
def filter_stocks_by_price(symbols: List[str], min_price: float, max_price: float) -> dict:
    """Filter stocks by price range."""
    try:
        if not isinstance(symbols, list):
            raise ValueError("Symbols must be a list")
        if not isinstance(min_price, (int, float)) or min_price < 0:
            raise ValueError("Min price must be a non-negative number")
        if not isinstance(max_price, (int, float)) or max_price < 0:
            raise ValueError("Max price must be a non-negative number")
        if min_price > max_price:
            raise ValueError("Min price cannot exceed max price")
        return bot.filter_stocks_by_price(symbols, min_price, max_price)
    except Exception as e:
        raise e

@mcp.tool()
def place_order(order_type: str, symbol: str, price: float, quantity: int) -> dict:
    """Place buy or sell order."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        if not bot.market_open:
            raise ValueError("Market is closed")
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not isinstance(price, (int, float)) or price <= 0:
            raise ValueError("Price must be a positive number")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")
        result = bot.place_order(order_type, symbol, price, quantity)
        if not result:
            raise ValueError("Order placement failed - no account found or insufficient balance")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_order_details(order_id: int) -> dict:
    """Get detailed order information."""
    try:
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("Order ID must be a positive integer")
        result = bot.get_order_details(order_id)
        if not result:
            raise ValueError(f"Order {order_id} not found")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def cancel_order(order_id: int) -> dict:
    """Cancel pending or open order."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("Order ID must be a positive integer")
        return bot.cancel_order(order_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_order_history(status: Optional[str] = None, symbol: Optional[str] = None) -> dict:
    """Get order history with optional filtering."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        return bot.get_order_history(status, symbol)
    except Exception as e:
        raise e

@mcp.tool()
def get_watchlist() -> dict:
    """Get user's watchlist."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        return bot.get_watchlist()
    except Exception as e:
        raise e

@mcp.tool()
def add_to_watchlist(symbol: str) -> dict:
    """Add stock to watchlist."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return bot.add_to_watchlist(symbol)
    except Exception as e:
        raise e

@mcp.tool()
def remove_from_watchlist(symbol: str) -> dict:
    """Remove stock from watchlist."""
    try:
        if not bot.current_user:
            raise ValueError("No user logged in")
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        return bot.remove_from_watchlist(symbol)
    except Exception as e:
        raise e

@mcp.tool()
def notify_price_change(symbols: List[str], threshold: float) -> dict:
    """Monitor stocks for significant price changes."""
    try:
        if not isinstance(symbols, list) or len(symbols) == 0:
            raise ValueError("Symbols must be a non-empty list")
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            raise ValueError("Threshold must be a positive number")
        return bot.notify_price_change(symbols, threshold)
    except Exception as e:
        raise e

@mcp.tool()
def update_stock_price(symbol: str, new_price: float) -> dict:
    """Update stock price manually."""
    try:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not isinstance(new_price, (int, float)) or new_price <= 0:
            raise ValueError("New price must be a positive number")
        result = bot.update_stock_price(symbol, new_price)
        if not result:
            raise ValueError(f"Stock symbol {symbol} not found")
        return result
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()