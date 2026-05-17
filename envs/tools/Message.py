from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class User(BaseModel):
    """Represents a user in the messaging workspace."""
    user_id: str = Field(..., min_length=1, description="Unique identifier for the user")
    username: str = Field(..., pattern="^[a-zA-Z0-9\u4e00-\u9fff]+$", min_length=1, description="Human-readable username")

class Message(BaseModel):
    """Represents a message in the system."""
    message_id: int = Field(..., ge=0, description="Unique message identifier")
    sender_id: str = Field(..., min_length=1, description="Sender's user ID")
    receiver_id: str = Field(..., min_length=1, description="Receiver's user ID")
    message: str = Field(..., min_length=1, description="Message content")
    sent_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Timestamp in YYYY-MM-DD HH:MM:SS format")
    is_read: bool = Field(default=False, description="Read status for received messages")

class MessageScenario(BaseModel):
    """Main scenario model for messaging workspace."""
    users: Dict[str, User] = Field(default={
        "user_001": {"user_id": "user_001", "username": "alice"},
        "user_002": {"user_id": "user_002", "username": "bob"},
        "user_003": {"user_id": "user_003", "username": "charlie"},
        "user_004": {"user_id": "user_004", "username": "david"},
        "user_005": {"user_id": "user_005", "username": "eve"},
    }, description="All users in the workspace")
    messages: Dict[int, Message] = Field(default={}, description="All messages in the system")
    current_user_id: Optional[str] = Field(default=None, description="Currently logged-in user ID")
    next_message_id: int = Field(default=1, ge=1, description="Next available message ID")
    next_user_id_counter: int = Field(default=6, ge=1, description="Counter for generating user IDs")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [User, Message, MessageScenario]

