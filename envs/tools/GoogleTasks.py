from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
from datetime import  timedelta
import re

# Section 1: Schema
class TaskList(BaseModel):
    """Represents a task list."""
    tasklist_id: str = Field(..., description="The unique identifier of the task list")
    title: str = Field(..., max_length=1024, description="The display title of the task list")

class Task(BaseModel):
    """Represents a task."""
    task_id: str = Field(..., description="The unique identifier of the task")
    title: str = Field(..., max_length=1024, description="The title or name of the task")
    status: str = Field(default="needsAction", pattern=r"^(needsAction|completed)$", description="Current status of the task")
    due: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", description="Due date/time of the task in RFC3339 format")
    completed: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", description="Date/time when the task was completed in RFC3339 format")
    notes: Optional[str] = Field(default=None, max_length=8192, description="Additional details or description of the task")
    tasklist_id: str = Field(..., description="The unique identifier of the task list containing this task")
    task_parent: Optional[str] = Field(default=None, description="The unique identifier of the parent task")
    task_previous: Optional[str] = Field(default=None, description="The unique identifier of the task after which this task is positioned")

class GoogleTasksScenario(BaseModel):
    """Main scenario model for Google Tasks management."""
    tasklists: Dict[str, TaskList] = Field(default={}, description="Task lists indexed by tasklist_id")
    tasks: Dict[str, Task] = Field(default={}, description="Tasks indexed by task_id")
    next_tasklist_id: int = Field(default=1, ge=1, description="Next available tasklist ID counter")
    next_task_id: int = Field(default=1, ge=1, description="Next available task ID counter")
    default_tasklist_id: str = Field(default="@default", description="Default task list ID")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [TaskList, Task, GoogleTasksScenario]

