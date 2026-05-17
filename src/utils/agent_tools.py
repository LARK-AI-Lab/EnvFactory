from agents import function_tool
from ddgs import DDGS
from datetime import datetime

# Search
SEARCH_ERR_MSG = "Search operation failed for query {query}. Error: {error}. Please try using a different search engine or adjusting your query."

@function_tool
def search(query: str, max_results: int=3, timeout: int=5) -> str:
    """
    Web search using DuckDuckGo.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of search results to return (default 3).
        timeout (int): Timeout in seconds for the search (default 5).
    """
    try:
        with DDGS(timeout=timeout) as ddgs:
            result_text = ""
            results_count = 0
            
            for i, result in enumerate(ddgs.text(query, max_results=max_results), 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                
                result_text += f"Title {i}: {title}\n"
                result_text += f"Description: {body}\n\n"
                results_count += 1
            
            if results_count == 0:
                return f"No results found for: '{query}'"
            else:
                return f"Found {results_count} results for '{query}':\n\n{result_text}"
                
    except Exception as e:
        return SEARCH_ERR_MSG.format(query=query, error=str(e))


# Datetime
@function_tool
def get_current_datetime() -> str:
    """
    Get current datetime in YYYY-MM-DDTHH:MM:SS format.
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


# Code Sandbox
from src.manager.mcp_client_manager import MCPManager

@function_tool
def execute_mcp_tool(tool_name: str, tool_args: str, client_id: str) -> str:
    """
    Execute an MCP tool with proper error handling and client management.

    Args:
        tool_name (str): The name of the MCP tool to execute in format "{mcp_server}-{tool_name}".
        tool_args (str): JSON string containing the arguments for the tool.
        client_id (str): Client identifier in format "{mcp_server}-{request_id}".
    
    Returns:
        str: The execution result from the MCP tool as a string.
    """
    tool_response = MCPManager.call_tool(
        tool_name = tool_name,
        tool_args = tool_args,
        client_id = client_id,
    )

    return tool_response

# Dynamic MCP Tool Execution
import json
import importlib.util
from pathlib import Path

def load_and_execute_mcp_tool(
    tool_file_path: str,
    tool_name: str,
    tool_args: dict,
    mcp_server_name: str
) -> str:
    """
    Dynamically load and execute an MCP tool from a file.
    
    Args:
        tool_file_path: Path to the tool implementation file
        tool_name: Name of the tool function to execute
        tool_args: Dictionary of arguments for the tool
        mcp_server_name: Name of the MCP server
        
    Returns:
        str: JSON string of the tool execution result
    """
    try:
        # Load the tool module
        spec = importlib.util.spec_from_file_location(f"{mcp_server_name}_tools", tool_file_path)
        if spec is None or spec.loader is None:
            return json.dumps({"error": f"Failed to load tool file: {tool_file_path}"})
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the FastMCP instance (usually named 'mcp')
        if not hasattr(module, 'mcp'):
            return json.dumps({"error": "Tool file does not contain 'mcp' instance"})
        
        mcp = module.mcp
        
        # Find the tool function
        tool_func = None
        for tool in mcp.list_tools():
            if tool.name == tool_name:
                # Get the actual function from the tool
                tool_func = tool.func if hasattr(tool, 'func') else None
                break
        
        if tool_func is None:
            return json.dumps({"error": f"Tool '{tool_name}' not found in module"})
        
        # Execute the tool function
        result = tool_func(**tool_args)
        
        # Convert result to JSON string
        if isinstance(result, str):
            try:
                # Try to parse as JSON first
                json.loads(result)
                return result
            except:
                return json.dumps({"result": result})
        else:
            return json.dumps(result, ensure_ascii=False, default=str)
            
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})