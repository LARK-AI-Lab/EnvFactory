
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class FileItem(BaseModel):
    """Represents a file in OneDrive."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="File name")
    content: str = Field(..., description="File content as bytes")
    size: int = Field(..., ge=0, description="File size in bytes")
    content_type: str = Field(default="application/octet-stream", description="MIME type")
    parent_id: Optional[str] = Field(default=None, description="Parent folder ID")
    webUrl: str = Field(..., description="Web URL")
    downloadUrl: str = Field(..., description="Download URL")
    createdDateTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Creation timestamp")
    lastModifiedDateTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Last modified timestamp")

class FolderItem(BaseModel):
    """Represents a folder in OneDrive."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Folder name")
    parent_id: Optional[str] = Field(default=None, description="Parent folder ID")
    webUrl: str = Field(..., description="Web URL")
    createdDateTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Creation timestamp")
    lastModifiedDateTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Last modified timestamp")

class ShareLink(BaseModel):
    """Represents a sharing link."""
    id: str = Field(..., description="Permission ID")
    item_id: str = Field(..., description="Item ID")
    roles: List[str] = Field(..., description="Permission roles")
    link_type: str = Field(..., description="Link type")
    scope: str = Field(..., description="Link scope")
    webUrl: str = Field(..., description="Shareable URL")
    webHtml: Optional[str] = Field(default=None, description="HTML embed code")

class OneDriveScenario(BaseModel):
    """Main scenario model for OneDrive."""
    files: Dict[str, FileItem] = Field(default={}, description="Files storage")
    folders: Dict[str, FolderItem] = Field(default={}, description="Folders storage")
    share_links: Dict[str, ShareLink] = Field(default={}, description="Share links storage")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Current timestamp")

Scenario_Schema = [FileItem, FolderItem, ShareLink, OneDriveScenario]

