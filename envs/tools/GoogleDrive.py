
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class DriveFile(BaseModel):
    """Represents a Google Drive file."""
    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    mimeType: str = Field(..., description="MIME type")
    size: str = Field(..., description="File size in bytes")
    createdTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Creation timestamp")
    modifiedTime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", description="Modification timestamp")
    parents: List[str] = Field(default=[], description="Parent folder IDs")
    description: Optional[str] = Field(default="", description="File description")
    webViewLink: Optional[str] = Field(default="", description="Web view URL")
    webContentLink: Optional[str] = Field(default="", description="Download URL")
    content: str = Field(default="", description="File content as bytes")

class Permission(BaseModel):
    """Represents a file permission."""
    id: str = Field(..., description="Permission ID")
    file_id: str = Field(..., description="File ID")
    role: str = Field(..., description="Permission role")
    type: str = Field(..., description="Grantee type")
    emailAddress: Optional[str] = Field(default="", description="Email address")
    link: Optional[str] = Field(default="", description="Shareable link")

class GoogleDriveScenario(BaseModel):
    """Main scenario model for Google Drive."""
    files: Dict[str, DriveFile] = Field(default={}, description="Files in Drive")
    permissions: Dict[str, Permission] = Field(default={}, description="File permissions")

Scenario_Schema = [DriveFile, Permission, GoogleDriveScenario]

# Section 2: Class
class GoogleDriveAPI:
    def __init__(self):
        """Initialize Google Drive API with empty state."""
        self.files: Dict[str, DriveFile] = {}
        self.permissions: Dict[str, Permission] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = GoogleDriveScenario(**scenario)
        self.files = model.files
        self.permissions = model.permissions

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "files": {fid: f.model_dump() for fid, f in self.files.items()},
            "permissions": {pid: p.model_dump() for pid, p in self.permissions.items()}
        }

    def upload_file(self, name: str, content: str, mime_type: Optional[str], parents: Optional[List[str]]) -> dict:
        """Upload a new file to Google Drive."""
        file_id = f"file_{len(self.files) + 1}"
        file = DriveFile(
            id=file_id,
            name=name,
            mimeType=mime_type or "application/octet-stream",
            size=str(len(content)),
            createdTime="2026-03-05T11:37:55",
            modifiedTime="2026-03-05T11:37:55",
            parents=parents or [],
            content=content
        )
        self.files[file_id] = file
        return {
            "id": file.id,
            "name": file.name,
            "mimeType": file.mimeType,
            "size": file.size,
            "createdTime": file.createdTime,
            "parents": file.parents
        }

    def download_file(self, file_id: str, acknowledge_abuse: bool) -> dict:
        """Download a file's content and metadata."""
        file = self.files[file_id]
        return {
            "content": file.content,
            "name": file.name,
            "mimeType": file.mimeType,
            "size": file.size
        }

    def list_files(self, page_size: int, q: Optional[str], order_by: Optional[str]) -> dict:
        """List files in Google Drive."""
        files_list = []
        for file in self.files.values():
            files_list.append({
                "id": file.id,
                "name": file.name,
                "mimeType": file.mimeType,
                "size": file.size,
                "modifiedTime": file.modifiedTime,
                "parents": file.parents
            })
        return {
            "files": files_list[:page_size],
            "nextPageToken": "",
            "incompleteSearch": False
        }

    def get_file(self, file_id: str, fields: str) -> dict:
        """Retrieve detailed metadata for a specific file."""
        file = self.files[file_id]
        return {
            "id": file.id,
            "name": file.name,
            "mimeType": file.mimeType,
            "description": file.description,
            "size": file.size,
            "createdTime": file.createdTime,
            "modifiedTime": file.modifiedTime,
            "parents": file.parents,
            "webViewLink": file.webViewLink,
            "webContentLink": file.webContentLink
        }

    def create_permission(self, file_id: str, role: str, type: str, email_address: Optional[str]) -> dict:
        """Create a sharing permission for a file."""
        perm_id = f"perm_{len(self.permissions) + 1}"
        permission = Permission(
            id=perm_id,
            file_id=file_id,
            role=role,
            type=type,
            emailAddress=email_address or "",
            link=f"https://drive.google.com/file/d/{file_id}/view" if type == "anyone" else ""
        )
        self.permissions[perm_id] = permission
        return {
            "id": permission.id,
            "role": permission.role,
            "type": permission.type,
            "emailAddress": permission.emailAddress,
            "link": permission.link
        }

