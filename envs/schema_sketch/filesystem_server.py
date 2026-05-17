# Server: Filesystem

def read_text_file(path: str, head: int = None, tail: int = None) -> str:
    """
    Read complete contents of a file as text.
    
    Args:
        path (str): File path to read
        head (int): [Optional] First N lines
        tail (int): [Optional] Last N lines
        
    Returns:
        str: File contents as UTF-8 text
    """
    pass

def read_media_file(path: str) -> dict:
    """
    Read an image or audio file.
    
    Args:
        path (str): File path to read
        
    Returns:
        dict: {
            "data": str (base64),
            "mime_type": str
        }
    """
    pass

def read_multiple_files(paths: list[str]) -> dict:
    """
    Read multiple files simultaneously.
    
    Args:
        paths (list[str]): List of file paths to read
        
    Returns:
        dict: {
            "results": list of dicts with path, content (or error)
        }
    """
    pass

def write_file(path: str, content: str) -> dict:
    """
    Create new file or overwrite existing.
    
    Args:
        path (str): File location
        content (str): File content
        
    Returns:
        dict: {
            "path": str,
            "success": str
        }
    """
    pass

def edit_file(
    path: str,
    oldText: str = None,
    newText: str = None,
    dryRun: bool = False
) -> dict:
    """
    Make selective edits using advanced pattern matching and formatting.
    
    Args:
        path (str): File to edit
        oldText (str): [Optional] Text to search for (can be substring)
        newText (str): [Optional] Text to replace with
        dryRun (bool): [Optional] Preview changes without applying (default False)
        
    Returns:
        dict: {
            "diff": str,
            "matches": list, including line number and context
            "applied": bool
        }
    """
    pass

def create_directory(path: str) -> dict:
    """
    Create new directory or ensure it exists.
    
    Args:
        path (str): Directory path to create
        
    Returns:
        dict: {
            "path": str,
            "created": bool
        }
    """
    pass

def list_directory(path: str) -> list:
    """
    List directory contents with [FILE] or [DIR] prefixes.
    
    Args:
        path (str): Directory path to list
        
    Returns:
        list: Each entry contains {
            "name": str,
            "type": str ("FILE" or "DIR")
            "size": int
        }
    """
    pass

def move_file(source: str, destination: str) -> dict:
    """
    Move or rename files and directories.
    
    Args:
        source (str): Source file or directory path
        destination (str): Destination file or directory path
        
    Returns:
        dict: {
            "source": str,
            "destination": str,
            "success": bool
        }
    """
    pass

def search_files(
    path: str,
    pattern: str,
    excludePatterns: list[str] = None
) -> list:
    """
    Recursively search for files/directories that match or do not match patterns.
    
    Args:
        path (str): Starting directory
        pattern (str): Search pattern (glob-style)
        excludePatterns (list[str]): [Optional] Exclude any patterns (glob formats)
        
    Returns:
        list: Full paths to matches
    """
    pass

def directory_tree(
    path: str,
    excludePatterns: list[str] = None
) -> list:
    """
    Get recursive JSON tree structure of directory contents.
    
    Args:
        path (str): Starting directory
        excludePatterns (list[str]): [Optional] Exclude any patterns (glob formats)
        
    Returns:
        list: Each entry contains {
            "name": str,
            "type": str ("file" or "directory"),
            "children": list (present only for directories)
        }
    """
    pass

def get_file_info(path: str) -> dict:
    """
    Get detailed file/directory metadata.
    
    Args:
        path (str): File or directory path
        
    Returns:
        dict: {
            "path": str,
            "type": str ("file" or "directory"),
            "size": int,
            "created_time": str,
            "modified_time": str,
            "access_time": str,
            "permissions": str
        }
    """
    pass

