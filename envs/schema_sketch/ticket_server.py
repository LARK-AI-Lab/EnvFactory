# Server: Ticket

def login(username: str, password: str) -> dict:
    """
    Authenticate user and establish session for ticket system operations.
    
    Args:
        username (str): The username for authentication
        password (str): The password for authentication
        
    Returns:
        dict: A dictionary containing success (bool) indicating login success or failure, session_token (str) [Optional] session token if login successful, username (str) [Optional] authenticated username.
    """
    pass

def logout() -> dict:
    """
    Log out the currently authenticated user and invalidate session.
    
    Returns:
        dict: A dictionary containing success (bool) indicating logout success or failure.
    """
    pass

def check_login_status() -> dict:
    """
    Check if a user is currently authenticated and session is valid.
    
    Returns:
        dict: A dictionary containing is_authenticated (bool) indicating current authentication status, username (str) [Optional] current authenticated username if logged in.
    """
    pass

def create_ticket(title: str, description: str = "", priority: int = 1, category: str = None, assignee: str = None) -> dict:
    """
    Create a new support ticket in the system. Requires authentication.
    
    Args:
        title (str): The title or subject of the ticket
        description (str): [Optional] Detailed description of the issue or request. Defaults to empty string.
        priority (int): [Optional] Priority level of the ticket from 1 to 5, where 5 is the highest priority. Defaults to 1.
        category (str): [Optional] Category of the ticket. [Enum]: ["technical", "billing", "general", "feature_request", "bug_report"]. If not provided, defaults to "general".
        assignee (str): [Optional] Username of the person to assign the ticket to. If not provided, ticket remains unassigned.
        
    Returns:
        dict: A dictionary containing ticket_id (int) unique identifier of the created ticket, title (str), description (str), status (str) [Enum]: ["open"], priority (int), category (str), created_by (str) username of creator, created_at (str) timestamp in YYYY-MM-DD HH:MM:SS format, assignee (str) [Optional] assigned user if provided.
    """
    pass

def get_ticket(ticket_id: int) -> dict:
    """
    Get detailed information about a specific ticket by its ID.
    
    Args:
        ticket_id (int): The unique identifier of the ticket. 
        
    Returns:
        dict: A dictionary containing ticket_id (int), title (str), description (str), status (str) [Enum]: ["open", "in_progress", "resolved", "closed"], priority (int), category (str), created_by (str), created_at (str), updated_at (str) [Optional] last update timestamp, assignee (str) [Optional] assigned user, resolution (str) [Optional] resolution details if resolved.
    """
    pass

def list_tickets(status: str = None, priority: int = None, category: str = None, assignee: str = None, limit: int = 5, offset: int = 0) -> list:
    """
    List tickets with optional filtering and pagination. Requires authentication.
    
    Args:
        status (str): [Optional] Filter tickets by status. [Enum]: ["open", "in_progress", "resolved", "closed"]. If not provided, returns all statuses.
        priority (int): [Optional] Filter tickets by priority level (1-5). If not provided, returns all priorities.
        category (str): [Optional] Filter tickets by category. [Enum]: ["technical", "billing", "general", "feature_request", "bug_report"]. If not provided, returns all categories.
        assignee (str): [Optional] Filter tickets by assignee username. If not provided, returns tickets for all assignees.
        limit (int): [Optional] Maximum number of tickets to return. Defaults to 5.
        offset (int): [Optional] Number of tickets to skip for pagination. Defaults to 0.
        
    Returns:
        list: A list of ticket summaries, each containing ticket_id (int), title (str), status (str), priority (int), category (str), created_by (str), created_at (str), assignee (str) [Optional]. Ticket IDs can be used with get_ticket for full information.
    """
    pass

def search_tickets(query: str, status: str = None, limit: int = 5) -> list:
    """
    Search tickets by keyword in title or description. Requires authentication.
    
    Args:
        query (str): The search keyword to match against ticket title or description
        status (str): [Optional] Filter results by status. [Enum]: ["open", "in_progress", "resolved", "closed"]. If not provided, searches all statuses.
        limit (int): [Optional] Maximum number of results to return. Defaults to 5.
        
    Returns:
        list: A list of matching tickets, each containing ticket_id (int), title (str), description (str), status (str), priority (int), created_by (str), created_at (str). Ticket IDs can be used with get_ticket for full information.
    """
    pass

