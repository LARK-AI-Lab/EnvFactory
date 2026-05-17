# Server: TickTick

def ticktick_oauth2_authorization_step1(scope: str, client_id: str, redirect_uri: str, state: str = None) -> dict:
    """
    Generate TickTick OAuth2 authorization URL to redirect user for authorization code.
    
    Args:
        scope (str): Space-separated permission scopes. Available scopes: 'tasks:read', 'tasks:write'
        client_id (str): TickTick application's client ID from Developer Center
        redirect_uri (str): Exact redirect URI registered with TickTick application
        state (str): [Optional] Opaque value for CSRF protection and request state
        
    Returns:
        dict: {
            "authorization_url": str
        }
    """
    pass

def ticktick_get_user_project() -> list:
    """
    Retrieve all projects for the authenticated user.
    
    Returns:
        list: Each project contains {
            "project_id": str,
            "name": str,
            "color": str,
            "kind": str
        }
    """
    pass

def ticktick_get_project_with_data(project_id: str) -> dict:
    """
    Retrieve a project and its associated data including tasks and columns.
    
    Args:
        project_id (str): Project identifier to retrieve data for
        
    Returns:
        dict: {
            "project_id": str,
            "name": str,
            "tasks": list,
            "columns": list
        }
    """
    pass

def ticktick_create_project(name: str, kind: str = None, color: str = None, viewMode: str = None, sortOrder: int = None) -> dict:
    """
    Create a new project in TickTick.
    
    Args:
        name (str): Name of the new project
        kind (str): [Optional] Project kind
        color (str): [Optional] Hex color code for the project (e.g., '#F18181')
        viewMode (str): [Optional] View mode for the project
        sortOrder (int): [Optional] Sort order value of the project
        
    Returns:
        dict: {
            "project_id": str,
            "name": str,
            "color": str,
            "kind": str
        }
    """
    pass

def ticktick_update_project(project_id: str, name: str = None, kind: str = None, color: str = None, viewMode: str = None, sortOrder: int = None) -> dict:
    """
    Update an existing project.
    
    Args:
        project_id (str): Project identifier to update
        name (str): [Optional] New name of the project
        kind (str): [Optional] Kind of the project, 'TASK' or 'NOTE'
        color (str): [Optional] Hex color code for the project (e.g., '#F18181')
        viewMode (str): [Optional] View mode for the project
        sortOrder (int): [Optional] Sort order value of the project
        
    Returns:
        dict: {
            "project_id": str,
            "name": str,
            "color": str,
            "kind": str
        }
    """
    pass

def ticktick_delete_project(project_id: str) -> dict:
    """
    Delete a specific project permanently.
    
    Args:
        project_id (str): Project identifier to delete
        
    Returns:
        dict: {
            "project_id": str,
            "deleted": bool
        }
    """
    pass

def ticktick_create_task(title: str, project_id: str = None, notes: str = None, description: str = None, due_date: str = None, priority: int = None) -> dict:
    """
    Create a new task in TickTick with basic parameters.
    
    Args:
        title (str): Title of the task
        project_id (str): [Optional] ID of the project (list) to add the task to
        notes (str): [Optional] Main content or notes of the task
        description (str): [Optional] Extended description of the task
        due_date (str): [Optional] ISO 8601 due date/time (e.g., '2023-04-24T17:00:00+0000')
        priority (int): [Optional] Task priority (0=None, 1=Low, 3=Medium, 5=High)
        
    Returns:
        dict: {
            "taskId": str,
            "title": str,
            "project_id": str,
            "dueDate": str,
            "priority": int
        }
    """
    pass


def ticktick_update_task(task_id: str, project_id: str, title: str = None, notes: str = None, description: str = None, due_date: str = None, priority: int = None) -> dict:
    """
    Update an existing task with basic parameters.
    
    Args:
        task_id (str): Task identifier to update
        project_id (str): Project identifier containing the task
        title (str): [Optional] New title of the task
        notes (str): [Optional] Content or notes of the task
        description (str): [Optional] Extended description of the task
        due_date (str): [Optional] ISO 8601 due date/time (e.g., '2023-04-24T17:00:00+0000')
        priority (int): [Optional] Task priority (0=None, 1=Low, 3=Medium, 5=High)
        
    Returns:
        dict: {
            "taskId": str,
            "title": str,
            "project_id": str,
            "dueDate": str,
            "priority": int
        }
    """
    pass


def ticktick_complete_task(task_id: str, project_id: str) -> dict:
    """
    Mark a task as complete.
    
    Args:
        task_id (str): Identifier of the task to mark as complete
        project_id (str): Project identifier containing the task to complete
        
    Returns:
        dict: {
            "task_id": str,
            "project_id": str,
            "status": str
        }
    """
    pass

def ticktick_delete_task(task_id: str, project_id: str) -> dict:
    """
    Delete a specific task from a project.
    
    Args:
        task_id (str): Task identifier to delete
        project_id (str): Project identifier containing the task to delete
        
    Returns:
        dict: {
            "task_id": str,
            "project_id": str,
            "deleted": bool
        }
    """
    pass