# Section 2: Class
class OneDriveAPI:
    def __init__(self):
        """Initialize OneDrive API with empty state."""
        self.files: Dict[str, FileItem] = {}
        self.folders: Dict[str, FolderItem] = {}
        self.share_links: Dict[str, ShareLink] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = OneDriveScenario(**scenario)
        self.files = model.files
        self.folders = model.folders
        self.share_links = model.share_links
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "files": {fid: f.model_dump() for fid, f in self.files.items()},
            "folders": {fid: f.model_dump() for fid, f in self.folders.items()},
            "share_links": {sid: s.model_dump() for sid, s in self.share_links.items()},
            "current_time": self.current_time
        }

    def upload_file(self, name: str, content: str, parent_id: Optional[str]) -> dict:
        """Upload a file to OneDrive."""
        file_id = f"file_{len(self.files) + 1}"
        size = len(content)
        file_item = FileItem(
            id=file_id,
            name=name,
            content=content,
            size=size,
            parent_id=parent_id,
            webUrl=f"https://onedrive.live.com/?id={file_id}",
            downloadUrl=f"https://onedrive.live.com/download?id={file_id}",
            createdDateTime=self.current_time,
            lastModifiedDateTime=self.current_time
        )
        self.files[file_id] = file_item
        return {
            "id": file_id,
            "name": name,
            "size": size,
            "webUrl": file_item.webUrl,
            "downloadUrl": file_item.downloadUrl,
            "createdDateTime": self.current_time,
            "lastModifiedDateTime": self.current_time
        }

    def upload_large_file(self, name: str, content: str, parent_id: Optional[str], chunk_size: Optional[int]) -> dict:
        """Upload a large file using resumable upload."""
        file_id = f"file_{len(self.files) + 1}"
        session_id = f"session_{file_id}"
        size = len(content)
        file_item = FileItem(
            id=file_id,
            name=name,
            content=content,
            size=size,
            parent_id=parent_id,
            webUrl=f"https://onedrive.live.com/?id={file_id}",
            downloadUrl=f"https://onedrive.live.com/download?id={file_id}",
            createdDateTime=self.current_time,
            lastModifiedDateTime=self.current_time
        )
        self.files[file_id] = file_item
        return {
            "id": file_id,
            "name": name,
            "size": size,
            "webUrl": file_item.webUrl,
            "upload_session_id": session_id
        }

    def download_file(self, item_id: str) -> dict:
        """Download a file's content."""
        file_item = self.files[item_id]
        return {
            "content": file_item.content,
            "name": file_item.name,
            "size": file_item.size,
            "content_type": file_item.content_type
        }

    def list_children(self, item_id: Optional[str], top: Optional[int]) -> dict:
        """List files and folders in a directory."""
        parent_id = item_id
        children = []
        
        for fid, folder in self.folders.items():
            if folder.parent_id == parent_id:
                children.append({
                    "id": folder.id,
                    "name": folder.name,
                    "size": 0,
                    "folder": {},
                    "webUrl": folder.webUrl,
                    "createdDateTime": folder.createdDateTime,
                    "lastModifiedDateTime": folder.lastModifiedDateTime
                })
        
        for fid, file_item in self.files.items():
            if file_item.parent_id == parent_id:
                children.append({
                    "id": file_item.id,
                    "name": file_item.name,
                    "size": file_item.size,
                    "file": {},
                    "webUrl": file_item.webUrl,
                    "createdDateTime": file_item.createdDateTime,
                    "lastModifiedDateTime": file_item.lastModifiedDateTime
                })
        
        limit = top if top else 200
        return {"value": children[:limit]}

    def get_item(self, item_id: str) -> dict:
        """Retrieve metadata for a file or folder."""
        if item_id in self.files:
            file_item = self.files[item_id]
            return {
                "id": file_item.id,
                "name": file_item.name,
                "size": file_item.size,
                "webUrl": file_item.webUrl,
                "downloadUrl": file_item.downloadUrl,
                "createdDateTime": file_item.createdDateTime,
                "lastModifiedDateTime": file_item.lastModifiedDateTime,
                "parentReference": {"id": file_item.parent_id} if file_item.parent_id else {}
            }
        else:
            folder = self.folders[item_id]
            return {
                "id": folder.id,
                "name": folder.name,
                "size": 0,
                "webUrl": folder.webUrl,
                "downloadUrl": "",
                "createdDateTime": folder.createdDateTime,
                "lastModifiedDateTime": folder.lastModifiedDateTime,
                "parentReference": {"id": folder.parent_id} if folder.parent_id else {}
            }

    def create_share_link(self, item_id: str, link_type: Optional[str], scope: Optional[str]) -> dict:
        """Generate a sharing link for an item."""
        share_id = f"share_{len(self.share_links) + 1}"
        link_type = link_type if link_type else "view"
        scope = scope if scope else "anonymous"
        roles = ["read"] if link_type == "view" else ["write"]
        
        share_link = ShareLink(
            id=share_id,
            item_id=item_id,
            roles=roles,
            link_type=link_type,
            scope=scope,
            webUrl=f"https://onedrive.live.com/share/{share_id}",
            webHtml=f"<iframe src='https://onedrive.live.com/embed/{share_id}'></iframe>" if link_type == "embed" else None
        )
        self.share_links[share_id] = share_link
        
        result = {
            "id": share_id,
            "roles": roles,
            "link": {
                "type": link_type,
                "scope": scope,
                "webUrl": share_link.webUrl
            }
        }
        if share_link.webHtml:
            result["link"]["webHtml"] = share_link.webHtml
        return result

# Section 3: MCP Tools
mcp = FastMCP(name="OneDrive")
api = OneDriveAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the OneDrive API.

    Args:
        scenario (dict): Scenario dictionary matching OneDriveScenario schema.

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
    Save current OneDrive state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def upload_file(name: str, content: str, parent_id: str = None) -> dict:
    """
    Upload a file to OneDrive storage.

    Args:
        name (str): The name of the file to be uploaded, including file extension.
        content (str): The file content encoded as bytes.
        parent_id (str) [Optional]: The unique identifier of the parent folder.

    Returns:
        id (str): The unique identifier of the uploaded item.
        name (str): The name of the uploaded file.
        size (int): The size of the file in bytes.
        webUrl (str): The URL to access the file in the OneDrive web interface.
        downloadUrl (str): The direct download URL for the file content.
        createdDateTime (str): The timestamp when the file was created.
        lastModifiedDateTime (str): The timestamp when the file was last modified.
    """
    try:
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        if not content or not isinstance(content, str):
            raise ValueError("Content must be a non-empty string")
        return api.upload_file(name, content, parent_id)
    except Exception as e:
        raise e

