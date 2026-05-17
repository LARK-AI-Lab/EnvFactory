# Server: MetMuseum

def list_departments() -> list:
    """
    List all valid departments at The Met.
    
    Returns:
        list: Each department contains {
            "departmentId": int,
            "displayName": str
        }
    """
    pass

def search_museum_objects(
    q: str,
    title: bool = False,
    departmentId: int = None
) -> dict:
    """
    Search for various objects in The Met based on the inputs.
    
    Args:
        q (str): Search term (e.g., "sunflowers")
        title (bool): [Optional] Search specifically against the title field
        departmentId (int): [Optional] Filter objects by department ID
        
    Returns:
        dict: {
            "total": int,
            "objectIds": list[int]
        }
    """
    pass

def get_museum_object(objectId: int) -> dict:
    """
    Get a specific object from The Met containing all open access data about that object, including its image if available under Open Access.
    
    Args:
        objectId (int): The ID of the object to retrieve
        
    Returns:
        dict: {
            "objectId": int,
            "title": str,
            "artist": str,
            "artistBio": str,
            "department": str,
            "creditLine": str,
            "medium": str,
            "dimensions": str,
            "primaryImageUrl": str,
            "tags": list[str]
        }
    """
    pass

