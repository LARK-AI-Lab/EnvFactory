# Data Source: https://docs.microsoft.com/en-us/onedrive/developer/rest-api/
# Server: OneDrive
# Category: storage


def upload_file(name: str, content: bytes, parent_id: str = "root") -> dict:
    """
    Upload a file to OneDrive.
    
    Args:
        name (str): File name
        content (bytes): File content as bytes
        parent_id (str): [Optional] Parent folder ID (default: root)
        
    Returns:
        dict: {
            "id": str,             # Unique item ID
            "name": str,
            "size": int,
            "webUrl": str,         # OneDrive web URL
            "downloadUrl": str,    # Direct download URL
            "createdDateTime": str,# ISO 8601 timestamp
            "lastModifiedDateTime": str
        }
    """
    pass


def upload_large_file(name: str, content: bytes, parent_id: str = "root",
                      chunk_size: int = 5242880) -> dict:
    """
    Upload a large file using resumable upload sessions.
    
    Args:
        name (str): File name
        content (bytes): File content as bytes
        parent_id (str): [Optional] Parent folder ID (default: root)
        chunk_size (int): [Optional] Upload chunk size in bytes (default: 5MB)
        
    Returns:
        dict: {
            "id": str,
            "name": str,
            "size": int,
            "webUrl": str,
            "upload_session_id": str
        }
    """
    pass


def download_file(item_id: str) -> dict:
    """
    Download a file from OneDrive.
    
    Args:
        item_id (str): OneDrive item ID
        
    Returns:
        dict: {
            "content": bytes,      # File content as bytes
            "name": str,
            "size": int,
            "content_type": str    # MIME type
        }
    """
    pass


def list_children(item_id: str = "root", top: int = 200) -> dict:
    """
    List files and folders in a OneDrive directory.
    
    Args:
        item_id (str): [Optional] Folder ID (default: root)
        top (int): [Optional] Max items to return (default: 200)
        
    Returns:
        dict: {
            "value": [{
                "id": str,
                "name": str,
                "size": int,
                "folder": dict,    # Present if item is folder
                "file": dict,      # Present if item is file
                "webUrl": str,
                "createdDateTime": str,
                "lastModifiedDateTime": str
            }],
            "@odata.nextLink": str  # For pagination
        }
    """
    pass


def get_item(item_id: str) -> dict:
    """
    Get metadata for a file or folder.
    
    Args:
        item_id (str): OneDrive item ID
        
    Returns:
        dict: {
            "id": str,
            "name": str,
            "size": int,
            "webUrl": str,
            "downloadUrl": str,    # Temporary direct download URL
            "createdDateTime": str,
            "lastModifiedDateTime": str,
            "parentReference": dict
        }
    """
    pass


def create_share_link(item_id: str, type: str = "view", 
                      scope: str = "anonymous") -> dict:
    """
    Create a sharing link for an item.
    
    Args:
        item_id (str): OneDrive item ID
        type (str): [Optional] Link type: view | edit | embed (default: view)
        scope (str): [Optional] Scope: anonymous | organization (default: anonymous)
        
    Returns:
        dict: {
            "id": str,
            "roles": list,
            "link": {
                "type": str,
                "scope": str,
                "webUrl": str,     # Share URL
                "webHtml": str     # Embed HTML (if type=embed)
            }
        }
    """
    pass