# Section 2: Class
class GoogleTasksAPI:
    def __init__(self):
        """Initialize Google Tasks API with empty state."""
        self.tasklists: Dict[str, TaskList] = {}
        self.tasks: Dict[str, Task] = {}
        self.next_tasklist_id: int = 1
        self.next_task_id: int = 1
        self.default_tasklist_id: str = "@default"
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = GoogleTasksScenario(**scenario)
        self.tasklists = model.tasklists
        self.tasks = model.tasks
        self.next_tasklist_id = model.next_tasklist_id
        self.next_task_id = model.next_task_id
        self.default_tasklist_id = model.default_tasklist_id
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "tasklists": {tid: tl.model_dump() for tid, tl in self.tasklists.items()},
            "tasks": {tid: t.model_dump() for tid, t in self.tasks.items()},
            "next_tasklist_id": self.next_tasklist_id,
            "next_task_id": self.next_task_id,
            "default_tasklist_id": self.default_tasklist_id,
            "current_time": self.current_time
        }

    def list_task_lists(self, max_results: Optional[int] = None, page_token: Optional[str] = None) -> dict:
        """List all task lists with optional pagination."""
        all_lists = list(self.tasklists.values())
        
        # Simple pagination logic
        start_idx = 0
        if page_token and page_token.isdigit():
            start_idx = int(page_token)
        
        end_idx = len(all_lists)
        if max_results and max_results > 0:
            end_idx = min(start_idx + max_results, len(all_lists))
        
        result_lists = all_lists[start_idx:end_idx]
        
        return {
            "task_lists": [{"tasklist_id": tl.tasklist_id, "title": tl.title} for tl in result_lists]
        }

    def get_task_list(self, tasklist_id: str) -> dict:
        """Retrieve a specific task list by ID."""
        if tasklist_id not in self.tasklists:
            raise ValueError(f"Task list {tasklist_id} not found")
        
        tl = self.tasklists[tasklist_id]
        return {"tasklist_id": tl.tasklist_id, "title": tl.title}

    def create_task_list(self, tasklist_title: str) -> dict:
        """Create a new task list."""
        tasklist_id = f"TL{self.next_tasklist_id}"
        self.next_tasklist_id += 1
        
        new_list = TaskList(tasklist_id=tasklist_id, title=tasklist_title)
        self.tasklists[tasklist_id] = new_list
        
        return {"tasklist_id": tasklist_id, "title": tasklist_title}

    def update_task_list(self, tasklist_id: str, title: str) -> dict:
        """Update task list title."""
        if tasklist_id not in self.tasklists:
            raise ValueError(f"Task list {tasklist_id} not found")
        
        self.tasklists[tasklist_id].title = title
        return {"tasklist_id": tasklist_id, "title": title}

    def delete_task_list(self, tasklist_id: str) -> dict:
        """Delete a task list and all its tasks."""
        if tasklist_id not in self.tasklists:
            raise ValueError(f"Task list {tasklist_id} not found")
        
        # Delete all tasks in this list
        tasks_to_delete = [tid for tid, task in self.tasks.items() if task.tasklist_id == tasklist_id]
        for tid in tasks_to_delete:
            del self.tasks[tid]
        
        del self.tasklists[tasklist_id]
        return {}

    def list_tasks(self, tasklist_id: str, max_results: Optional[int] = None, show_completed: bool = True,
                   due_min: Optional[str] = None, due_max: Optional[str] = None) -> dict:
        """List tasks from a task list with filtering."""
        if tasklist_id != "@default" and tasklist_id not in self.tasklists:
            raise ValueError(f"Task list {tasklist_id} not found")
        
        if tasklist_id == "@default":
            tasklist_id = self.default_tasklist_id
        
        filtered_tasks = []
        for task in self.tasks.values():
            if task.tasklist_id != tasklist_id:
                continue
            
            # Filter by completion status
            if not show_completed and task.status == "completed":
                continue
            
            # Filter by due date range
            if due_min and task.due and task.due < due_min:
                continue
            if due_max and task.due and task.due > due_max:
                continue
            
            filtered_tasks.append(task)
        
        # Apply max results limit
        if max_results and max_results > 0:
            filtered_tasks = filtered_tasks[:max_results]
        
        return {
            "tasks": [{
                "task_id": t.task_id,
                "title": t.title,
                "status": t.status,
                "due": t.due,
                "completed": t.completed,
                "notes": t.notes,
                "tasklist_id": t.tasklist_id
            } for t in filtered_tasks]
        }

    def get_task(self, task_id: str, tasklist_id: str) -> dict:
        """Retrieve a specific task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        if task.tasklist_id != tasklist_id:
            raise ValueError(f"Task {task_id} not found in task list {tasklist_id}")
        
        return {
            "task_id": task.task_id,
            "title": task.title,
            "status": task.status,
            "due": task.due,
            "completed": task.completed,
            "notes": task.notes,
            "tasklist_id": task.tasklist_id
        }

    def create_task(self, tasklist_id: str, title: str, notes: Optional[str] = None,
                    due: Optional[str] = None, status: str = "needsAction",
                    completed: Optional[str] = None, task_parent: Optional[str] = None,
                    task_previous: Optional[str] = None) -> dict:
        """Create a new task."""
        if tasklist_id != "@default" and tasklist_id not in self.tasklists:
            raise ValueError(f"Task list {tasklist_id} not found")
        
        if tasklist_id == "@default":
            tasklist_id = self.default_tasklist_id
        
        task_id = f"T{self.next_task_id}"
        self.next_task_id += 1
        
        new_task = Task(
            task_id=task_id,
            title=title,
            status=status,
            due=due,
            completed=completed,
            notes=notes,
            tasklist_id=tasklist_id,
            task_parent=task_parent,
            task_previous=task_previous
        )
        
        self.tasks[task_id] = new_task
        
        return {
            "task_id": task_id,
            "title": title,
            "status": status,
            "due": due,
            "completed": completed,
            "notes": notes,
            "tasklist_id": tasklist_id
        }

    def update_task(self, tasklist_id: str, task_id: str, title: Optional[str] = None,
                    notes: Optional[str] = None, due: Optional[str] = None,
                    status: Optional[str] = None, completed: Optional[str] = None) -> dict:
        """Update an existing task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        if task.tasklist_id != tasklist_id:
            raise ValueError(f"Task {task_id} not found in task list {tasklist_id}")
        
        # Update only provided fields
        if title is not None:
            task.title = title
        if notes is not None:
            task.notes = notes
        if due is not None:
            task.due = due
        if status is not None:
            task.status = status
        if completed is not None:
            task.completed = completed
        
        return {
            "task_id": task.task_id,
            "title": task.title,
            "status": task.status,
            "due": task.due,
            "completed": task.completed,
            "notes": task.notes,
            "tasklist_id": task.tasklist_id
        }

    def delete_task(self, task_id: str, tasklist_id: str) -> dict:
        """Delete a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        if task.tasklist_id != tasklist_id:
            raise ValueError(f"Task {task_id} not found in task list {tasklist_id}")
        
        del self.tasks[task_id]
        return {}

    def move_task(self, tasklist_id: str, task_id: str, destination_tasklist: Optional[str] = None,
                  parent: Optional[str] = None, previous: Optional[str] = None) -> dict:
        """Move a task within or between task lists."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        if task.tasklist_id != tasklist_id:
            raise ValueError(f"Task {task_id} not found in task list {tasklist_id}")
        
        # Handle destination tasklist
        if destination_tasklist and destination_tasklist != tasklist_id:
            if destination_tasklist not in self.tasklists:
                raise ValueError(f"Destination task list {destination_tasklist} not found")
            task.tasklist_id = destination_tasklist
        
        # Update positioning
        if parent is not None:
            task.task_parent = parent
        if previous is not None:
            task.task_previous = previous
        
        return {
            "task_id": task_id,
            "tasklist_id": task.tasklist_id
        }

    def clear_tasks(self, tasklist_id: str) -> dict:
        """Clear all completed tasks from a task list."""
        if tasklist_id != "@default" and tasklist_id not in self.tasklists:
            raise ValueError(f"Task list {tasklist_id} not found")
        
        if tasklist_id == "@default":
            tasklist_id = self.default_tasklist_id
        
        tasks_to_delete = [tid for tid, task in self.tasks.items() 
                          if task.tasklist_id == tasklist_id and task.status == "completed"]
        
        for tid in tasks_to_delete:
            del self.tasks[tid]
        
        return {}

    def get_upcoming_tasks(self, tasklist_id: str, days_ahead: int = 7,
                          max_results: Optional[int] = None) -> dict:
        """Get tasks due within specified days."""
        if tasklist_id != "@default" and tasklist_id not in self.tasklists:
            raise ValueError(f"Task list {tasklist_id} not found")
        
        if tasklist_id == "@default":
            tasklist_id = self.default_tasklist_id
        
        # Calculate date range
        # Parse current_time and add days_ahead
        from datetime import datetime as dt
        now_dt = dt.strptime(self.current_time, "%Y-%m-%dT%H:%M:%S")
        future_dt = now_dt + timedelta(days=days_ahead)
        now_str = self.current_time + "Z"
        future_str = future_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        upcoming_tasks = []
        for task in self.tasks.values():
            if task.tasklist_id != tasklist_id:
                continue
            
            if task.status == "completed":
                continue
            
            if task.due and task.due >= now_str and task.due <= future_str:
                upcoming_tasks.append(task)
        
        # Sort by due date
        upcoming_tasks.sort(key=lambda t: t.due or "")
        
        # Apply max results
        if max_results and max_results > 0:
            upcoming_tasks = upcoming_tasks[:max_results]
        
        return {
            "tasks": [{
                "task_id": t.task_id,
                "title": t.title,
                "status": t.status,
                "due": t.due,
                "completed": t.completed,
                "notes": t.notes,
                "tasklist_id": t.tasklist_id
            } for t in upcoming_tasks]
        }

