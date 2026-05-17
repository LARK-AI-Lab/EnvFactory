from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Task(BaseModel):
    """Represents a task in TickTick."""
    taskId: str = Field(..., description="Unique identifier for the task")
    title: str = Field(..., description="Title of the task")
    project_id: str = Field(..., description="ID of the project containing the task")
    dueDate: Optional[str] = Field(default=None, description="Due date in ISO 8601 format")
    priority: int = Field(default=0, ge=0, le=5, description="Priority level (0=None, 1=Low, 3=Medium, 5=High)")
    notes: Optional[str] = Field(default=None, description="Notes content for the task")
    description: Optional[str] = Field(default=None, description="Extended description of the task")
    status: str = Field(default="pending", description="Current status of the task")

class Project(BaseModel):
    """Represents a project in TickTick."""
    project_id: str = Field(..., description="Unique identifier for the project")
    name: str = Field(..., description="Display name of the project")
    color: str = Field(default="#F18181", description="Hex color code for visual identification")
    kind: str = Field(default="TASK", description="Type of project (TASK or NOTE)")
    viewMode: Optional[str] = Field(default=None, description="View mode configuration")
    sortOrder: Optional[int] = Field(default=None, description="Sort order for project positioning")

class Column(BaseModel):
    """Represents a column/section within a project."""
    column_id: str = Field(..., description="Unique identifier for the column")
    name: str = Field(..., description="Name of the column")
    project_id: str = Field(..., description="ID of the project containing the column")

class TickTickScenario(BaseModel):
    """Main scenario model for TickTick task management."""
    projects: Dict[str, Project] = Field(default={}, description="All projects indexed by project_id")
    tasks: Dict[str, Task] = Field(default={}, description="All tasks indexed by task_id")
    columns: Dict[str, Column] = Field(default={}, description="All columns indexed by column_id")
    project_columns: Dict[str, List[str]] = Field(default={}, description="Mapping of project_id to list of column_ids")
    task_project_mapping: Dict[str, str] = Field(default={}, description="Mapping of task_id to project_id")
    oauth_state: Dict[str, str] = Field(default={}, description="OAuth2 state storage")
    colorPaletteMap: Dict[str, str] = Field(default={
        "#F18181": "Red", "#F9A825": "Orange", "#FDD835": "Yellow", "#7CB342": "Green",
        "#29B6F6": "Blue", "#AB47BC": "Purple", "#EC407A": "Pink", "#8D6E63": "Brown",
        "#78909C": "Gray", "#26C6DA": "Cyan", "#66BB6A": "Light Green", "#FFA726": "Light Orange",
        "#5C6BC0": "Indigo", "#D4E157": "Lime", "#26A69A": "Teal", "#EF5350": "Light Red",
        "#9CCC65": "Pale Green", "#FFEE58": "Pale Yellow", "#42A5F5": "Light Blue", "#BDBDBD": "Light Gray"
    }, description="Available color palette for projects")
    priorityLabelsMap: Dict[int, str] = Field(default={
        0: "None", 1: "Low", 3: "Medium", 5: "High"
    }, description="Priority level labels")

Scenario_Schema = [Task, Project, Column, TickTickScenario]

