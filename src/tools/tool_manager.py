"""In-process execution of EnvFactory environments for RL rollouts.

Each environment file under ``envs/tools`` defines a backend class, one module-level
backend instance, and ``@mcp.tool()`` wrapper functions on ``mcp = FastMCP(...)``.
No MCP package is used: while an environment file is imported, ``mcp.server.fastmcp``
resolves to ``ToolRegistry``, which records the wrappers with the argument models,
schemas, and validation FastMCP (mcp 1.x) applied when the SFT data was synthesized.

Every rollout gets its own ``EnvClient``: a fresh backend plus the wrapper functions
rebound to a private copy of the module globals. Module-level rebinding inside the
wrappers (the backend instance, ``global`` session tokens) therefore stays isolated
per rollout, without re-importing the module.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
import threading
import types
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Callable

import pydantic_core
from pydantic import BaseModel, ConfigDict, Field, WithJsonSchema, create_model

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


class ArgModelBase(BaseModel):
    """Validated tool arguments (FastMCP's ``ArgModelBase``)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_dump_one_level(self) -> dict[str, Any]:
        """Field values by call name; nested models stay models."""
        return {info.alias or name: getattr(self, name) for name, info in type(self).model_fields.items()}


def _arg_model(fn: Callable) -> type[ArgModelBase]:
    """Pydantic model of ``fn``'s parameters, built exactly as FastMCP's ``func_metadata``."""
    fields: dict[str, Any] = {}
    for param in inspect.signature(fn, eval_str=True).parameters.values():
        annotation = Any if param.annotation is inspect.Parameter.empty else param.annotation
        metadata = [WithJsonSchema({"title": param.name, "type": "string"})] if param.annotation is inspect.Parameter.empty else []
        name, field_kwargs = param.name, {}
        if callable(getattr(BaseModel, name, None)):  # Avoid shadowing BaseModel methods.
            name, field_kwargs = f"field_{name}", {"alias": name}
        typed = Annotated[(annotation, *metadata, Field(**field_kwargs))]
        fields[name] = typed if param.default is inspect.Parameter.empty else (typed, param.default)
    return create_model(f"{fn.__name__}Arguments", __base__=ArgModelBase, **fields)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    fn: types.FunctionType
    description: str
    parameters: dict
    arg_model: type[ArgModelBase]

    def parse_arguments(self, arguments: dict) -> dict:
        """FastMCP's argument handling: JSON-decode non-string fields given as strings, then validate."""
        fields = {info.alias or name: info for name, info in self.arg_model.model_fields.items()}
        decoded = dict(arguments)
        for key, value in arguments.items():
            if key in fields and isinstance(value, str) and fields[key].annotation is not str:
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    continue
                if not isinstance(parsed, (str, int, float)):
                    decoded[key] = parsed
        return self.arg_model.model_validate(decoded).model_dump_one_level()


class ToolRegistry:
    """Stands in for ``FastMCP(name=...)`` while an environment file is imported."""

    def __init__(self, name: str | None = None, *args: Any, **kwargs: Any):
        self.name = name
        self.tools: dict[str, ToolSpec] = {}

    def tool(self, name: str | None = None, description: str | None = None, **kwargs: Any) -> Callable:
        def register(fn: types.FunctionType) -> types.FunctionType:
            arg_model = _arg_model(fn)
            spec = ToolSpec(
                name=name or fn.__name__,
                fn=fn,
                description=description or fn.__doc__ or "",
                parameters=arg_model.model_json_schema(by_alias=True),
                arg_model=arg_model,
            )
            self.tools[spec.name] = spec
            return fn

        return register

    def run(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("EnvFactory environments run in-process through src.tools.tool_manager; there is no server.")


_FASTMCP_MODULE = "mcp.server.fastmcp"


@contextmanager
def _local_fastmcp():
    """Resolve ``from mcp.server.fastmcp import FastMCP`` to ``ToolRegistry`` for one import."""
    stub = types.ModuleType(_FASTMCP_MODULE)
    stub.FastMCP = ToolRegistry
    previous = sys.modules.get(_FASTMCP_MODULE)
    sys.modules[_FASTMCP_MODULE] = stub
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop(_FASTMCP_MODULE, None)
        else:
            sys.modules[_FASTMCP_MODULE] = previous


class EnvServer:
    """One environment module, imported once and shared read-only by its clients."""

    def __init__(self, name: str, path: Path):
        spec = importlib.util.spec_from_file_location(f"envfactory_envs.{name}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load environment {name} from {path}.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # Pydantic resolves model annotations through sys.modules.
        with _local_fastmcp():
            spec.loader.exec_module(module)

        registry = getattr(module, "mcp", None)
        if not isinstance(registry, ToolRegistry):
            raise AttributeError(f"Environment {name} ({path}) defines no tool registry 'mcp = FastMCP(...)'.")
        self.tools: dict[str, ToolSpec] = registry.tools
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
        return self._fns[tool_name](**self.server.tools[tool_name].parse_arguments(arguments))

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
