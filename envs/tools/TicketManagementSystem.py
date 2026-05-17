from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
from datetime import datetime
import time

# Section 1: Schema
class User(BaseModel):
    """Represents a user account."""
    username: str = Field(..., description="Unique username")
    password: str = Field(..., description="User password")
    is_staff: bool = Field(default=False, description="Whether user is staff member")

class Ticket(BaseModel):
    """Represents a support ticket."""
    ticket_id: int = Field(..., ge=1, description="Unique ticket identifier")
    title: str = Field(..., description="Ticket title")
    description: str = Field(default="", description="Ticket description")
    status: str = Field(default="open", description="Ticket status")
    priority: int = Field(default=1, ge=1, le=5, description="Priority level 1-5")
    category: str = Field(default="general", description="Ticket category")
    created_by: str = Field(..., description="Username of creator")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Creation timestamp")
    updated_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Last update timestamp")
    assignee: Optional[str] = Field(default=None, description="Assigned staff username")
    resolution: Optional[str] = Field(default=None, description="Resolution details")

class Comment(BaseModel):
    """Represents a ticket comment."""
    comment_id: int = Field(..., ge=1, description="Unique comment identifier")
    ticket_id: int = Field(..., ge=1, description="Associated ticket ID")
    comment: str = Field(..., description="Comment text")
    author: str = Field(..., description="Comment author username")
    is_internal: bool = Field(default=False, description="Whether comment is internal")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Creation timestamp")

