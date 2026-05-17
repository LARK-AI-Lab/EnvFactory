# Server: Message

def login(user_id: str) -> dict:
    """
    Authenticate and log in a user to the messaging system.
    
    Args:
        user_id (str): The user ID to log in (e.g., "USR001", "USR002")
        
    Returns:
        dict: A dictionary containing success (bool) indicating login success, user_id (str) [Optional] logged in user ID if successful, message (str) status message.
    """
    pass

def logout() -> dict:
    """
    Log out the currently authenticated user from the messaging system.
    
    Returns:
        dict: A dictionary containing success (bool) indicating logout success, message (str) status message.
    """
    pass

def check_login_status() -> dict:
    """
    Check if a user is currently logged in to the messaging system.
    
    Returns:
        dict: A dictionary containing is_logged_in (bool) indicating current login status, user_id (str) [Optional] current logged in user ID if authenticated.
    """
    pass

def list_users() -> list:
    """
    List all users available in the messaging workspace.
    
    Returns:
        list: A list of users, each user is a dict containing username (str), user_id (str). User IDs can be used with login, send_message, and other operations.
    """
    pass

def get_user_id(username: str) -> dict:
    """
    Get the user ID for a given username.
    
    Args:
        username (str): The username to look up (e.g., "Alice", "Bob")
        
    Returns:
        dict: A dictionary containing user_id (str) the user ID corresponding to the username, username (str). User ID can be used with login and send_message.
    """
    pass

def add_contact(username: str) -> dict:
    """
    Add a new contact to the messaging workspace. The system will automatically assign a unique user ID.
    
    Args:
        username (str): The username for the new contact
        
    Returns:
        dict: A dictionary containing success (bool) indicating addition success, username (str), user_id (str) the newly assigned user ID, message (str) status message. User ID can be used with login and send_message.
    """
    pass

def send_message(receiver_id: str, message: str) -> dict:
    """
    Send a message to another user. Requires authentication via login.
    
    Args:
        receiver_id (str): The user ID of the recipient (from list_users or get_user_id)
        message (str): The message content to send
        
    Returns:
        dict: A dictionary containing success (bool) indicating send success, message_id (int) unique identifier of the sent message, receiver_id (str), sent_at (str) timestamp in YYYY-MM-DD HH:MM:SS format, message (str) status message. Message ID can be used with delete_message.
    """
    pass

def view_inbox(limit: int = 50, offset: int = 0) -> list:
    """
    View all messages received by the current logged-in user. Requires authentication via login.
    
    Args:
        limit (int): [Optional] Maximum number of messages to return. Defaults to 50.
        offset (int): [Optional] Number of messages to skip for pagination. Defaults to 0.
        
    Returns:
        list: A list of received messages, each message is a dict containing message_id (int), sender_id (str), sender_username (str) [Optional], message (str), received_at (str) timestamp. Message IDs can be used with delete_message.
    """
    pass

def view_sent_messages(receiver_id: str = None, limit: int = 50, offset: int = 0) -> list:
    """
    View all messages sent by the current logged-in user. Requires authentication via login.
    
    Args:
        receiver_id (str): [Optional] Filter messages by receiver user ID (from list_users or get_user_id). If not provided, returns messages to all receivers.
        limit (int): [Optional] Maximum number of messages to return. Defaults to 50.
        offset (int): [Optional] Number of messages to skip for pagination. Defaults to 0.
        
    Returns:
        list: A list of sent messages, each message is a dict containing message_id (int), receiver_id (str), receiver_username (str) [Optional], message (str), sent_at (str) timestamp. Message IDs can be used with delete_message.
    """
    pass

def get_message(message_id: int) -> dict:
    """
    Get detailed information about a specific message by its ID.
    
    Args:
        message_id (int): The unique identifier of the message (from view_inbox, view_sent_messages, or send_message)
        
    Returns:
        dict: A dictionary containing message_id (int), sender_id (str), receiver_id (str), message (str), sent_at (str) timestamp, is_read (bool) [Optional] read status for received messages.
    """
    pass

def delete_message(message_id: int) -> dict:
    """
    Delete a message. Users can delete messages they sent or received. Requires authentication via login.
    
    Args:
        message_id (int): The unique identifier of the message to delete (from view_inbox, view_sent_messages, or send_message)
        
    Returns:
        dict: A dictionary containing success (bool) indicating deletion success, message_id (int), message (str) status message.
    """
    pass

def search_messages(keyword: str, sender_id: str = None, receiver_id: str = None, limit: int = None) -> list:
    """
    Search for messages containing a specific keyword. Searches both sent and received messages for the current user. Requires authentication via login.
    
    Args:
        keyword (str): The keyword to search for in message content
        sender_id (str): [Optional] Filter results by sender user ID (from list_users or get_user_id). If not provided, searches all senders.
        receiver_id (str): [Optional] Filter results by receiver user ID (from list_users or get_user_id). If not provided, searches all receivers.
        limit (int): [Optional] Maximum number of results to return. Defaults to 20.
        
    Returns:
        list: A list of matching messages, each message is a dict containing message_id (int), sender_id (str), receiver_id (str), message (str), sent_at (str) timestamp. Message IDs can be used with get_message or delete_message.
    """
    pass

def get_message_stats(time_period: str = None) -> dict:
    """
    Get messaging statistics for the current logged-in user. Requires authentication via login.
    
    Args:
        time_period (str): [Optional] Time period for statistics. [Enum]: ["today", "week", "month", "year", "all"]. Defaults to "all".
        
    Returns:
        dict: A dictionary containing total_sent (int) total messages sent, total_received (int) total messages received, total_contacts (int) number of unique contacts interacted with, messages_by_contact (dict) [Optional] count of messages per contact user ID.
    """
    pass