# Section 3: MCP Tools
mcp = FastMCP(name="GoogleTasks")
api = GoogleTasksAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the Google Tasks API."""
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current Google Tasks state as scenario dictionary."""
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def list_task_lists(max_results: Optional[int] = None, page_token: Optional[str] = None) -> dict:
    """List all task lists with optional pagination."""
    try:
        return api.list_task_lists(max_results, page_token)
    except Exception as e:
        raise e

@mcp.tool()
def get_task_list(tasklist_id: str) -> dict:
    """Retrieve a specific task list by ID."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        return api.get_task_list(tasklist_id)
    except Exception as e:
        raise e

@mcp.tool()
def create_task_list(tasklist_title: str) -> dict:
    """Create a new task list."""
    try:
        if not tasklist_title or not isinstance(tasklist_title, str):
            raise ValueError("Tasklist_title must be a non-empty string")
        return api.create_task_list(tasklist_title)
    except Exception as e:
        raise e

@mcp.tool()
def update_task_list(tasklist_id: str, title: str) -> dict:
    """Update task list title."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        return api.update_task_list(tasklist_id, title)
    except Exception as e:
        raise e

@mcp.tool()
def delete_task_list(tasklist_id: str) -> dict:
    """Delete a task list and all its tasks."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        return api.delete_task_list(tasklist_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_tasks(tasklist_id: str, max_results: Optional[int] = None, show_completed: bool = True,
               due_min: Optional[str] = None, due_max: Optional[str] = None) -> dict:
    """List tasks from a task list with filtering."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        return api.list_tasks(tasklist_id, max_results, show_completed, due_min, due_max)
    except Exception as e:
        raise e

