"""Offline validation for the fixed MoLab mini MCP catalog."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import importlib.util
import json
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .config import MiniConfig, load_config


LIFECYCLE_TOOLS = frozenset({"load_scenario", "save_scenario"})
_FORBIDDEN_IMPORTS = frozenset(
    {
        "aiohttp",
        "httpx",
        "litellm",
        "openai",
        "requests",
        "urllib3",
    }
)


class CatalogValidationError(ValueError):
    """Raised when the configured mini catalog is incomplete or unsafe."""


@dataclass(frozen=True)
class CatalogServer:
    name: str
    metadata_path: Path
    tool_path: Path
    metadata: dict[str, Any]
    metadata_tool_names: tuple[str, ...]
    registered_tool_names: tuple[str, ...]


@dataclass(frozen=True)
class CatalogReport:
    servers: tuple[CatalogServer, ...]
    digest: str

    @property
    def server_count(self) -> int:
        return len(self.servers)

    @property
    def metadata_tool_count(self) -> int:
        return sum(len(server.metadata_tool_names) for server in self.servers)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    except CatalogValidationError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogValidationError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogValidationError(f"JSON root must be an object: {path}")
    return value


def _repo_file(root: Path, raw_path: Any, *, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise CatalogValidationError(f"{label} must be a non-empty repository-relative path")
    if "\\" in raw_path or Path(raw_path).is_absolute():
        raise CatalogValidationError(f"{label} must use a repository-relative POSIX path: {raw_path!r}")
    path = (root / raw_path).resolve()
    if not path.is_relative_to(root):
        raise CatalogValidationError(f"{label} escapes repository root: {raw_path!r}")
    if not path.is_file():
        raise CatalogValidationError(f"{label} does not exist: {path}")
    return path


def _validate_no_http_client_imports(tool_path: Path) -> None:
    try:
        source = tool_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(tool_path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise CatalogValidationError(f"cannot parse tool implementation {tool_path}: {exc}") from exc

    forbidden: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                root = name.split(".", 1)[0]
                if root in _FORBIDDEN_IMPORTS or name in {"http.client", "urllib.request"}:
                    forbidden.add(name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root in _FORBIDDEN_IMPORTS or node.module in {"http.client", "urllib.request"}:
                forbidden.add(node.module)
            if node.module == "urllib" and any(alias.name == "request" for alias in node.names):
                forbidden.add("urllib.request")
    if forbidden:
        names = ", ".join(sorted(forbidden))
        raise CatalogValidationError(f"{tool_path} imports external HTTP client modules: {names}")


def _metadata_tool_names(metadata: dict[str, Any], server_name: str) -> tuple[str, ...]:
    class_name = metadata.get("class_name")
    if class_name != server_name:
        raise CatalogValidationError(
            f"metadata class_name mismatch for {server_name}: expected {server_name!r}, got {class_name!r}"
        )
    tools = metadata.get("tools")
    if not isinstance(tools, list) or not tools:
        raise CatalogValidationError(f"metadata for {server_name} has an empty tool list")
    names: list[str] = []
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str) or not tool["name"]:
            raise CatalogValidationError(f"metadata tool {index} for {server_name} has no valid name")
        names.append(tool["name"])
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise CatalogValidationError(
            f"metadata for {server_name} contains duplicate tools: {', '.join(duplicates)}"
        )
    return tuple(names)


async def _registered_tool_names(tool_path: Path, server_name: str) -> tuple[str, ...]:
    module_name = f"_envfactory_mini_catalog_{server_name}_{hashlib.sha256(str(tool_path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, tool_path)
    if spec is None or spec.loader is None:
        raise CatalogValidationError(f"cannot import tool implementation: {tool_path}")
    module = importlib.util.module_from_spec(spec)
    try:
        with warnings.catch_warnings():
            # FastMCP 3.1 currently emits this warning while introspecting its
            # own forward-referenced settings model; it is unrelated to the
            # generated server schema and would otherwise pollute CLI output.
            warnings.filterwarnings(
                "ignore",
                message=r"Field 'lifespan' has an incomplete definition:.*",
            )
            spec.loader.exec_module(module)
    except Exception as exc:
        raise CatalogValidationError(f"failed to import {tool_path}: {type(exc).__name__}: {exc}") from exc

    mcp = getattr(module, "mcp", None)
    if mcp is None or not callable(getattr(mcp, "list_tools", None)):
        raise CatalogValidationError(f"{tool_path} does not expose an MCP server named 'mcp'")
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"Field 'lifespan' has an incomplete definition:.*",
            )
            registered = await mcp.list_tools()
    except Exception as exc:
        raise CatalogValidationError(f"failed to list MCP tools for {server_name}: {exc}") from exc
    names = tuple(tool.name for tool in registered)
    missing_lifecycle = LIFECYCLE_TOOLS.difference(names)
    if missing_lifecycle:
        raise CatalogValidationError(
            f"{server_name} is missing lifecycle tools: {', '.join(sorted(missing_lifecycle))}"
        )
    return names


def _digest_payload(hasher: Any, label: str, payload: bytes) -> None:
    label_bytes = label.encode("utf-8")
    hasher.update(len(label_bytes).to_bytes(8, "big"))
    hasher.update(label_bytes)
    hasher.update(len(payload).to_bytes(8, "big"))
    hasher.update(payload)


async def validate_catalog_async(config: MiniConfig) -> CatalogReport:
    """Import, inspect, and hash every configured server without network access."""
    mcp_config = _load_json(config.catalog.mcp_config)
    servers_value = mcp_config.get("mcpServers")
    if not isinstance(servers_value, dict) or not servers_value:
        raise CatalogValidationError("MCP config must contain a non-empty 'mcpServers' object")

    configured_names = tuple(config.catalog.servers)
    mcp_names = tuple(servers_value)
    if mcp_names != configured_names:
        raise CatalogValidationError(
            "MCP server names/order must exactly match catalog.servers: "
            f"expected {list(configured_names)!r}, got {list(mcp_names)!r}"
        )

    hasher = hashlib.sha256()
    validated: list[CatalogServer] = []
    for server_name in configured_names:
        entry = servers_value[server_name]
        if not isinstance(entry, dict):
            raise CatalogValidationError(f"MCP configuration for {server_name} must be an object")
        unknown = set(entry).difference({"tool_path", "stateless"})
        if unknown:
            raise CatalogValidationError(
                f"MCP configuration for {server_name} has unknown keys: {', '.join(sorted(unknown))}"
            )
        if entry.get("stateless") is not False:
            raise CatalogValidationError(f"mini server {server_name} must set stateless=false")
        tool_path = _repo_file(
            config.repo_root, entry.get("tool_path"), label=f"tool_path for {server_name}"
        )
        if tool_path.stem != server_name:
            raise CatalogValidationError(
                f"tool filename mismatch for {server_name}: expected {server_name}.py, got {tool_path.name}"
            )
        metadata_path = config.catalog.metadata_dir / f"{server_name}_metadata.json"
        if not metadata_path.is_file():
            raise CatalogValidationError(f"metadata path does not exist for {server_name}: {metadata_path}")

        metadata = _load_json(metadata_path)
        metadata_names = _metadata_tool_names(metadata, server_name)
        _validate_no_http_client_imports(tool_path)
        registered_names = await _registered_tool_names(tool_path, server_name)
        public_registered = tuple(name for name in registered_names if name not in LIFECYCLE_TOOLS)
        if set(public_registered) != set(metadata_names) or len(public_registered) != len(metadata_names):
            raise CatalogValidationError(
                f"tool-name mismatch for {server_name}: metadata={list(metadata_names)!r}, "
                f"registered={list(public_registered)!r}"
            )

        normalized_metadata = json.dumps(
            metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        _digest_payload(hasher, f"{server_name}:metadata", normalized_metadata)
        _digest_payload(hasher, f"{server_name}:tool", tool_path.read_bytes())
        validated.append(
            CatalogServer(
                name=server_name,
                metadata_path=metadata_path,
                tool_path=tool_path,
                metadata=metadata,
                metadata_tool_names=metadata_names,
                registered_tool_names=registered_names,
            )
        )

    return CatalogReport(servers=tuple(validated), digest=hasher.hexdigest())


def validate_catalog(config: MiniConfig) -> CatalogReport:
    """Synchronous CLI-friendly wrapper for :func:`validate_catalog_async`."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(validate_catalog_async(config))
    raise RuntimeError("validate_catalog() cannot run inside an event loop; await validate_catalog_async()")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the offline MoLab mini MCP catalog")
    parser.add_argument("--config", required=True, help="Mini pipeline TOML path")
    parser.add_argument("--repo-root", help="Explicit EnvFactory repository root")
    parser.add_argument("--check", action="store_true", help="Run all catalog acceptance checks")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.check:
        parser.error("--check is required")
    try:
        config = load_config(args.config, repo_root=args.repo_root)
        report = validate_catalog(config)
    except (CatalogValidationError, ValueError) as exc:
        print(f"catalog check failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"catalog check passed: {report.server_count} servers, "
        f"{report.metadata_tool_count} metadata tools, sha256={report.digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CatalogReport",
    "CatalogServer",
    "CatalogValidationError",
    "LIFECYCLE_TOOLS",
    "main",
    "validate_catalog",
    "validate_catalog_async",
]
