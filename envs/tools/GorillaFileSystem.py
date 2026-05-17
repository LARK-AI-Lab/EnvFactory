from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
from copy import deepcopy

# Section 1: Schema
class GorillaFileSystemScenario(BaseModel):
    """Main scenario model for Gorilla file system."""
    root: Dict[str, Any] = Field(
        default={
            "root": {
                "type": "directory",
                "contents": {
                    "example.txt": {
                        "type": "file",
                        "content": "This is an example file"
                    },
                    "subdir": {
                        "type": "directory",
                        "contents": {}
                    }
                }
            }
        },
        description="Root directory structure with nested files and directories. Format: {\"root\": {\"type\": \"directory\", \"contents\": {\"filename\": {\"type\": \"file\", \"content\": \"...\"}, \"dirname\": {\"type\": \"directory\", \"contents\": {...}}}}}"
    )
    current_dir: str = Field(default="/", description="Current working directory path, e.g., \"/\" or \"/home/user\"")
    current_time: str = Field(default="2024-01-01T00:00:00", pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [GorillaFileSystemScenario]

# Section 2: Class
class File:
    """Internal file representation."""
    def __init__(self, name: str, content: str = "", current_time: Optional[str] = None) -> None:
        self.name: str = name
        self.content: str = content
        # Store as string to match scenario format
        self._last_modified: str = current_time or "2024-01-01T00:00:00"

    def _write(self, new_content: str, current_time: Optional[str] = None) -> None:
        self.content = new_content
        self._last_modified = current_time or "2024-01-01T00:00:00"

    def _read(self) -> str:
        return self.content

    def _append(self, additional_content: str, current_time: Optional[str] = None) -> None:
        self.content += additional_content
        self._last_modified = current_time or "2024-01-01T00:00:00"

    def __repr__(self):
        return f"<<File: {self.name}, Content: {self.content}>>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, File):
            return False
        return self.name == other.name and self.content == other.content


class Directory:
    """Internal directory representation."""
    def __init__(self, name: str, parent: Optional["Directory"] = None) -> None:
        self.name: str = name
        self.parent: Optional["Directory"] = parent
        self.contents: Dict[str, Union["File", "Directory"]] = {}

    def _add_file(self, file_name: str, content: str = "", current_time: Optional[str] = None) -> None:
        if file_name in self.contents:
            raise ValueError(f"File '{file_name}' already exists in directory '{self.name}'.")
        new_file = File(file_name, content, current_time)
        self.contents[file_name] = new_file

    def _add_directory(self, dir_name: str) -> None:
        if dir_name in self.contents:
            raise ValueError(f"Directory '{dir_name}' already exists in directory '{self.name}'.")
        new_dir = Directory(dir_name, self)
        self.contents[dir_name] = new_dir

    def _get_item(self, item_name: str) -> Union["File", "Directory", None]:
        if item_name == ".":
            return self
        return self.contents.get(item_name)

    def _list_contents(self) -> List[str]:
        return list(self.contents.keys())

    def __repr__(self):
        return f"<Directory: {self.name}, Parent: {self.parent.name if self.parent else None}, Contents: {self.contents}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Directory):
            return False
        return self.name == other.name and self.contents == other.contents


class GorillaFileSystemAPI:
    def __init__(self):
        """Initialize Gorilla file system API with empty state."""
        self.root: Directory = Directory("/", None)
        self._current_dir: Directory = self.root
        self.current_time: str = "2024-01-01T00:00:00"

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the file system instance."""
        model = GorillaFileSystemScenario(**scenario)
        
        # Set current time
        self.current_time = model.current_time
        
        # Initialize root directory
        DEFAULT_STATE = {"root": Directory("/", None)}
        DEFAULT_STATE_COPY = deepcopy(DEFAULT_STATE)
        self.root = DEFAULT_STATE_COPY["root"]
        
        # Load root structure from scenario
        if model.root:
            root_name = list(model.root.keys())[0] if model.root else "/"
            root_dir = Directory(root_name, None)
            self.root = self._load_directory(model.root[root_name].get("contents", {}), root_dir, self.current_time)
        
        # Set current directory
        self._current_dir = self.root
        if model.current_dir and model.current_dir != "/":
            restored = self._navigate_to_directory(model.current_dir)
            if isinstance(restored, Directory):
                self._current_dir = restored

    def save_scenario(self) -> dict:
        """Save current file system state as scenario dictionary."""
        def serialize_directory(directory):
            contents = {}
            for name, item in directory.contents.items():
                if isinstance(item, Directory):
                    contents[name] = {
                        "type": "directory",
                        "contents": serialize_directory(item),
                    }
                elif isinstance(item, File):
                    contents[name] = {
                        "type": "file",
                        "content": item.content,
                    }
            return contents

        root_dir = self.root
        root_name = root_dir.name if root_dir.name != "/" else "root"
        
        scenario = {
            "root": {
                root_name: {
                    "type": "directory",
                    "contents": serialize_directory(root_dir),
                }
            },
            "current_dir": self.pwd()["current_working_directory"],
            "current_time": self.current_time
        }
        return scenario

    def _load_directory(self, current: dict, parent: Optional[Directory] = None, current_time: Optional[str] = None) -> Directory:
        """Load a directory and its contents from a dictionary."""
        for dir_name, dir_data in current.items():
            if dir_data["type"] == "directory":
                new_dir = Directory(dir_name, parent)
                new_dir = self._load_directory(dir_data.get("contents", {}), new_dir, current_time)
                parent.contents[dir_name] = new_dir
            elif dir_data["type"] == "file":
                content = dir_data.get("content", "")
                new_file = File(dir_name, content, current_time)
                parent.contents[dir_name] = new_file
        return parent

    def pwd(self) -> dict:
        """Return the current working directory path."""
        path = []
        dir = self._current_dir
        while dir is not None and dir.name != self.root.name:
            path.append(dir.name)
            dir = dir.parent
        return {"current_working_directory": "/" + "/".join(reversed(path))}

    def ls(self, a: bool = False) -> dict:
        """List the contents of the current directory."""
        contents = self._current_dir._list_contents()
        if not a:
            contents = [item for item in contents if not item.startswith(".")]
        return {"current_directory_content": contents}

    def cd(self, folder: str) -> Union[None, dict]:
        """Change the current working directory to the specified folder."""
        if folder == "..":
            if self._current_dir.parent:
                self._current_dir = self._current_dir.parent
            elif self.root == self._current_dir:
                return {"error": "Current directory is already the root. Cannot go back."}
            else:
                return {"error": "cd: ..: No such directory"}
            return None

        target_dir = self._navigate_to_directory(folder)
        if isinstance(target_dir, dict):
            return {"error": f"cd: {folder}: No such directory. You cannot use path to change directory."}
        self._current_dir = target_dir
        return None

    def _validate_file_or_directory_name(self, dir_name: str) -> bool:
        """Validate file or directory name."""
        if any(c in dir_name for c in '|/\\?%*:"><'):
            return False
        return True

    def mkdir(self, dir_name: str) -> Union[None, dict]:
        """Create a new directory in the current directory."""
        if not self._validate_file_or_directory_name(dir_name):
            return {"error": f"mkdir: cannot create directory '{dir_name}': Invalid character"}
        if dir_name in self._current_dir.contents:
            return {"error": f"mkdir: cannot create directory '{dir_name}': File exists"}
        self._current_dir._add_directory(dir_name)
        return None

    def touch(self, file_name: str) -> Union[None, dict]:
        """Create a new file of any extension in the current directory."""
        if not self._validate_file_or_directory_name(file_name):
            return {"error": f"touch: cannot touch '{file_name}': Invalid character"}
        if file_name in self._current_dir.contents:
            return {"error": f"touch: cannot touch '{file_name}': File exists"}
        self._current_dir._add_file(file_name, current_time=self.current_time)
        return None

    def echo(self, content: str, file_name: Optional[str] = None) -> Union[dict, None]:
        """Write content to a file at current directory or display it in the terminal."""
        if file_name is None:
            return {"terminal_output": content}
        if not self._validate_file_or_directory_name(file_name):
            return {"error": f"echo: cannot touch '{file_name}': Invalid character"}
        if file_name:
            if file_name in self._current_dir.contents:
                self._current_dir._get_item(file_name)._write(content, self.current_time)
            else:
                self._current_dir._add_file(file_name, content, self.current_time)
        return None

    def cat(self, file_name: str) -> dict:
        """Display the contents of a file of any extension from current directory."""
        if not self._validate_file_or_directory_name(file_name):
            return {"error": f"cat: '{file_name}': Invalid character"}
        if file_name in self._current_dir.contents:
            item = self._current_dir._get_item(file_name)
            if isinstance(item, File):
                return {"file_content": item._read()}
            else:
                return {"error": f"cat: {file_name}: Is a directory"}
        else:
            return {"error": f"cat: {file_name}: No such file or directory"}

    def find(self, path: str = ".", name: Optional[str] = None) -> dict:
        """Find any file or directories under specific path that contain name in its file name."""
        matches = []
        target_dir = self._current_dir

        def recursive_search(directory: Directory, base_path: str) -> None:
            for item_name, item in directory.contents.items():
                item_path = f"{base_path}/{item_name}"
                if name is None or name in item_name:
                    matches.append(item_path)
                if isinstance(item, Directory):
                    recursive_search(item, item_path)

        recursive_search(target_dir, path.rstrip("/"))
        return {"matches": matches}

    def wc(self, file_name: str, mode: str = "l") -> dict:
        """Count the number of lines, words, and characters in a file."""
        if mode not in ["l", "w", "c"]:
            return {"error": f"wc: invalid mode '{mode}'"}
        if file_name in self._current_dir.contents:
            file = self._current_dir._get_item(file_name)
            if isinstance(file, File):
                content = file._read()
                if mode == "l":
                    line_count = len(content.splitlines())
                    return {"count": line_count, "type": "lines"}
                elif mode == "w":
                    word_count = len(content.split())
                    return {"count": word_count, "type": "words"}
                elif mode == "c":
                    char_count = len(content)
                    return {"count": char_count, "type": "characters"}
        return {"error": f"wc: {file_name}: No such file or directory"}

    def sort(self, file_name: str) -> dict:
        """Sort the contents of a file line by line."""
        if file_name in self._current_dir.contents:
            file = self._current_dir._get_item(file_name)
            if isinstance(file, File):
                content = file._read()
                sorted_content = "\n".join(sorted(content.splitlines()))
                return {"sorted_content": sorted_content}
        return {"error": f"sort: {file_name}: No such file or directory"}

    def grep(self, file_name: str, pattern: str) -> dict:
        """Search for lines in a file that contain the specified pattern."""
        if file_name in self._current_dir.contents:
            file = self._current_dir._get_item(file_name)
            if isinstance(file, File):
                content = file._read()
                matching_lines = [line for line in content.splitlines() if pattern in line]
                return {"matching_lines": matching_lines}
        return {"error": f"grep: {file_name}: No such file or directory"}

    def du(self, human_readable: bool = False) -> dict:
        """Estimate the disk usage of a directory and its contents."""
        def get_size(item: Union[File, Directory]) -> int:
            if isinstance(item, File):
                return len(item._read().encode("utf-8"))
            elif isinstance(item, Directory):
                return sum(get_size(child) for child in item.contents.values())
            return 0

        target_dir = self._navigate_to_directory(None)
        if isinstance(target_dir, dict):
            return target_dir

        total_size = get_size(target_dir)
        if human_readable:
            size_val = total_size
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_val < 1024:
                    size_str = f"{size_val:.2f} {unit}"
                    break
                size_val /= 1024
            else:
                size_str = f"{size_val:.2f} PB"
        else:
            size_str = f"{total_size} bytes"
        return {"disk_usage": size_str}

    def tail(self, file_name: str, lines: int = 10) -> dict:
        """Display the last part of a file."""
        if file_name in self._current_dir.contents:
            file = self._current_dir._get_item(file_name)
            if isinstance(file, File):
                content = file._read().splitlines()
                if lines > len(content):
                    lines = len(content)
                last_lines = content[-lines:]
                return {"last_lines": "\n".join(last_lines)}
        return {"error": f"tail: {file_name}: No such file or directory"}

    def diff(self, file_name1: str, file_name2: str) -> dict:
        """Compare two files line by line."""
        if file_name1 in self._current_dir.contents and file_name2 in self._current_dir.contents:
            file1 = self._current_dir._get_item(file_name1)
            file2 = self._current_dir._get_item(file_name2)
            if isinstance(file1, File) and isinstance(file2, File):
                content1 = file1._read().splitlines()
                content2 = file2._read().splitlines()
                diff_lines = [
                    f"- {line1}\n+ {line2}"
                    for line1, line2 in zip(content1, content2)
                    if line1 != line2
                ]
                return {"diff_lines": "\n".join(diff_lines)}
        return {"error": f"diff: {file_name1} or {file_name2}: No such file or directory"}

    def mv(self, source: str, destination: str) -> dict:
        """Move a file or directory from one location to another."""
        if source not in self._current_dir.contents:
            return {"error": f"mv: cannot move '{source}': No such file or directory"}
        item = self._current_dir._get_item(source)
        if not isinstance(item, (File, Directory)):
            return {"error": f"mv: cannot move '{source}': Not a file or directory"}
        if "/" in destination:
            return {"error": f"mv: no path allowed in destination. Only file name and folder name is supported for this operation."}
        
        if destination in self._current_dir.contents:
            dest_item = self._current_dir._get_item(destination)
            if isinstance(dest_item, Directory):
                if source in dest_item.contents:
                    return {"error": f"mv: cannot move '{source}' to '{destination}/{source}': File exists"}
                self._current_dir.contents.pop(source)
                if isinstance(item, File):
                    dest_item._add_file(source, item.content, self.current_time)
                else:
                    dest_item._add_directory(source)
                    dest_item.contents[source].contents = item.contents
                return {"result": f"'{source}' moved to '{destination}/{source}'"}
            else:
                return {"error": f"mv: cannot move '{source}' to '{destination}': Not a directory"}
        else:
            self._current_dir.contents.pop(source)
            if isinstance(item, File):
                self._current_dir._add_file(destination, item.content, self.current_time)
            else:
                self._current_dir._add_directory(destination)
                self._current_dir.contents[destination].contents = item.contents
            return {"result": f"'{source}' moved to '{destination}'"}

    def rm(self, file_name: str) -> dict:
        """Remove a file or directory."""
        if file_name in self._current_dir.contents:
            item = self._current_dir._get_item(file_name)
            if isinstance(item, File) or isinstance(item, Directory):
                self._current_dir.contents.pop(file_name)
                return {"result": f"'{file_name}' removed"}
            else:
                return {"error": f"rm: cannot remove '{file_name}': Not a file or directory"}
        else:
            return {"error": f"rm: cannot remove '{file_name}': No such file or directory"}

    def rmdir(self, dir_name: str) -> dict:
        """Remove a directory at current directory."""
        if dir_name in self._current_dir.contents:
            item = self._current_dir._get_item(dir_name)
            if isinstance(item, Directory):
                if item.contents:
                    return {"error": f"rmdir: failed to remove '{dir_name}': Directory not empty"}
                else:
                    self._current_dir.contents.pop(dir_name)
                    return {"result": f"'{dir_name}' removed"}
            else:
                return {"error": f"rmdir: cannot remove '{dir_name}': Not a directory"}
        else:
            return {"error": f"rmdir: cannot remove '{dir_name}': No such file or directory"}

    def cp(self, source: str, destination: str) -> dict:
        """Copy a file or directory from one location to another."""
        if source not in self._current_dir.contents:
            return {"error": f"cp: cannot copy '{source}': No such file or directory"}
        item = self._current_dir._get_item(source)
        if not isinstance(item, (File, Directory)):
            return {"error": f"cp: cannot copy '{source}': Not a file or directory"}
        if "/" in destination:
            return {"error": f"cp: don't allow path in destination. Only file name and folder name is supported for this operation."}
        
        if destination in self._current_dir.contents:
            dest_item = self._current_dir._get_item(destination)
            if isinstance(dest_item, Directory):
                if source in dest_item.contents:
                    return {"error": f"cp: cannot copy '{source}' to '{destination}/{source}': File exists"}
                if isinstance(item, File):
                    dest_item._add_file(source, item.content, self.current_time)
                else:
                    dest_item._add_directory(source)
                    dest_item.contents[source].contents = item.contents.copy()
                return {"result": f"'{source}' copied to '{destination}/{source}'"}
            else:
                return {"error": f"cp: cannot copy '{source}' to '{destination}': Not a directory"}
        else:
            if isinstance(item, File):
                self._current_dir._add_file(destination, item.content, self.current_time)
            else:
                self._current_dir._add_directory(destination)
                self._current_dir.contents[destination].contents = item.contents.copy()
            return {"result": f"'{source}' copied to '{destination}'"}

    def _navigate_to_directory(self, path: Optional[str]) -> Union[Directory, dict]:
        """Navigate to a specified directory path from the current directory."""
        if path is None or path == ".":
            return self._current_dir
        elif path == "/":
            return self.root

        dirs = path.strip("/").split("/")
        temp_dir = self._current_dir if not path.startswith("/") else self.root
        
        if dirs and dirs[0] == self.root.name:
            dirs = dirs[1:]

        for dir_name in dirs:
            next_dir = temp_dir._get_item(dir_name)
            if isinstance(next_dir, Directory):
                temp_dir = next_dir
            else:
                return {"error": f"cd: '{path}': No such file or directory"}
        return temp_dir

# Section 3: MCP Tools
mcp = FastMCP(name="GorillaFileSystemAPI")
api = GorillaFileSystemAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load file system scenario data.
    
    Args:
        scenario (dict): Scenario dictionary matching GorillaFileSystemScenario schema.
    
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
    """Save current file system state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def pwd() -> dict:
    """Return the current working directory path.
    
    Returns:
        current_working_directory (str): The current working directory path.
    """
    try:
        return api.pwd()
    except Exception as e:
        raise e

@mcp.tool()
def ls(a: bool = False) -> dict:
    """List the contents of the current directory.
    
    Args:
        a (bool): [Optional] Show hidden files and directories. Defaults to False.
    
    Returns:
        current_directory_content (list): A list of the contents of the directory.
    """
    try:
        return api.ls(a)
    except Exception as e:
        raise e

@mcp.tool()
def cd(folder: str) -> str:
    """Change the current working directory to the specified folder.
    
    Args:
        folder (str): The folder of the directory to change to. You can only change one folder at a time.
    
    Returns:
        success_message (str): Success message or error message.
    """
    try:
        if not folder or not isinstance(folder, str):
            raise ValueError("Folder must be a non-empty string")
        result = api.cd(folder)
        if result is None:
            pwd_result = api.pwd()
            return f"Changed to {pwd_result['current_working_directory']}"
        elif isinstance(result, dict) and "error" in result:
            return result["error"]
        return "Successfully changed directory"
    except Exception as e:
        raise e

@mcp.tool()
def mkdir(dir_name: str) -> str:
    """Create a new directory in the current directory.
    
    Args:
        dir_name (str): The name of the new directory at current directory.
    
    Returns:
        success_message (str): Success message or error message.
    """
    try:
        if not dir_name or not isinstance(dir_name, str):
            raise ValueError("Directory name must be a non-empty string")
        result = api.mkdir(dir_name)
        if result is None:
            return f"Successfully created directory '{dir_name}'"
        elif isinstance(result, dict) and "error" in result:
            return result["error"]
        return "Successfully created directory"
    except Exception as e:
        raise e

@mcp.tool()
def touch(file_name: str) -> str:
    """Create a new file of any extension in the current directory.
    
    Args:
        file_name (str): The name of the new file in the current directory.
    
    Returns:
        success_message (str): Success message or error message.
    """
    try:
        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")
        result = api.touch(file_name)
        if result is None:
            return f"Successfully created file '{file_name}'"
        elif isinstance(result, dict) and "error" in result:
            return result["error"]
        return "Successfully created file"
    except Exception as e:
        raise e

@mcp.tool()
def echo(content: str, file_name: Optional[str] = None) -> dict:
    """Write content to a file at current directory or display it in the terminal.
    
    Args:
        content (str): The content to write or display.
        file_name (str): [Optional] The name of the file at current directory to write the content to.
    
    Returns:
        terminal_output (str): The content if no file name is provided, or None if written to file.
    """
    try:
        if content is None:
            raise ValueError("Content cannot be None")
        if file_name is not None and not isinstance(file_name, str):
            raise ValueError("File name must be a string")
        result = api.echo(content, file_name)
        if result is None:
            return {"terminal_output": "Content written to file"}
        return result
    except Exception as e:
        raise e

@mcp.tool()
def cat(file_name: str) -> dict:
    """Display the contents of a file of any extension from current directory.
    
    Args:
        file_name (str): The name of the file from current directory to display.
    
    Returns:
        file_content (str): The content of the file.
    """
    try:
        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")
        return api.cat(file_name)
    except Exception as e:
        raise e

@mcp.tool()
def find(path: str = ".", name: Optional[str] = None) -> dict:
    """Find any file or directories under specific path that contain name in its file name.
    
    Args:
        path (str): [Optional] The directory path to start the search. Defaults to current directory.
        name (str): [Optional] The name of the file or directory to search for.
    
    Returns:
        matches (list): A list of matching file and directory paths.
    """
    try:
        if not isinstance(path, str):
            raise ValueError("Path must be a string")
        if name is not None and not isinstance(name, str):
            raise ValueError("Name must be a string")
        return api.find(path, name)
    except Exception as e:
        raise e

@mcp.tool()
def wc(file_name: str, mode: str = "l") -> dict:
    """Count the number of lines, words, and characters in a file.
    
    Args:
        file_name (str): Name of the file of current directory to perform wc operation on.
        mode (str): [Optional] Mode of operation ('l' for lines, 'w' for words, 'c' for characters). Defaults to 'l'.
    
    Returns:
        count (int): The count of the number of lines, words, or characters in the file.
        type (str): The type of unit we are counting.
    """
    try:
        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")
        if not isinstance(mode, str) or mode not in ["l", "w", "c"]:
            raise ValueError("Mode must be 'l', 'w', or 'c'")
        return api.wc(file_name, mode)
    except Exception as e:
        raise e

@mcp.tool()
def sort(file_name: str) -> dict:
    """Sort the contents of a file line by line.
    
    Args:
        file_name (str): The name of the file appeared at current directory to sort.
    
    Returns:
        sorted_content (str): The sorted content of the file.
    """
    try:
        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")
        return api.sort(file_name)
    except Exception as e:
        raise e

@mcp.tool()
def grep(file_name: str, pattern: str) -> dict:
    """Search for lines in a file that contain the specified pattern.
    
    Args:
        file_name (str): The name of the file to search.
        pattern (str): The pattern to search for.
    
    Returns:
        matching_lines (list): Lines that match the pattern.
    """
    try:
        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")
        if not pattern or not isinstance(pattern, str):
            raise ValueError("Pattern must be a non-empty string")
        return api.grep(file_name, pattern)
    except Exception as e:
        raise e

@mcp.tool()
def du(human_readable: bool = False) -> dict:
    """Estimate the disk usage of a directory and its contents.
    
    Args:
        human_readable (bool): [Optional] If True, returns the size in human-readable format. Defaults to False.
    
    Returns:
        disk_usage (str): The estimated disk usage.
    """
    try:
        if not isinstance(human_readable, bool):
            raise ValueError("Human readable must be a boolean")
        return api.du(human_readable)
    except Exception as e:
        raise e

@mcp.tool()
def tail(file_name: str, lines: int = 10) -> dict:
    """Display the last part of a file.
    
    Args:
        file_name (str): The name of the file to display.
        lines (int): [Optional] The number of lines to display from the end of the file. Defaults to 10.
    
    Returns:
        last_lines (str): The last part of the file.
    """
    try:
        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")
        if not isinstance(lines, int) or lines < 0:
            raise ValueError("Lines must be a non-negative integer")
        return api.tail(file_name, lines)
    except Exception as e:
        raise e

@mcp.tool()
def diff(file_name1: str, file_name2: str) -> dict:
    """Compare two files line by line at the current directory.
    
    Args:
        file_name1 (str): The name of the first file in current directory.
        file_name2 (str): The name of the second file in current directory.
    
    Returns:
        diff_lines (str): The differences between the two files.
    """
    try:
        if not file_name1 or not isinstance(file_name1, str):
            raise ValueError("File name 1 must be a non-empty string")
        if not file_name2 or not isinstance(file_name2, str):
            raise ValueError("File name 2 must be a non-empty string")
        return api.diff(file_name1, file_name2)
    except Exception as e:
        raise e

@mcp.tool()
def mv(source: str, destination: str) -> dict:
    """Move a file or directory from one location to another.
    
    Args:
        source (str): Source name of the file or directory to move.
        destination (str): The destination name to move the file or directory to.
    
    Returns:
        result (str): The result of the move operation.
    """
    try:
        if not source or not isinstance(source, str):
            raise ValueError("Source must be a non-empty string")
        if not destination or not isinstance(destination, str):
            raise ValueError("Destination must be a non-empty string")
        return api.mv(source, destination)
    except Exception as e:
        raise e

@mcp.tool()
def rm(file_name: str) -> dict:
    """Remove a file or directory.
    
    Args:
        file_name (str): The name of the file or directory to remove.
    
    Returns:
        result (str): The result of the remove operation.
    """
    try:
        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")
        return api.rm(file_name)
    except Exception as e:
        raise e

@mcp.tool()
def rmdir(dir_name: str) -> dict:
    """Remove a directory at current directory.
    
    Args:
        dir_name (str): The name of the directory to remove.
    
    Returns:
        result (str): The result of the remove operation.
    """
    try:
        if not dir_name or not isinstance(dir_name, str):
            raise ValueError("Directory name must be a non-empty string")
        return api.rmdir(dir_name)
    except Exception as e:
        raise e

@mcp.tool()
def cp(source: str, destination: str) -> dict:
    """Copy a file or directory from one location to another.
    
    Args:
        source (str): The name of the file or directory to copy.
        destination (str): The destination name to copy the file or directory to.
    
    Returns:
        result (str): The result of the copy operation.
    """
    try:
        if not source or not isinstance(source, str):
            raise ValueError("Source must be a non-empty string")
        if not destination or not isinstance(destination, str):
            raise ValueError("Destination must be a non-empty string")
        return api.cp(source, destination)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()

