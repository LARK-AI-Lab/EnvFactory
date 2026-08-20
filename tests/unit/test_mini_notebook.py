from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from src.mini.notebook import (
    JobAlreadyRunning,
    NotebookError,
    NotebookProcessSupervisor,
    artifact_checklist,
    export_command,
    redact,
    resolve_run_directory,
    session_clock,
    tail_log,
)


def test_redaction_preserves_secret_indirection_but_removes_values():
    environment = {"VLLM_API_KEY": "very-secret-value", "SAFE": "public"}
    value = {
        "api_key_env": "VLLM_API_KEY",
        "api_key": "very-secret-value",
        "message": "failure included very-secret-value",
    }

    result = redact(value, environment=environment)

    assert result["api_key_env"] == "VLLM_API_KEY"
    assert result["api_key"] == "[REDACTED]"
    assert result["message"] == "failure included [REDACTED]"


def test_run_and_export_paths_fail_closed(tmp_path: Path):
    assert resolve_run_directory(tmp_path, "run-001") == tmp_path / "runs" / "run-001"
    with pytest.raises(NotebookError):
        resolve_run_directory(tmp_path, "../escape")
    run_dir = tmp_path / "runs" / "run-001"
    with pytest.raises(NotebookError, match="absolute"):
        export_command(run_dir, "relative/export")
    with pytest.raises(NotebookError, match="separate"):
        export_command(run_dir, tmp_path)


def test_session_warning_and_artifact_checklist(tmp_path: Path):
    clock = session_clock(time.monotonic() - 10.6 * 3600)
    assert clock["warning"] is True
    run_dir = tmp_path / "runs" / "run-001"
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text("{}", encoding="utf-8")
    checklist = artifact_checklist(run_dir)
    assert next(item for item in checklist if item["artifact"] == "run manifest")["present"]
    assert not next(item for item in checklist if item["artifact"] == "training adapter")["present"]


def test_supervisor_is_idempotent_and_streams_log(tmp_path: Path):
    supervisor = NotebookProcessSupervisor(tmp_path / "artifacts")
    command = [
        sys.executable,
        "-c",
        "import time; print('ready', flush=True); time.sleep(30)",
    ]
    status = supervisor.start("long-job", command, cwd=tmp_path)
    try:
        assert status.pid > 0
        assert Path(status.log_path).is_relative_to(tmp_path)
        with pytest.raises(JobAlreadyRunning):
            supervisor.start("long-job", command, cwd=tmp_path)
        deadline = time.monotonic() + 5
        while "ready" not in tail_log(status.log_path) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert "ready" in tail_log(status.log_path)
    finally:
        stopped = supervisor.stop("long-job", graceful_timeout_seconds=2)
    assert stopped is not None
    assert stopped.state == "stopped"


def test_supervisor_rejects_secret_in_argv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("VLLM_API_KEY", "do-not-log-this")
    supervisor = NotebookProcessSupervisor(tmp_path / "artifacts")
    with pytest.raises(NotebookError, match="secret"):
        supervisor.start(
            "unsafe",
            [sys.executable, "-c", "print('do-not-log-this')"],
            cwd=tmp_path,
        )


def test_reattached_completed_job_has_explicit_unknown_exit_state(tmp_path: Path):
    owner = NotebookProcessSupervisor(tmp_path / "artifacts")
    status = owner.start("quick-job", [sys.executable, "-c", "pass"], cwd=tmp_path)
    owner._processes["quick-job"].wait(timeout=5)

    reattached = NotebookProcessSupervisor(tmp_path / "artifacts")
    completed = reattached.status("quick-job")

    assert completed is not None
    assert completed.state == "exited"
    assert completed.return_code is None
    owner.status("quick-job")


@pytest.mark.skipif(os.name == "nt", reason="POSIX process-group signaling is the MoLab path")
def test_reattached_supervisor_stops_process_group(tmp_path: Path):
    owner = NotebookProcessSupervisor(tmp_path / "artifacts")
    started = owner.start(
        "reattached-job",
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
    )
    reattached = NotebookProcessSupervisor(tmp_path / "artifacts")

    stopped = reattached.stop("reattached-job", graceful_timeout_seconds=2)

    assert stopped is not None
    assert stopped.pid == started.pid
    assert stopped.state == "stopped"
    assert reattached.status("reattached-job").state == "stopped"
    owner.status("reattached-job")


@pytest.mark.parametrize(
    ("notebook_name", "ordered_headings", "required_commands"),
    [
        (
            "molab_mini_generate.py",
            [
                "Repository, artifacts, and session clock",
                "Read-only environment doctor",
                "One-time dependency installation",
                "Redacted configuration preview",
                "Model server start/stop",
                "Model health check",
                "Catalog validation",
                "Graph build/cache status",
                "Smoke, pilot, full, and resume controls",
                "Live manifest metrics",
                "Dataset conversion and validation",
                "Artifact export checklist",
            ],
            [
                "src.mini.doctor",
                "src.mini.catalog",
                "src.mini.build_graph",
                "src.mini.synthesize",
                "src.mini.prepare_dataset",
                "vllm_molab.sh",
            ],
        ),
        (
            "molab_mini_train.py",
            [
                "Doctor report and vLLM-stopped verification",
                "Dataset and run selection",
                "Dataset manifest and sample inspection",
                "Training configuration preview",
                "Smoke training",
                "Full training and resume",
                "Adapter integrity check",
                "Teacher or student evaluation server",
                "Evaluation controls and report",
                "Artifact export checklist",
            ],
            ["src.mini.doctor", "src.mini.training", "llamafactory-cli", "src.mini.evaluate", "vllm_molab.sh"],
        ),
    ],
)
def test_marimo_notebooks_are_ordered_cli_orchestrators(
    notebook_name: str,
    ordered_headings: list[str],
    required_commands: list[str],
):
    notebook_path = Path(__file__).resolve().parents[2] / "examples" / notebook_name
    source = notebook_path.read_text(encoding="utf-8")
    runbook = (Path(__file__).resolve().parents[2] / "docs" / "MOLAB_MINI_RUNBOOK.md").read_text(encoding="utf-8")
    compile(source, str(notebook_path), "exec")
    positions = [source.index(heading) for heading in ordered_headings]
    assert positions == sorted(positions)
    for command in required_commands:
        assert command in source
        assert command in runbook
    assert "mo.ui.run_button" in source
    assert "NotebookProcessSupervisor" in source
    assert "asyncio.run(" not in source
    assert "10.5" in source
    assert "Refresh doctor status and report" in source
    assert "VLLM_API_KEY" not in source or "VLLM_API_KEY` from the environment" in source
    assert '["uv"' not in source
    assert "rsync -a --protect-args" in runbook
    assert "kill -TERM" in runbook
    assert "kill -KILL" in runbook
    if notebook_name == "molab_mini_generate.py":
        assert source.count("environment=deployment_environment") >= 5
    else:
        assert source.count("environment=train_deployment_environment") >= 6
        assert "gpu_exclusive" in source
        assert "resume checkpoint must be inside this run's training/checkpoints directory" in source
