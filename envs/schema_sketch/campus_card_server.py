# Server: CampusCard

def query_balance(userId: str) -> dict:
    """
    Query campus card balance for a user.
    
    Args:
        userId (str): User identifier for the campus card account
        
    Returns:
        dict: {
            "userId": str,
            "balance": float,
            "currency": str
        }
    """
    pass

def query_transactions(userId: str, startDate: str = None, endDate: str = None) -> list:
    """
    Query transaction history for a user within a date range.
    
    Args:
        userId (str): User identifier for the campus card account
        startDate (str): [Optional] Start date in YYYY-MM-DD format
        endDate (str): [Optional] End date in YYYY-MM-DD format
        
    Returns:
        list: Each transaction contains {
            "tradeId": str,
            "merchantName": str,
            "date": str (YYYY-MM-DD HH:mm:ss),
            "amount": float,
            "balanceAfter": float
        }
    """
    pass

def query_basic_info(userId: str, password: str) -> dict:
    """
    Query campus card status information.
    
    Args:
        userId (str): User identifier for the campus card account
        password (str): Campus card password for authentication
        
    Returns:
        dict: {
            "userId": str,
            "name": str,
            "status": int (1-normal, 2-lost, 3-system frozen, 4-closed, 5-pre-closed, 6-manually frozen),
            "statusText": str
        }
    """
    pass

def recharge(userId: str, amount: float, paymentMethod: str) -> dict:
    """
    Recharge campus card balance.
    
    Args:
        userId (str): User identifier for the campus card account
        amount (float): Recharge amount
        paymentMethod (str): Payment method (enum: "alipay", "wechat", "bank_card")
        
    Returns:
        dict: {
            "userId": str,
            "success": bool,
            "amount": float,
            "balanceAfter": float,
            "transactionId": str,
            "message": str
        }
    """
    pass

def update_info(userId: str, password: str, **kwargs) -> dict:
    """
    Update campus card user information.
    
    Args:
        userId (str): User identifier for the campus card account
        password (str): Campus card password for authentication
        **kwargs: Optional fields to update, such as:
            - phone (str): Phone number
            - email (str): Email address
            - address (str): Address
            
    Returns:
        dict: {
            "userId": str,
            "success": bool,
            "updatedFields": list,
            "message": str
        }
    """
    pass

def lostCard(userId: str, password: str) -> dict:
    """
    Report a lost campus card.
    
    Args:
        userId (str): User identifier for the campus card account
        password (str): Campus card password for authentication
        
    Returns:
        dict: {
            "userId": str,
            "success": bool,
            "message": str,
            "status": int
        }
    """
    pass