class TicketManagementScenario(BaseModel):
    """Main scenario model for ticket management system."""
    users: Dict[str, User] = Field(default={}, description="Registered users")
    tickets: Dict[int, Ticket] = Field(default={}, description="All tickets")
    comments: Dict[int, Comment] = Field(default={}, description="All comments")
    sessions: Dict[str, str] = Field(default={}, description="Active sessions")
    next_ticket_id: int = Field(default=1, ge=1, description="Next ticket ID")
    next_comment_id: int = Field(default=1, ge=1, description="Next comment ID")
    staffUsers: List[str] = Field(default=["admin", "support1", "support2", "support3", "manager"], description="Staff usernames")
    current_time: str = Field(default="2024-01-01 00:00:00", pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", description="Current timestamp in YYYY-MM-DD HH:mm:ss format")

Scenario_Schema = [User, Ticket, Comment, TicketManagementScenario]

# Section 2: Class
class TicketManagementSystem:
    def __init__(self):
        """Initialize ticket management system with empty state."""
        self.users: Dict[str, User] = {}
        self.tickets: Dict[int, Ticket] = {}
        self.comments: Dict[int, Comment] = {}
        self.sessions: Dict[str, str] = {}
        self.next_ticket_id: int = 1
        self.next_comment_id: int = 1
        self.staffUsers: List[str] = []
        self.current_time: str = "2024-01-01 00:00:00"

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the system."""
        model = TicketManagementScenario(**scenario)
        self.users = model.users
        self.tickets = model.tickets
        self.comments = model.comments
        self.sessions = model.sessions
        self.next_ticket_id = model.next_ticket_id
        self.next_comment_id = model.next_comment_id
        self.staffUsers = model.staffUsers
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "users": {username: user.model_dump() for username, user in self.users.items()},
            "tickets": {ticket_id: ticket.model_dump() for ticket_id, ticket in self.tickets.items()},
            "comments": {comment_id: comment.model_dump() for comment_id, comment in self.comments.items()},
            "sessions": self.sessions,
            "next_ticket_id": self.next_ticket_id,
            "next_comment_id": self.next_comment_id,
            "staffUsers": self.staffUsers,
            "current_time": self.current_time
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in YYYY-MM-DD HH:MM:SS format."""
        return self.current_time

    def _is_authenticated(self, session_token: str) -> Optional[str]:
        """Check if session token is valid and return username."""
        for username, token in self.sessions.items():
            if token == session_token:
                return username
        return None

    def login(self, username: str, password: str) -> dict:
        """Authenticate user with credentials."""
        if username not in self.users:
            return {"success": False, "session_token": "", "username": ""}
        
        user = self.users[username]
        if user.password != password:
            return {"success": False, "session_token": "", "username": ""}
        
        # Generate session token using current_time
        time_hash = hash(self.current_time) % 100000
        session_token = f"session_{username}_{time_hash}"
        self.sessions[username] = session_token
        return {"success": True, "session_token": session_token, "username": username}

    def logout(self, session_token: str) -> dict:
        """Terminate current user session."""
        username = self._is_authenticated(session_token)
        if username:
            del self.sessions[username]
            return {"success": True}
        return {"success": False}

    def check_login_status(self, session_token: str) -> dict:
        """Verify current authentication state."""
        username = self._is_authenticated(session_token)
        if username:
            return {"is_authenticated": True, "username": username}
        return {"is_authenticated": False, "username": ""}

    def create_ticket(self, session_token: str, title: str, description: str = "", priority: int = 1, category: str = "general", assignee: Optional[str] = None) -> dict:
        """Create a new support ticket."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        if assignee and assignee not in self.staffUsers:
            raise ValueError("Invalid assignee")
        
        ticket_id = self.next_ticket_id
        self.next_ticket_id += 1
        timestamp = self._get_current_timestamp()
        
        ticket = Ticket(
            ticket_id=ticket_id,
            title=title,
            description=description,
            priority=priority,
            category=category,
            created_by=username,
            created_at=timestamp,
            updated_at=timestamp,
            assignee=assignee
        )
        
        self.tickets[ticket_id] = ticket
        return {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "status": "open",
            "priority": priority,
            "category": category,
            "created_by": username,
            "created_at": timestamp,
            "assignee": assignee
        }

    def get_ticket(self, ticket_id: int) -> dict:
        """Retrieve ticket details by ID."""
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket = self.tickets[ticket_id]
        return ticket.model_dump()

    def list_tickets(self, session_token: str, status: Optional[str] = None, priority: Optional[int] = None, category: Optional[str] = None, assignee: Optional[str] = None, limit: int = 5, offset: int = 0) -> dict:
        """List tickets with optional filtering."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        filtered_tickets = []
        for ticket in self.tickets.values():
            if status and ticket.status != status:
                continue
            if priority and ticket.priority != priority:
                continue
            if category and ticket.category != category:
                continue
            if assignee is not None and ticket.assignee != assignee:
                continue
            
            filtered_tickets.append({
                "ticket_id": ticket.ticket_id,
                "title": ticket.title,
                "status": ticket.status,
                "priority": ticket.priority,
                "category": ticket.category,
                "created_by": ticket.created_by,
                "created_at": ticket.created_at,
                "assignee": ticket.assignee
            })
        
        filtered_tickets = filtered_tickets[offset:offset + limit]
        return {"tickets": filtered_tickets}

    def search_tickets(self, session_token: str, query: str, status: Optional[str] = None, limit: int = 5) -> dict:
        """Search tickets by keywords."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        query_lower = query.lower()
        matching_tickets = []
        
        for ticket in self.tickets.values():
            if query_lower in ticket.title.lower() or query_lower in ticket.description.lower():
                if status and ticket.status != status:
                    continue
                
                matching_tickets.append({
                    "ticket_id": ticket.ticket_id,
                    "title": ticket.title,
                    "description": ticket.description,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "created_by": ticket.created_by,
                    "created_at": ticket.created_at
                })
        
        return {"tickets": matching_tickets[:limit]}

    def update_ticket(self, session_token: str, ticket_id: int, title: Optional[str] = None, description: Optional[str] = None, priority: Optional[int] = None, category: Optional[str] = None, assignee: Optional[str] = None, status: Optional[str] = None) -> dict:
        """Update ticket fields."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket = self.tickets[ticket_id]
        updated_fields = []
        
        if title is not None:
            ticket.title = title
            updated_fields.append("title")
        
        if description is not None:
            ticket.description = description
            updated_fields.append("description")
        
        if priority is not None:
            ticket.priority = priority
            updated_fields.append("priority")
        
        if category is not None:
            ticket.category = category
            updated_fields.append("category")
        
        if assignee is not None:
            if assignee == "":
                ticket.assignee = None
            else:
                if assignee not in self.staffUsers:
                    raise ValueError("Invalid assignee")
                ticket.assignee = assignee
            updated_fields.append("assignee")
        
        if status is not None:
            ticket.status = status
            updated_fields.append("status")
        
        ticket.updated_at = self._get_current_timestamp()
        
        return {
            "ticket_id": ticket_id,
            "status": "Ticket updated successfully",
            "updated_fields": updated_fields,
            "updated_at": ticket.updated_at
        }

    def close_ticket(self, session_token: str, ticket_id: int) -> dict:
        """Close a ticket."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket = self.tickets[ticket_id]
        ticket.status = "closed"
        ticket.updated_at = self._get_current_timestamp()
        
        return {
            "ticket_id": ticket_id,
            "status": "closed",
            "message": "Ticket closed successfully",
            "updated_at": ticket.updated_at
        }

    def resolve_ticket(self, session_token: str, ticket_id: int, resolution: str) -> dict:
        """Resolve a ticket with resolution details."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket = self.tickets[ticket_id]
        ticket.status = "resolved"
        ticket.resolution = resolution
        resolved_at = self._get_current_timestamp()
        ticket.updated_at = resolved_at
        
        return {
            "ticket_id": ticket_id,
            "status": "resolved",
            "resolution": resolution,
            "resolved_at": resolved_at,
            "updated_at": resolved_at
        }

    def get_user_tickets(self, session_token: str, username: Optional[str] = None, status: Optional[str] = None, limit: int = 5) -> dict:
        """Get tickets for a specific user."""
        current_username = self._is_authenticated(session_token)
        if not current_username:
            raise ValueError("Authentication required")
        
        if username is None:
            username = current_username
        
        user_tickets = []
        for ticket in self.tickets.values():
            if ticket.created_by == username:
                if status and ticket.status != status:
                    continue
                
                user_tickets.append({
                    "ticket_id": ticket.ticket_id,
                    "title": ticket.title,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "category": ticket.category,
                    "created_at": ticket.created_at,
                    "assignee": ticket.assignee
                })
        
        return {"tickets": user_tickets[:limit]}

    def add_comment(self, session_token: str, ticket_id: int, comment: str, is_internal: bool = False) -> dict:
        """Add a comment to a ticket."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        comment_id = self.next_comment_id
        self.next_comment_id += 1
        timestamp = self._get_current_timestamp()
        
        new_comment = Comment(
            comment_id=comment_id,
            ticket_id=ticket_id,
            comment=comment,
            author=username,
            is_internal=is_internal,
            created_at=timestamp
        )
        
        self.comments[comment_id] = new_comment
        
        return {
            "comment_id": comment_id,
            "ticket_id": ticket_id,
            "comment": comment,
            "author": username,
            "is_internal": is_internal,
            "created_at": timestamp
        }

    def get_ticket_comments(self, session_token: str, ticket_id: int, include_internal: bool = False) -> dict:
        """Get comments for a ticket."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket_comments = []
        for comment in self.comments.values():
            if comment.ticket_id == ticket_id:
                if comment.is_internal and not include_internal:
                    continue
                if comment.is_internal and username not in self.staffUsers:
                    continue
                
                ticket_comments.append({
                    "comment_id": comment.comment_id,
                    "ticket_id": comment.ticket_id,
                    "comment": comment.comment,
                    "author": comment.author,
                    "is_internal": comment.is_internal,
                    "created_at": comment.created_at
                })
        
        return {"comments": ticket_comments}

    def get_ticket_statistics(self, session_token: str, time_period: str = "all") -> dict:
        """Get ticket statistics."""
        username = self._is_authenticated(session_token)
        if not username:
            raise ValueError("Authentication required")
        
        total_tickets = len(self.tickets)
        open_tickets = sum(1 for t in self.tickets.values() if t.status == "open")
        in_progress_tickets = sum(1 for t in self.tickets.values() if t.status == "in_progress")
        resolved_tickets = sum(1 for t in self.tickets.values() if t.status == "resolved")
        closed_tickets = sum(1 for t in self.tickets.values() if t.status == "closed")
        
        resolved_times = []
        for ticket in self.tickets.values():
            if ticket.status == "resolved" and ticket.resolution:
                try:
                    created_time = datetime.strptime(ticket.created_at, "%Y-%m-%d %H:%M:%S")
                    updated_time = datetime.strptime(ticket.updated_at, "%Y-%m-%d %H:%M:%S")
                    hours = (updated_time - created_time).total_seconds() / 3600
                    resolved_times.append(hours)
                except:
                    pass
        
        avg_resolution_time = sum(resolved_times) / len(resolved_times) if resolved_times else 0
        
        tickets_by_category = {}
        tickets_by_priority = {}
        
        for ticket in self.tickets.values():
            tickets_by_category[ticket.category] = tickets_by_category.get(ticket.category, 0) + 1
            tickets_by_priority[str(ticket.priority)] = tickets_by_priority.get(str(ticket.priority), 0) + 1
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets,
            "average_resolution_time": round(avg_resolution_time, 2),
            "tickets_by_category": tickets_by_category,
            "tickets_by_priority": tickets_by_priority
        }

