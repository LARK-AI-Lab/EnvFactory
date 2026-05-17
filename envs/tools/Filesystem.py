from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import base64
import glob
import difflib

# Section 1: Schema
class FileEntry(BaseModel):
    """Represents a file or directory entry."""
    name: str = Field(..., description="Name of the file or directory")
    type: str = Field(..., description="Type: 'file' or 'directory'")
    size: int = Field(..., ge=0, description="Size in bytes")

class FileInfo(BaseModel):
    """Detailed file metadata."""
    path: str = Field(..., description="Full path to file/directory")
    type: str = Field(..., description="Type: 'file' or 'directory'")
    size: int = Field(..., ge=0, description="Size in bytes")
    created_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Creation timestamp ISO 8601")
    modified_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Modification timestamp ISO 8601")
    access_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Access timestamp ISO 8601")
    permissions: str = Field(..., description="File permissions in symbolic notation")

class FileResult(BaseModel):
    """Result for individual file read operation."""
    path: str = Field(..., description="File path")
    content: Optional[str] = Field(default=None, description="File content if successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")

class TreeNode(BaseModel):
    """Node in directory tree structure."""
    name: str = Field(..., description="Name of file/directory")
    type: str = Field(..., description="Type: 'file' or 'directory'")
    children: Optional[List['TreeNode']] = Field(default=None, description="Nested entries for directories")

