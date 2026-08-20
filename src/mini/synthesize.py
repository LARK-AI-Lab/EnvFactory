"""Bounded, resumable trajectory synthesis for the MoLab mini profile."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from .artifacts import append_jsonl, atomic_write_json, atomic_write_text
from .build_graph import GraphBuildError, GraphBuildResult, load_cached_graph
from .catalog import CatalogReport, CatalogValidationError, validate_catalog_async
from .config import MiniConfig, MiniConfigError, load_config
from .doctor import collect_report
from .manifest import RunLock, RunLockError, RunManifest, utc_now


class SynthesisError(RuntimeError):
    """Raised for a safe, user-actionable synthesis failure."""


class TrajectoryValidationError(SynthesisError):
    """Raised when generated output is not a usable ToolQueryChain."""


@dataclass(frozen=True)
class SynthesisPreflight:
    graph_result: GraphBuildResult
    catalog: CatalogReport
    environment: dict[str, Any]
    model_identity: str
    config_sha256: str


@dataclass(frozen=True)
class RunPaths:
    root: Path
    manifest: Path
    resolved_config: Path
    environment: Path
    events: Path
    sampled_chains: Path
    completed: Path
    failed: Path
    lock: Path

    @classmethod
    def for_run(cls, config: MiniConfig, run_id: str) -> "RunPaths":
        root = (config.artifact_root / "runs" / run_id).resolve()
        runs_root = (config.artifact_root / "runs").resolve()
        if not root.is_relative_to(runs_root):
            raise SynthesisError("run output escapes the configured artifact root")
        return cls(
            root=root,
            manifest=root / "run_manifest.json",
            resolved_config=root / "resolved_config.toml",
            environment=root / "environment.json",
            events=root / "logs" / "events.jsonl",
            sampled_chains=root / "sampled_chains",
            completed=root / "trajectories" / "completed",
            failed=root / "trajectories" / "failed",
            lock=root / ".synthesis.lock",
        )


_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SECRET_PATTERN = re.compile(
    r"(?i)(authorization|api[_ -]?key|token|bearer)\s*[:=]\s*[^\s,;]+"
)


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _resolved_config_value(config: MiniConfig) -> dict[str, Any]:
    return json.loads(config.model_dump_json())


def config_compatibility_hash(config: MiniConfig) -> str:
    """Hash all resolved, non-secret structural/deployment configuration."""
    return _canonical_hash(_resolved_config_value(config))


def deterministic_seeds(run_seed: int, target: int) -> list[int]:
    if target <= 0:
        raise ValueError("target must be positive")
    return random.Random(run_seed).sample(range(2**31), target)


def _git_state(repo_root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
        )
        return commit or None, dirty
    except (OSError, subprocess.SubprocessError):
        return None, False


def make_run_id(config: MiniConfig, config_sha256: str) -> str:
    commit, _ = _git_state(config.repo_root)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"{stamp}-{commit or 'nogit'}-{config_sha256[:8]}"


def _validate_output_parent(config: MiniConfig) -> None:
    root = config.artifact_root.resolve()
    if root.exists() and not root.is_dir():
        raise SynthesisError(f"artifact root is not a directory: {root}")
    ancestor = root
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if not ancestor.is_dir() or not os.access(ancestor, os.W_OK):
        raise SynthesisError(f"artifact root is not writable: {root}")


async def production_preflight(
    config: MiniConfig,
    *,
    require_model_completion: bool = True,
    expected_model: str | None = None,
) -> SynthesisPreflight:
    """Validate the live runtime without creating a run directory."""
    _validate_output_parent(config)
    catalog = await validate_catalog_async(config)
    graph_result = load_cached_graph(config, catalog=catalog)

    if require_model_completion:
        models = [expected_model or config.teacher.model]
        if expected_model is None and config.teacher.fallback_model not in models:
            models.append(config.teacher.fallback_model)
        reports = []
        for model in models:
            report = collect_report(config, require_model=True, expected_model=model)
            reports.append(report)
            if report["compatible"]:
                break
    else:
        reports = [collect_report(config, require_model=False)]
    environment = next((report for report in reports if report["compatible"]), None)
    if environment is None:
        errors = reports[-1].get("errors", ["unknown doctor failure"])
        raise SynthesisError("MoLab doctor failed: " + "; ".join(errors))
    endpoint = environment.get("model_endpoint", {})
    identity = endpoint.get("returned_model") if require_model_completion else expected_model
    if identity not in {config.teacher.model, config.teacher.fallback_model}:
        raise SynthesisError(f"unexpected model identity: {identity!r}")
    return SynthesisPreflight(
        graph_result=graph_result,
        catalog=catalog,
        environment=environment,
        model_identity=identity,
        config_sha256=config_compatibility_hash(config),
    )


def _event(paths: RunPaths, run_id: str, operation: str, outcome: str, **values: Any) -> None:
    record = {
        "timestamp": utc_now(),
        "run_id": run_id,
        "stage": "synthesis",
        "operation": operation,
        "outcome": outcome,
    }
    record.update({key: value for key, value in values.items() if value is not None})
    append_jsonl(paths.events, record)


def _safe_message(exc: BaseException, secret_values: Sequence[str] = ()) -> str:
    message = str(exc).replace("\r", " ").replace("\n", " ")
    for secret in secret_values:
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return _SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", message)[:500]


def _is_transient(exc: BaseException, stage: str) -> bool:
    if stage not in {"model", "transport", "timeout"}:
        return False
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError, ConnectionError)):
        return True
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    return any(
        token in name or token in message
        for token in ("timeout", "connection", "transport", "ratelimit", "temporar", "unavailable")
    )


def _serialize_sample(seed: int, chain: Any) -> dict[str, Any]:
    tools = [tool.name for tool in chain.init_tool_chain]
    if not tools:
        raise TrajectoryValidationError("sampled chain contains no tools")
    return {
        "schema_version": 1,
        "seed": seed,
        "tool_names": tools,
        "servers": sorted({tool.server for tool in chain.init_tool_chain}),
    }


def _tool_map(graph: Any) -> dict[str, Any]:
    from src.graph.tool_node import Tool

    return {node.name: node for node in graph.graph.nodes if isinstance(node, Tool)}


def _load_sample(path: Path, graph: Any) -> Any:
    from src.graph.tool_chain import ToolQueryChain

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        seed = int(value["seed"])
        names = value["tool_names"]
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise TrajectoryValidationError(f"invalid sampled chain {path.name}: {exc}") from exc
    if not isinstance(names, list) or not names or any(not isinstance(name, str) for name in names):
        raise TrajectoryValidationError(f"invalid sampled tool names in {path.name}")
    mapping = _tool_map(graph)
    missing = [name for name in names if name not in mapping]
    if missing:
        raise TrajectoryValidationError(f"sample references unknown tools: {missing}")
    return ToolQueryChain([mapping[name] for name in names], seed=seed)


def _sample_chain(graph: Any, config: MiniConfig, seed: int) -> Any:
    from src.graph.sampler import TopologySampler

    for offset in range(100):
        sample_seed = (seed + offset * 1_000_003) % (2**31)
        chain = graph.sample(
            TopologySampler(), max_nodes=config.generation.max_nodes, seed=sample_seed
        )
        servers = {tool.server for tool in chain.init_tool_chain}
        if (
            chain.init_tool_chain
            and len(chain.init_tool_chain) <= config.generation.max_nodes
            and len(servers) <= config.generation.max_servers
        ):
            chain.seed = seed
            return chain
    raise TrajectoryValidationError(
        f"could not sample a chain within {config.generation.max_servers} servers"
    )


def _serialize_trajectory(chain: Any) -> dict[str, Any]:
    return {
        "nodes": [
            {
                **node.save(),
                "raw_tool_call": [tool.name for tool in node.raw_tool_call],
                "mcp_servers": sorted(node.mcp_servers),
            }
            for node in chain.tool_chain
        ],
        "seed": chain.seed,
        "scenario": chain.scenario,
        "user_tools": chain.user_tools,
        "user_profile": chain.user_profile,
        "sampled_tool_names": [tool.name for tool in chain.init_tool_chain],
        "mcp_servers": sorted(chain.mcp_servers),
    }


def validate_trajectory(chain: Any, allowed_tools: set[str]) -> dict[str, Any]:
    """Validate and serialize a generated chain before its immutable commit."""
    payload = _serialize_trajectory(chain)
    # Prove compatibility with the existing public deserializer.
    from src.graph.tool_chain import ToolQueryChain

    ToolQueryChain.load(payload)
    accepted = [node for node in chain.tool_chain if node.decision is True]
    if not accepted:
        raise TrajectoryValidationError("trajectory has no accepted node")
    tool_call_count = 0
    for node in accepted:
        referenced = set(node.mcp_servers)
        if not isinstance(node.initial_scenario, dict) or not all(
            server in node.initial_scenario for server in referenced
        ):
            raise TrajectoryValidationError("initial scenarios are incomplete")
        if not isinstance(node.final_scenario, dict) or not all(
            server in node.final_scenario and node.final_scenario[server] is not None
            for server in referenced
        ):
            raise TrajectoryValidationError("final scenarios are incomplete")
        expect_response = False
        for step in node.steps:
            role = step.get("role") if isinstance(step, dict) else None
            if expect_response:
                if role != "tool_response":
                    raise TrajectoryValidationError("tool calls and responses do not alternate")
                expect_response = False
                continue
            if role == "tool_response":
                raise TrajectoryValidationError("tool response has no preceding tool call")
            if role == "tool_call":
                calls = step.get("content")
                if not isinstance(calls, list) or not calls:
                    raise TrajectoryValidationError("tool_call step must contain calls")
                for call in calls:
                    name = call.get("name") if isinstance(call, dict) else None
                    if name not in allowed_tools:
                        raise TrajectoryValidationError(f"tool call is outside mini catalog: {name!r}")
                    tool_call_count += 1
                expect_response = True
        if expect_response:
            raise TrajectoryValidationError("trajectory ends before a tool response")
    if tool_call_count == 0:
        raise TrajectoryValidationError("trajectory contains no tool calls")
    return payload


def validate_trajectory_payload(payload: dict[str, Any], allowed_tools: set[str]) -> None:
    """Validate the durable subset needed to reconcile completed artifacts."""
    from src.graph.tool_chain import ToolQueryChain

    chain = ToolQueryChain.load(payload)
    accepted = [node for node in chain.tool_chain if node.decision is True]
    if not accepted:
        raise TrajectoryValidationError("completed trajectory has no accepted node")
    calls = 0
    for node_data in payload.get("nodes", []):
        referenced = set(node_data.get("mcp_servers") or [])
        initial = node_data.get("initial_scenario")
        final = node_data.get("final_scenario")
        if not isinstance(initial, dict) or not referenced.issubset(initial):
            raise TrajectoryValidationError("completed trajectory has incomplete initial scenarios")
        if not isinstance(final, dict) or any(final.get(server) is None for server in referenced):
            raise TrajectoryValidationError("completed trajectory has incomplete final scenarios")
        expect_response = False
        for step in node_data.get("steps") or []:
            role = step.get("role") if isinstance(step, dict) else None
            if expect_response:
                if role != "tool_response":
                    raise TrajectoryValidationError("completed steps do not alternate")
                expect_response = False
            elif role == "tool_response":
                raise TrajectoryValidationError("completed tool response is unpaired")
            elif role == "tool_call":
                content = step.get("content")
                if not isinstance(content, list) or not content:
                    raise TrajectoryValidationError("completed tool call is empty")
                for call in content:
                    if not isinstance(call, dict) or call.get("name") not in allowed_tools:
                        raise TrajectoryValidationError("completed trajectory references unknown tool")
                    calls += 1
                expect_response = True
        if expect_response:
            raise TrajectoryValidationError("completed tool call is unpaired")
    if calls == 0:
        raise TrajectoryValidationError("completed trajectory has no tool calls")


def _failure_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        records = value.get("failures", [])
        return records if isinstance(records, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _record_failure(
    paths: RunPaths,
    manifest: RunManifest,
    *,
    seed: int,
    stage: str,
    exc: BaseException,
    attempt: int,
    retryable: bool,
    secret_values: Sequence[str],
) -> None:
    record = {
        "stage": stage,
        "exception_class": type(exc).__name__,
        "safe_message": _safe_message(exc, secret_values),
        "retryable": retryable,
        "attempt": attempt,
        "timestamp": utc_now(),
    }
    destination = paths.failed / f"{seed}.json"
    records = _failure_records(destination)
    records.append(record)
    atomic_write_json(destination, {"schema_version": 1, "seed": seed, "failures": records})
    key = type(exc).__name__
    manifest.failure_summary[key] = manifest.failure_summary.get(key, 0) + 1
    _event(
        paths,
        manifest.run_id,
        "trajectory_failed",
        "retry" if retryable else "failed",
        seed=seed,
        retry_count=max(0, attempt - 1),
        exception_class=key,
        safe_message=record["safe_message"],
    )
    # A retry is scheduled only after both the failure artifact and manifest land.
    manifest.checkpoint(paths.manifest)


def _catalog_tool_names(catalog: CatalogReport) -> set[str]:
    return {
        f"{server.name}-{name}"
        for server in catalog.servers
        for name in server.metadata_tool_names
    }


def _reconcile_completed(
    paths: RunPaths, manifest: RunManifest, allowed_tools: set[str]
) -> None:
    completed: list[int] = []
    for seed in manifest.seeds:
        path = paths.completed / f"{seed}.json"
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("seed") != seed:
                raise TrajectoryValidationError("completed filename/seed mismatch")
            validate_trajectory_payload(payload, allowed_tools)
        except (OSError, json.JSONDecodeError, TrajectoryValidationError) as exc:
            raise SynthesisError(f"cannot resume with invalid completed artifact {path}: {exc}") from exc
        completed.append(seed)
    manifest.completed_seeds = completed
    manifest.valid_count = len(completed)
    completed_set = set(completed)
    failed: list[int] = []
    pending: list[int] = []
    for seed in manifest.seeds:
        if seed in completed_set:
            continue
        records = _failure_records(paths.failed / f"{seed}.json")
        if records:
            recorded_attempts = [
                record.get("attempt")
                for record in records
                if isinstance(record.get("attempt"), int)
            ]
            if recorded_attempts:
                manifest.attempts_by_seed[str(seed)] = max(
                    manifest.attempts_by_seed.get(str(seed), 0), max(recorded_attempts)
                )
        latest = records[-1] if records else None
        attempts = manifest.attempts_by_seed.get(str(seed), 0)
        can_retry = bool(
            latest
            and latest.get("retryable") is True
            and attempts < manifest.target_trajectories  # tightened by caller below
        )
        if latest and not can_retry:
            failed.append(seed)
        else:
            pending.append(seed)
    manifest.failed_seeds = failed
    manifest.pending_seeds = pending


def _default_generator_factory(
    config: MiniConfig, paths: RunPaths, graph: Any, model_identity: str
) -> Callable[[int], Any]:
    from src.gen.query_gen import QueryGen, QueryGenConfig

    secret = os.environ.get(config.teacher.api_key_env)
    if not secret:
        raise SynthesisError(f"required environment variable {config.teacher.api_key_env} is absent")
    os.environ["VLLM_BASE_URL"] = config.teacher.base_url
    os.environ["VLLM_API_KEY"] = secret
    os.environ["VLLM_MODEL"] = model_identity

    def factory(worker_id: int) -> Any:
        query_config = QueryGenConfig(
            model_name="vllm",
            pass_k=config.generation.pass_k,
            max_iterations=config.generation.max_iterations,
            max_solve_iterations=config.generation.max_solve_iterations,
            enable_split_turns=False,
            enable_query_refinement=config.generation.enable_query_refinement,
            enable_user_interaction=config.generation.enable_user_interaction,
            enable_user_tool_use=config.generation.enable_user_tool_use,
            enable_filteration=config.generation.enable_filteration,
            enable_log_thinking_content=False,
            log_folder=str(paths.root / "logs" / f"worker-{worker_id}"),
            save_folder=str(paths.completed),
            persist_trajectory=False,
        )
        return QueryGen(graph, query_config)

    return factory


async def _monitor_resources(
    manifest: RunManifest, paths: RunPaths, stop: asyncio.Event, interval: float
) -> None:
    while not stop.is_set():
        try:
            import psutil

            rss = psutil.Process().memory_info().rss
            manifest.peak_host_rss_bytes = max(manifest.peak_host_rss_bytes or 0, rss)
        except Exception:
            pass
        try:
            import pynvml

            pynvml.nvmlInit()
            try:
                used = pynvml.nvmlDeviceGetMemoryInfo(
                    pynvml.nvmlDeviceGetHandleByIndex(0)
                ).used
                manifest.peak_gpu_memory_bytes = max(
                    manifest.peak_gpu_memory_bytes or 0, used
                )
            finally:
                pynvml.nvmlShutdown()
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except TimeoutError:
            continue


def _write_resolved_config(path: Path, config: MiniConfig) -> None:
    try:
        import toml

        rendered = toml.dumps(_resolved_config_value(config))
    except Exception as exc:
        raise SynthesisError(f"could not render resolved configuration: {exc}") from exc
    atomic_write_text(path, rendered)


async def synthesize(
    config: MiniConfig,
    *,
    target: int,
    workers: int,
    run_id: str | None = None,
    resume: bool = False,
    recover_stale_lock: bool = False,
    preflight: SynthesisPreflight | None = None,
    generator_factory: Callable[[int], Any] | None = None,
    stop_event: asyncio.Event | None = None,
    monitor_interval: float = 10.0,
    initialize_mcp: bool = True,
) -> RunManifest:
    """Run or resume synthesis with bounded concurrency and durable checkpoints."""
    if target <= 0:
        raise SynthesisError("target must be positive")
    if workers <= 0 or workers > 4:
        raise SynthesisError("workers must be between 1 and 4")
    if resume and not run_id:
        raise SynthesisError("--resume requires --run-id")
    if run_id is not None and not _RUN_ID.fullmatch(run_id):
        raise SynthesisError("run ID contains unsafe characters")
    if preflight is None:
        expected_model = None
        require_model_completion = True
        if resume and run_id:
            tentative_paths = RunPaths.for_run(config, run_id)
            if tentative_paths.manifest.exists():
                tentative = RunManifest.load(tentative_paths.manifest)
                if (
                    tentative.state == "completed"
                    and len(tentative.completed_seeds) == target
                ):
                    expected_model = tentative.teacher_model
                    require_model_completion = False
        preflight = await production_preflight(
            config,
            require_model_completion=require_model_completion,
            expected_model=expected_model,
        )
    run_id = run_id or make_run_id(config, preflight.config_sha256)
    if not _RUN_ID.fullmatch(run_id):
        raise SynthesisError("run ID contains unsafe characters")
    paths = RunPaths.for_run(config, run_id)
    allowed_tools = _catalog_tool_names(preflight.catalog)
    graph_sha = preflight.graph_result.manifest.get("output_sha256")
    if not isinstance(graph_sha, str):
        raise SynthesisError("graph manifest has no output SHA-256")
    secret_values = [os.environ.get(config.teacher.api_key_env, "")]

    with RunLock(paths.lock, recover_stale=recover_stale_lock):
        exists = paths.manifest.exists()
        if exists and not resume:
            raise SynthesisError(f"run already exists; use --resume: {run_id}")
        if resume and not exists:
            raise SynthesisError(f"run manifest does not exist: {run_id}")

        if exists:
            manifest = RunManifest.load(paths.manifest)
            # monotonic clocks are process-local and may reset across sessions;
            # preserve accumulated elapsed time while starting a fresh baseline.
            manifest.started_monotonic_seconds = time.monotonic() - manifest.elapsed_seconds
            mismatches = []
            for label, old, new in (
                ("configuration", manifest.config_sha256, preflight.config_sha256),
                ("graph", manifest.graph_sha256, graph_sha),
                ("catalog", manifest.catalog_sha256, preflight.catalog.digest),
                ("model", manifest.teacher_model, preflight.model_identity),
                ("target", manifest.target_trajectories, target),
            ):
                if old != new:
                    mismatches.append(label)
            if mismatches:
                raise SynthesisError(
                    "resume compatibility check failed for: " + ", ".join(mismatches)
                )
            _reconcile_completed(paths, manifest, allowed_tools)
            # Apply the configured retry ceiling after disk reconciliation.
            pending: list[int] = []
            failed: list[int] = []
            for seed in manifest.seeds:
                if seed in manifest.completed_seeds:
                    continue
                records = _failure_records(paths.failed / f"{seed}.json")
                latest = records[-1] if records else None
                attempts = manifest.attempts_by_seed.get(str(seed), 0)
                if latest and (
                    latest.get("retryable") is not True
                    or attempts >= config.generation.max_attempts_per_seed
                ):
                    failed.append(seed)
                else:
                    pending.append(seed)
            manifest.failed_seeds = failed
            manifest.pending_seeds = pending
        else:
            commit, dirty = _git_state(config.repo_root)
            seeds = deterministic_seeds(config.run_seed, target)
            manifest = RunManifest.create(
                run_id=run_id,
                config_sha256=preflight.config_sha256,
                graph_sha256=graph_sha,
                catalog_sha256=preflight.catalog.digest,
                teacher_model=preflight.model_identity,
                target_trajectories=target,
                seeds=seeds,
                git_commit=commit,
                git_dirty=dirty,
                environment=preflight.environment,
            )
            _write_resolved_config(paths.resolved_config, config)
            atomic_write_json(paths.environment, preflight.environment)
            manifest.checkpoint(paths.manifest)
            _event(paths, run_id, "run_created", "created", target=target, workers=workers)

        if len(manifest.completed_seeds) == target:
            manifest.state = "completed"
            manifest.completed_at = manifest.completed_at or utc_now()
            manifest.pending_seeds = []
            manifest.failed_seeds = []
            manifest.checkpoint(paths.manifest)
            _event(paths, run_id, "resume", "already_completed")
            return manifest

        manifest.state = "running"
        manifest.completed_at = None
        manifest.checkpoint(paths.manifest)
        _event(paths, run_id, "run_state", "running")

        from src.manager.mcp_client_manager import MCPManager

        if initialize_mcp:
            resolved_mcp = {
                "mcpServers": {
                    server.name: {
                        "tool_path": str(server.tool_path.resolve()),
                        "stateless": False,
                    }
                    for server in preflight.catalog.servers
                }
            }
            resolved_mcp_path = paths.root / "resolved_mcp_server.json"
            atomic_write_json(resolved_mcp_path, resolved_mcp)
            MCPManager.init_config(resolved_mcp_path, overwrite=True)
        factory = generator_factory or _default_generator_factory(
            config,
            paths,
            preflight.graph_result.graph,
            preflight.model_identity,
        )
        stop = stop_event or asyncio.Event()
        monitor_stop = asyncio.Event()
        monitor = asyncio.create_task(
            _monitor_resources(manifest, paths, monitor_stop, monitor_interval)
        )
        queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=max(2, workers * 2))
        progress_lock = asyncio.Lock()

        async def producer() -> None:
            for seed in list(manifest.pending_seeds):
                if stop.is_set():
                    break
                sample_path = paths.sampled_chains / f"{seed}.json"
                if not sample_path.exists():
                    try:
                        chain = _sample_chain(preflight.graph_result.graph, config, seed)
                        atomic_write_json(
                            sample_path, _serialize_sample(seed, chain), overwrite=False
                        )
                    except Exception as exc:
                        if seed not in manifest.failed_seeds:
                            manifest.failed_seeds.append(seed)
                            manifest.failed_seeds.sort(key=manifest.seeds.index)
                        if seed in manifest.pending_seeds:
                            manifest.pending_seeds.remove(seed)
                        _record_failure(
                            paths,
                            manifest,
                            seed=seed,
                            stage="sampling",
                            exc=exc,
                            attempt=1,
                            retryable=False,
                            secret_values=secret_values,
                        )
                        continue
                    _event(paths, run_id, "chain_sampled", "completed", seed=seed)
                await queue.put(seed)
            for _ in range(workers):
                await queue.put(None)

        async def worker(worker_id: int) -> None:
            generator = factory(worker_id)
            while True:
                seed = await queue.get()
                try:
                    if seed is None:
                        return
                    if stop.is_set():
                        continue
                    sample_path = paths.sampled_chains / f"{seed}.json"
                    start_attempt = manifest.attempts_by_seed.get(str(seed), 0) + 1
                    for attempt in range(
                        start_attempt, config.generation.max_attempts_per_seed + 1
                    ):
                        if stop.is_set():
                            break
                        manifest.attempts_by_seed[str(seed)] = attempt
                        manifest.attempted_count += 1
                        if attempt > 1:
                            manifest.retried_count += 1
                        started = time.monotonic()
                        _event(
                            paths,
                            run_id,
                            "trajectory_started",
                            "running",
                            seed=seed,
                            worker_id=worker_id,
                            retry_count=attempt - 1,
                        )
                        stage = "model"
                        try:
                            # Every retry starts from the immutable sampled
                            # chain; partial model/MCP state is never reused.
                            chain = _load_sample(
                                sample_path, preflight.graph_result.graph
                            )
                            if hasattr(generator, "reset_run_state"):
                                generator.reset_run_state()
                            result = await generator.gen(chain)
                            stage = "validation"
                            payload = validate_trajectory(result, allowed_tools)
                            stage = "persistence"
                            atomic_write_json(
                                paths.completed / f"{seed}.json", payload, overwrite=False
                            )
                        except BaseException as exc:
                            if isinstance(exc, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)):
                                raise
                            retryable = _is_transient(exc, stage) and (
                                attempt < config.generation.max_attempts_per_seed
                            )
                            _record_failure(
                                paths,
                                manifest,
                                seed=seed,
                                stage=stage,
                                exc=exc,
                                attempt=attempt,
                                retryable=retryable,
                                secret_values=secret_values,
                            )
                            if retryable:
                                continue
                            if seed not in manifest.failed_seeds:
                                manifest.failed_seeds.append(seed)
                                manifest.failed_seeds.sort(key=manifest.seeds.index)
                            if seed in manifest.pending_seeds:
                                manifest.pending_seeds.remove(seed)
                            manifest.checkpoint(paths.manifest)
                            break
                        else:
                            async with progress_lock:
                                if seed not in manifest.completed_seeds:
                                    manifest.completed_seeds.append(seed)
                                    manifest.completed_seeds.sort(key=manifest.seeds.index)
                                manifest.valid_count = len(manifest.completed_seeds)
                                if seed in manifest.failed_seeds:
                                    manifest.failed_seeds.remove(seed)
                                if seed in manifest.pending_seeds:
                                    manifest.pending_seeds.remove(seed)
                                manifest.checkpoint(paths.manifest)
                                _event(
                                    paths,
                                    run_id,
                                    "trajectory_completed",
                                    "completed",
                                    seed=seed,
                                    worker_id=worker_id,
                                    duration=time.monotonic() - started,
                                    retry_count=attempt - 1,
                                )
                                print(
                                    f"[{run_id}] completed {len(manifest.completed_seeds)}/{target} "
                                    f"(failed {len(manifest.failed_seeds)})",
                                    flush=True,
                                )
                            break
                        finally:
                            if hasattr(generator, "reset_run_state"):
                                generator.reset_run_state()
                finally:
                    queue.task_done()

        tasks = [asyncio.create_task(producer())]
        tasks.extend(asyncio.create_task(worker(index)) for index in range(workers))
        fatal: BaseException | None = None
        try:
            await asyncio.gather(*tasks)
        except BaseException as exc:
            fatal = exc
            stop.set()
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            monitor_stop.set()
            await monitor
            # QueryGen closes per-seed clients; this is a final safety net after
            # every worker has stopped, so it cannot disrupt another worker.
            if initialize_mcp:
                try:
                    await MCPManager.aclose_all_clients()
                except Exception:
                    pass

        if fatal is not None:
            manifest.state = "interrupted" if isinstance(
                fatal, (KeyboardInterrupt, asyncio.CancelledError)
            ) else "failed"
            manifest.checkpoint(paths.manifest)
            _event(
                paths,
                run_id,
                "run_state",
                manifest.state,
                exception_class=type(fatal).__name__,
                safe_message=_safe_message(fatal, secret_values),
            )
            if isinstance(fatal, asyncio.CancelledError):
                return manifest
            raise fatal

        if stop.is_set():
            manifest.state = "interrupted"
        elif len(manifest.completed_seeds) == target:
            manifest.state = "completed"
            manifest.completed_at = utc_now()
        else:
            manifest.state = "failed"
        manifest.checkpoint(paths.manifest)
        _event(paths, run_id, "run_state", manifest.state)
        return manifest


def _install_signal_handlers(loop: asyncio.AbstractEventLoop, stop: asyncio.Event) -> None:
    def request_stop() -> None:
        if not stop.is_set():
            print("shutdown requested; finishing in-flight atomic writes...", file=sys.stderr)
            stop.set()

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, request_stop)
        except (NotImplementedError, RuntimeError):
            signal.signal(signum, lambda *_: loop.call_soon_threadsafe(request_stop))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run resumable MoLab mini synthesis")
    parser.add_argument("--config", required=True, help="Mini pipeline TOML path")
    parser.add_argument("--repo-root", help="Explicit EnvFactory repository root")
    parser.add_argument("--run-id", help="Existing run identifier for resume")
    parser.add_argument("--target", type=int, help="Requested unique trajectory count")
    parser.add_argument("--workers", type=int, help="Bounded generation worker count")
    parser.add_argument("--resume", action="store_true", help="Resume an existing run")
    parser.add_argument(
        "--recover-stale-lock",
        action="store_true",
        help="Replace a verified non-live run lock",
    )
    return parser


async def _async_main(args: argparse.Namespace) -> RunManifest:
    config = load_config(args.config, repo_root=args.repo_root)
    target = args.target or config.generation.target_trajectories
    workers = args.workers or config.generation.workers
    stop = asyncio.Event()
    _install_signal_handlers(asyncio.get_running_loop(), stop)
    return await synthesize(
        config,
        target=target,
        workers=workers,
        run_id=args.run_id,
        resume=args.resume,
        recover_stale_lock=args.recover_stale_lock,
        stop_event=stop,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        manifest = asyncio.run(_async_main(args))
    except (
        CatalogValidationError,
        GraphBuildError,
        MiniConfigError,
        RunLockError,
        SynthesisError,
        ValueError,
    ) as exc:
        print(f"synthesis failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"run {manifest.run_id}: {manifest.state}; "
        f"completed={len(manifest.completed_seeds)}, failed={len(manifest.failed_seeds)}, "
        f"pending={len(manifest.pending_seeds)}"
    )
    return 0 if manifest.state == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "RunPaths",
    "SynthesisError",
    "SynthesisPreflight",
    "TrajectoryValidationError",
    "config_compatibility_hash",
    "deterministic_seeds",
    "main",
    "production_preflight",
    "synthesize",
    "validate_trajectory",
    "validate_trajectory_payload",
]
