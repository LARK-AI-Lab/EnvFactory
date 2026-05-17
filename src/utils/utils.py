import json
import re
from pathlib import Path
from typing import Dict, Any, List

SYSTEM_PROMPT = '''You are a helpful assistant. Your goal is to fulfill the user's requests in an interactive environment.
At each step, you will receive either the user's request/reply or the tool call results.
- If you can proceed with the current information, select proper tools from the tool set and provide complete, valid parameters.
- If you lack essential information to complete the task or perform a tool call, and it cannot be obtained through the existing tool set, actively ask the user for specific details.
- Avoid calling tools while interacting with user in one step.
- When a task involves sensitive credentials or physical device actions (e.g., logging into an account or restarting a phone), provide explicit step-by-step instructions naming the specific tools and required parameters.
- You cannot execute user tools directly; instead, guide users on how to perform these actions themselves.
{user_tools}
- When you believe the task is completed, provide a direct and concise response to the user's original request.

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{\"name\": <function-name>, \"arguments\": <args-json-object>}
</tool_call>
'''

def to_JSON(text: str, force_return_dict: bool = False) -> dict:
    # Convert to JSON directly
    try:
        return json.loads(text)
    except:
        pass

    # Extract the outermost JSON object
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = text[start_index:end_index+1]
            return json.loads(json_str)
    except:
        pass

    # Extract the outermost List object
    try:
        start_index = text.find('[')
        end_index = text.rfind(']')

        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = text[start_index:end_index+1]
            return json.loads(json_str)
    except:
        pass
    
    if force_return_dict:
        return {}
    return text

def parse_structured_output(text):
    """
    Parse a string with XML-like tags and extract key-content pair.

    Args:
        text (str): Input string containing structured content
        
    Returns:
        dict: Dictionary with keys and their corresponding content
            - think: reasoning content
            - non_think: non-reasoning content
            - other_keys: parsed XML-like tags from non_think content
    """
    result = {}
    non_think_text = text.strip()
    
    # Extract reasoning content
    delimiter = '</think>'
    idx = text.find(delimiter)
    if idx != -1:
        result["think"] = text[:idx].strip()
        non_think_text = text[idx + len(delimiter):].strip()

    result["non_think"] = non_think_text
    
    # Extract XML-like tags from non_think content
    # Handle last unclosed tags
    pattern = r'<([a-zA-Z_][a-zA-Z0-9_-]*)\s*>[^<]*$'
    matches = re.findall(pattern, non_think_text)
    if matches:
        last_unclosed_tag = matches[-1]
        print(last_unclosed_tag)
        if f"</{last_unclosed_tag}>" not in non_think_text:
            non_think_text += f"</{last_unclosed_tag}>"

    # Handle properly closed tags
    pattern = r'(?s)<([a-zA-Z_][a-zA-Z0-9_-]*)>(.*?)</\1>'
    matches = re.findall(pattern, non_think_text)
    
    for tag, content in matches:
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            parsed_content = content
        
        if tag in result:
            if isinstance(result[tag], list):
                result[tag].append(parsed_content)
            else:
                result[tag] = [result[tag]]
                result[tag].append(parsed_content)
        else:
            result[tag] = parsed_content
        
    return result


import sys
from io import StringIO
from contextlib import contextmanager

@contextmanager
def capture_stdout():
    """Context manager to capture stdout safely."""
    original_stdout = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output
    try:
        yield captured_output
    finally:
        sys.stdout = original_stdout

