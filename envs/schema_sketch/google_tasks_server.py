# Server: GoogleTasks

def list_task_lists(max_results: int = None, page_token: str = None) -> list:
    """
    List all task lists for the authenticated user.
    
    Args:
        max_results (int): [Optional] Maximum number of task lists to return per page
        page_token (str): [Optional] Token for pagination, omit for first page
        
    Returns:
        list: Each task list contains {
            "tasklist_id": str,
            "title": str
        }
    """
    pass

def get_task_list(tasklist_id: str) -> dict:
    """
    Get a specific task list by its identifier.
    
    Args:
        tasklist_id (str): Unique identifier of the task list
        
    Returns:
        dict: {
            "tasklist_id": str,
            "title": str
        }
    """
    pass

def create_task_list(tasklist_title: str) -> dict:
    """
    Create a new task list with the specified title.
    
    Args:
        tasklist_title (str): Title for the new task list, maximum 1024 characters
        
    Returns:
        dict: {
            "tasklist_id": str,
            "title": str
        }
    """
    pass

def update_task_list(tasklist_id: str, title: str) -> dict:
    """
    Update the title of an existing task list.
    
    Args:
        tasklist_id (str): Unique identifier of the task list to be updated
        title (str): New title for the task list, maximum 1024 characters
        
    Returns:
        dict: {
            "tasklist_id": str,
            "title": str
        }
    """
    pass

def delete_task_list(tasklist_id: str) -> None:
    """
    Permanently delete a task list and all its tasks.
    
    Args:
        tasklist_id (str): Unique identifier of the task list to be deleted
        
    Returns:
        None
    """
    pass

def list_tasks(tasklist_id: str, max_results: int = None, show_completed: bool = True, due_min: str = None, due_max: str = None) -> list:
    """
    List tasks from a specific task list with optional filtering.
    
    Args:
        tasklist_id (str): Unique identifier of the task list, use '@default' for default list
        max_results (int): [Optional] Maximum number of tasks to return, default 20, maximum 100
        show_completed (bool): [Optional] Include completed tasks, defaults to True
        due_min (str): [Optional] Exclude tasks due before this date (RFC3339 format)
        due_max (str): [Optional] Exclude tasks due after this date (RFC3339 format)
        
    Returns:
        list: Each task contains {
            "task_id": str,
            "title": str,
            "status": str,
            "due": str,
            "completed": str,
            "notes": str,
            "tasklist_id": str
        }
    """
    pass

def get_task(task_id: str, tasklist_id: str) -> dict:
    """
    Get a specific task by its identifier.
    
    Args:
        task_id (str): Unique identifier of the task
        tasklist_id (str): Unique identifier of the task list containing the task
        
    Returns:
        dict: {
            "task_id": str,
            "title": str,
            "status": str,
            "due": str,
            "completed": str,
            "notes": str,
            "tasklist_id": str
        }
    """
    pass

def create_task(tasklist_id: str, title: str, notes: str = None, due: str = None, status: str = "needsAction", completed: str = None, task_parent: str = None, task_previous: str = None) -> dict:
    """
    Create a new task in a task list, optionally as a subtask or positioned after another task.
    
    Args:
        tasklist_id (str): Unique identifier of the task list where the task will be created
        title (str): Title or name of the task, maximum 1024 characters
        notes (str): [Optional] Additional details or description, maximum 8192 characters
        due (str): [Optional] Due date in RFC3339 format (e.g., "2025-09-22T13:48:27Z")
        status (str): [Optional] Current status, either "needsAction" or "completed", defaults to "needsAction"
        completed (str): [Optional] Date/time when task was completed in RFC3339 format
        task_parent (str): [Optional] Identifier of parent task to create as subtask
        task_previous (str): [Optional] Identifier of task after which to place this task
        
    Returns:
        dict: {
            "task_id": str,
            "title": str,
            "status": str,
            "due": str,
            "completed": str,
            "notes": str,
            "tasklist_id": str
        }
    """
    pass

def update_task(tasklist_id: str, task_id: str, title: str = None, notes: str = None, due: str = None, status: str = None, completed: str = None) -> dict:
    """
    Update an existing task with new values. Only provided attributes will be updated.
    
    Args:
        tasklist_id (str): Unique identifier of the task list containing the task
        task_id (str): Unique identifier of the task to be updated
        title (str): [Optional] New title for the task
        notes (str): [Optional] New notes describing the task
        due (str): [Optional] New due date in RFC3339 format
        status (str): [Optional] New status, either "needsAction" or "completed"
        completed (str): [Optional] Date/time when task was completed in RFC3339 format
        
    Returns:
        dict: {
            "task_id": str,
            "title": str,
            "status": str,
            "due": str,
            "completed": str,
            "notes": str,
            "tasklist_id": str
        }
    """
    pass

def delete_task(task_id: str, tasklist_id: str) -> None:
    """
    Delete a specific task from a task list.
    
    Args:
        task_id (str): Unique identifier of the task to be deleted
        tasklist_id (str): Unique identifier of the task list containing the task
        
    Returns:
        None
    """
    pass

def move_task(tasklist_id: str, task_id: str, destination_tasklist: str = None, parent: str = None, previous: str = None) -> dict:
    """
    Move a task to another position in the same or different task list.
    
    Args:
        tasklist_id (str): Unique identifier of the task list containing the task
        task_id (str): Unique identifier of the task to be moved
        destination_tasklist (str): [Optional] Destination task list identifier, if set moves to this list
        parent (str): [Optional] New parent task identifier, if not provided moves to top level
        previous (str): [Optional] New previous sibling task identifier, if not provided moves to first position
        
    Returns:
        dict: {
            "task_id": str,
            "tasklist_id": str
        }
    """
    pass

def clear_tasks(tasklist_id: str) -> None:
    """
    Permanently clear all completed tasks from a task list.
    
    Args:
        tasklist_id (str): Unique identifier of the task list, use '@default' for default list
        
    Returns:
        None
    """
    pass

def get_upcoming_tasks(tasklist_id: str, days_ahead: int = 7, max_results: int = None) -> list:
    """
    Get tasks that are due within a specified number of days (upcoming deadlines).
    
    Args:
        tasklist_id (str): Unique identifier of the task list, use '@default' for default list
        days_ahead (int): [Optional] Number of days ahead to look for due tasks, defaults to 7
        max_results (int): [Optional] Maximum number of tasks to return
        
    Returns:
        list: Each task contains {
            "task_id": str,
            "title": str,
            "status": str,
            "due": str,
            "completed": str,
            "notes": str,
            "tasklist_id": str
        }
    """
    pass