# Section 2: Class
class MessageAPI:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.messages: Dict[int, Message] = {}
        self.current_user_id: Optional[str] = None
        self.next_message_id: int = 1
        self.next_user_id_counter: int = 1
        self.current_time: str = ""
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = MessageScenario(**scenario)
        self.users = model.users
        self.messages = model.messages
        self.current_user_id = model.current_user_id
        self.next_message_id = model.next_message_id
        self.next_user_id_counter = model.next_user_id_counter
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "users": {uid: user.model_dump() if hasattr(user, 'model_dump') else user for uid, user in self.users.items()},
            "messages": {mid: msg.model_dump() if hasattr(msg, 'model_dump') else msg for mid, msg in self.messages.items()},
            "current_user_id": self.current_user_id,
            "next_message_id": self.next_message_id,
            "next_user_id_counter": self.next_user_id_counter,
            "current_time": self.current_time
        }
    
    def login(self, user_id: str) -> dict:
        """Authenticate and log in a user to the messaging system."""
        if user_id not in self.users:
            return {"success": False, "message": f"User ID '{user_id}' not found"}
        self.current_user_id = user_id
        return {"success": True, "user_id": user_id, "message": "Login successful"}
    
    def logout(self) -> dict:
        """Log out the currently authenticated user."""
        if not self.current_user_id:
            return {"success": False, "message": "No user is currently logged in"}
        self.current_user_id = None
        return {"success": True, "message": "Logout successful"}
    
    def check_login_status(self) -> dict:
        """Check the current login status."""
        if self.current_user_id:
            return {"is_logged_in": True, "user_id": self.current_user_id}
        return {"is_logged_in": False}
    
    def list_users(self) -> List[dict]:
        """Retrieve a list of all users in the messaging workspace."""
        return [{"username": user.username, "user_id": user.user_id} for user in self.users.values()]
    
    def get_user_id(self, username: str) -> dict:
        """Retrieve the user ID for a given username."""
        for user in self.users.values():
            if user.username == username:
                return {"user_id": user.user_id, "username": username}
        raise ValueError(f"Username '{username}' not found")
    
    def add_contact(self, username: str) -> dict:
        """Add a new contact to the messaging workspace."""
        for user in self.users.values():
            if user.username == username:
                raise ValueError(f"Username '{username}' already exists")
        
        user_id = f"user_{self.next_user_id_counter:03d}"
        self.next_user_id_counter += 1
        
        new_user = User(user_id=user_id, username=username)
        self.users[user_id] = new_user
        
        return {
            "success": True,
            "username": username,
            "user_id": user_id,
            "message": f"Contact '{username}' added successfully with user ID '{user_id}'"
        }
    
    def send_message(self, receiver_id: str, message: str) -> dict:
        """Send a message to another user."""
        if not self.current_user_id:
            raise ValueError("Authentication required. Please log in first.")
        
        if receiver_id not in self.users:
            raise ValueError(f"Receiver ID '{receiver_id}' not found")
        
        if not message.strip():
            raise ValueError("Message content cannot be empty")
        
        message_id = self.next_message_id
        self.next_message_id += 1
        
        sent_at = self.current_time.replace("T", " ")[:19]
        
        new_message = Message(
            message_id=message_id,
            sender_id=self.current_user_id,
            receiver_id=receiver_id,
            message=message,
            sent_at=sent_at,
            is_read=False
        )
        
        self.messages[message_id] = new_message
        
        return {
            "success": True,
            "message_id": message_id,
            "receiver_id": receiver_id,
            "sent_at": sent_at,
            "message": "Message sent successfully"
        }
    
    def view_inbox(self, limit: Optional[int] = 50, offset: Optional[int] = 0) -> List[dict]:
        """View all messages received by the currently logged-in user."""
        if not self.current_user_id:
            raise ValueError("Authentication required. Please log in first.")
        
        received = [msg for msg in self.messages.values() if msg.receiver_id == self.current_user_id]
        received.sort(key=lambda x: x.message_id, reverse=True)
        
        start = offset
        end = offset + limit
        paginated = received[start:end]
        
        return [
            {
                "message_id": msg.message_id,
                "sender_id": msg.sender_id,
                "sender_username": self.users[msg.sender_id].username if msg.sender_id in self.users else "Unknown",
                "message": msg.message,
                "received_at": msg.sent_at
            }
            for msg in paginated
        ]
    
    def view_sent_messages(self, receiver_id: Optional[str] = None, limit: Optional[int] = 50, offset: Optional[int] = 0) -> List[dict]:
        """View all messages sent by the currently logged-in user."""
        if not self.current_user_id:
            raise ValueError("Authentication required. Please log in first.")
        
        sent = [
            msg for msg in self.messages.values() 
            if msg.sender_id == self.current_user_id and (receiver_id is None or msg.receiver_id == receiver_id)
        ]
        sent.sort(key=lambda x: x.message_id, reverse=True)
        
        start = offset
        end = offset + limit
        paginated = sent[start:end]
        
        return [
            {
                "message_id": msg.message_id,
                "receiver_id": msg.receiver_id,
                "receiver_username": self.users[msg.receiver_id].username if msg.receiver_id in self.users else "Unknown",
                "message": msg.message,
                "sent_at": msg.sent_at
            }
            for msg in paginated
        ]
    
    def get_message(self, message_id: int) -> dict:
        """Retrieve detailed information about a specific message."""
        if message_id not in self.messages:
            raise ValueError(f"Message ID '{message_id}' not found")
        
        msg = self.messages[message_id]
        result = {
            "message_id": msg.message_id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "message": msg.message,
            "sent_at": msg.sent_at
        }
        
        if self.current_user_id == msg.receiver_id:
            result["is_read"] = msg.is_read
        
        return result
    
    def delete_message(self, message_id: int) -> dict:
        """Delete a message that the user has sent or received."""
        if not self.current_user_id:
            raise ValueError("Authentication required. Please log in first.")
        
        if message_id not in self.messages:
            raise ValueError(f"Message ID '{message_id}' not found")
        
        msg = self.messages[message_id]
        
        if msg.sender_id != self.current_user_id and msg.receiver_id != self.current_user_id:
            raise ValueError("You can only delete messages you sent or received")
        
        del self.messages[message_id]
        
        return {
            "success": True,
            "message_id": message_id,
            "message": "Message deleted successfully"
        }
    
    def search_messages(self, keyword: str, sender_id: Optional[str] = None, receiver_id: Optional[str] = None, limit: Optional[int] = 20) -> List[dict]:
        """Search for messages containing a specific keyword."""
        if not self.current_user_id:
            raise ValueError("Authentication required. Please log in first.")
        
        if not keyword.strip():
            raise ValueError("Search keyword cannot be empty")
        
        matches = []
        for msg in self.messages.values():
            if msg.sender_id != self.current_user_id and msg.receiver_id != self.current_user_id:
                continue
            
            if sender_id and msg.sender_id != sender_id:
                continue
            if receiver_id and msg.receiver_id != receiver_id:
                continue
            
            if keyword.lower() in msg.message.lower():
                matches.append(msg)
        
        matches.sort(key=lambda x: x.message_id, reverse=True)
        matches = matches[:limit]
        
        return [
            {
                "message_id": msg.message_id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "message": msg.message,
                "sent_at": msg.sent_at
            }
            for msg in matches
        ]
    
    def get_message_stats(self, time_period: Optional[str] = "all") -> dict:
        """Retrieve messaging statistics for the currently logged-in user."""
        if not self.current_user_id:
            raise ValueError("Authentication required. Please log in first.")
        
        total_sent = 0
        total_received = 0
        contacts = set()
        messages_by_contact = {}
        
        for msg in self.messages.values():
            if msg.sender_id == self.current_user_id:
                total_sent += 1
                contacts.add(msg.receiver_id)
                messages_by_contact[msg.receiver_id] = messages_by_contact.get(msg.receiver_id, 0) + 1
            elif msg.receiver_id == self.current_user_id:
                total_received += 1
                contacts.add(msg.sender_id)
                messages_by_contact[msg.sender_id] = messages_by_contact.get(msg.sender_id, 0) + 1
        
        result = {
            "total_sent": total_sent,
            "total_received": total_received,
            "total_contacts": len(contacts)
        }
        
        if messages_by_contact:
            result["messages_by_contact"] = messages_by_contact
        
        return result

