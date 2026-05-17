# Data Source: https://www.dropbox.com/developers/documentation/http/documentation
# Server: Dropbox
# Category: storage


def upload_file(path: str, content: bytes, mode: str = "add", autorename: bool = False) -> dict:
    """
    Upload a file to Dropbox.
    
    Args:
        path (str): Destination path in Dropbox (e.g., "/folder/file.txt")
        content (bytes): File content as bytes
        mode (str): [Optional] Write mode: add | overwrite | update (default: add)
        autorename (bool): [Optional] Auto-rename if file exists (default: False)
        
    Returns:
        dict: {
            "name": str,           # File name
            "id": str,             # Unique file ID
            "path_lower": str,     # Lowercase full path
            "content_hash": str,   # Content hash for verification
            "size": int            # File size in bytes
        }
    """
    pass


def download_file(path: str = None, file_id: str = None) -> dict:
    """
    Download a file from Dropbox.
    
    Args:
        path (str): [Optional] File path in Dropbox
        file_id (str): [Optional] Unique file ID (alternative to path)
        
    Returns:
        dict: {
            "content": bytes,      # File content as bytes
            "name": str,           # File name
            "content_type": str,   # MIME type
            "size": int            # File size in bytes
        }
    """
    pass


def list_folder(path: str = "", recursive: bool = False, 
                limit: int = 2000) -> dict:
    """
    List files and folders in a Dropbox directory.
    
    Args:
        path (str): [Optional] Folder path (default: root "")
        recursive (bool): [Optional] List recursively (default: False)
        limit (int): [Optional] Max entries to return (default: 2000)
        
    Returns:
        dict: {
            "entries": [{
                "tag": str,        # file | folder
                "name": str,
                "id": str,
                "path_lower": str,
                "size": int,       # For files only
                "modified": str    # ISO 8601 timestamp
            }],
            "cursor": str,         # For pagination
            "has_more": bool       # True if more entries available
        }
    """
    pass


def get_metadata(path: str = None, file_id: str = None) -> dict:
    """
    Get metadata for a file or folder.
    
    Args:
        path (str): [Optional] Path to file/folder
        file_id (str): [Optional] File ID (alternative to path)
        
    Returns:
        dict: {
            "tag": str,            # file | folder
            "name": str,
            "id": str,
            "path_lower": str,
            "size": int,           # For files
            "modified": str,       # ISO 8601 timestamp
            "content_hash": str    # For files
        }
    """
    pass


def create_shared_link(path: str, expires: str = None, 
                       allow_download: bool = True) -> dict:
    """
    Create a shared link for a file or folder.
    
    Args:
        path (str): Path to file/folder
        expires (str): [Optional] Expiration time (ISO 8601)
        allow_download (bool): [Optional] Allow downloads (default: True)
        
    Returns:
        dict: {
            "url": str,            # Shared link URL
            "expires": str,        # ISO 8601 timestamp
            "visibility": str      # public | team_only | password
        }
    """
    pass