# Section 3: MCP Tools
mcp = FastMCP(name="TicketManagementSystem")
system = TicketManagementSystem()

# Global session storage to maintain state across tool calls
_current_session_token = None

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the ticket management system.
    
    Args:
        scenario (dict): Scenario dictionary matching TicketManagementScenario schema.
    
    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        system.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current ticket management state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return system.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def login(username: str, password: str) -> dict:
    """Authenticate a user with credentials and establish an active session.
    
    Args:
        username (str): The username credential for authenticating the user account.
        password (str): The password credential for authenticating the user account.
    
    Returns:
        success (bool): Indicates whether the authentication attempt was successful.
        session_token (str): The session token issued upon successful authentication.
        username (str): The username of the successfully authenticated user account.
    """
    try:
        global _current_session_token
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        result = system.login(username, password)
        if result["success"]:
            _current_session_token = result["session_token"]
        return result
    except Exception as e:
        raise e

@mcp.tool()
def logout() -> dict:
    """Terminate the current user session and invalidate the authentication token.
    
    Returns:
        success (bool): Indicates whether the logout operation completed successfully.
    """
    try:
        global _current_session_token
        result = system.logout(_current_session_token or "")
        if result["success"]:
            _current_session_token = None
        return result
    except Exception as e:
        raise e

