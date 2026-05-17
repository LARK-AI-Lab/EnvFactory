from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Course(BaseModel):
    """Represents a Canvas course."""
    id: str = Field(..., description="Unique Canvas course identifier")
    name: str = Field(..., description="Course display name")

class Module(BaseModel):
    """Represents a Canvas module."""
    module_id: str = Field(..., description="Unique module identifier within course")
    name: str = Field(..., description="Module display name")
    status: str = Field(..., description="Current module status (locked, unlocked, completed)")

class ModuleItem(BaseModel):
    """Represents an item within a Canvas module."""
    item_id: str = Field(..., description="Unique module item identifier")
    title: str = Field(..., description="Item display title")
    type: str = Field(..., description="Type of content (File, Page, Assignment, Quiz, ExternalUrl)")
    url: str = Field(..., description="URL to access the module item")

class Assignment(BaseModel):
    """Represents a Canvas assignment."""
    assignment_id: str = Field(..., description="Unique assignment identifier")
    name: str = Field(..., description="Assignment display name")
    description: str = Field(default="", description="Detailed assignment description")
    due_date: str = Field(default="", description="Due date in ISO 8601 format")
    submission_status: str = Field(default="not_submitted", description="Current submission status")

class Student(BaseModel):
    """Represents a student enrolled in a course."""
    student_id: str = Field(..., description="Unique student identifier in Canvas")
    name: str = Field(..., description="Student full name")
    email: str = Field(..., description="Student email address")
    enrollment_status: str = Field(..., description="Enrollment status (active, invited, inactive)")

class Submission(BaseModel):
    """Represents a submission for an assignment."""
    student_id: str = Field(..., description="Student identifier")
    student_name: str = Field(..., description="Student full name")
    submitted_at: str = Field(default="", description="Submission timestamp in ISO 8601 format")
    submission_status: str = Field(default="not_submitted", description="Submission status")
    score: float = Field(default=0.0, ge=0, description="Numerical score awarded")
    graded_at: str = Field(default="", description="Grading timestamp in ISO 8601 format")
    workflow_state: str = Field(default="unsubmitted", description="Workflow state of submission")

class CanvasScenario(BaseModel):
    """Main scenario model for Canvas LMS data."""
    courses: Dict[str, Course] = Field(default={}, description="Dictionary mapping course IDs to Course objects")
    course_name_map: Dict[str, str] = Field(default={}, description="Dictionary mapping course names to course IDs")
    modules: Dict[str, List[Module]] = Field(default={}, description="Dictionary mapping course IDs to lists of modules")
    module_items: Dict[str, List[ModuleItem]] = Field(default={}, description="Dictionary mapping module IDs to lists of items")
    assignments: Dict[str, List[Assignment]] = Field(default={}, description="Dictionary mapping course IDs to lists of assignments")
    students: Dict[str, List[Student]] = Field(default={}, description="Dictionary mapping course IDs to lists of students")
    submissions: Dict[str, Dict[str, Submission]] = Field(default={}, description="Dictionary mapping assignment IDs to student submissions")
    files: Dict[str, Dict[str, str]] = Field(default={}, description="Dictionary mapping course IDs to file download URLs by file ID")

Scenario_Schema = [Course, Module, ModuleItem, Assignment, Student, Submission, CanvasScenario]