# Section 3: MCP Tools
mcp = FastMCP(name="GoogleDrive")
api = GoogleDriveAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Google Drive API.

    Args:
        scenario (dict): Scenario dictionary matching GoogleDriveScenario schema.

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
    Save current Google Drive state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def upload_file(name: str, content: str, mime_type: str = None, parents: List[str] = None) -> dict:
    """
    Upload a new file to Google Drive with optional parent folder assignment.

    Args:
        name (str): The name to assign to the uploaded file in Google Drive.
        content (str): The file content as bytes to be uploaded.
        mime_type (str): [Optional] The MIME type of the file.
        parents (List[str]): [Optional] List of parent folder IDs.

    Returns:
        id (str): The unique identifier of the uploaded file in Google Drive.
        name (str): The name of the uploaded file.
        mimeType (str): The MIME type of the uploaded file.
        size (str): The size of the uploaded file in bytes.
        createdTime (str): The creation timestamp of the file in RFC 3339 format.
        parents (List[str]): List of parent folder IDs where the file is located.
    """
    try:
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")
        if not content or not isinstance(content, str):
            raise ValueError("Content must be a non-empty string")
        return api.upload_file(name, content, mime_type, parents)
    except Exception as e:
        raise e

@mcp.tool()
def download_file(file_id: str, acknowledge_abuse: bool = False) -> dict:
    """
    Download a file's content and metadata from Google Drive by its file ID.

    Args:
        file_id (str): The unique identifier of the file to download from Google Drive.
        acknowledge_abuse (bool): [Optional] Whether to acknowledge the abuse warning.

    Returns:
        content (str): The file content as bytes.
        name (str): The name of the downloaded file.
        mimeType (str): The MIME type of the downloaded file.
        size (str): The size of the downloaded file in bytes.
    """
    try:
        if not file_id or not isinstance(file_id, str):
            raise ValueError("File ID must be a non-empty string")
        if file_id not in api.files:
            raise ValueError(f"File {file_id} not found")
        return api.download_file(file_id, acknowledge_abuse)
    except Exception as e:
        raise e

@mcp.tool()
def list_files(page_size: int = 100, q: str = None, order_by: str = None) -> dict:
    """
    List files in Google Drive with optional filtering, sorting, and pagination.

    Args:
        page_size (int): [Optional] Maximum number of files to return per page.
        q (str): [Optional] Query string for filtering files.
        order_by (str): [Optional] Sort order for the file list.

    Returns:
        files (List[dict]): Array of file objects matching the query criteria.
        nextPageToken (str): Token for retrieving the next page of results.
        incompleteSearch (bool): Indicates whether the search results are incomplete.
    """
    try:
        return api.list_files(page_size, q, order_by)
    except Exception as e:
        raise e

@mcp.tool()
def get_file(file_id: str, fields: str = "*") -> dict:
    """
    Retrieve detailed metadata for a specific file in Google Drive.

    Args:
        file_id (str): The unique identifier of the file to retrieve metadata for.
        fields (str): [Optional] Comma-separated list of metadata fields to return.

    Returns:
        id (str): The unique identifier of the file in Google Drive.
        name (str): The name of the file.
        mimeType (str): The MIME type of the file.
        description (str): The user-provided description of the file.
        size (str): The size of the file in bytes.
        createdTime (str): The creation timestamp of the file in RFC 3339 format.
        modifiedTime (str): The last modification timestamp of the file in RFC 3339 format.
        parents (List[str]): List of parent folder IDs where the file is located.
        webViewLink (str): URL to view the file in the Google Drive web interface.
        webContentLink (str): Direct download URL for the file content.
    """
    try:
        if not file_id or not isinstance(file_id, str):
            raise ValueError("File ID must be a non-empty string")
        if file_id not in api.files:
            raise ValueError(f"File {file_id} not found")
        return api.get_file(file_id, fields)
    except Exception as e:
        raise e

@mcp.tool()
def create_permission(file_id: str, role: str, type: str, email_address: str = None) -> dict:
    """
    Create a sharing permission for a file in Google Drive to grant access to users, groups, domains, or anyone.

    Args:
        file_id (str): The unique identifier of the file to share.
        role (str): The permission role to grant.
        type (str): The type of grantee.
        email_address (str): [Optional] The email address of the user or group.

    Returns:
        id (str): The unique identifier of the created permission.
        role (str): The permission role that was granted.
        type (str): The type of grantee for this permission.
        emailAddress (str): The email address of the user or group that was granted permission.
        link (str): The shareable link for the file when permission type is 'anyone'.
    """
    try:
        if not file_id or not isinstance(file_id, str):
            raise ValueError("File ID must be a non-empty string")
        if file_id not in api.files:
            raise ValueError(f"File {file_id} not found")
        if not role or not isinstance(role, str):
            raise ValueError("Role must be a non-empty string")
        if not type or not isinstance(type, str):
            raise ValueError("Type must be a non-empty string")
        return api.create_permission(file_id, role, type, email_address)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