@mcp.tool()
def check_login_status() -> dict:
    """Verify the current authentication state and retrieve active session information.
    
    Returns:
        is_authenticated (bool): Indicates whether a valid user session is currently active.
        username (str): The username of the currently authenticated user account.
    """
    try:
        return system.check_login_status(_current_session_token or "")
    except Exception as e:
        raise e

@mcp.tool()
def create_ticket(title: str, description: str = "", priority: int = 1, category: str = "general", assignee: Optional[str] = None) -> dict:
    """Create a new support ticket with specified details, priority, and optional assignment.
    
    Args:
        title (str): The title or subject line summarizing the ticket issue or request.
        description (str): [Optional] Detailed description of the issue, request, or context for the ticket.
        priority (int): [Optional] Priority level of the ticket ranging from 1 (lowest) to 5 (highest priority).
        category (str): [Optional] The category classifying the type of ticket.
        assignee (str): [Optional] The username of the staff member to assign this ticket to.
    
    Returns:
        ticket_id (int): The unique identifier assigned to the newly created ticket.
        title (str): The title or subject line of the created ticket.
        description (str): The detailed description of the ticket issue or request.
        status (str): The current status of the ticket, which is 'open' for newly created tickets.
        priority (int): The priority level assigned to the ticket, ranging from 1 (lowest) to 5 (highest).
        category (str): The category classifying the type of ticket.
        created_by (str): The username of the authenticated user who created the ticket.
        created_at (str): The timestamp when the ticket was created, in YYYY-MM-DD HH:MM:SS format.
        assignee (str): The username of the staff member assigned to the ticket, if an assignee was specified.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        # Priority and category validation handled by Pydantic Ticket model
        return system.create_ticket(_current_session_token or "", title, description, priority, category, assignee)
    except Exception as e:
        raise e

@mcp.tool()
def get_ticket(ticket_id: int) -> dict:
    """Retrieve comprehensive details about a specific ticket using its unique identifier.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to retrieve.
    
    Returns:
        ticket_id (int): The unique identifier of the ticket.
        title (str): The title or subject line of the ticket.
        description (str): The detailed description of the ticket issue or request.
        status (str): The current status of the ticket in its lifecycle.
        priority (int): The priority level assigned to the ticket, ranging from 1 (lowest) to 5 (highest).
        category (str): The category classifying the type of ticket.
        created_by (str): The username of the user who created the ticket.
        created_at (str): The timestamp when the ticket was created, in YYYY-MM-DD HH:MM:SS format.
        updated_at (str): The timestamp of the most recent update to the ticket, in YYYY-MM-DD HH:MM:SS format.
        assignee (str): The username of the staff member assigned to the ticket, if assigned.
        resolution (str): Detailed description of how the ticket was resolved or the solution provided, if the ticket has been resolved.
    """
    try:
        # Business logic check: verify ticket exists (not format/range validation)
        if not isinstance(ticket_id, int) or ticket_id < 1:
            raise ValueError("Ticket ID must be a positive integer")
        return system.get_ticket(ticket_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_tickets(status: Optional[str] = None, priority: Optional[int] = None, category: Optional[str] = None, assignee: Optional[str] = None, limit: int = 5, offset: int = 0) -> dict:
    """Retrieve a paginated list of tickets with optional filtering by status, priority, category, or assignee.
    
    Args:
        status (str): [Optional] Filter tickets by their current status.
        priority (int): [Optional] Filter tickets by priority level, ranging from 1 (lowest) to 5 (highest).
        category (str): [Optional] Filter tickets by category.
        assignee (str): [Optional] Filter tickets by the username of the assigned staff member.
        limit (int): [Optional] Maximum number of tickets to return in the result set.
        offset (int): [Optional] Number of tickets to skip before returning results, used for pagination.
    
    Returns:
        tickets (array): A list of ticket summaries matching the specified filters.
    """
    try:
        # Basic parameter checks only - validation handled by Pydantic models
        if limit < 0 or offset < 0:
            raise ValueError("Limit and offset must be non-negative")
        return system.list_tickets(_current_session_token or "", status, priority, category, assignee, limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def search_tickets(query: str, status: Optional[str] = None, limit: int = 5) -> dict:
    """Search for tickets by matching keywords in their title or description fields.
    
    Args:
        query (str): The search keyword or phrase to match against ticket titles and descriptions.
        status (str): [Optional] Filter search results by ticket status.
        limit (int): [Optional] Maximum number of matching tickets to return in the result set.
    
    Returns:
        tickets (array): A list of tickets matching the search query.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        if limit < 1:
            raise ValueError("Limit must be positive")
        return system.search_tickets(_current_session_token or "", query, status, limit)
    except Exception as e:
        raise e

