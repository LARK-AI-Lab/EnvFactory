"""Static regressions for Phase 2 async MCP call paths."""

import ast
import inspect
from pathlib import Path

import pytest

from src.manager.mcp_client_manager import MCPClientManager


ROOT = Path(__file__).resolve().parents[2]
ASYNC_MCP_CALLERS = (
    ROOT / "src" / "gen" / "query_gen" / "query_gen_non_conv.py",
    ROOT / "src" / "gen" / "query_gen" / "query_gen_conv.py",
    ROOT / "src" / "gen" / "env_gen" / "validate_revise.py",
    ROOT / "src" / "utils" / "agent_tools.py",
)
SYNC_MANAGER_METHODS = {
    "call_tool",
    "close_client",
    "get_client",
    "load_scenario",
    "save_all_scenario",
    "save_all_scenarios",
}


def test_required_async_mcp_api_is_public():
    for method_name in (
        "aload_scenario",
        "acall_tool",
        "asave_all_scenarios",
        "aclose_client",
    ):
        assert inspect.iscoroutinefunction(
            getattr(MCPClientManager, method_name)
        ), method_name


@pytest.mark.parametrize("path", ASYNC_MCP_CALLERS, ids=lambda path: path.name)
def test_async_generation_paths_do_not_call_sync_mcp_methods(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations = []
    for function in ast.walk(tree):
        if not isinstance(function, ast.AsyncFunctionDef):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr in SYNC_MANAGER_METHODS:
                violations.append((function.name, node.lineno, node.func.attr))

    assert not violations