def update_ticket(ticket_id: int, title: str = None, description: str = None, priority: int = None, category: str = None, assignee: str = None, status: str = None) -> dict:
    """
    Update one or more fields of an existing ticket. Requires authentication. All fields are optional for partial updates.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to update. 
        title (str): [Optional] New title for the ticket
        description (str): [Optional] New description for the ticket
        priority (int): [Optional] New priority level (1-5)
        category (str): [Optional] New category. [Enum]: ["technical", "billing", "general", "feature_request", "bug_report"]
        assignee (str): [Optional] New assignee username. Use empty string to unassign.
        status (str): [Optional] New status. [Enum]: ["open", "in_progress", "resolved", "closed"]
        
    Returns:
        dict: A dictionary containing ticket_id (int), status (str) indicating update success, updated_fields (list[str]) list of fields that were updated, updated_at (str) timestamp of the update.
    """
    pass

def close_ticket(ticket_id: int) -> dict:
    """
    Close a ticket. This marks the ticket as closed but does not resolve it. Requires authentication.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to close. 
        
    Returns:
        dict: A dictionary containing ticket_id (int), status (str) [Enum]: ["closed"], message (str) confirmation message, updated_at (str) timestamp when ticket was closed.
    """
    pass

def resolve_ticket(ticket_id: int, resolution: str) -> dict:
    """
    Resolve a ticket with resolution details. This sets the status to resolved. Requires authentication.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to resolve. 
        resolution (str): Detailed description of how the ticket was resolved or the solution provided
        
    Returns:
        dict: A dictionary containing ticket_id (int), status (str) [Enum]: ["resolved"], resolution (str) the resolution details, resolved_at (str) timestamp when ticket was resolved, updated_at (str) timestamp of the update.
    """
    pass

def get_user_tickets(username: str = None, status: str = None, limit: int = 5) -> list:
    """
    Get all tickets created by a specific user or the current authenticated user. Requires authentication.
    
    Args:
        username (str): [Optional] Username to filter tickets by. If not provided, returns tickets for the current authenticated user.
        status (str): [Optional] Filter tickets by status. [Enum]: ["open", "in_progress", "resolved", "closed"]. If not provided, returns all statuses.
        limit (int): [Optional] Maximum number of tickets to return. Defaults to 5.
        
    Returns:
        list: A list of tickets created by the specified user, each containing ticket_id (int), title (str), status (str), priority (int), category (str), created_at (str), assignee (str) [Optional]. Ticket IDs can be used with get_ticket for full information.
    """
    pass

def add_comment(ticket_id: int, comment: str, is_internal: bool = False) -> dict:
    """
    Add a comment to a ticket. Comments can be public or internal (visible only to staff). Requires authentication.
    
    Args:
        ticket_id (int): The unique identifier of the ticket. 
        comment (str): The comment text to add
        is_internal (bool): [Optional] If True, the comment is internal and only visible to staff. Defaults to False (public comment).
        
    Returns:
        dict: A dictionary containing comment_id (int) unique identifier of the comment, ticket_id (int), comment (str), author (str) username of comment author, is_internal (bool), created_at (str) timestamp in YYYY-MM-DD HH:MM:SS format.
    """
    pass

def get_ticket_comments(ticket_id: int, include_internal: bool = False) -> list:
    """
    Get all comments for a specific ticket. Internal comments are only visible to staff. Requires authentication.
    
    Args:
        ticket_id (int): The unique identifier of the ticket. 
        include_internal (bool): [Optional] If True, includes internal comments (requires staff privileges). Defaults to False.
        
    Returns:
        list: A list of comments, each containing comment_id (int), ticket_id (int), comment (str), author (str), is_internal (bool), created_at (str).
    """
    pass

def get_ticket_statistics(time_period: str = None) -> dict:
    """
    Get statistics about tickets in the system. Requires authentication.
    
    Args:
        time_period (str): [Optional] Time period for statistics. [Enum]: ["today", "week", "month", "year", "all"]. Defaults to "all".
        
    Returns:
        dict: A dictionary containing total_tickets (int), open_tickets (int), in_progress_tickets (int), resolved_tickets (int), closed_tickets (int), average_resolution_time (float) [Optional] in hours, tickets_by_category (dict) [Optional] count of tickets per category, tickets_by_priority (dict) [Optional] count of tickets per priority level.
    """
    pass

