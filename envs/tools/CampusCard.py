from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import datetime

# Section 1: Schema
class Transaction(BaseModel):
    """Represents a campus card transaction."""
    tradeId: str = Field(..., description="Unique identifier for the transaction")
    merchantName: str = Field(..., description="Name of the merchant or location")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Transaction timestamp in YYYY-MM-DD HH:mm:ss format")
    amount: float = Field(..., description="Transaction amount; negative for expenses, positive for refunds/recharges")
    balanceAfter: float = Field(..., description="Account balance immediately after the transaction")

class UserAccount(BaseModel):
    """Represents a campus card account."""
    userId: str = Field(..., description="Unique identifier of the campus card account")
    name: str = Field(..., description="Full name of the cardholder")
    password: str = Field(..., description="Campus card password for authentication")
    balance: float = Field(..., ge=0, description="Current available balance on the card")
    currency: str = Field(default="CNY", description="ISO-4217 currency code for the balance")
    status: int = Field(default=1, ge=1, le=6, description="Numeric status code: 1-normal, 2-lost, 3-system frozen, 4-closed, 5-pre-closed, 6-manually frozen")
    phone: Optional[str] = Field(default=None, description="Phone number associated with the account")
    email: Optional[str] = Field(default=None, description="Email address associated with the account")
    address: Optional[str] = Field(default=None, description="Residential or office address associated with the account")

class CampusCardScenario(BaseModel):
    """Main scenario model for campus card service."""
    accounts: Dict[str, UserAccount] = Field(default={}, description="Campus card accounts by userId")
    transactions: Dict[str, List[Transaction]] = Field(default={}, description="Transaction history by userId")
    statusTextMap: Dict[int, str] = Field(default={
        1: "normal", 2: "lost", 3: "system frozen", 4: "closed", 5: "pre-closed", 6: "manually frozen"
    }, description="Mapping of status codes to human-readable descriptions")
    current_time: str = Field(default="2024-01-01 00:00:00", pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Current timestamp in YYYY-MM-DD HH:mm:ss format")

Scenario_Schema = [Transaction, UserAccount, CampusCardScenario]

# Section 2: Class
class CampusCardAPI:
    def __init__(self):
        """Initialize campus card API with empty state."""
        self.accounts: Dict[str, UserAccount] = {}
        self.transactions: Dict[str, List[Transaction]] = {}
        self.statusTextMap: Dict[int, str] = {}
        self.current_time: str = "2024-01-01 00:00:00"
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        # Ensure scenario is a dictionary
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        
        # Validate and load the scenario
        model = CampusCardScenario(**scenario)
        self.accounts = model.accounts
        self.transactions = model.transactions
        self.statusTextMap = model.statusTextMap
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "accounts": {user_id: account.model_dump() for user_id, account in self.accounts.items()},
            "transactions": {user_id: [txn.model_dump() for txn in txns] for user_id, txns in self.transactions.items()},
            "statusTextMap": self.statusTextMap,
            "current_time": self.current_time
        }

    def query_balance(self, userId: str) -> dict:
        """Retrieve the current balance and currency of a campus card account."""
        account = self.accounts[userId]
        return {"userId": userId, "balance": account.balance, "currency": account.currency}

    def query_transactions(self, userId: str, startDate: Optional[str] = None, endDate: Optional[str] = None) -> dict:
        """Fetch paginated transaction history for a campus card within an optional date range."""
        user_transactions = self.transactions.get(userId, [])
        
        if startDate or endDate:
            filtered_transactions = []
            for txn in user_transactions:
                txn_date = datetime.datetime.strptime(txn.date, "%Y-%m-%d %H:%M:%S").date()
                if startDate:
                    start = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
                    if txn_date < start:
                        continue
                if endDate:
                    end = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()
                    if txn_date > end:
                        continue
                filtered_transactions.append(txn)
            return {"transactions": [txn.model_dump() for txn in filtered_transactions]}
        
        return {"transactions": [txn.model_dump() for txn in user_transactions]}

    def query_basic_info(self, userId: str, password: str) -> dict:
        """Obtain status and personal details of a campus card after password verification."""
        account = self.accounts[userId]
        if account.password != password:
            raise ValueError("Invalid password")
        
        return {
            "userId": userId,
            "name": account.name,
            "status": account.status,
            "statusText": self.statusTextMap.get(account.status, "unknown")
        }

    def recharge(self, userId: str, amount: float, paymentMethod: str) -> dict:
        """Add funds to a campus card using a supported payment method."""
        account = self.accounts[userId]
        
        # Create transaction using current_time
        time_str = self.current_time.replace("-", "").replace(" ", "").replace(":", "")
        trade_id = f"RECHARGE_{time_str}_{userId}"
        new_balance = account.balance + amount
        
        transaction = Transaction(
            tradeId=trade_id,
            merchantName="Campus Card Recharge",
            date=self.current_time,
            amount=amount,
            balanceAfter=new_balance
        )
        
        # Update account balance and add transaction
        account.balance = new_balance
        if userId not in self.transactions:
            self.transactions[userId] = []
        self.transactions[userId].append(transaction)
        
        return {
            "userId": userId,
            "success": True,
            "amount": amount,
            "balanceAfter": new_balance,
            "transactionId": trade_id,
            "message": f"Successfully recharged {amount} {account.currency}"
        }

    def update_info(self, userId: str, password: str, phone: Optional[str] = None, email: Optional[str] = None, address: Optional[str] = None) -> dict:
        """Update optional profile fields of a campus card after password verification."""
        account = self.accounts[userId]
        if account.password != password:
            raise ValueError("Invalid password")
        
        updated_fields = []
        
        if phone is not None:
            account.phone = phone
            updated_fields.append("phone")
        
        if email is not None:
            account.email = email
            updated_fields.append("email")
        
        if address is not None:
            account.address = address
            updated_fields.append("address")
        
        return {
            "userId": userId,
            "success": len(updated_fields) > 0,
            "updatedFields": updated_fields,
            "message": f"Updated {len(updated_fields)} field(s)" if updated_fields else "No fields updated"
        }

    def lostCard(self, userId: str, password: str) -> dict:
        """Report the campus card as lost to freeze it and prevent unauthorized use."""
        account = self.accounts[userId]
        if account.password != password:
            raise ValueError("Invalid password")
        
        account.status = 2  # Lost status
        
        return {
            "userId": userId,
            "success": True,
            "message": "Card has been reported as lost and frozen",
            "status": account.status
        }

