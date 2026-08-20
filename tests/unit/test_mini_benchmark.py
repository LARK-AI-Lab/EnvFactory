"""Unit tests for Phase 11 benchmark records and comparisons."""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mini.artifacts import append_jsonl
from src.mini.benchmark import (
    BenchmarkError,
    _safe_error_message,
    benchmark_generation_workers,
    measure_operation,
    render_comparison_markdown,
    render_generation_matrix_markdown,
)
from src.mini.synthesize import RunPaths


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"


def test_measure_operation_records_both_clocks_and_process_resources():
    value, resources = measure_operation(lambda: (time.sleep(0.03), "done")[1])

    assert value == "done"
    assert resources.wall_seconds >= 0.02
    assert resources.monotonic_seconds >= 0.02
    assert resources.peak_rss_bytes > 0
    assert resources.sample_count >= 1
    assert resources.child_processes_peak >= resources.child_processes_before
    assert resources.child_processes_after >= 0


def test_benchmark_errors_redact_environment_secrets(monkeypatch):
    monkeypatch.setenv("VLLM_API_KEY", "super-secret-value")
    rendered = _safe_error_message(
        RuntimeError("request api_key=super-secret-value could not complete")
    )
    assert "super-secret-value" not in rendered
    assert "api_key=[REDACTED]" in rendered


def test_comparison_is_source_labelled_and_calculates_duration_change():
    before = {
        "stage": "catalog_registration",
        "label": "unbounded",
        "registration_concurrency": None,
        "summary": {
            "monotonic_seconds_median": 2.0,
            "monotonic_seconds_p95": 2.2,
            "peak_rss_bytes_max": 200,
            "child_processes_peak_max": 8,
            "child_processes_after_max": 0,
        },
    }
    after = {
        "stage": "catalog_registration",
        "label": "bounded-2",
        "registration_concurrency": 2,
        "summary": {
            "monotonic_seconds_median": 2.5,
            "monotonic_seconds_p95": 2.6,
            "peak_rss_bytes_max": 150,
            "child_processes_peak_max": 2,
            "child_processes_after_max": 0,
        },
    }

    rendered = render_comparison_markdown(before, after)

    assert "| Label | unbounded | bounded-2 |" in rendered
    assert "| Peak child processes | 8 | 2 |" in rendered
    assert "+0.5000 seconds (+25.0%)" in rendered


def test_comparison_rejects_different_stages():
    with pytest.raises(BenchmarkError, match="same stage"):
        render_comparison_markdown(
            {"stage": "catalog_registration"}, {"stage": "graph_build"}
        )


def test_generation_worker_matrix_uses_identical_inputs_and_renders(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVFACTORY_MINI_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    calls = []
    preflight = SimpleNamespace(
        graph_result=SimpleNamespace(manifest={"output_sha256": "graph-sha"}),
        catalog=SimpleNamespace(digest="catalog-sha"),
        model_identity="teacher-model",
    )

    async def runner(config, *, target, workers, run_id, preflight):
        calls.append((target, workers, run_id, preflight))
        paths = RunPaths.for_run(config, run_id)
        for index in range(target):
            append_jsonl(
                paths.events,
                {
                    "operation": "trajectory_completed",
                    "duration": workers + index / 10,
                },
            )
        return SimpleNamespace(
            run_id=run_id,
            state="completed",
            target_trajectories=target,
            completed_seeds=list(range(target)),
            failed_seeds=[],
            attempted_count=target,
            retried_count=0,
            failure_summary={},
            trajectory_rate_per_hour=float(workers * 100),
        )

    report = benchmark_generation_workers(
        CONFIG_PATH,
        label="smoke",
        workers=(1, 2),
        target=3,
        _preflight=preflight,
        _runner=runner,
    )

    assert [(target, workers) for target, workers, _, _ in calls] == [(3, 1), (3, 2)]
    assert len({run_id for _, _, run_id, _ in calls}) == 2
    assert all(value is preflight for _, _, _, value in calls)
    assert report["inputs"]["worker_counts"] == [1, 2]
    assert report["inputs"]["seeds_sha256"]
    assert [item["workers"] for item in report["summary"]["by_worker_count"]] == [1, 2]
    assert report["iterations"][0]["trajectory_duration_seconds_p95"] == pytest.approx(1.19)
    rendered = render_generation_matrix_markdown(report)
    assert "| 1 | 1 |" in rendered
    assert "| 2 | 1 |" in rendered
    assert "same run seed, target, graph, catalog, and model identity" in rendered


def test_generation_worker_matrix_stops_and_returns_partial_failure_report(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ENVFACTORY_MINI_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    preflight = SimpleNamespace(
        graph_result=SimpleNamespace(manifest={"output_sha256": "graph-sha"}),
        catalog=SimpleNamespace(digest="catalog-sha"),
        model_identity="teacher-model",
    )
    calls = []

    async def runner(config, *, target, workers, run_id, preflight):
        calls.append(workers)
        return SimpleNamespace(
            run_id=run_id,
            state="failed",
            target_trajectories=target,
            completed_seeds=[],
            failed_seeds=list(range(target)),
            attempted_count=target,
            retried_count=0,
            failure_summary={"TimeoutError": target},
            trajectory_rate_per_hour=0.0,
        )

    report = benchmark_generation_workers(
        CONFIG_PATH,
        label="partial",
        workers=(1, 2, 4),
        target=2,
        _preflight=preflight,
        _runner=runner,
    )

    assert calls == [1]
    assert report["summary"]["complete"] is False
    assert report["summary"]["aborted_after_run_id"] == report["iterations"][0]["run_id"]
    assert report["iterations"][0]["failure_summary"] == {"TimeoutError": 2}
    assert "**Incomplete:**" in render_generation_matrix_markdown(report)


@pytest.mark.parametrize("workers", [(), (1, 1), (0,), (5,)])
def test_generation_worker_matrix_rejects_unsafe_worker_lists(workers):
    with pytest.raises(BenchmarkError, match="worker"):
        benchmark_generation_workers(
            CONFIG_PATH,
            label="invalid",
            workers=workers,
            _preflight=object(),
            _runner=lambda **_: None,
        )