# Section 2: Class
class CanvasAPI:
    def __init__(self):
        """Initialize Canvas API with empty state."""
        self.courses: Dict[str, Course] = {}
        self.course_name_map: Dict[str, str] = {}
        self.modules: Dict[str, List[Module]] = {}
        self.module_items: Dict[str, List[ModuleItem]] = {}
        self.assignments: Dict[str, List[Assignment]] = {}
        self.students: Dict[str, List[Student]] = {}
        self.submissions: Dict[str, Dict[str, Submission]] = {}
        self.files: Dict[str, Dict[str, str]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = CanvasScenario(**scenario)
        self.courses = model.courses
        self.course_name_map = model.course_name_map
        self.modules = model.modules
        self.module_items = model.module_items
        self.assignments = model.assignments
        self.students = model.students
        self.submissions = model.submissions
        self.files = model.files

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "courses": {k: v.model_dump() for k, v in self.courses.items()},
            "course_name_map": self.course_name_map,
            "modules": {k: [m.model_dump() for m in v] for k, v in self.modules.items()},
            "module_items": {k: [i.model_dump() for i in v] for k, v in self.module_items.items()},
            "assignments": {k: [a.model_dump() for a in v] for k, v in self.assignments.items()},
            "students": {k: [s.model_dump() for s in v] for k, v in self.students.items()},
            "submissions": {k: {s_id: s.model_dump() for s_id, s in v.items()} for k, v in self.submissions.items()},
            "files": self.files
        }

    def get_courses(self) -> dict:
        """Retrieve all available Canvas courses."""
        return {"courses": {course.name: course.id for course in self.courses.values()}}

    def get_modules(self, course_id: str) -> dict:
        """Retrieve all modules within a specific Canvas course."""
        modules = self.modules.get(course_id, [])
        return {"modules": [m.model_dump() for m in modules]}

    def get_module_items(self, course_id: str, module_id: str) -> dict:
        """Retrieve all items within a specific module in a Canvas course."""
        items = self.module_items.get(module_id, [])
        return {"items": [i.model_dump() for i in items]}

    def get_file_url(self, file_id: str, course_id: str) -> dict:
        """Get the direct download URL for a file stored in Canvas."""
        course_files = self.files.get(course_id, {})
        url = course_files.get(file_id, "")
        return {"download_url": url}

    def get_course_assignments(self, course_id: str, bucket: Optional[str] = None) -> dict:
        """Retrieve all assignments for a specific Canvas course, with optional filtering."""
        assignments = self.assignments.get(course_id, [])
        if bucket:
            filtered = [a for a in assignments if a.submission_status == bucket]
            return {"assignments": [a.model_dump() for a in filtered]}
        return {"assignments": [a.model_dump() for a in assignments]}

    def get_assignments_by_course_name(self, course_name: str, bucket: Optional[str] = None) -> dict:
        """Retrieve all assignments for a Canvas course using its name."""
        course_id = None
        for name, cid in self.course_name_map.items():
            if course_name.lower() in name.lower():
                course_id = cid
                break
        
        if not course_id:
            return {"assignments": []}
        
        return self.get_course_assignments(course_id, bucket)

    def get_students_in_course(self, course_id: str) -> dict:
        """Retrieve all students enrolled in a specific Canvas course."""
        students = self.students.get(course_id, [])
        return {"students": [s.model_dump() for s in students]}

    def get_submission_status(self, course_id: str, assignment_id: str, student_id: Optional[str] = None) -> dict:
        """Retrieve submission status and grading details for a specific assignment."""
        submissions_dict = self.submissions.get(assignment_id, {})
        
        if student_id:
            if student_id in submissions_dict:
                return {"submissions": {student_id: submissions_dict[student_id].model_dump()}}
            else:
                return {"submissions": {}}
        
        return {"submissions": {k: v.model_dump() for k, v in submissions_dict.items()}}

# Section 3: MCP Tools
mcp = FastMCP(name="Canvas")
api = CanvasAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Canvas API.
    
    Args:
        scenario (dict): Scenario dictionary matching CanvasScenario schema.
    
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
    Save current Canvas state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_courses() -> dict:
    """
    Retrieve all available Canvas courses for the current authenticated user.
    
    Returns:
        courses (dict): Dictionary mapping course names to their Canvas course identifiers.
    """
    try:
        return api.get_courses()
    except Exception as e:
        raise e