# Section 3: MCP Tools
mcp = FastMCP(name="CampusCard")
api = CampusCardAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the campus card API.
    
    Args:
        scenario (dict): Scenario dictionary matching CampusCardScenario schema.
    
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
    Save current campus card state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def query_balance(userId: str) -> dict:
    """
    Retrieve the current balance and currency of a campus card account.
    
    Args:
        userId (str): The unique identifier of the campus card account.
    
    Returns:
        userId (str): The unique identifier of the campus card account.
        balance (float): Current available balance on the card.
        currency (str): ISO-4217 currency code for the balance.
    """
    try:
        if not userId or not isinstance(userId, str):
            raise ValueError("userId must be a non-empty string")
        if userId not in api.accounts:
            raise ValueError(f"User {userId} not found")
        return api.query_balance(userId)
    except Exception as e:
        raise e

@mcp.tool()
def query_transactions(userId: str, startDate: Optional[str] = None, endDate: Optional[str] = None) -> dict:
    """
    Fetch paginated transaction history for a campus card within an optional date range.
    
    Args:
        userId (str): The unique identifier of the campus card account.
        startDate (str) [Optional]: Start date in YYYY-MM-DD format; inclusive.
        endDate (str) [Optional]: End date in YYYY-MM-DD format; inclusive.
    
    Returns:
        transactions (list): Chronological list of transactions.
    """
    try:
        if not userId or not isinstance(userId, str):
            raise ValueError("userId must be a non-empty string")
        if userId not in api.accounts:
            raise ValueError(f"User {userId} not found")
        return api.query_transactions(userId, startDate, endDate)
    except Exception as e:
        raise e