class FilesystemScenario(BaseModel):
    """Main scenario model for filesystem operations."""
    files: Dict[str, str] = Field(default={}, description="File contents indexed by absolute path")
    directories: Dict[str, List[str]] = Field(default={}, description="Directory contents indexed by absolute path, value is list of child names")
    file_metadata: Dict[str, FileInfo] = Field(default={}, description="File metadata indexed by absolute path")
    allowed_extensions: List[str] = Field(default=[".txt", ".md", ".py", ".json", ".csv", ".xml", ".html", ".css", ".js", ".ts"], description="Allowed file extensions for text operations")
    max_file_size: int = Field(default=10485760, ge=0, description="Maximum file size in bytes (10MB)")
    binary_extensions: List[str] = Field(default=[".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".mp3", ".wav", ".mp4", ".avi", ".pdf", ".zip"], description="Binary file extensions for media operations")
    exclude_patterns_default: List[str] = Field(default=["*.pyc", "__pycache__", ".git", ".DS_Store", "node_modules"], description="Default exclusion patterns")
    mime_types_map: Dict[str, str] = Field(default={
        ".txt": "text/plain", ".md": "text/markdown", ".py": "text/x-python", ".json": "application/json",
        ".csv": "text/csv", ".xml": "application/xml", ".html": "text/html", ".css": "text/css",
        ".js": "application/javascript", ".ts": "application/typescript", ".png": "image/png",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".bmp": "image/bmp",
        ".ico": "image/x-icon", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".mp4": "video/mp4",
        ".avi": "video/x-msvideo", ".pdf": "application/pdf", ".zip": "application/zip"
    }, description="MIME type mapping by file extension")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [FileEntry, FileInfo, FileResult, TreeNode, FilesystemScenario]

# Section 2: Class
class FilesystemAPI:
    def __init__(self):
        """Initialize filesystem API with default settings."""
        self.files: Dict[str, str] = {}
        self.directories: Dict[str, List[str]] = {}
        self.file_metadata: Dict[str, FileInfo] = {}
        self.allowed_extensions: List[str] = []
        self.max_file_size: int = 0
        self.binary_extensions: List[str] = []
        self.exclude_patterns_default: List[str] = []
        self.mime_types_map: Dict[str, str] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario configuration into the API instance."""
        model = FilesystemScenario(**scenario)
        self.files = model.files
        self.directories = model.directories
        self.file_metadata = {}
        for k, v in model.file_metadata.items():
            if isinstance(v, dict):
                self.file_metadata[k] = FileInfo(**v)
            else:
                self.file_metadata[k] = v
        self.allowed_extensions = model.allowed_extensions
        self.max_file_size = model.max_file_size
        self.binary_extensions = model.binary_extensions
        self.exclude_patterns_default = model.exclude_patterns_default
        self.mime_types_map = model.mime_types_map
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current configuration as scenario dictionary."""
        return {
            "files": self.files,
            "directories": self.directories,
            "file_metadata": {k: v.model_dump() if hasattr(v, 'model_dump') else v for k, v in self.file_metadata.items()},
            "allowed_extensions": self.allowed_extensions,
            "max_file_size": self.max_file_size,
            "binary_extensions": self.binary_extensions,
            "exclude_patterns_default": self.exclude_patterns_default,
            "mime_types_map": self.mime_types_map,
            "current_time": self.current_time
        }

    def _normalize_path(self, path: str) -> str:
        """Normalize path to use forward slashes."""
        return path.replace("\\", "/")

    def _get_parent_path(self, path: str) -> str:
        """Get parent directory path."""
        normalized = self._normalize_path(path)
        if normalized == "/":
            return "/"
        parts = normalized.rstrip("/").split("/")
        if len(parts) == 1:
            return "/"
        return "/".join(parts[:-1]) or "/"

    def _get_name(self, path: str) -> str:
        """Get file/directory name from path."""
        normalized = self._normalize_path(path)
        if normalized == "/":
            return "/"
        return normalized.rstrip("/").split("/")[-1]

    def _is_directory(self, path: str) -> bool:
        """Check if path is a directory."""
        return path in self.directories

    def _is_file(self, path: str) -> bool:
        """Check if path is a file."""
        return path in self.files

    def _ensure_directory_exists(self, path: str) -> None:
        """Ensure directory and all parent directories exist."""
        if path == "/":
            if "/" not in self.directories:
                self.directories["/"] = []
            return

        parent = self._get_parent_path(path)
        self._ensure_directory_exists(parent)

        if path not in self.directories:
            self.directories[path] = []
            parent_children = self.directories.get(parent, [])
            name = self._get_name(path)
            if name not in parent_children:
                parent_children.append(name)
                self.directories[parent] = parent_children

    def read_text_file(self, path: str, head: Optional[int] = None, tail: Optional[int] = None) -> dict:
        """Read text file content with optional line filtering."""
        normalized_path = self._normalize_path(path)
        if normalized_path not in self.files:
            return {"file_content": ""}

        content = self.files[normalized_path]
        lines = content.split('\n')

        if head is not None:
            lines = lines[:head]
        elif tail is not None:
            lines = lines[-tail:]

        return {"file_content": '\n'.join(lines)}

    def read_media_file(self, path: str) -> dict:
        """Read binary media file and return base64 encoded data."""
        normalized_path = self._normalize_path(path)
        if normalized_path not in self.files:
            return {"data": "", "mime_type": "application/octet-stream"}

        content = self.files[normalized_path]
        # For binary files stored as strings, encode to base64
        data = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        mime_type = self._get_mime_type(normalized_path)
        return {"data": data, "mime_type": mime_type}

    def read_multiple_files(self, paths: List[str]) -> dict:
        """Read multiple files and return results with errors."""
        results = []
        for path in paths:
            normalized_path = self._normalize_path(path)
            if normalized_path not in self.files:
                results.append({"path": path, "content": None, "error": f"File not found: {path}"})
                continue

            try:
                if self._is_binary_file(normalized_path):
                    result = self.read_media_file(normalized_path)
                    content = f"[Binary file: {result['mime_type']}, {len(result['data'])} bytes]"
                else:
                    result = self.read_text_file(normalized_path)
                    content = result['file_content']
                results.append({"path": path, "content": content, "error": None})
            except Exception as e:
                results.append({"path": path, "content": None, "error": str(e)})
        return {"results": results}

    def write_file(self, path: str, content: str) -> dict:
        """Create or overwrite file with specified content."""
        normalized_path = self._normalize_path(path)
        parent = self._get_parent_path(normalized_path)
        self._ensure_directory_exists(parent)

        self.files[normalized_path] = content
        name = self._get_name(normalized_path)
        parent_children = self.directories.get(parent, [])
        if name not in parent_children:
            parent_children.append(name)
            self.directories[parent] = parent_children

        # Update metadata
        now = self.current_time
        self.file_metadata[normalized_path] = FileInfo(
            path=normalized_path,
            type="file",
            size=len(content.encode('utf-8')),
            created_time=now,
            modified_time=now,
            access_time=now,
            permissions="rw-r--r--"
        )

        return {"path": path, "success": "File written successfully"}

    def edit_file(self, path: str, oldText: Optional[str] = None, newText: Optional[str] = None, dryRun: bool = False) -> dict:
        """Edit file with pattern matching and optional dry run."""
        normalized_path = self._normalize_path(path)
        if normalized_path not in self.files:
            return {"diff": "", "matches": [], "applied": False}

        content = self.files[normalized_path]
        original_content = content
        matches = []

        if oldText is not None and newText is not None:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if oldText in line:
                    matches.append({"line_number": i, "context": line.strip()})

            if not dryRun:
                content = content.replace(oldText, newText)

        if not dryRun and content != original_content:
            self.files[normalized_path] = content
            if normalized_path in self.file_metadata:
                self.file_metadata[normalized_path].modified_time = self.current_time
                self.file_metadata[normalized_path].size = len(content.encode('utf-8'))

        # difflib is now imported at the top of the file
        diff = '\n'.join(difflib.unified_diff(
            original_content.split('\n'),
            content.split('\n'),
            fromfile=path,
            tofile=path,
            lineterm=''
        ))

        return {"diff": diff, "matches": matches, "applied": not dryRun and content != original_content}

    def create_directory(self, path: str) -> dict:
        """Create directory or ensure it exists."""
        normalized_path = self._normalize_path(path)
        created = normalized_path not in self.directories

        self._ensure_directory_exists(normalized_path)

        # Update metadata
        now = self.current_time
        self.file_metadata[normalized_path] = FileInfo(
            path=normalized_path,
            type="directory",
            size=0,
            created_time=now,
            modified_time=now,
            access_time=now,
            permissions="rwxr-xr-x"
        )

        return {"path": path, "created": created}

    def list_directory(self, path: str) -> dict:
        """List directory contents with metadata."""
        normalized_path = self._normalize_path(path)
        entries = []

        if normalized_path not in self.directories:
            return {"entries": entries}

        for name in self.directories[normalized_path]:
            child_path = normalized_path.rstrip("/") + "/" + name if normalized_path != "/" else "/" + name
            if child_path in self.directories:
                entry_type = "DIR"
                size = 0
            elif child_path in self.files:
                entry_type = "FILE"
                size = len(self.files[child_path].encode('utf-8'))
            else:
                continue

            entries.append({
                "name": name,
                "type": entry_type,
                "size": size
            })

        return {"entries": entries}

    def move_file(self, source: str, destination: str) -> dict:
        """Move or rename file/directory."""
        normalized_source = self._normalize_path(source)
        normalized_dest = self._normalize_path(destination)

        # Ensure destination parent directory exists
        dest_parent = self._get_parent_path(normalized_dest)
        self._ensure_directory_exists(dest_parent)

        # Move file
        if normalized_source in self.files:
            self.files[normalized_dest] = self.files.pop(normalized_source)
            if normalized_source in self.file_metadata:
                metadata = self.file_metadata.pop(normalized_source)
                metadata.path = normalized_dest
                self.file_metadata[normalized_dest] = metadata

            # Update parent directories
            source_parent = self._get_parent_path(normalized_source)
            source_name = self._get_name(normalized_source)
            if source_parent in self.directories and source_name in self.directories[source_parent]:
                self.directories[source_parent].remove(source_name)

            dest_name = self._get_name(normalized_dest)
            dest_parent_children = self.directories.get(dest_parent, [])
            if dest_name not in dest_parent_children:
                dest_parent_children.append(dest_name)
                self.directories[dest_parent] = dest_parent_children

        # Move directory
        elif normalized_source in self.directories:
            children = self.directories.pop(normalized_source)
            self.directories[normalized_dest] = children

            # Update all child paths
            for child_name in children:
                old_child_path = normalized_source.rstrip("/") + "/" + child_name if normalized_source != "/" else "/" + child_name
                new_child_path = normalized_dest.rstrip("/") + "/" + child_name if normalized_dest != "/" else "/" + child_name

                if old_child_path in self.files:
                    self.files[new_child_path] = self.files.pop(old_child_path)
                elif old_child_path in self.directories:
                    self.directories[new_child_path] = self.directories.pop(old_child_path)

            # Update parent directories
            source_parent = self._get_parent_path(normalized_source)
            source_name = self._get_name(normalized_source)
            if source_parent in self.directories and source_name in self.directories[source_parent]:
                self.directories[source_parent].remove(source_name)

            dest_name = self._get_name(normalized_dest)
            dest_parent_children = self.directories.get(dest_parent, [])
            if dest_name not in dest_parent_children:
                dest_parent_children.append(dest_name)
                self.directories[dest_parent] = dest_parent_children
        else:
            return {"source": source, "destination": destination, "success": False}

        return {"source": source, "destination": destination, "success": True}

    def search_files(self, path: str, pattern: str, excludePatterns: Optional[List[str]] = None) -> dict:
        """Search for files matching glob pattern with exclusions."""
        if excludePatterns is None:
            excludePatterns = self.exclude_patterns_default

        normalized_path = self._normalize_path(path)
        matches = []

        def search_recursive(current_path: str, base_path: str) -> None:
            if current_path not in self.directories:
                return

            for name in self.directories[current_path]:
                child_path = current_path.rstrip("/") + "/" + name if current_path != "/" else "/" + name
                rel_path = child_path[len(base_path):].lstrip("/")

                if glob.fnmatch.fnmatch(rel_path, pattern):
                    excluded = False
                    for exclude_pattern in excludePatterns:
                        if glob.fnmatch.fnmatch(rel_path, exclude_pattern):
                            excluded = True
                            break

                    if not excluded:
                        matches.append(child_path)

                if child_path in self.directories:
                    search_recursive(child_path, base_path)

        search_recursive(normalized_path, normalized_path)
        return {"matches": matches}

    def directory_tree(self, path: str, excludePatterns: Optional[List[str]] = None) -> dict:
        """Generate recursive directory tree structure."""
        if excludePatterns is None:
            excludePatterns = self.exclude_patterns_default

        normalized_path = self._normalize_path(path)

        def build_tree(current_path: str, base_path: str) -> List[dict]:
            tree = []
            if current_path not in self.directories:
                return tree

            for name in sorted(self.directories[current_path]):
                child_path = current_path.rstrip("/") + "/" + name if current_path != "/" else "/" + name
                rel_path = child_path[len(base_path):].lstrip("/")

                excluded = False
                for pattern in excludePatterns:
                    if glob.fnmatch.fnmatch(rel_path, pattern):
                        excluded = True
                        break

                if excluded:
                    continue

                if child_path in self.directories:
                    node = {
                        "name": name,
                        "type": "directory",
                        "children": build_tree(child_path, base_path)
                    }
                elif child_path in self.files:
                    node = {
                        "name": name,
                        "type": "file"
                    }
                else:
                    continue

                tree.append(node)

            return tree

        return {"tree": build_tree(normalized_path, normalized_path)}

    def get_file_info(self, path: str) -> dict:
        """Get detailed file/directory metadata."""
        normalized_path = self._normalize_path(path)

        if normalized_path in self.file_metadata:
            metadata = self.file_metadata[normalized_path]
            return {
                "path": metadata.path,
                "type": metadata.type,
                "size": metadata.size,
                "created_time": metadata.created_time,
                "modified_time": metadata.modified_time,
                "access_time": metadata.access_time,
                "permissions": metadata.permissions
            }

        # Create default metadata if not exists
        now = self.current_time
        if normalized_path in self.directories:
            file_type = "directory"
            size = 0
            permissions = "rwxr-xr-x"
        elif normalized_path in self.files:
            file_type = "file"
            size = len(self.files[normalized_path].encode('utf-8'))
            permissions = "rw-r--r--"
        else:
            return {
                "path": path,
                "type": "file",
                "size": 0,
                "created_time": now,
                "modified_time": now,
                "access_time": now,
                "permissions": "rw-r--r--"
            }

        metadata = FileInfo(
            path=normalized_path,
            type=file_type,
            size=size,
            created_time=now,
            modified_time=now,
            access_time=now,
            permissions=permissions
        )
        self.file_metadata[normalized_path] = metadata

        return {
            "path": metadata.path,
            "type": metadata.type,
            "size": metadata.size,
            "created_time": metadata.created_time,
            "modified_time": metadata.modified_time,
            "access_time": metadata.access_time,
            "permissions": metadata.permissions
        }

    def _get_mime_type(self, path: str) -> str:
        """Get MIME type for file path."""
        ext = "." + path.split(".")[-1] if "." in path else ""
        return self.mime_types_map.get(ext, "application/octet-stream")

    def _is_binary_file(self, path: str) -> bool:
        """Check if file should be treated as binary."""
        ext = "." + path.split(".")[-1] if "." in path else ""
        return ext in self.binary_extensions

# Section 3: MCP Tools
mcp = FastMCP(name="FilesystemAPI")
api = FilesystemAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load filesystem configuration scenario.

    Args:
        scenario (dict): Configuration dictionary matching FilesystemScenario schema.

    Returns:
        success_message (str): Success confirmation.
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
    """Save current filesystem configuration.

    Returns:
        scenario (dict): Current configuration dictionary.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def read_text_file(path: str, head: Optional[int] = None, tail: Optional[int] = None) -> dict:
    """Read text file with optional line filtering.

    Args:
        path (str): File path to read.
        head (int): [Optional] Number of lines from start.
        tail (int): [Optional] Number of lines from end.

    Returns:
        file_content (str): File contents as text.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        if head is not None and (not isinstance(head, int) or head < 0):
            raise ValueError("Head must be non-negative integer")
        if tail is not None and (not isinstance(tail, int) or tail < 0):
            raise ValueError("Tail must be non-negative integer")
        return api.read_text_file(path, head, tail)
    except Exception as e:
        raise e

@mcp.tool()
def read_media_file(path: str) -> dict:
    """Read binary media file as base64.

    Args:
        path (str): Media file path.

    Returns:
        data (str): Base64 encoded content.
        mime_type (str): MIME type of file.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        return api.read_media_file(path)
    except Exception as e:
        raise e

@mcp.tool()
def read_multiple_files(paths: List[str]) -> dict:
    """Read multiple files simultaneously.

    Args:
        paths (list): List of file paths to read.

    Returns:
        results (list): List of results with content or error for each file.
    """
    try:
        if not isinstance(paths, list):
            raise ValueError("Paths must be a list")
        return api.read_multiple_files(paths)
    except Exception as e:
        raise e

@mcp.tool()
def write_file(path: str, content: str) -> dict:
    """Write content to file.

    Args:
        path (str): Destination file path.
        content (str): Text content to write.

    Returns:
        path (str): File path where written.
        success (str): Success message.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        if content is None:
            raise ValueError("Content cannot be None")
        return api.write_file(path, content)
    except Exception as e:
        raise e

@mcp.tool()
def edit_file(path: str, oldText: Optional[str] = None, newText: Optional[str] = None, dryRun: bool = False) -> dict:
    """Edit file with pattern matching.

    Args:
        path (str): File path to edit.
        oldText (str): [Optional] Text pattern to search.
        newText (str): [Optional] Replacement text.
        dryRun (bool): [Optional] Preview changes without applying.

    Returns:
        diff (str): Unified diff of changes.
        matches (list): List of matches found.
        applied (bool): Whether changes were applied.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        return api.edit_file(path, oldText, newText, dryRun)
    except Exception as e:
        raise e

@mcp.tool()
def create_directory(path: str) -> dict:
    """Create directory.

    Args:
        path (str): Directory path to create.

    Returns:
        path (str): Created directory path.
        created (bool): Whether new directory was created.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        return api.create_directory(path)
    except Exception as e:
        raise e

@mcp.tool()
def list_directory(path: str) -> dict:
    """List directory contents.

    Args:
        path (str): Directory path to list.

    Returns:
        entries (list): List of directory entries with metadata.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        return api.list_directory(path)
    except Exception as e:
        raise e

@mcp.tool()
def move_file(source: str, destination: str) -> dict:
    """Move or rename file/directory.

    Args:
        source (str): Source path.
        destination (str): Destination path.

    Returns:
        source (str): Original path.
        destination (str): New path.
        success (bool): Operation success status.
    """
    try:
        if not source or not isinstance(source, str):
            raise ValueError("Source must be a non-empty string")
        if not destination or not isinstance(destination, str):
            raise ValueError("Destination must be a non-empty string")
        return api.move_file(source, destination)
    except Exception as e:
        raise e

@mcp.tool()
def search_files(path: str, pattern: str, excludePatterns: Optional[List[str]] = None) -> dict:
    """Search files with glob pattern.

    Args:
        path (str): Search starting directory.
        pattern (str): Glob pattern to match.
        excludePatterns (list): [Optional] Patterns to exclude.

    Returns:
        matches (list): List of matching file paths.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        if not pattern or not isinstance(pattern, str):
            raise ValueError("Pattern must be a non-empty string")
        return api.search_files(path, pattern, excludePatterns)
    except Exception as e:
        raise e

@mcp.tool()
def directory_tree(path: str, excludePatterns: Optional[List[str]] = None) -> dict:
    """Generate directory tree structure.

    Args:
        path (str): Root directory path.
        excludePatterns (list): [Optional] Patterns to exclude.

    Returns:
        tree (list): Hierarchical tree structure.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        return api.directory_tree(path, excludePatterns)
    except Exception as e:
        raise e

@mcp.tool()
def get_file_info(path: str) -> dict:
    """Get detailed file metadata.

    Args:
        path (str): File/directory path.

    Returns:
        path (str): Inspected path.
        type (str): Entry type.
        size (int): Size in bytes.
        created_time (str): Creation timestamp.
        modified_time (str): Modification timestamp.
        access_time (str): Access timestamp.
        permissions (str): File permissions.
    """
    try:
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        return api.get_file_info(path)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
