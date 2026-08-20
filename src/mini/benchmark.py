"""Reproducible resource benchmarks for MoLab mini hardening work.

The supported benchmarks measure fixed-catalog MCP registration and identical-
seed generation worker sweeps.  Resulting JSON contains no prompts, scenario
data, environment variables, or command-line secrets.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import platform
import re
import statistics
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Sequence, TypeVar

from src.mini.artifacts import atomic_write_json, atomic_write_text, read_jsonl
from src.mini.config import MiniConfigError, load_config

try:
    import psutil
except ImportError:  # pragma: no cover - exercised by the minimal-runtime guard
    psutil = None  # type: ignore[assignment]


class BenchmarkError(RuntimeError):
    """Raised when a benchmark cannot produce trustworthy measurements."""


T = TypeVar("T")
_BENCHMARK_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,47}\Z")
_SECRET_NAME = re.compile(r"(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)
_SECRET_VALUE = re.compile(
    r"(?i)(api[_-]?key|token|authorization|password|secret)\s*[:=]\s*[^\s,;]+"
)


def _safe_error_message(exc: BaseException) -> str:
    message = str(exc).replace("\r", " ").replace("\n", " ")
    for name, value in os.environ.items():
        if _SECRET_NAME.search(name) and len(value) >= 8:
            message = message.replace(value, "[REDACTED]")
    return _SECRET_VALUE.sub(lambda match: f"{match.group(1)}=[REDACTED]", message)[:500]


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


@dataclass(frozen=True)
class ResourceMeasurement:
    wall_seconds: float
    monotonic_seconds: float
    cpu_percent_average: float | None
    cpu_percent_peak: float | None
    peak_rss_bytes: int
    child_processes_before: int
    child_processes_peak: int
    child_processes_after: int
    gpu_utilization_percent_peak: float | None
    gpu_memory_used_bytes_peak: int | None
    gpu_temperature_celsius_peak: float | None
    sample_count: int


class _ResourceSampler:
    """Sample one process tree without retaining subprocess output or arguments."""

    def __init__(self, interval_seconds: float = 0.01):
        if psutil is None:
            raise BenchmarkError(
                "psutil is required for benchmarks; install the development or MoLab requirements"
            )
        if interval_seconds <= 0:
            raise ValueError("sample interval must be positive")
        self.interval_seconds = interval_seconds
        self.process = psutil.Process()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.cpu_samples: list[float] = []
        self.peak_rss_bytes = 0
        self.peak_children = 0
        self.gpu_utilization_peak: float | None = None
        self.gpu_memory_peak: int | None = None
        self.gpu_temperature_peak: float | None = None
        self._nvml: Any = None
        self._gpu_handle: Any = None

    def _start_gpu(self) -> None:
        try:
            import pynvml

            pynvml.nvmlInit()
            self._nvml = pynvml
            self._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        except Exception:
            self._nvml = None
            self._gpu_handle = None

    def _sample_gpu(self) -> None:
        if self._nvml is None or self._gpu_handle is None:
            return
        try:
            utilization = self._nvml.nvmlDeviceGetUtilizationRates(self._gpu_handle)
            memory = self._nvml.nvmlDeviceGetMemoryInfo(self._gpu_handle)
            temperature = self._nvml.nvmlDeviceGetTemperature(
                self._gpu_handle, self._nvml.NVML_TEMPERATURE_GPU
            )
            self.gpu_utilization_peak = max(
                self.gpu_utilization_peak or 0.0, float(utilization.gpu)
            )
            self.gpu_memory_peak = max(self.gpu_memory_peak or 0, int(memory.used))
            self.gpu_temperature_peak = max(
                self.gpu_temperature_peak or 0.0, float(temperature)
            )
        except Exception:
            return

    def _sample(self) -> None:
        try:
            children = self.process.children(recursive=True)
            processes = [self.process, *children]
            rss = 0
            for process in processes:
                try:
                    rss += int(process.memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
            self.peak_children = max(self.peak_children, len(children))
            self.cpu_samples.append(float(psutil.cpu_percent(interval=None)))
            self._sample_gpu()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return

    def _run(self) -> None:
        while not self.stop_event.wait(self.interval_seconds):
            self._sample()

    def start(self) -> int:
        self._start_gpu()
        psutil.cpu_percent(interval=None)
        before = len(self.process.children(recursive=True))
        self._sample()
        self.thread = threading.Thread(
            target=self._run, name="mini-benchmark-sampler", daemon=True
        )
        self.thread.start()
        return before

    def finish(self, before: int, wall_seconds: float, monotonic_seconds: float) -> ResourceMeasurement:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=max(1.0, self.interval_seconds * 5))
        self._sample()
        after = len(self.process.children(recursive=True))
        if self._nvml is not None:
            try:
                self._nvml.nvmlShutdown()
            except Exception:
                pass
        return ResourceMeasurement(
            wall_seconds=wall_seconds,
            monotonic_seconds=monotonic_seconds,
            cpu_percent_average=(
                statistics.fmean(self.cpu_samples) if self.cpu_samples else None
            ),
            cpu_percent_peak=max(self.cpu_samples) if self.cpu_samples else None,
            peak_rss_bytes=self.peak_rss_bytes,
            child_processes_before=before,
            child_processes_peak=self.peak_children,
            child_processes_after=after,
            gpu_utilization_percent_peak=self.gpu_utilization_peak,
            gpu_memory_used_bytes_peak=self.gpu_memory_peak,
            gpu_temperature_celsius_peak=self.gpu_temperature_peak,
            sample_count=len(self.cpu_samples),
        )


def measure_operation(
    operation: Callable[[], T], *, sample_interval_seconds: float = 0.01
) -> tuple[T, ResourceMeasurement]:
    """Measure a synchronous operation using both wall and monotonic clocks."""
    sampler = _ResourceSampler(sample_interval_seconds)
    before = sampler.start()
    wall_started = time.time()
    monotonic_started = time.monotonic()
    try:
        result = operation()
    except BaseException:
        wall_seconds = time.time() - wall_started
        monotonic_seconds = time.monotonic() - monotonic_started
        sampler.finish(before, wall_seconds, monotonic_seconds)
        raise
    wall_seconds = time.time() - wall_started
    monotonic_seconds = time.monotonic() - monotonic_started
    return result, sampler.finish(before, wall_seconds, monotonic_seconds)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def benchmark_catalog_registration(
    config_path: str | Path,
    *,
    label: str,
    samples: int = 3,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Measure real registration of the audited mini catalog."""
    if samples <= 0:
        raise BenchmarkError("samples must be positive")
    config = load_config(config_path, repo_root=repo_root)
    os.environ.setdefault("SKIP_MCP_AUTO_INIT", "true")
    from src.manager.mcp_client_manager import MCPManager

    iterations: list[dict[str, Any]] = []
    for _ in range(samples):
        def register() -> dict[str, int]:
            MCPManager.init_config(config.catalog.mcp_config, overwrite=True)
            return {
                "registered_servers": len(MCPManager.server_to_path_mapping),
                "registered_tools_including_lifecycle": len(MCPManager.tools),
            }

        result, measurement = measure_operation(register)
        iterations.append({"result": result, "resources": asdict(measurement)})

    durations = [item["resources"]["monotonic_seconds"] for item in iterations]
    return {
        "schema_version": 1,
        "stage": "catalog_registration",
        "label": label,
        "recorded_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "logical_cpu_count": os.cpu_count(),
        },
        "inputs": {
            "config_sha256": _sha256(config.config_path),
            "mcp_config_sha256": _sha256(config.catalog.mcp_config),
            "server_names": list(config.catalog.servers),
            "sample_count": samples,
        },
        "registration_concurrency": getattr(MCPManager, "registration_concurrency", None),
        "iterations": iterations,
        "summary": {
            "monotonic_seconds_min": min(durations),
            "monotonic_seconds_median": statistics.median(durations),
            "monotonic_seconds_p95": _percentile(durations, 0.95),
            "monotonic_seconds_max": max(durations),
            "peak_rss_bytes_max": max(
                item["resources"]["peak_rss_bytes"] for item in iterations
            ),
            "child_processes_peak_max": max(
                item["resources"]["child_processes_peak"] for item in iterations
            ),
            "child_processes_after_max": max(
                item["resources"]["child_processes_after"] for item in iterations
            ),
        },
    }