@mcp.tool()
def query_basic_info(userId: str, password: str) -> dict:
    """
    Obtain status and personal details of a campus card after password verification.
    
    Args:
        userId (str): The unique identifier of the campus card account.
        password (str): Campus card password for authentication.
    
    Returns:
        userId (str): The unique identifier of the campus card account.
        name (str): Full name of the cardholder.
        status (int): Numeric status code: 1-normal, 2-lost, 3-system frozen, 4-closed, 5-pre-closed, 6-manually frozen.
        statusText (str): Human-readable description of the current card status.
    """
    try:
        if not userId or not isinstance(userId, str):
            raise ValueError("userId must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("password must be a non-empty string")
        if userId not in api.accounts:
            raise ValueError(f"User {userId} not found")
        return api.query_basic_info(userId, password)
    except Exception as e:
        raise e

@mcp.tool()
def recharge(userId: str, amount: float, paymentMethod: str) -> dict:
    """
    Add funds to a campus card using a supported payment method.
    
    Args:
        userId (str): The unique identifier of the campus card account.
        amount (float): Recharge amount in the card's currency.
        paymentMethod (str): Payment channel used for the recharge (alipay, wechat, bank_card).
    
    Returns:
        userId (str): The unique identifier of the campus card account.
        success (bool): True if the recharge succeeded.
        amount (float): Actual amount recharged.
        balanceAfter (float): New balance after the recharge.
        transactionId (str): Unique identifier for the recharge transaction.
        message (str): Human-readable result message.
    """
    try:
        if not userId or not isinstance(userId, str):
            raise ValueError("userId must be a non-empty string")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("amount must be a positive number")
        if paymentMethod not in ["alipay", "wechat", "bank_card"]:
            raise ValueError("paymentMethod must be one of: alipay, wechat, bank_card")
        if userId not in api.accounts:
            raise ValueError(f"User {userId} not found")
        return api.recharge(userId, amount, paymentMethod)
    except Exception as e:
        raise e

@mcp.tool()
def update_info(userId: str, password: str, phone: Optional[str] = None, email: Optional[str] = None, address: Optional[str] = None) -> dict:
    """
    Update optional profile fields of a campus card after password verification.
    
    Args:
        userId (str): The unique identifier of the campus card account.
        password (str): Campus card password for authentication.
        phone (str) [Optional]: New phone number to associate with the account.
        email (str) [Optional]: New email address to associate with the account.
        address (str) [Optional]: New residential or office address to associate with the account.
    
    Returns:
        userId (str): The unique identifier of the campus card account.
        success (bool): True if at least one field was updated.
        updatedFields (list): List of field names that were successfully modified.
        message (str): Human-readable result message.
    """
    try:
        if not userId or not isinstance(userId, str):
            raise ValueError("userId must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("password must be a non-empty string")
        if userId not in api.accounts:
            raise ValueError(f"User {userId} not found")
        return api.update_info(userId, password, phone, email, address)
    except Exception as e:
        raise e

@mcp.tool()
def lostCard(userId: str, password: str) -> dict:
    """
    Report the campus card as lost to freeze it and prevent unauthorized use.
    
    Args:
        userId (str): The unique identifier of the campus card account.
        password (str): Campus card password for authentication.
    
    Returns:
        userId (str): The unique identifier of the campus card account.
        success (bool): True if the card was successfully flagged as lost.
        message (str): Human-readable result message.
        status (int): Numeric status code after the operation.
    """
    try:
        if not userId or not isinstance(userId, str):
            raise ValueError("userId must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("password must be a non-empty string")
        if userId not in api.accounts:
            raise ValueError(f"User {userId} not found")
        return api.lostCard(userId, password)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()