# Section 2: Class
class TickTickAPI:
    def __init__(self):
        """Initialize TickTick API with empty state."""
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}
        self.columns: Dict[str, Column] = {}
        self.project_columns: Dict[str, List[str]] = {}
        self.task_project_mapping: Dict[str, str] = {}
        self.oauth_state: Dict[str, str] = {}
        self.colorPaletteMap: Dict[str, str] = {}
        self.priorityLabelsMap: Dict[int, str] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = TickTickScenario(**scenario)
        self.projects = model.projects
        self.tasks = model.tasks
        self.columns = model.columns
        self.project_columns = model.project_columns
        self.task_project_mapping = model.task_project_mapping
        self.oauth_state = model.oauth_state
        self.colorPaletteMap = model.colorPaletteMap
        self.priorityLabelsMap = model.priorityLabelsMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "projects": {pid: proj.model_dump() for pid, proj in self.projects.items()},
            "tasks": {tid: task.model_dump() for tid, task in self.tasks.items()},
            "columns": {cid: col.model_dump() for cid, col in self.columns.items()},
            "project_columns": self.project_columns,
            "task_project_mapping": self.task_project_mapping,
            "oauth_state": self.oauth_state,
            "colorPaletteMap": self.colorPaletteMap,
            "priorityLabelsMap": self.priorityLabelsMap
        }

    def ticktick_oauth2_authorization_step1(self, scope: str, client_id: str, redirect_uri: str, state: Optional[str] = None) -> dict:
        """Generate OAuth2 authorization URL."""
        auth_url = f"https://ticktick.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
        if state:
            auth_url += f"&state={state}"
            self.oauth_state[state] = "pending"
        return {"authorization_url": auth_url}

    def ticktick_get_user_project(self) -> dict:
        """Retrieve all projects for the authenticated user."""
        projects_list = [proj.model_dump() for proj in self.projects.values()]
        return {"projects": projects_list}

    def ticktick_get_project_with_data(self, project_id: str) -> dict:
        """Retrieve specific project with tasks and columns."""
        if project_id not in self.projects:
            return {"error": "Project not found"}
        
        project = self.projects[project_id]
        project_tasks = [task.model_dump() for task in self.tasks.values() if task.project_id == project_id]
        project_cols = [col.model_dump() for col in self.columns.values() if col.project_id == project_id]
        
        return {
            "project_id": project_id,
            "name": project.name,
            "tasks": project_tasks,
            "columns": project_cols
        }

    def ticktick_create_project(self, name: str, kind: Optional[str] = "TASK", color: Optional[str] = "#F18181", viewMode: Optional[str] = None, sortOrder: Optional[int] = None) -> dict:
        """Create a new project."""
        import uuid
        project_id = str(uuid.uuid4())
        
        project = Project(
            project_id=project_id,
            name=name,
            kind=kind or "TASK",
            color=color or "#F18181",
            viewMode=viewMode,
            sortOrder=sortOrder
        )
        
        self.projects[project_id] = project
        self.project_columns[project_id] = []
        
        return {
            "project_id": project_id,
            "name": project.name,
            "color": project.color,
            "kind": project.kind
        }

    def ticktick_update_project(self, project_id: str, name: Optional[str] = None, kind: Optional[str] = None, color: Optional[str] = None, viewMode: Optional[str] = None, sortOrder: Optional[int] = None) -> dict:
        """Update existing project properties."""
        if project_id not in self.projects:
            return {"error": "Project not found"}
        
        project = self.projects[project_id]
        
        if name is not None:
            project.name = name
        if kind is not None:
            project.kind = kind
        if color is not None:
            project.color = color
        if viewMode is not None:
            project.viewMode = viewMode
        if sortOrder is not None:
            project.sortOrder = sortOrder
        
        self.projects[project_id] = project
        
        return {
            "project_id": project_id,
            "name": project.name,
            "color": project.color,
            "kind": project.kind
        }

    def ticktick_delete_project(self, project_id: str) -> dict:
        """Delete a project and all associated data."""
        if project_id not in self.projects:
            return {"error": "Project not found"}
        
        # Remove all tasks in the project
        tasks_to_remove = [tid for tid, task in self.tasks.items() if task.project_id == project_id]
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.task_project_mapping:
                del self.task_project_mapping[task_id]
        
        # Remove all columns in the project
        columns_to_remove = [cid for cid, col in self.columns.items() if col.project_id == project_id]
        for column_id in columns_to_remove:
            del self.columns[column_id]
        
        # Remove project and its column mapping
        del self.projects[project_id]
        if project_id in self.project_columns:
            del self.project_columns[project_id]
        
        return {
            "project_id": project_id,
            "deleted": True
        }

    def ticktick_create_task(self, title: str, project_id: Optional[str] = None, notes: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[int] = 0) -> dict:
        """Create a new task."""
        import uuid
        task_id = str(uuid.uuid4())
        
        task = Task(
            taskId=task_id,
            title=title,
            project_id=project_id or "",
            notes=notes,
            description=description,
            dueDate=due_date,
            priority=priority or 0
        )
        
        self.tasks[task_id] = task
        if project_id:
            self.task_project_mapping[task_id] = project_id
        
        return {
            "taskId": task_id,
            "title": title,
            "project_id": project_id or "",
            "dueDate": due_date,
            "priority": priority or 0
        }

    def ticktick_update_task(self, task_id: str, project_id: str, title: Optional[str] = None, notes: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[int] = None) -> dict:
        """Update existing task properties."""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if title is not None:
            task.title = title
        if notes is not None:
            task.notes = notes
        if description is not None:
            task.description = description
        if due_date is not None:
            task.dueDate = due_date
        if priority is not None:
            task.priority = priority
        
        task.project_id = project_id
        self.task_project_mapping[task_id] = project_id
        self.tasks[task_id] = task
        
        return {
            "taskId": task_id,
            "title": task.title,
            "project_id": project_id,
            "dueDate": task.dueDate,
            "priority": task.priority
        }

    def ticktick_complete_task(self, task_id: str, project_id: str) -> dict:
        """Mark a task as complete."""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        task.status = "completed"
        self.tasks[task_id] = task
        
        return {
            "task_id": task_id,
            "project_id": project_id,
            "status": "completed"
        }

    def ticktick_delete_task(self, task_id: str, project_id: str) -> dict:
        """Delete a specific task."""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        del self.tasks[task_id]
        if task_id in self.task_project_mapping:
            del self.task_project_mapping[task_id]
        
        return {
            "task_id": task_id,
            "project_id": project_id,
            "deleted": True
        }