def load_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load MCP server information from metadata JSON file.
    
    Args:
        metadata_path: Path to metadata file (e.g., 'envs/metadata/AmapLocation-metadata.json')
        
    Returns:
        Dict containing class_name, description, and tools
    """
    metadata_file = Path(metadata_path)
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Extract required information
    class_name = metadata.get('class_name', '')
    description = metadata.get('description', '')
    tools = metadata.get('tools', [])
    
    if not class_name:
        raise ValueError("Metadata file missing 'class_name' field")
    if not description:
        raise ValueError("Metadata file missing 'description' field")
    if not tools:
        raise ValueError("Metadata file missing 'tools' field or tools list is empty")
    
    return {
        'class_name': class_name,
        'description': description,
        'tools': tools
    }


def format_tools_for_prompt(tools: List[Dict[str, Any]]) -> str:
    """
    Format tools list into string for prompt.
    
    Args:
        tools: List of tools, each containing name, description, input_schema, output_schema
        
    Returns:
        Formatted tools string
    """
    formatted_tools = []
    for tool in tools:
        tool_str = f"Tool Name: {tool.get('name', 'unknown')}\n"
        tool_str += f"Description: {tool.get('description', 'No description')}\n"
        
        # Format input_schema
        if 'input_schema' in tool:
            input_schema = tool['input_schema']
            tool_str += f"Input Schema: {json.dumps(input_schema, indent=2, ensure_ascii=False)}\n"
        
        # Format output_schema
        if 'output_schema' in tool:
            output_schema = tool['output_schema']
            tool_str += f"Output Schema: {json.dumps(output_schema, indent=2, ensure_ascii=False)}\n"
        
        formatted_tools.append(tool_str)
    
    return "\n\n".join(formatted_tools)

def update_mcp_server_config(
    config_path: str,
    mcp_server_name: str,
    tool_path: str,
    is_stateless: bool = False
) -> None:
    """
    Update or add MCP server configuration to configs/mcp_server.json.
    
    Args:
        config_path: Path to the config file
        mcp_server_name: Name of the MCP server
        tool_path: Path to the tool file (e.g., "envs/tools/ChinaRailway.py")
        is_stateless: Whether the server is stateless (default: False)
    """
    config_path_obj = Path(config_path)
    
    # Read existing config or create new one
    if config_path_obj.exists():
        try:
            with open(config_path_obj, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    config = json.loads(content)
                else:
                    # File exists but is empty
                    config = {"mcpServers": {}}
        except json.JSONDecodeError:
            # File exists but contains invalid JSON
            config = {"mcpServers": {}}
    else:
        config = {"mcpServers": {}}
    
    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Convert paths to strings if they are Path objects
    tool_path_str = str(tool_path) if isinstance(tool_path, Path) else tool_path
    
    # Update or add server configuration
    config["mcpServers"][mcp_server_name] = {
        "tool_path": tool_path_str,
        "stateless": is_stateless
    }
    
    # Write updated config back to file
    with open(config_path_obj, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    



import inspect
from functools import wraps
from typing import Any, Callable, Type
from mcp.server.fastmcp import FastMCP

def register_mcp_tools(tool_class: Type, mcp: FastMCP, tool_instance: Any = None):
    """Register all public methods of a class as MCP tools."""
    if tool_instance is None:
        tool_instance = tool_class()
    
    for name, method in inspect.getmembers(tool_instance, predicate=inspect.ismethod):
        if name.startswith("_"):
            continue
            
        signature = inspect.signature(method)
        
        @wraps(method)
        def wrapper(*args, _method_name: str = name, **kwargs):
            try:
                method_to_call = getattr(tool_instance, _method_name)
                result = method_to_call(*args, **kwargs)
                return result
            except Exception as error:
                return f"Error: {error}"
        
        wrapper.__signature__ = signature
        mcp.tool()(wrapper)


import importlib.util
import sys
from typing import Any, Optional

def load_from_file(file_path: str, target_name: str) -> Optional[Any]:
    """
    Load a specific target (variable, class, function) from a Python file
    
    Args:
        file_path: Path to the Python file
        target_name: Name of the target to load (variable, class, function name)
        
    Returns:
        The requested target if found, None otherwise
    """
    try:
        # Create a unique module name from the file path
        module_name = file_path.replace('/', '_').replace('.', '_')
        
        # Create module specification from file location
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            print(f"Error: Could not create spec from {file_path}")
            return None
        
        # Create module from specification
        module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules to avoid reloading issues
        sys.modules[module_name] = module
        
        # Execute the module (this runs all the code in the file)
        spec.loader.exec_module(module)
        
        # Get the target from the module
        target = getattr(module, target_name, None)
        
        if target is None:
            print(f"Warning: Target '{target_name}' not found in {file_path}")
            return None
            
        return target
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading target '{target_name}' from {file_path}: {e}")
        return None
    

import inspect
from src.manager.mcp_client_manager import MCPManager

def read_scenario_schema(mcp_servers: str | list[str], mode: str = "JSON") -> str:
    """
    Read the scenario schema example for given MCP servers.

    Args:
        mcp_servers (str or list of str): Target MCP servers.
        mode (str): "JSON" or "Pydantic".
    """
    if isinstance(mcp_servers, str):
        mcp_servers = [mcp_servers]

    schema_desc = ""
    for mcp_server in mcp_servers:
        tool_path = MCPManager.server_to_path_mapping[mcp_server]
        scenario_schema = load_from_file(file_path=tool_path, target_name="Scenario_Schema")

        schema_desc += f"## MCP Server: {mcp_server}\n"
        if mode == "JSON": # JSON
            schema_desc += f"{str(scenario_schema[-1].model_json_schema())}\n"
        else: # Pydantic
            for schema in scenario_schema:
                schema_desc += f"{inspect.getsource(schema)}\n"
            schema_desc += "\n"

    return schema_desc