@mcp.tool()
def upload_large_file(name: str, content: str, parent_id: str = None, chunk_size: int = None) -> dict:
    """
    Upload a large file to OneDrive using resumable upload sessions.

    Args:
        name (str): The name of the file to be uploaded, including file extension.
        content (str): The file content encoded as bytes.
        parent_id (str) [Optional]: The unique identifier of the parent folder.
        chunk_size (int) [Optional]: The size of each upload chunk in bytes.

    Returns:
        id (str): The unique identifier of the uploaded item.
        name (str): The name of the uploaded file.
        size (int): The size of the file in bytes.
        webUrl (str): The URL to access the file in the OneDrive web interface.
        upload_session_id (str): The identifier of the upload session.
    """
    try:
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        if not content or not isinstance(content, str):
            raise ValueError("Content must be a non-empty string")
        return api.upload_large_file(name, content, parent_id, chunk_size)
    except Exception as e:
        raise e

@mcp.tool()
def download_file(item_id: str) -> dict:
    """
    Download a file's content from OneDrive storage.

    Args:
        item_id (str): The unique identifier of the item in OneDrive to download.

    Returns:
        content (str): The downloaded file content as bytes.
        name (str): The name of the downloaded file.
        size (int): The size of the file in bytes.
        content_type (str): The MIME type of the file content.
    """
    try:
        if not item_id or not isinstance(item_id, str):
            raise ValueError("Item ID must be a non-empty string")
        if item_id not in api.files:
            raise ValueError(f"File {item_id} not found")
        return api.download_file(item_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_children(item_id: str = None, top: int = None) -> dict:
    """
    List all files and folders contained within a OneDrive directory.

    Args:
        item_id (str) [Optional]: The unique identifier of the folder to list.
        top (int) [Optional]: The maximum number of items to return.

    Returns:
        value (list): The list of child items (files and folders) in the directory.
        @odata.nextLink (str) [Optional]: The URL to retrieve the next page of results.
    """
    try:
        return api.list_children(item_id, top)
    except Exception as e:
        raise e

@mcp.tool()
def get_item(item_id: str) -> dict:
    """
    Retrieve metadata for a specific file or folder in OneDrive.

    Args:
        item_id (str): The unique identifier of the item in OneDrive to retrieve.

    Returns:
        id (str): The unique identifier of the item.
        name (str): The name of the item.
        size (int): The size of the file in bytes.
        webUrl (str): The URL to access the item in the OneDrive web interface.
        downloadUrl (str): The temporary direct download URL for the file content.
        createdDateTime (str): The timestamp when the item was created.
        lastModifiedDateTime (str): The timestamp when the item was last modified.
        parentReference (dict): Reference information about the parent folder.
    """
    try:
        if not item_id or not isinstance(item_id, str):
            raise ValueError("Item ID must be a non-empty string")
        if item_id not in api.files and item_id not in api.folders:
            raise ValueError(f"Item {item_id} not found")
        return api.get_item(item_id)
    except Exception as e:
        raise e

@mcp.tool()
def create_share_link(item_id: str, type: str = None, scope: str = None) -> dict:
    """
    Generate a sharing link to grant access to a OneDrive item.

    Args:
        item_id (str): The unique identifier of the item in OneDrive to share.
        type (str) [Optional]: The type of sharing link to create (view, edit, or embed).
        scope (str) [Optional]: The scope of the sharing link (anonymous or organization).

    Returns:
        id (str): The unique identifier of the sharing permission.
        roles (list): The list of permission roles granted by this sharing link.
        link (dict): The sharing link details containing type, scope, webUrl, and optionally webHtml.
    """
    try:
        if not item_id or not isinstance(item_id, str):
            raise ValueError("Item ID must be a non-empty string")
        if item_id not in api.files and item_id not in api.folders:
            raise ValueError(f"Item {item_id} not found")
        return api.create_share_link(item_id, type, scope)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