@mcp.tool()
def update_ticket(ticket_id: int, title: Optional[str] = None, description: Optional[str] = None, priority: Optional[int] = None, category: Optional[str] = None, assignee: Optional[str] = None, status: Optional[str] = None) -> dict:
    """Modify one or more fields of an existing ticket with partial update support.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to update.
        title (str): [Optional] New title or subject line for the ticket.
        description (str): [Optional] New detailed description for the ticket.
        priority (int): [Optional] New priority level for the ticket, ranging from 1 (lowest) to 5 (highest).
        category (str): [Optional] New category for the ticket.
        assignee (str): [Optional] New assignee username for the ticket. Provide an empty string to remove the current assignee.
        status (str): [Optional] New status for the ticket.
    
    Returns:
        ticket_id (int): The unique identifier of the updated ticket.
        status (str): Confirmation message indicating the update operation was successful.
        updated_fields (array): List of field names that were modified during the update operation.
        updated_at (str): The timestamp when the ticket was updated, in YYYY-MM-DD HH:MM:SS format.
    """
    try:
        # Business logic check: verify ticket exists
        if not isinstance(ticket_id, int) or ticket_id < 1:
            raise ValueError("Ticket ID must be a positive integer")
        return system.update_ticket(_current_session_token or "", ticket_id, title, description, priority, category, assignee, status)
    except Exception as e:
        raise e

@mcp.tool()
def close_ticket(ticket_id: int) -> dict:
    """Mark a ticket as closed without providing resolution details.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to close.
    
    Returns:
        ticket_id (int): The unique identifier of the closed ticket.
        status (str): The updated status of the ticket, which is 'closed'.
        message (str): Confirmation message indicating the ticket was successfully closed.
        updated_at (str): The timestamp when the ticket was closed, in YYYY-MM-DD HH:MM:SS format.
    """
    try:
        # Business logic check: verify ticket exists
        if not isinstance(ticket_id, int) or ticket_id < 1:
            raise ValueError("Ticket ID must be a positive integer")
        return system.close_ticket(_current_session_token or "", ticket_id)
    except Exception as e:
        raise e

