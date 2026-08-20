"""Build, validate, and cache the audited MoLab mini tool graph."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

from src.graph.embedding import (
    CachedEmbeddingBackend,
    EmbeddingBackend,
    EmbeddingError,
    HTTPEmbeddingBackend,
    SentenceTransformersBackend,
)
from src.graph.tool_node import Parameter, Tool

from .catalog import CatalogReport, CatalogValidationError, LIFECYCLE_TOOLS, validate_catalog
from .classification import (
    CachedUserProvidedClassifier,
    ClassificationError,
    TeacherUserProvidedClassifier,
    UserProvidedClassifier,
)
from .config import MiniConfig, MiniConfigError, load_config

if TYPE_CHECKING:
    from src.graph.tool_graph import ToolGraph


class GraphBuildError(RuntimeError):
    """Raised when graph inputs, construction, or acceptance checks fail."""


class LiveGraphDependencyError(GraphBuildError):
    """Raised when a configured live backend is unavailable."""


@dataclass(frozen=True)
class GraphBuildResult:
    graph: ToolGraph
    manifest: dict[str, Any]
    cached: bool


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _manifest_path(path: Path, repo_root: Path) -> str:
    """Prefer a portable repository-relative path, allowing external artifact roots."""
    if path.is_relative_to(repo_root):
        return path.relative_to(repo_root).as_posix()
    return str(path)


def _embedding_identity(config: MiniConfig) -> str:
    graph = config.graph
    if graph.embedding_backend == "sentence_transformers":
        return f"sentence-transformers:{graph.embedding_model}@{graph.embedding_device}"
    url = os.environ.get("EMBEDDING_URL", "").rstrip("/")
    if not url:
        raise LiveGraphDependencyError("HTTP embedding backend requires EMBEDDING_URL")
    return f"http:{graph.embedding_model}@{url}"


def _teacher_descriptor(config: MiniConfig) -> TeacherUserProvidedClassifier:
    # The placeholder is retained only in this private object and is never used
    # for a request. It lets dry runs/fingerprint checks remain credential-free.
    return TeacherUserProvidedClassifier(
        base_url=config.teacher.base_url,
        api_key="unused-local-placeholder",
        model=config.teacher.model,
        seed=config.run_seed,
    )


def _input_record(
    config: MiniConfig,
    catalog: CatalogReport,
    *,
    embedding_identity: str,
    classifier_identity: str | None,
    classifier_settings: dict[str, Any] | None,
) -> dict[str, Any]:
    files: list[dict[str, str]] = [
        {
            "kind": "mcp_config",
            "path": config.catalog.mcp_config.relative_to(config.repo_root).as_posix(),
            "sha256": _sha256_file(config.catalog.mcp_config),
        }
    ]
    for server in catalog.servers:
        files.extend(
            [
                {
                    "kind": "metadata",
                    "server": server.name,
                    "path": server.metadata_path.relative_to(config.repo_root).as_posix(),
                    "sha256": _sha256_file(server.metadata_path),
                },
                {
                    "kind": "tool",
                    "server": server.name,
                    "path": server.tool_path.relative_to(config.repo_root).as_posix(),
                    "sha256": _sha256_file(server.tool_path),
                },
            ]
        )
    settings = {
        "ignore_tool_class": False,
        "build_edge_threshold": 0.85,
        "merge_param_threshold": 0.92,
        "enable_parameter_merge": config.graph.enable_parameter_merge,
        "enable_llm_edges": config.graph.enable_llm_edges,
        "classify_user_provided": config.graph.classify_user_provided,
        "embedding_backend_identity": embedding_identity,
        "classifier_identity": classifier_identity,
        "classifier_settings": classifier_settings,
    }
    record = {
        "config_sha256": _sha256_file(config.config_path),
        "catalog_sha256": catalog.digest,
        "files": files,
        "settings": settings,
    }
    record["build_fingerprint"] = _canonical_hash(record)
    return record


def _validate_output_paths(config: MiniConfig) -> None:
    paths = (
        config.graph.path,
        config.graph.manifest_path,
        config.graph.embedding_cache,
        config.graph.user_provided_cache,
    )
    for path in paths:
        if not path.is_relative_to(config.artifact_root):
            raise GraphBuildError(f"graph artifact path is outside artifact_root: {path}")
    if len(set(paths)) != len(paths):
        raise GraphBuildError("graph output and cache paths must be distinct")


def _make_embedding_backend(config: MiniConfig) -> EmbeddingBackend:
    graph = config.graph
    if graph.embedding_backend == "sentence_transformers":
        return SentenceTransformersBackend(
            graph.embedding_model,
            device=graph.embedding_device,
            batch_size=graph.embedding_batch_size,
        )
    try:
        return HTTPEmbeddingBackend.from_environment(
            model=graph.embedding_model, batch_size=graph.embedding_batch_size
        )
    except Exception as exc:
        raise LiveGraphDependencyError(str(exc)) from exc


def _make_classifier(config: MiniConfig) -> UserProvidedClassifier:
    api_key = os.environ.get(config.teacher.api_key_env)
    if not api_key:
        raise LiveGraphDependencyError(
            f"teacher classification requires environment variable {config.teacher.api_key_env}"
        )
    return TeacherUserProvidedClassifier(
        base_url=config.teacher.base_url,
        api_key=api_key,
        model=config.teacher.model,
        seed=config.run_seed,
    )


def _graph_counts(graph: ToolGraph) -> dict[str, int]:
    return {
        "servers": len(graph.server_to_tools),
        "tools": sum(isinstance(node, Tool) for node in graph.graph.nodes),
        "parameters": sum(isinstance(node, Parameter) for node in graph.graph.nodes),
        "nodes": graph.graph.number_of_nodes(),
        "edges": graph.graph.number_of_edges(),
    }


def validate_graph(
    graph: ToolGraph,
    catalog: CatalogReport,
    config: MiniConfig,
    *,
    sampling_seeds: int = 100,
) -> dict[str, int]:
    """Apply the static and deterministic-sampling graph acceptance checks."""
    from src.graph.sampler import TopologySampler
    from src.graph.tool_graph import EdgeType

    allowed_servers = {server.name for server in catalog.servers}
    expected_tools = {
        f"{server.name}-{name}"
        for server in catalog.servers
        for name in server.metadata_tool_names
    }
    tools = [node for node in graph.graph.nodes if isinstance(node, Tool)]
    actual_tools = {tool.name for tool in tools}
    if actual_tools != expected_tools or len(tools) != len(expected_tools):
        missing = sorted(expected_tools - actual_tools)
        extra = sorted(actual_tools - expected_tools)
        raise GraphBuildError(f"graph tool mismatch; missing={missing}, extra={extra}")
    invalid_servers = sorted({tool.server for tool in tools} - allowed_servers)
    if invalid_servers:
        raise GraphBuildError(f"graph contains disallowed servers: {invalid_servers}")
    lifecycle_nodes = sorted(
        tool.name for tool in tools if tool.name.rsplit("-", 1)[-1] in LIFECYCLE_TOOLS
    )
    if lifecycle_nodes:
        raise GraphBuildError(f"graph contains lifecycle tools: {lifecycle_nodes}")

    for tool in tools:
        for parameter in tool.input_schema["parameters"]:
            edge = graph.graph.get_edge_data(parameter, tool) or {}
            if not edge.get("required", False) or parameter.user_provided is True:
                continue
            reachable = False
            for provider in tools:
                direct = graph.graph.get_edge_data(provider, parameter) or {}
                if direct.get("edge_type") == EdgeType.Tool_Output:
                    reachable = True
                    break
                if any(
                    (graph.graph.get_edge_data(output, parameter) or {}).get("edge_type")
                    == EdgeType.Parameter_Relate
                    for output in provider.output_schema["parameters"]
                ):
                    reachable = True
                    break
            if not reachable:
                raise GraphBuildError(
                    f"required parameter is neither user-provided nor tool-reachable: "
                    f"{tool.name}.{parameter.name}"
                )

    sampler = TopologySampler(max_servers=config.generation.max_servers)
    for seed in range(sampling_seeds):
        chain = graph.sample(sampler, max_nodes=config.generation.max_nodes, seed=seed)
        sampled = chain.init_tool_chain
        if len(sampled) > config.generation.max_nodes:
            raise GraphBuildError(f"seed {seed} sampled too many tools: {len(sampled)}")
        servers = {tool.server for tool in sampled}
        if len(servers) > config.generation.max_servers:
            raise GraphBuildError(f"seed {seed} sampled too many servers: {len(servers)}")
        if any(tool.name.rsplit("-", 1)[-1] in LIFECYCLE_TOOLS for tool in sampled):
            raise GraphBuildError(f"seed {seed} sampled a lifecycle tool")
        if not graph.validate_tool_chain(sampled):
            raise GraphBuildError(f"seed {seed} produced an invalid dependency chain")
    return _graph_counts(graph)


def _atomic_save_graph(graph: ToolGraph, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        graph.save(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write_json(destination: Path, value: object) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _load_cached_graph(config: MiniConfig, inputs: dict[str, Any]) -> GraphBuildResult | None:
    graph_exists = config.graph.path.exists()
    manifest_exists = config.graph.manifest_path.exists()
    if not graph_exists and not manifest_exists:
        return None
    if graph_exists != manifest_exists:
        raise GraphBuildError("graph cache is incomplete; use --force to rebuild it")
    try:
        manifest = json.loads(config.graph.manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GraphBuildError(f"cannot read graph manifest: {exc}") from exc
    if manifest.get("inputs", {}).get("build_fingerprint") != inputs["build_fingerprint"]:
        raise GraphBuildError("graph inputs changed; use --force to rebuild")
    actual_hash = _sha256_file(config.graph.path)
    if manifest.get("output_sha256") != actual_hash:
        raise GraphBuildError("graph output hash does not match its trusted manifest")
    # Pickle loading occurs only after both current-input and output hashes pass.
    from src.graph.tool_graph import ToolGraph

    graph = ToolGraph.load(config.graph.path)
    return GraphBuildResult(graph=graph, manifest=manifest, cached=True)


def load_cached_graph(
    config: MiniConfig, *, catalog: CatalogReport | None = None
) -> GraphBuildResult:
    """Load only a trusted, current graph cache without performing live work."""
    _validate_output_paths(config)
    catalog = catalog or validate_catalog(config)
    classifier_descriptor = (
        _teacher_descriptor(config) if config.graph.classify_user_provided else None
    )
    inputs = _input_record(
        config,
        catalog,
        embedding_identity=_embedding_identity(config),
        classifier_identity=(classifier_descriptor.identity if classifier_descriptor else None),
        classifier_settings=(classifier_descriptor.settings if classifier_descriptor else None),
    )
    result = _load_cached_graph(config, inputs)
    if result is None:
        raise GraphBuildError(
            "trusted graph cache is missing; run python -m src.mini.build_graph first"
        )
    validate_graph(result.graph, catalog, config)
    return result


def build_graph(
    config: MiniConfig,
    *,
    catalog: CatalogReport | None = None,
    embedding_backend: EmbeddingBackend | None = None,
    user_classifier: UserProvidedClassifier | None = None,
    force: bool = False,
) -> GraphBuildResult:
    """Build or safely reuse the graph described by a resolved mini config."""
    _validate_output_paths(config)
    catalog = catalog or validate_catalog(config)
    embedding_identity = (
        embedding_backend.identity if embedding_backend is not None else _embedding_identity(config)
    )
    classifier_descriptor = None
    if config.graph.classify_user_provided:
        classifier_descriptor = user_classifier or _teacher_descriptor(config)
    inputs = _input_record(
        config,
        catalog,
        embedding_identity=embedding_identity,
        classifier_identity=(classifier_descriptor.identity if classifier_descriptor else None),
        classifier_settings=(classifier_descriptor.settings if classifier_descriptor else None),
    )

    if not force:
        cached = _load_cached_graph(config, inputs)
        if cached is not None:
            validate_graph(cached.graph, catalog, config)
            return cached

    raw_backend = embedding_backend or _make_embedding_backend(config)
    cached_backend = CachedEmbeddingBackend(raw_backend, config.graph.embedding_cache)
    cached_classifier = None
    if config.graph.classify_user_provided:
        raw_classifier = user_classifier or _make_classifier(config)
        cached_classifier = CachedUserProvidedClassifier(
            raw_classifier, config.graph.user_provided_cache
        )

    started = time.monotonic()
    from src.graph.tool_graph import ToolGraph

    graph = ToolGraph()
    graph.build_tool_graph(
        [server.metadata for server in catalog.servers],
        enable_merge=config.graph.enable_parameter_merge,
        enable_build_edge_with_llm=config.graph.enable_llm_edges,
        embedding_backend=cached_backend,
        user_provided_classifier=cached_classifier,
        classify_user_provided=config.graph.classify_user_provided,
    )
    counts = validate_graph(graph, catalog, config)
    _atomic_save_graph(graph, config.graph.path)
    output_hash = _sha256_file(config.graph.path)
    duration = time.monotonic() - started
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "counts": counts,
        "sampling_validation_seeds": 100,
        "duration_seconds": duration,
        "embedding_cache": {
            "hits": cached_backend.hits,
            "misses": cached_backend.misses,
        },
        "classification_cache": None
        if cached_classifier is None
        else {"hits": cached_classifier.hits, "misses": cached_classifier.misses},
        "output_path": _manifest_path(config.graph.path, config.repo_root),
        "output_sha256": output_hash,
    }
    _atomic_write_json(config.graph.manifest_path, manifest)
    return GraphBuildResult(graph=graph, manifest=manifest, cached=False)


def dry_run(config: MiniConfig) -> tuple[CatalogReport, list[str]]:
    """Validate static graph inputs without loading models or writing artifacts."""
    _validate_output_paths(config)
    catalog = validate_catalog(config)
    _embedding_identity(config)
    unmet: list[str] = []
    if config.graph.classify_user_provided:
        unmet.append(
            f"teacher classification endpoint ({config.teacher.model} at {config.teacher.base_url})"
        )
    return catalog, unmet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the cached MoLab mini tool graph")
    parser.add_argument("--config", required=True, help="Mini pipeline TOML path")
    parser.add_argument("--repo-root", help="Explicit EnvFactory repository root")
    parser.add_argument("--force", action="store_true", help="Replace a stale/current graph")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate inputs without loading models or writing"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        config = load_config(args.config, repo_root=args.repo_root)
        if args.dry_run:
            catalog, unmet = dry_run(config)
            dependency = ", ".join(unmet) if unmet else "none"
            print(
                f"graph dry run passed: {catalog.server_count} servers, "
                f"{catalog.metadata_tool_count} tools; unmet live dependencies: {dependency}"
            )
            return 0
        result = build_graph(config, force=args.force)
    except (
        CatalogValidationError,
        ClassificationError,
        EmbeddingError,
        GraphBuildError,
        MiniConfigError,
        ValueError,
    ) as exc:
        print(f"graph build failed: {exc}", file=sys.stderr)
        return 1
    counts = result.manifest["counts"]
    state = "cache hit" if result.cached else "built"
    print(
        f"graph {state}: {counts['tools']} tools, {counts['parameters']} parameters, "
        f"{counts['edges']} edges, sha256={result.manifest['output_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "GraphBuildError",
    "GraphBuildResult",
    "LiveGraphDependencyError",
    "build_graph",
    "dry_run",
    "load_cached_graph",
    "main",
    "validate_graph",
]