# Section 3: MCP Tools
mcp = FastMCP(name="Message")
api = MessageAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the messaging API."""
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current messaging state as scenario dictionary."""
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def login(user_id: str) -> dict:
    """Authenticate and log in a user to the messaging system."""
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        return api.login(user_id)
    except Exception as e:
        raise e

@mcp.tool()
def logout() -> dict:
    """Log out the currently authenticated user from the messaging system."""
    try:
        return api.logout()
    except Exception as e:
        raise e

@mcp.tool()
def check_login_status() -> dict:
    """Check the current login status of the user in the messaging system."""
    try:
        return api.check_login_status()
    except Exception as e:
        raise e

@mcp.tool()
def list_users() -> list:
    """Retrieve a list of all users available in the messaging workspace."""
    try:
        return api.list_users()
    except Exception as e:
        raise e

@mcp.tool()
def get_user_id(username: str) -> dict:
    """Retrieve the user ID for a given username."""
    try:
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        return api.get_user_id(username)
    except Exception as e:
        raise e

@mcp.tool()
def add_contact(username: str) -> dict:
    """Add a new contact to the messaging workspace."""
    try:
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        return api.add_contact(username)
    except Exception as e:
        raise e

@mcp.tool()
def send_message(receiver_id: str, message: str) -> dict:
    """Send a message to another user in the messaging system."""
    try:
        if not receiver_id or not isinstance(receiver_id, str):
            raise ValueError("Receiver ID must be a non-empty string")
        if not message or not isinstance(message, str):
            raise ValueError("Message must be a non-empty string")
        return api.send_message(receiver_id, message)
    except Exception as e:
        raise e

@mcp.tool()
def view_inbox(limit: Optional[int] = 50, offset: Optional[int] = 0) -> list:
    """View all messages received by the currently logged-in user."""
    try:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        if offset is not None and (not isinstance(offset, int) or offset < 0):
            raise ValueError("Offset must be a non-negative integer")
        return api.view_inbox(limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def view_sent_messages(receiver_id: Optional[str] = None, limit: Optional[int] = 50, offset: Optional[int] = 0) -> list:
    """View all messages sent by the currently logged-in user."""
    try:
        if receiver_id is not None and not isinstance(receiver_id, str):
            raise ValueError("Receiver ID must be a string")
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        if offset is not None and (not isinstance(offset, int) or offset < 0):
            raise ValueError("Offset must be a non-negative integer")
        return api.view_sent_messages(receiver_id, limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def get_message(message_id: int) -> dict:
    """Retrieve detailed information about a specific message."""
    try:
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("Message ID must be a non-negative integer")
        return api.get_message(message_id)
    except Exception as e:
        raise e

@mcp.tool()
def delete_message(message_id: int) -> dict:
    """Delete a message that the user has sent or received."""
    try:
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("Message ID must be a non-negative integer")
        return api.delete_message(message_id)
    except Exception as e:
        raise e

@mcp.tool()
def search_messages(keyword: str, sender_id: Optional[str] = None, receiver_id: Optional[str] = None, limit: Optional[int] = 20) -> list:
    """Search for messages containing a specific keyword."""
    try:
        if not keyword or not isinstance(keyword, str):
            raise ValueError("Keyword must be a non-empty string")
        if sender_id is not None and not isinstance(sender_id, str):
            raise ValueError("Sender ID must be a string")
        if receiver_id is not None and not isinstance(receiver_id, str):
            raise ValueError("Receiver ID must be a string")
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        return api.search_messages(keyword, sender_id, receiver_id, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_message_stats(time_period: Optional[str] = "all") -> dict:
    """Retrieve messaging statistics for the currently logged-in user."""
    try:
        valid_periods = ["today", "week", "month", "year", "all"]
        if time_period is not None and time_period not in valid_periods:
            raise ValueError(f"Time period must be one of {valid_periods}")
        return api.get_message_stats(time_period)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()