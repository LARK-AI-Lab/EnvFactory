# Data Source: https://developer.box.com/reference/
# Server: Box
# Category: storage


def upload_file(name: str, content: bytes, parent_id: str = "0") -> dict:
    """
    Upload a file to Box.
    
    Args:
        name (str): File name
        content (bytes): File content as bytes
        parent_id (str): [Optional] Parent folder ID (default: 0 = root)
        
    Returns:
        dict: {
            "id": str,             # Unique file ID
            "name": str,
            "size": int,
            "sha1": str,           # SHA1 hash of content
            "created_at": str,     # ISO 8601 timestamp
            "modified_at": str,
            "parent": {
                "id": str,
                "name": str
            }
        }
    """
    pass


def upload_file_version(file_id: str, content: bytes) -> dict:
    """
    Upload a new version of an existing file.
    
    Args:
        file_id (str): Existing Box file ID
        content (bytes): New file content as bytes
        
    Returns:
        dict: {
            "id": str,
            "name": str,
            "size": int,
            "sha1": str,
            "version_number": str,
            "modified_at": str
        }
    """
    pass


def download_file(file_id: str, version_id: str = None) -> dict:
    """
    Download a file from Box.
    
    Args:
        file_id (str): Box file ID
        version_id (str): [Optional] Specific version ID to download
        
    Returns:
        dict: {
            "content": bytes,      # File content as bytes
            "name": str,
            "content_type": str,   # MIME type
            "size": int
        }
    """
    pass


def list_folder_items(folder_id: str = "0", limit: int = 100, 
                      offset: int = 0) -> dict:
    """
    List items in a Box folder.
    
    Args:
        folder_id (str): [Optional] Folder ID (default: 0 = root)
        limit (int): [Optional] Items per page (default: 100, max: 1000)
        offset (int): [Optional] Pagination offset (default: 0)
        
    Returns:
        dict: {
            "total_count": int,    # Total items in folder
            "entries": [{
                "type": str,       # file | folder | web_link
                "id": str,
                "name": str,
                "size": int,       # For files
                "modified_at": str
            }],
            "offset": int,
            "limit": int,
            "order": list
        }
    """
    pass


def get_item_info(item_id: str, item_type: str = "file") -> dict:
    """
    Get information about a file or folder.
    
    Args:
        item_id (str): Box item ID
        item_type (str): [Optional] Type: file | folder (default: file)
        
    Returns:
        dict: {
            "id": str,
            "type": str,
            "name": str,
            "size": int,
            "created_at": str,
            "modified_at": str,
            "shared_link": dict,   # If shared
            "parent": dict,
            "path_collection": dict
        }
    """
    pass


def create_shared_link(item_id: str, access: str = "open", 
                       password: str = None, expires_at: str = None) -> dict:
    """
    Create or update a shared link for an item.
    
    Args:
        item_id (str): Box item ID
        access (str): [Optional] Access level: open | company | collaborators
        password (str): [Optional] Password protection
        expires_at (str): [Optional] Expiration timestamp (ISO 8601)
        
    Returns:
        dict: {
            "url": str,            # Shareable URL
            "download_url": str,   # Direct download URL
            "vanity_url": str,     # Custom URL if configured
            "access": str,
            "effective_access": str,
            "unshared_at": str     # Expiration time
        }
    """
    pass