# Section 3: MCP Tools
mcp = FastMCP(name="TickTick")
api = TickTickAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the TickTick API.
    
    Args:
        scenario (dict): Scenario dictionary matching TickTickScenario schema.
    
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
    Save current TickTick state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_oauth2_authorization_step1(scope: str, client_id: str, redirect_uri: str, state: Optional[str] = None) -> dict:
    """
    Generate a TickTick OAuth2 authorization URL to redirect the user for obtaining an authorization code.
    
    Args:
        scope (str): Space-separated permission scopes for the authorization request.
        client_id (str): The TickTick application's client ID obtained from the Developer Center.
        redirect_uri (str): The exact redirect URI registered with the TickTick application for OAuth2 callback.
        state (str) [Optional]: An opaque value used for CSRF protection and maintaining request state.
    
    Returns:
        authorization_url (str): The fully constructed OAuth2 authorization URL.
    """
    try:
        if not scope or not isinstance(scope, str):
            raise ValueError("Scope must be a non-empty string")
        if not client_id or not isinstance(client_id, str):
            raise ValueError("Client ID must be a non-empty string")
        if not redirect_uri or not isinstance(redirect_uri, str):
            raise ValueError("Redirect URI must be a non-empty string")
        return api.ticktick_oauth2_authorization_step1(scope, client_id, redirect_uri, state)
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_get_user_project() -> dict:
    """
    Retrieve all projects belonging to the authenticated user.
    
    Returns:
        projects (list): List of all projects owned by the authenticated user.
    """
    try:
        return api.ticktick_get_user_project()
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_get_project_with_data(project_id: str) -> dict:
    """
    Retrieve a specific project along with its associated tasks and columns.
    
    Args:
        project_id (str): The unique identifier of the project to retrieve data for.
    
    Returns:
        project_id (str): The unique identifier of the project.
        name (str): The display name of the project.
        tasks (list): List of tasks contained within the project.
        columns (list): List of columns or sections defined within the project.
    """
    try:
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a non-empty string")
        result = api.ticktick_get_project_with_data(project_id)
        if "error" in result:
            raise ValueError(result["error"])
        return result
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_create_project(name: str, kind: Optional[str] = "TASK", color: Optional[str] = "#F18181", viewMode: Optional[str] = None, sortOrder: Optional[int] = None) -> dict:
    """
    Create a new project in TickTick with specified configuration options.
    
    Args:
        name (str): The display name for the new project.
        kind (str) [Optional]: The type of the project (TASK or NOTE). Defaults to TASK.
        color (str) [Optional]: The hex color code for the project. Defaults to #F18181.
        viewMode (str) [Optional]: The view mode configuration for displaying the project.
        sortOrder (int) [Optional]: The numeric sort order value determining project position.
    
    Returns:
        project_id (str): The unique identifier of the newly created project.
        name (str): The display name of the project.
        color (str): The hex color code assigned to the project.
        kind (str): The type of the project.
    """
    try:
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        return api.ticktick_create_project(name, kind, color, viewMode, sortOrder)
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_update_project(project_id: str, name: Optional[str] = None, kind: Optional[str] = None, color: Optional[str] = None, viewMode: Optional[str] = None, sortOrder: Optional[int] = None) -> dict:
    """
    Update an existing project's properties such as name, color, or view settings.
    
    Args:
        project_id (str): The unique identifier of the project to update.
        name (str) [Optional]: The new display name for the project.
        kind (str) [Optional]: The type of the project (TASK or NOTE).
        color (str) [Optional]: The hex color code for the project.
        viewMode (str) [Optional]: The view mode configuration for displaying the project.
        sortOrder (int) [Optional]: The numeric sort order value determining project position.
    
    Returns:
        project_id (str): The unique identifier of the updated project.
        name (str): The display name of the project.
        color (str): The hex color code assigned to the project.
        kind (str): The type of the project.
    """
    try:
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a non-empty string")
        result = api.ticktick_update_project(project_id, name, kind, color, viewMode, sortOrder)
        if "error" in result:
            raise ValueError(result["error"])
        return result
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_delete_project(project_id: str) -> dict:
    """
    Permanently delete a specific project and all its associated data.
    
    Args:
        project_id (str): The unique identifier of the project to delete.
    
    Returns:
        project_id (str): The unique identifier of the deleted project.
        deleted (bool): Indicates whether the project was successfully deleted.
    """
    try:
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a non-empty string")
        result = api.ticktick_delete_project(project_id)
        if "error" in result:
            raise ValueError(result["error"])
        return result
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_create_task(title: str, project_id: Optional[str] = None, notes: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[int] = 0) -> dict:
    """
    Create a new task in TickTick with specified title, project assignment, and optional details.
    
    Args:
        title (str): The title or name of the task to create.
        project_id (str) [Optional]: The unique identifier of the project to add the task to.
        notes (str) [Optional]: The main content or notes associated with the task.
        description (str) [Optional]: An extended description providing additional details.
        due_date (str) [Optional]: The due date and time in ISO 8601 format.
        priority (int) [Optional]: The priority level (0=None, 1=Low, 3=Medium, 5=High).
    
    Returns:
        taskId (str): The unique identifier of the newly created task.
        title (str): The title or name of the task.
        project_id (str): The unique identifier of the project containing the task.
        dueDate (str): The due date and time assigned to the task.
        priority (int): The priority level of the task.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        return api.ticktick_create_task(title, project_id, notes, description, due_date, priority)
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_update_task(task_id: str, project_id: str, title: Optional[str] = None, notes: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[int] = None) -> dict:
    """
    Update an existing task's properties such as title, notes, due date, or priority.
    
    Args:
        task_id (str): The unique identifier of the task to update.
        project_id (str): The unique identifier of the project containing the task.
        title (str) [Optional]: The new title or name for the task.
        notes (str) [Optional]: The main content or notes associated with the task.
        description (str) [Optional]: An extended description providing additional details.
        due_date (str) [Optional]: The due date and time in ISO 8601 format.
        priority (int) [Optional]: The priority level (0=None, 1=Low, 3=Medium, 5=High).
    
    Returns:
        taskId (str): The unique identifier of the updated task.
        title (str): The title or name of the task.
        project_id (str): The unique identifier of the project containing the task.
        dueDate (str): The due date and time assigned to the task.
        priority (int): The priority level of the task.
    """
    try:
        if not task_id or not isinstance(task_id, str):
            raise ValueError("Task ID must be a non-empty string")
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a non-empty string")
        result = api.ticktick_update_task(task_id, project_id, title, notes, description, due_date, priority)
        if "error" in result:
            raise ValueError(result["error"])
        return result
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_complete_task(task_id: str, project_id: str) -> dict:
    """
    Mark a specific task as complete within its project.
    
    Args:
        task_id (str): The unique identifier of the task to mark as complete.
        project_id (str): The unique identifier of the project containing the task.
    
    Returns:
        task_id (str): The unique identifier of the completed task.
        project_id (str): The unique identifier of the project containing the task.
        status (str): The current completion status of the task.
    """
    try:
        if not task_id or not isinstance(task_id, str):
            raise ValueError("Task ID must be a non-empty string")
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a non-empty string")
        result = api.ticktick_complete_task(task_id, project_id)
        if "error" in result:
            raise ValueError(result["error"])
        return result
    except Exception as e:
        raise e

@mcp.tool()
def ticktick_delete_task(task_id: str, project_id: str) -> dict:
    """
    Permanently delete a specific task from a project.
    
    Args:
        task_id (str): The unique identifier of the task to delete.
        project_id (str): The unique identifier of the project containing the task.
    
    Returns:
        task_id (str): The unique identifier of the deleted task.
        project_id (str): The unique identifier of the project that contained the task.
        deleted (bool): Indicates whether the task was successfully deleted.
    """
    try:
        if not task_id or not isinstance(task_id, str):
            raise ValueError("Task ID must be a non-empty string")
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a non-empty string")
        result = api.ticktick_delete_task(task_id, project_id)
        if "error" in result:
            raise ValueError(result["error"])
        return result
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()