@mcp.tool()
def get_task(task_id: str, tasklist_id: str) -> dict:
    """Retrieve a specific task."""
    try:
        if not task_id or not isinstance(task_id, str):
            raise ValueError("Task_id must be a non-empty string")
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        return api.get_task(task_id, tasklist_id)
    except Exception as e:
        raise e

@mcp.tool()
def create_task(tasklist_id: str, title: str, notes: Optional[str] = None,
                due: Optional[str] = None, status: str = "needsAction",
                completed: Optional[str] = None, task_parent: Optional[str] = None,
                task_previous: Optional[str] = None) -> dict:
    """Create a new task."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        return api.create_task(tasklist_id, title, notes, due, status, completed, task_parent, task_previous)
    except Exception as e:
        raise e

@mcp.tool()
def update_task(tasklist_id: str, task_id: str, title: Optional[str] = None,
                notes: Optional[str] = None, due: Optional[str] = None,
                status: Optional[str] = None, completed: Optional[str] = None) -> dict:
    """Update an existing task."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        if not task_id or not isinstance(task_id, str):
            raise ValueError("Task_id must be a non-empty string")
        return api.update_task(tasklist_id, task_id, title, notes, due, status, completed)
    except Exception as e:
        raise e

@mcp.tool()
def delete_task(task_id: str, tasklist_id: str) -> dict:
    """Delete a task."""
    try:
        if not task_id or not isinstance(task_id, str):
            raise ValueError("Task_id must be a non-empty string")
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        return api.delete_task(task_id, tasklist_id)
    except Exception as e:
        raise e

@mcp.tool()
def move_task(tasklist_id: str, task_id: str, destination_tasklist: Optional[str] = None,
              parent: Optional[str] = None, previous: Optional[str] = None) -> dict:
    """Move a task within or between task lists."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        if not task_id or not isinstance(task_id, str):
            raise ValueError("Task_id must be a non-empty string")
        return api.move_task(tasklist_id, task_id, destination_tasklist, parent, previous)
    except Exception as e:
        raise e

@mcp.tool()
def clear_tasks(tasklist_id: str) -> dict:
    """Clear all completed tasks from a task list."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        return api.clear_tasks(tasklist_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_upcoming_tasks(tasklist_id: str, days_ahead: int = 7,
                      max_results: Optional[int] = None) -> dict:
    """Get tasks due within specified days."""
    try:
        if not tasklist_id or not isinstance(tasklist_id, str):
            raise ValueError("Tasklist_id must be a non-empty string")
        if not isinstance(days_ahead, int) or days_ahead <= 0:
            raise ValueError("Days_ahead must be a positive integer")
        return api.get_upcoming_tasks(tasklist_id, days_ahead, max_results)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()