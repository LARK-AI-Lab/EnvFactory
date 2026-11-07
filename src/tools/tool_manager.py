"""In-process execution of EnvFactory environments for RL rollouts.

Each environment file under ``envs/tools`` defines a backend class, one module-level
backend instance, and FastMCP-decorated wrapper functions. FastMCP serves here only
as the tool registry (names, descriptions, and argument schemas the policy saw in
SFT); no MCP server, client, or transport is started.

Every rollout gets its own ``EnvClient``: a fresh backend plus the wrapper functions
rebound to a private copy of the module globals. Module-level rebinding inside the
wrappers (the backend instance, ``global`` session tokens) therefore stays isolated
per rollout, without re-importing the module.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import types
from functools import lru_cache
from pathlib import Path
from typing import Any

import pydantic_core

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_TOOLS = frozenset({"load_scenario", "save_scenario"})


def _resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _text_blocks(result: Any) -> list[str]:
    """Mirror FastMCP's unstructured content: lists flatten, None vanishes, objects become JSON."""
    if result is None:
        return []
    if isinstance(result, (list, tuple)):
        return [block for item in result for block in _text_blocks(item)]
    if isinstance(result, str):
        return [result]
    return [pydantic_core.to_json(result, fallback=str, indent=2).decode()]


def format_tool_result(result: Any) -> str:
    """Render a tool result as the text MCPClientManager produced during data synthesis."""
    return ",".join(_text_blocks(result))


def _rebind(fn: types.FunctionType, namespace: dict) -> types.FunctionType:
    clone = types.FunctionType(fn.__code__, namespace, fn.__name__, fn.__defaults__, fn.__closure__)
    clone.__kwdefaults__ = fn.__kwdefaults__
    return clone


class EnvServer:
    """One environment module, imported once and shared read-only by its clients."""

    def __init__(self, name: str, path: Path):
        spec = importlib.util.spec_from_file_location(f"envfactory_envs.{name}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load environment {name} from {path}.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # Pydantic resolves model annotations through sys.modules.
        spec.loader.exec_module(module)

        registry = getattr(module, "mcp", None)
        if registry is None:
            raise AttributeError(f"Environment {name} ({path}) defines no FastMCP registry named 'mcp'.")
        self.tools = {tool.name: tool for tool in registry._tool_manager.list_tools()}
        missing = SCENARIO_TOOLS - self.tools.keys()
        if missing:
            raise ValueError(f"Environment {name} lacks scenario tools: {sorted(missing)}.")

        # The wrappers call the single module-level backend instance (``api``, ``server``, ...).
        backends = [
            key for key, value in vars(module).items()
            if type(value).__module__ == spec.name and callable(getattr(value, "load_scenario", None))
        ]
        if len(backends) != 1:
            raise ValueError(f"Environment {name} must define exactly one backend instance, found {backends}.")

        self.name = name
        self.module = module
        self.backend_name = backends[0]
        self.backend_cls = type(getattr(module, self.backend_name))
        self.schemas = [
            {
                "type": "function",
                "function": {
                    "name": f"{name}-{tool.name}",
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self.tools.values()
            if tool.name not in SCENARIO_TOOLS
        ]


class EnvClient:
    """A rollout-private environment instance loaded with its initial scenario."""

    def __init__(self, server: EnvServer, initial_state: dict):
        self.server = server
        namespace = dict(vars(server.module))
        namespace[server.backend_name] = server.backend_cls()
        self._fns = {name: _rebind(tool.fn, namespace) for name, tool in server.tools.items()}
        self._invoke("load_scenario", {"scenario": initial_state})

    def _invoke(self, tool_name: str, arguments: dict) -> Any:
        """Validate and coerce arguments the way FastMCP does, then call the rebound wrapper."""
        metadata = self.server.tools[tool_name].fn_metadata
        parsed = metadata.arg_model.model_validate(metadata.pre_parse_json(arguments))
        return self._fns[tool_name](**parsed.model_dump_one_level())

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute one policy tool call; failures become the observation, as with an MCP server."""
        full_name = f"{self.server.name}-{tool_name}"
        if tool_name not in self._fns or tool_name in SCENARIO_TOOLS:
            return f"Unknown tool '{full_name}'."
        try:
            return format_tool_result(self._invoke(tool_name, arguments))
        except Exception as e:
            return f"Error executing tool {full_name}: {e}"

    def state(self) -> dict:
        """The scenario as JSON data, matching the synthesized ``final_scenario`` encoding."""
        return pydantic_core.to_jsonable_python(self._invoke("save_scenario", {}), fallback=str)


class ToolManager:
    """Registry of environments from an ``mcpServers`` config; modules load on first use."""

    def __init__(self, config_path: str | Path):
        with open(_resolve(config_path), encoding="utf-8") as f:
            config = json.load(f)
        self._paths = {name: _resolve(cfg["tool_path"]) for name, cfg in config["mcpServers"].items()}
        self._servers: dict[str, EnvServer] = {}
        self._lock = threading.Lock()

    @property
    def servers(self) -> list[str]:
        return list(self._paths)

    def server(self, name: str) -> EnvServer:
        with self._lock:
            if name not in self._servers:
                if name not in self._paths:
                    raise KeyError(f"Environment {name} is not registered in the environment config.")
                self._servers[name] = EnvServer(name, self._paths[name])
            return self._servers[name]

    def filter_tools(self, envs: list[str]) -> list[dict]:
        """Policy-visible tool schemas of the given environments, in the given order."""
        return [schema for env in envs for schema in self.server(env).schemas]

    def create_client(self, env: str, initial_state: dict) -> EnvClient:
        return EnvClient(self.server(env), initial_state)


@lru_cache(maxsize=None)
def get_tool_manager(config_path: str) -> ToolManager:
    return ToolManager(config_path)