@mcp.tool()
def resolve_ticket(ticket_id: int, resolution: str) -> dict:
    """Mark a ticket as resolved and record the resolution details explaining how the issue was addressed.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to resolve.
        resolution (str): Detailed description of how the ticket was resolved or the solution provided to address the issue.
    
    Returns:
        ticket_id (int): The unique identifier of the resolved ticket.
        status (str): The updated status of the ticket, which is 'resolved'.
        resolution (str): The detailed description of how the ticket was resolved or the solution provided.
        resolved_at (str): The timestamp when the ticket was marked as resolved, in YYYY-MM-DD HH:MM:SS format.
        updated_at (str): The timestamp when the ticket was updated, in YYYY-MM-DD HH:MM:SS format.
    """
    try:
        # Business logic checks
        if not isinstance(ticket_id, int) or ticket_id < 1:
            raise ValueError("Ticket ID must be a positive integer")
        if not resolution or not isinstance(resolution, str):
            raise ValueError("Resolution must be a non-empty string")
        return system.resolve_ticket(_current_session_token or "", ticket_id, resolution)
    except Exception as e:
        raise e

@mcp.tool()
def get_user_tickets(username: Optional[str] = None, status: Optional[str] = None, limit: int = 5) -> dict:
    """Retrieve all tickets created by a specific user or the currently authenticated user.
    
    Args:
        username (str): [Optional] The username to filter tickets by. If not provided, returns tickets created by the currently authenticated user.
        status (str): [Optional] Filter tickets by their current status.
        limit (int): [Optional] Maximum number of tickets to return in the result set.
    
    Returns:
        tickets (array): A list of tickets created by the specified user.
    """
    try:
        if limit < 1:
            raise ValueError("Limit must be positive")
        return system.get_user_tickets(_current_session_token or "", username, status, limit)
    except Exception as e:
        raise e

@mcp.tool()
def add_comment(ticket_id: int, comment: str, is_internal: bool = False) -> dict:
    """Add a comment to a ticket, with support for public or internal (staff-only) visibility.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to add a comment to.
        comment (str): The text content of the comment to add to the ticket.
        is_internal (bool): [Optional] If true, the comment is marked as internal and visible only to staff members.
    
    Returns:
        comment_id (int): The unique identifier assigned to the newly created comment.
        ticket_id (int): The unique identifier of the ticket the comment was added to.
        comment (str): The text content of the comment.
        author (str): The username of the authenticated user who authored the comment.
        is_internal (bool): Indicates whether the comment is internal (staff-only) or public.
        created_at (str): The timestamp when the comment was created, in YYYY-MM-DD HH:MM:SS format.
    """
    try:
        # Business logic checks
        if not isinstance(ticket_id, int) or ticket_id < 1:
            raise ValueError("Ticket ID must be a positive integer")
        if not comment or not isinstance(comment, str):
            raise ValueError("Comment must be a non-empty string")
        return system.add_comment(_current_session_token or "", ticket_id, comment, is_internal)
    except Exception as e:
        raise e

@mcp.tool()
def get_ticket_comments(ticket_id: int, include_internal: bool = False) -> dict:
    """Retrieve all comments associated with a specific ticket, with optional inclusion of internal staff-only comments.
    
    Args:
        ticket_id (int): The unique identifier of the ticket to retrieve comments for.
        include_internal (bool): [Optional] If true, includes internal staff-only comments in the results.
    
    Returns:
        comments (array): A list of comments associated with the ticket.
    """
    try:
        # Business logic check: verify ticket exists
        if not isinstance(ticket_id, int) or ticket_id < 1:
            raise ValueError("Ticket ID must be a positive integer")
        return system.get_ticket_comments(_current_session_token or "", ticket_id, include_internal)
    except Exception as e:
        raise e

@mcp.tool()
def get_ticket_statistics(time_period: str = "all") -> dict:
    """Retrieve aggregated statistics and metrics about tickets in the system for a specified time period.
    
    Args:
        time_period (str): [Optional] The time period to calculate statistics for.
    
    Returns:
        total_tickets (int): The total count of tickets in the system for the specified time period.
        open_tickets (int): The count of tickets with 'open' status.
        in_progress_tickets (int): The count of tickets with 'in_progress' status.
        resolved_tickets (int): The count of tickets with 'resolved' status.
        closed_tickets (int): The count of tickets with 'closed' status.
        average_resolution_time (number): The average time in hours taken to resolve tickets during the specified time period.
        tickets_by_category (object): A breakdown of ticket counts grouped by category.
        tickets_by_priority (object): A breakdown of ticket counts grouped by priority level.
    """
    try:
        return system.get_ticket_statistics(_current_session_token or "", time_period)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()