# Data Source: https://developers.google.com/drive/api/v3/reference
# Server: GoogleDrive
# Category: storage


def upload_file(name: str, content: bytes, mime_type: str = None,
                parents: list = None) -> dict:
    """
    Upload a file to Google Drive.
    
    Args:
        name (str): File name
        content (bytes): File content as bytes
        mime_type (str): [Optional] MIME type (auto-detected if not provided)
        parents (list): [Optional] List of parent folder IDs
        
    Returns:
        dict: {
            "id": str,             # Unique file ID
            "name": str,
            "mimeType": str,
            "size": str,           # File size as string
            "createdTime": str,    # RFC 3339 timestamp
            "parents": list        # Parent folder IDs
        }
    """
    pass


def download_file(file_id: str, acknowledge_abuse: bool = False) -> dict:
    """
    Download a file from Google Drive.
    
    Args:
        file_id (str): Google Drive file ID
        acknowledge_abuse (bool): [Optional] Acknowledge abuse warning (default: False)
        
    Returns:
        dict: {
            "content": bytes,      # File content as bytes
            "name": str,
            "mimeType": str,
            "size": str
        }
    """
    pass


def list_files(page_size: int = 100, q: str = None, 
               order_by: str = "modifiedTime desc") -> dict:
    """
    List files in Google Drive with optional filtering.
    
    Args:
        page_size (int): [Optional] Max files per page (default: 100)
        q (str): [Optional] Query string for filtering (e.g., "mimeType='image/jpeg'")
        order_by (str): [Optional] Sort order (default: modifiedTime desc)
        
    Returns:
        dict: {
            "files": [{
                "id": str,
                "name": str,
                "mimeType": str,
                "size": str,
                "modifiedTime": str,
                "parents": list
            }],
            "nextPageToken": str,  # For pagination
            "incompleteSearch": bool
        }
    """
    pass


def get_file(file_id: str, fields: str = "*") -> dict:
    """
    Get metadata for a specific file.
    
    Args:
        file_id (str): Google Drive file ID
        fields (str): [Optional] Fields to return (default: all)
        
    Returns:
        dict: {
            "id": str,
            "name": str,
            "mimeType": str,
            "description": str,
            "size": str,
            "createdTime": str,
            "modifiedTime": str,
            "parents": list,
            "webViewLink": str,    # Link to view in Drive
            "webContentLink": str  # Direct download link
        }
    """
    pass


def create_permission(file_id: str, role: str, type: str, 
                      email_address: str = None) -> dict:
    """
    Create a permission for a file (share).
    
    Args:
        file_id (str): Google Drive file ID
        role (str): Permission role: owner | organizer | fileOrganizer | 
                   writer | commenter | reader
        type (str): Permission type: user | group | domain | anyone
        email_address (str): [Optional] Email for user/group type
        
    Returns:
        dict: {
            "id": str,             # Permission ID
            "role": str,
            "type": str,
            "emailAddress": str,
            "link": str            # Share link if type is anyone
        }
    """
    pass