def _generation_iteration(
    manifest: Any,
    measurement: ResourceMeasurement,
    *,
    config: Any,
) -> dict[str, Any]:
    """Summarize one synthesis run without retaining prompts or scenarios."""
    from src.mini.synthesize import RunPaths

    events_path = RunPaths.for_run(config, manifest.run_id).events
    durations = [
        float(event["duration"])
        for event in read_jsonl(events_path)
        if event.get("operation") == "trajectory_completed"
        and isinstance(event.get("duration"), (int, float))
    ]
    return {
        "run_id": manifest.run_id,
        "state": manifest.state,
        "target_trajectories": manifest.target_trajectories,
        "completed_trajectories": len(manifest.completed_seeds),
        "failed_trajectories": len(manifest.failed_seeds),
        "trajectory_attempts": manifest.attempted_count,
        "retries": manifest.retried_count,
        "failure_summary": dict(sorted(manifest.failure_summary.items())),
        "trajectory_duration_seconds_p50": _percentile(durations, 0.50),
        "trajectory_duration_seconds_p95": _percentile(durations, 0.95),
        "trajectory_rate_per_hour": manifest.trajectory_rate_per_hour,
        "resources": asdict(measurement),
    }


def benchmark_generation_workers(
    config_path: str | Path,
    *,
    label: str,
    workers: Sequence[int] = (1, 2, 4),
    target: int = 10,
    samples: int = 1,
    repo_root: str | Path | None = None,
    _preflight: Any | None = None,
    _runner: Callable[..., Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    """Run an identical-seed synthesis sweep over safe worker counts.

    The fixed mini profile has a four-worker CPU safety contract.  Counts above
    four must first be justified by a doctor report and a configuration-contract
    change; this benchmark deliberately cannot bypass that gate.
    """
    if not _BENCHMARK_LABEL.fullmatch(label):
        raise BenchmarkError(
            "label must be 1-48 characters containing only letters, digits, dot, dash, or underscore"
        )
    if target <= 0:
        raise BenchmarkError("target must be positive")
    if samples <= 0:
        raise BenchmarkError("samples must be positive")
    worker_counts = list(workers)
    if not worker_counts or len(worker_counts) != len(set(worker_counts)):
        raise BenchmarkError("worker counts must be a non-empty unique list")
    if any(value < 1 or value > 4 for value in worker_counts):
        raise BenchmarkError("worker counts must remain within the mini safety bound of 1..4")

    config = load_config(config_path, repo_root=repo_root)
    from src.mini.synthesize import (
        deterministic_seeds,
        production_preflight,
        synthesize,
    )

    preflight = _preflight or asyncio.run(production_preflight(config))
    runner = _runner or synthesize
    seeds = deterministic_seeds(config.run_seed, target)
    seed_hash = hashlib.sha256(
        json.dumps(seeds, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    iterations: list[dict[str, Any]] = []
    aborted_after_run_id: str | None = None
    for worker_count in worker_counts:
        for sample_index in range(1, samples + 1):
            run_id = f"bench-{timestamp}-{label}-w{worker_count}-s{sample_index}"

            def run() -> Any:
                return asyncio.run(
                    runner(
                        config,
                        target=target,
                        workers=worker_count,
                        run_id=run_id,
                        preflight=preflight,
                    )
                )

            manifest, measurement = measure_operation(run)
            iteration = _generation_iteration(manifest, measurement, config=config)
            iteration.update({"workers": worker_count, "sample": sample_index})
            iterations.append(iteration)
            if manifest.state != "completed":
                aborted_after_run_id = run_id
                break
        if aborted_after_run_id is not None:
            break

    summaries: list[dict[str, Any]] = []
    for worker_count in worker_counts:
        selected = [item for item in iterations if item["workers"] == worker_count]
        if not selected:
            continue
        elapsed = [item["resources"]["monotonic_seconds"] for item in selected]
        rates = [item["trajectory_rate_per_hour"] for item in selected]
        latencies = [
            item["trajectory_duration_seconds_p95"]
            for item in selected
            if item["trajectory_duration_seconds_p95"] is not None
        ]
        summaries.append(
            {
                "workers": worker_count,
                "samples": len(selected),
                "monotonic_seconds_median": statistics.median(elapsed),
                "trajectory_rate_per_hour_median": statistics.median(rates),
                "trajectory_duration_seconds_p95_max": max(latencies) if latencies else None,
                "peak_rss_bytes_max": max(
                    item["resources"]["peak_rss_bytes"] for item in selected
                ),
                "gpu_memory_used_bytes_peak_max": max(
                    (
                        item["resources"]["gpu_memory_used_bytes_peak"]
                        for item in selected
                        if item["resources"]["gpu_memory_used_bytes_peak"] is not None
                    ),
                    default=None,
                ),
                "retries_total": sum(item["retries"] for item in selected),
                "failed_trajectories_total": sum(
                    item["failed_trajectories"] for item in selected
                ),
                "child_processes_after_max": max(
                    item["resources"]["child_processes_after"] for item in selected
                ),
            }
        )

    return {
        "schema_version": 1,
        "stage": "generation_worker_matrix",
        "label": label,
        "recorded_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "logical_cpu_count": os.cpu_count(),
        },
        "inputs": {
            "config_sha256": _sha256(config.config_path),
            "graph_sha256": preflight.graph_result.manifest.get("output_sha256"),
            "catalog_sha256": preflight.catalog.digest,
            "model_identity": preflight.model_identity,
            "run_seed": config.run_seed,
            "seeds_sha256": seed_hash,
            "target_trajectories": target,
            "worker_counts": worker_counts,
            "samples_per_worker_count": samples,
        },
        "iterations": iterations,
        "summary": {
            "complete": aborted_after_run_id is None,
            "aborted_after_run_id": aborted_after_run_id,
            "by_worker_count": summaries,
        },
    }


def render_generation_matrix_markdown(report: dict[str, Any]) -> str:
    """Render a compact decision table from a generation worker sweep."""
    if report.get("stage") != "generation_worker_matrix":
        raise BenchmarkError("report is not a generation worker matrix")
    rows = [
        "# MoLab mini generation worker matrix",
        "",
        f"Label: `{report['label']}`",
        "",
        "| Workers | Samples | Median duration (s) | Median trajectories/hour | Max p95 trajectory latency (s) | Peak RSS (bytes) | Peak GPU memory (bytes) | Retries | Failed | Children after |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["summary"]["by_worker_count"]:
        latency = item["trajectory_duration_seconds_p95_max"]
        gpu_memory = item["gpu_memory_used_bytes_peak_max"]
        rows.append(
            "| {workers} | {samples} | {duration:.4f} | {rate:.2f} | {latency} | "
            "{rss} | {gpu} | {retries} | {failed} | {children} |".format(
                workers=item["workers"],
                samples=item["samples"],
                duration=item["monotonic_seconds_median"],
                rate=item["trajectory_rate_per_hour_median"],
                latency="n/a" if latency is None else f"{latency:.4f}",
                rss=item["peak_rss_bytes_max"],
                gpu="n/a" if gpu_memory is None else gpu_memory,
                retries=item["retries_total"],
                failed=item["failed_trajectories_total"],
                children=item["child_processes_after_max"],
            )
        )
    rows.extend(
        [
            "",
            "All rows use the same run seed, target, graph, catalog, and model identity. "
            "Choose a new default only after inspecting failures, latency, memory, and cleanup as well as throughput.",
            "",
        ]
    )
    if report["summary"].get("complete") is False:
        rows.extend(
            [
                f"**Incomplete:** the sweep stopped after `{report['summary'].get('aborted_after_run_id')}`.",
                "",
            ]
        )
    return "\n".join(rows)


def render_comparison_markdown(before: dict[str, Any], after: dict[str, Any]) -> str:
    """Render a compact, source-labelled before/after comparison."""
    if before.get("stage") != after.get("stage"):
        raise BenchmarkError("before and after reports must measure the same stage")
    before_summary = before["summary"]
    after_summary = after["summary"]
    before_median = float(before_summary["monotonic_seconds_median"])
    after_median = float(after_summary["monotonic_seconds_median"])
    delta = after_median - before_median
    percent = (delta / before_median * 100.0) if before_median else None
    percent_text = "n/a" if percent is None else f"{percent:+.1f}%"
    return "\n".join(
        [
            "# MoLab mini benchmark comparison",
            "",
            f"Stage: `{before['stage']}`",
            "",
            "| Metric | Before | After |",
            "|---|---:|---:|",
            f"| Label | {before['label']} | {after['label']} |",
            f"| Registration concurrency | {before.get('registration_concurrency', 'n/a')} | {after.get('registration_concurrency', 'n/a')} |",
            f"| Median duration (s) | {before_median:.4f} | {after_median:.4f} |",
            f"| p95 duration (s) | {before_summary['monotonic_seconds_p95']:.4f} | {after_summary['monotonic_seconds_p95']:.4f} |",
            f"| Peak RSS (bytes) | {before_summary['peak_rss_bytes_max']} | {after_summary['peak_rss_bytes_max']} |",
            f"| Peak child processes | {before_summary['child_processes_peak_max']} | {after_summary['child_processes_peak_max']} |",
            f"| Child processes after | {before_summary['child_processes_after_max']} | {after_summary['child_processes_after_max']} |",
            "",
            f"Median-duration change: **{delta:+.4f} seconds ({percent_text})**.",
            "",
        ]
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure MoLab mini performance stages")
    subparsers = parser.add_subparsers(dest="command", required=True)
    catalog = subparsers.add_parser("catalog-registration")
    catalog.add_argument("--config", required=True)
    catalog.add_argument("--label", required=True)
    catalog.add_argument("--samples", type=int, default=3)
    catalog.add_argument("--output", required=True)
    catalog.add_argument("--repo-root")
    generation = subparsers.add_parser("generation-workers")
    generation.add_argument("--config", required=True)
    generation.add_argument("--label", required=True)
    generation.add_argument("--workers", type=int, nargs="+", default=(1, 2, 4))
    generation.add_argument("--target", type=int, default=10)
    generation.add_argument("--samples", type=int, default=1)
    generation.add_argument("--output", required=True)
    generation.add_argument("--markdown-output")
    generation.add_argument("--repo-root")
    compare = subparsers.add_parser("compare")
    compare.add_argument("--before", required=True)
    compare.add_argument("--after", required=True)
    compare.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "catalog-registration":
            report = benchmark_catalog_registration(
                args.config,
                label=args.label,
                samples=args.samples,
                repo_root=args.repo_root,
            )
            destination = Path(args.output).expanduser().resolve()
            atomic_write_json(destination, report)
            print(
                f"catalog registration median={report['summary']['monotonic_seconds_median']:.4f}s; "
                f"report={destination}"
            )
            return 0
        if args.command == "generation-workers":
            report = benchmark_generation_workers(
                args.config,
                label=args.label,
                workers=args.workers,
                target=args.target,
                samples=args.samples,
                repo_root=args.repo_root,
            )
            destination = Path(args.output).expanduser().resolve()
            atomic_write_json(destination, report)
            if args.markdown_output:
                markdown_destination = Path(args.markdown_output).expanduser().resolve()
                atomic_write_text(
                    markdown_destination, render_generation_matrix_markdown(report)
                )
                print(f"generation matrix report={destination}; summary={markdown_destination}")
            else:
                print(f"generation matrix report={destination}")
            return 0 if report["summary"]["complete"] else 2
        before = json.loads(Path(args.before).read_text(encoding="utf-8"))
        after = json.loads(Path(args.after).read_text(encoding="utf-8"))
        destination = Path(args.output).expanduser().resolve()
        atomic_write_text(destination, render_comparison_markdown(before, after))
        print(f"comparison={destination}")
        return 0
    except (BenchmarkError, MiniConfigError, OSError, RuntimeError, ValueError) as exc:
        print(f"benchmark failed: {_safe_error_message(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BenchmarkError",
    "ResourceMeasurement",
    "benchmark_catalog_registration",
    "benchmark_generation_workers",
    "main",
    "measure_operation",
    "render_comparison_markdown",
    "render_generation_matrix_markdown",
]