@mcp.tool()
def get_modules(course_id: str) -> dict:
    """
    Retrieve all modules within a specific Canvas course.
    
    Args:
        course_id (str): The unique identifier of the Canvas course.
    
    Returns:
        modules (list): List of modules within the specified course.
    """
    try:
        if not course_id or not isinstance(course_id, str):
            raise ValueError("Course ID must be a non-empty string")
        return api.get_modules(course_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_module_items(course_id: str, module_id: str) -> dict:
    """
    Retrieve all items within a specific module in a Canvas course.
    
    Args:
        course_id (str): The unique identifier of the Canvas course.
        module_id (str): The unique identifier of the module within the course.
    
    Returns:
        items (list): List of items contained within the specified module.
    """
    try:
        if not course_id or not isinstance(course_id, str):
            raise ValueError("Course ID must be a non-empty string")
        if not module_id or not isinstance(module_id, str):
            raise ValueError("Module ID must be a non-empty string")
        return api.get_module_items(course_id, module_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_file_url(file_id: str, course_id: str) -> dict:
    """
    Get the direct download URL for a file stored in Canvas.
    
    Args:
        file_id (str): The unique identifier of the file in Canvas.
        course_id (str): The unique identifier of the Canvas course.
    
    Returns:
        download_url (str): The direct download URL for accessing the file.
    """
    try:
        if not file_id or not isinstance(file_id, str):
            raise ValueError("File ID must be a non-empty string")
        if not course_id or not isinstance(course_id, str):
            raise ValueError("Course ID must be a non-empty string")
        result = api.get_file_url(file_id, course_id)
        if not result["download_url"]:
            raise ValueError(f"File {file_id} not found in course {course_id}")
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_course_assignments(course_id: str, bucket: Optional[str] = None) -> dict:
    """
    Retrieve all assignments for a specific Canvas course, with optional filtering by submission status.
    
    Args:
        course_id (str): The unique identifier of the Canvas course.
        bucket (str): [Optional] Filter for assignment status (past, overdue, undated, ungraded, unsubmitted, upcoming, future).
    
    Returns:
        assignments (list): List of assignments matching the specified criteria.
    """
    try:
        if not course_id or not isinstance(course_id, str):
            raise ValueError("Course ID must be a non-empty string")
        if bucket and not isinstance(bucket, str):
            raise ValueError("Bucket must be a string if provided")
        return api.get_course_assignments(course_id, bucket)
    except Exception as e:
        raise e

@mcp.tool()
def get_assignments_by_course_name(course_name: str, bucket: Optional[str] = None) -> dict:
    """
    Retrieve all assignments for a Canvas course using its name rather than ID, supporting partial name matches.
    
    Args:
        course_name (str): The name of the course as it appears in Canvas. Partial matches are supported.
        bucket (str): [Optional] Filter for assignment status (past, overdue, undated, ungraded, unsubmitted, upcoming, future).
    
    Returns:
        assignments (list): List of assignments matching the specified criteria.
    """
    try:
        if not course_name or not isinstance(course_name, str):
            raise ValueError("Course name must be a non-empty string")
        if bucket and not isinstance(bucket, str):
            raise ValueError("Bucket must be a string if provided")
        return api.get_assignments_by_course_name(course_name, bucket)
    except Exception as e:
        raise e

@mcp.tool()
def get_students_in_course(course_id: str) -> dict:
    """
    Retrieve all students enrolled in a specific Canvas course.
    
    Args:
        course_id (str): The unique identifier of the Canvas course.
    
    Returns:
        students (list): List of students enrolled in the specified course.
    """
    try:
        if not course_id or not isinstance(course_id, str):
            raise ValueError("Course ID must be a non-empty string")
        return api.get_students_in_course(course_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_submission_status(course_id: str, assignment_id: str, student_id: Optional[str] = None) -> dict:
    """
    Retrieve submission status and grading details for a specific assignment in a Canvas course, optionally filtered by student.
    
    Args:
        course_id (str): The unique identifier of the Canvas course.
        assignment_id (str): The unique identifier of the assignment.
        student_id (str): [Optional] The unique identifier of the student in Canvas. If not provided, returns submission status for all students.
    
    Returns:
        submissions (dict): Dictionary mapping student IDs to their submission details.
    """
    try:
        if not course_id or not isinstance(course_id, str):
            raise ValueError("Course ID must be a non-empty string")
        if not assignment_id or not isinstance(assignment_id, str):
            raise ValueError("Assignment ID must be a non-empty string")
        if student_id and not isinstance(student_id, str):
            raise ValueError("Student ID must be a string if provided")
        return api.get_submission_status(course_id, assignment_id, student_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()