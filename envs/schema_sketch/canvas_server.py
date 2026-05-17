# Server: Canvas

def get_courses() -> dict:
    """
    Retrieve all available Canvas courses for the current user.
    
    Returns:
        dict: Dictionary mapping course names to their corresponding course IDs
    """
    pass

def get_modules(course_id: str) -> list:
    """
    Retrieve all modules within a specific Canvas course.
    
    Args:
        course_id (str): Canvas course identifier
        
    Returns:
        list: Each module contains {
            "module_id": str,
            "name": str,
            "status": str
        }
    """
    pass

def get_module_items(course_id: str, module_id: str) -> list:
    """
    Retrieve all items within a specific module in a Canvas course.
    
    Args:
        course_id (str): Canvas course identifier
        module_id (str): Module identifier within the course
        
    Returns:
        list: Each module item contains {
            "item_id": str,
            "title": str,
            "type": str,
            "url": str
        }
    """
    pass

def get_file_url(file_id: str, course_id: str) -> str:
    """
    Get the direct download URL for a file stored in Canvas.
    
    Args:
        file_id (str): Canvas file identifier
        course_id (str): Canvas course identifier
        
    Returns:
        str: Direct download URL for the file
    """
    pass

def get_course_assignments(course_id: str, bucket: str = None) -> list:
    """
    Retrieve all assignments for a specific Canvas course, with optional filtering by status.
    
    Args:
        course_id (str): Canvas course identifier
        bucket (str): [Optional] Filter by status - past, overdue, undated, ungraded, unsubmitted, upcoming, future
        
    Returns:
        list: Each assignment contains {
            "assignment_id": str,
            "name": str,
            "description": str,
            "due_date": str,
            "submission_status": str
        }
    """
    pass

def get_assignments_by_course_name(course_name: str, bucket: str = None) -> list:
    """
    Retrieve all assignments for a Canvas course using its name rather than ID.
    
    Args:
        course_name (str): Name of the course as it appears in Canvas (partial matches supported)
        bucket (str): [Optional] Filter by status - past, overdue, undated, ungraded, unsubmitted, upcoming, future
        
    Returns:
        list: Each assignment contains {
            "assignment_id": str,
            "name": str,
            "description": str,
            "due_date": str,
            "submission_status": str
        }
    """
    pass

def get_students_in_course(course_id: str) -> list:
    """
    Retrieve all students enrolled in a specific Canvas course.
    
    Args:
        course_id (str): Canvas course identifier
        
    Returns:
        list: Each student contains {
            "student_id": str,
            "name": str,
            "email": str,
            "enrollment_status": str,
        }
    """
    pass

def get_submission_status(course_id: str, assignment_id: str, student_id: str = None) -> dict:
    """
    Retrieve submission status and details for a specific assignment in a Canvas course.
    
    Args:
        course_id (str): Canvas course identifier
        assignment_id (str): Canvas assignment identifier
        student_id (str): [Optional] Specific student identifier. If not provided, returns submission status for all students
        
    Returns:
        dict: If student_id is provided, returns a single submission {
            "student_id": str,
            "student_name": str,
            "submitted_at": str,
            "submission_status": str,
            "score": float,
            "graded_at": str,
            "workflow_state": str
        }
        If student_id is not provided, returns a dictionary mapping student_id to submission details
    """
    pass

