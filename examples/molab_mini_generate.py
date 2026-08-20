"""MoLab generation notebook. Run with ``marimo edit examples/molab_mini_generate.py``."""

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    import os
    import time
    import tomllib
    from pathlib import Path

    import marimo as mo

    from src.mini.notebook import (
        JobAlreadyRunning,
        NotebookError,
        NotebookProcessSupervisor,
        artifact_checklist,
        command_text,
        export_command,
        read_json_redacted,
        redact,
        resolve_run_directory,
        safe_text,
        session_clock,
        tail_log,
    )

    return (
        JobAlreadyRunning,
        NotebookError,
        NotebookProcessSupervisor,
        Path,
        artifact_checklist,
        command_text,
        export_command,
        json,
        mo,
        os,
        read_json_redacted,
        redact,
        resolve_run_directory,
        safe_text,
        session_clock,
        tail_log,
        time,
        tomllib,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # EnvFactory Mini — generation

    This notebook orchestrates the checked-in CLI workflow; it does not
    implement generation itself. **MoLab notebooks may be public-but-unlisted.**
    Never type a token or API key into a widget or source cell. Define
    `VLLM_API_KEY` and any Hugging Face credentials in the protected process
    environment. Generated tool code and graph pickle files are executable;
    use only this repository's audited eight-server inputs.
    """)
    return


@app.cell
def _(Path, mo, time):
    default_repo = str(Path(__file__).resolve().parents[1])
    repo_root_input = mo.ui.text(value=default_repo, label="Repository root", full_width=True)
    artifact_root_input = mo.ui.text(
        value=str(Path(default_repo) / "artifacts" / "mini"),
        label="Persistent artifact root",
        full_width=True,
    )
    session_started_monotonic = time.monotonic()
    mo.vstack(
        [
            mo.md("## 1. Repository, artifacts, and session clock"),
            repo_root_input,
            artifact_root_input,
            mo.md("Changing these paths never launches a job."),
        ]
    )
    return artifact_root_input, repo_root_input, session_started_monotonic


@app.cell
def _(
    NotebookProcessSupervisor,
    Path,
    artifact_root_input,
    mo,
    repo_root_input,
    session_clock,
    session_started_monotonic,
):
    repo_root = Path(repo_root_input.value).expanduser().resolve()
    artifact_root = Path(artifact_root_input.value).expanduser().resolve()
    config_path = repo_root / "configs" / "mini" / "pipeline.toml"
    runtime_python = repo_root / ".venv-mini-runtime" / "bin" / "python"
    deployment_environment = {"ENVFACTORY_MINI_ARTIFACT_ROOT": str(artifact_root)}
    supervisor = NotebookProcessSupervisor(artifact_root)
    clock = session_clock(session_started_monotonic)
    clock_message = (
        f"Session elapsed: **{clock['elapsed_hours']:.2f} h**. "
        + ("⚠️ Export or checkpoint now; the 10.5-hour warning threshold has passed." if clock["warning"] else "Warning begins at 10.5 hours.")
    )
    mo.md(clock_message)
    return artifact_root, config_path, deployment_environment, repo_root, runtime_python, supervisor


@app.cell
def _(mo):
    doctor_run = mo.ui.run_button(label="Run read-only doctor")
    doctor_refresh = mo.ui.run_button(label="Refresh doctor status and report")
    mo.vstack([mo.md("## 2. Read-only environment doctor"), mo.hstack([doctor_run, doctor_refresh])])
    return doctor_refresh, doctor_run


@app.cell
def _(config_path, deployment_environment, doctor_refresh, doctor_run, mo, repo_root, runtime_python, safe_text, supervisor, tail_log):
    doctor_result = "Click the button to run the doctor without contacting the model."
    doctor_report = ""
    if doctor_run.value:
        try:
            _status = supervisor.start(
                "generate-doctor",
                [runtime_python, "-m", "src.mini.doctor", "--config", config_path, "--without-model", "--json"],
                cwd=repo_root,
                environment=deployment_environment,
            )
            doctor_result = f"Started PID {_status.pid}; log: `{_status.log_path}`"
        except Exception as exc:
            doctor_result = safe_text(exc)
    if doctor_refresh.value:
        try:
            _status = supervisor.status("generate-doctor")
            if _status is None:
                doctor_result = "No doctor job has been launched."
            else:
                doctor_result = f"Doctor state: {_status.state}; PID {_status.pid}; log: `{_status.log_path}`"
                doctor_report = f"```text\n{tail_log(_status.log_path, lines=240)}\n```"
        except Exception as exc:
            doctor_result = safe_text(exc)
    mo.vstack([mo.md(doctor_result), mo.md(doctor_report)])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. One-time dependency installation

    Installation is intentionally instruction-only: reactive execution must
    never reinstall an environment. Run these once in a MoLab terminal:

    ```bash
    uv venv .venv-mini-runtime --python 3.12
    uv pip install --python .venv-mini-runtime/bin/python -e .
    uv pip install --python .venv-mini-runtime/bin/python --torch-backend=auto -r requirements-molab.txt
    ```
    """)
    return


@app.cell
def _(config_path, mo, redact, safe_text, tomllib):
    try:
        with config_path.open("rb") as config_handle:
            config_preview = redact(tomllib.load(config_handle))
    except Exception as exc:
        config_preview = {"error": safe_text(exc)}
    mo.vstack(
        [
            mo.md("## 4. Redacted configuration preview"),
            mo.json(config_preview),
            mo.md("Secret values are never read from or displayed by this preview."),
        ]
    )
    return


@app.cell
def _(mo):
    model_action = mo.ui.dropdown(
        options={"Start teacher": "start", "Stop server (graceful, then forced if needed)": "stop"},
        value="Start teacher",
        label="Model server action",
    )
    model_run = mo.ui.run_button(label="Run selected server action")
    mo.vstack([mo.md("## 5. Model server start/stop"), model_action, model_run])
    return model_action, model_run


@app.cell
def _(
    Path,
    artifact_root,
    config_path,
    deployment_environment,
    model_action,
    model_run,
    mo,
    repo_root,
    runtime_python,
    safe_text,
    supervisor,
):
    model_result = "Server actions run only when the button is clicked."
    if model_run.value:
        action = model_action.value
        model_environment = {
            **deployment_environment,
            "MOLAB_VLLM_RUN_DIR": str(artifact_root / "runs" / "notebook-teacher"),
            "MOLAB_VLLM_CONFIG": str(config_path),
            "MOLAB_VLLM_PYTHON": str(runtime_python),
            "MOLAB_VLLM_EXECUTABLE": str(repo_root / ".venv-mini-runtime" / "bin" / "vllm"),
        }
        try:
            _status = supervisor.start(
                f"teacher-server-{action}",
                ["bash", repo_root / "src" / "serve" / "vllm_molab.sh", action],
                cwd=repo_root,
                environment=model_environment,
            )
            server_pid_path = Path(model_environment["MOLAB_VLLM_RUN_DIR"]) / "logs" / "model_server.pid"
            model_result = f"Launcher PID {_status.pid}; log: `{_status.log_path}`; server PID file: `{server_pid_path}`"
        except Exception as exc:
            model_result = safe_text(exc)
    mo.md(model_result)
    return


@app.cell
def _(mo):
    health_run = mo.ui.run_button(label="Run authenticated localhost health check")
    mo.vstack([mo.md("## 6. Model health check"), health_run])
    return (health_run,)


@app.cell
def _(config_path, deployment_environment, health_run, mo, repo_root, runtime_python, safe_text, supervisor):
    health_result = "Health uses `VLLM_API_KEY` from the environment, never a command argument."
    if health_run.value:
        try:
            _status = supervisor.start(
                "generate-health",
                [runtime_python, "-m", "src.mini.doctor", "--config", config_path, "--require-model"],
                cwd=repo_root,
                environment=deployment_environment,
            )
            health_result = f"Started PID {_status.pid}; log: `{_status.log_path}`"
        except Exception as exc:
            health_result = safe_text(exc)
    mo.md(health_result)
    return


@app.cell
def _(mo):
    catalog_run = mo.ui.run_button(label="Validate fixed eight-server catalog")
    mo.vstack([mo.md("## 7. Catalog validation"), catalog_run])
    return (catalog_run,)


@app.cell
def _(catalog_run, config_path, deployment_environment, mo, repo_root, runtime_python, safe_text, supervisor):
    catalog_result = "Expected result: eight servers and 55 metadata tools."
    if catalog_run.value:
        try:
            _status = supervisor.start(
                "generate-catalog",
                [runtime_python, "-m", "src.mini.catalog", "--config", config_path, "--check"],
                cwd=repo_root,
                environment=deployment_environment,
            )
            catalog_result = f"Started PID {_status.pid}; log: `{_status.log_path}`"
        except Exception as exc:
            catalog_result = safe_text(exc)
    mo.md(catalog_result)
    return


@app.cell
def _(mo):
    graph_force = mo.ui.checkbox(value=False, label="Force a deliberate rebuild")
    graph_run = mo.ui.run_button(label="Build or reuse graph cache")
    mo.vstack([mo.md("## 8. Graph build/cache status"), graph_force, graph_run])
    return graph_force, graph_run


@app.cell
def _(config_path, deployment_environment, graph_force, graph_run, mo, repo_root, runtime_python, safe_text, supervisor):
    graph_result = "A trusted matching graph and manifest are reused by default."
    if graph_run.value:
        graph_command = [runtime_python, "-m", "src.mini.build_graph", "--config", config_path]
        if graph_force.value:
            graph_command.append("--force")
        try:
            _status = supervisor.start("generate-graph", graph_command, cwd=repo_root, environment=deployment_environment)
            graph_result = f"Started PID {_status.pid}; log: `{_status.log_path}`"
        except Exception as exc:
            graph_result = safe_text(exc)
    mo.md(graph_result)
    return


@app.cell
def _(mo):
    generation_mode = mo.ui.dropdown(
        options={"Smoke (10, 2 workers)": "smoke", "Pilot (100, 4 workers)": "pilot", "Full (configured target)": "full", "Resume selected run": "resume"},
        value="Smoke (10, 2 workers)",
        label="Generation action",
    )
    generation_run_id = mo.ui.text(label="Run ID (required only for resume)", full_width=True)
    full_target = mo.ui.number(start=1, stop=5000, step=1, value=2000, label="Full target")
    generation_run = mo.ui.run_button(label="Start generation")
    generation_stop = mo.ui.run_button(label="Gracefully stop selected generation job")
    mo.vstack(
        [
            mo.md("## 9. Smoke, pilot, full, and resume controls"),
            generation_mode,
            generation_run_id,
            full_target,
            mo.hstack([generation_run, generation_stop]),
        ]
    )
    return full_target, generation_mode, generation_run, generation_run_id, generation_stop


@app.cell
def _(
    config_path,
    deployment_environment,
    full_target,
    generation_mode,
    generation_run,
    generation_run_id,
    generation_stop,
    mo,
    repo_root,
    runtime_python,
    safe_text,
    supervisor,
):
    mode = generation_mode.value
    job_name = f"generation-{mode}"
    generation_result = "Each launch is an explicit subprocess; changing controls cannot replace a live named job."
    try:
        if generation_run.value:
            targets = {"smoke": (10, 2), "pilot": (100, 4), "full": (int(full_target.value), 4)}
            _command = [runtime_python, "-m", "src.mini.synthesize", "--config", config_path]
            if mode == "resume":
                _command.extend(["--run-id", generation_run_id.value.strip(), "--target", "100", "--workers", "4", "--resume"])
            else:
                target, workers = targets[mode]
                _command.extend(["--target", str(target), "--workers", str(workers)])
            _status = supervisor.start(job_name, _command, cwd=repo_root, environment=deployment_environment)
            generation_result = f"Started PID {_status.pid}; streaming log: `{_status.log_path}`"
        if generation_stop.value:
            _status = supervisor.stop(job_name, graceful_timeout_seconds=30)
            generation_result = "No live job found." if _status is None else f"Stop state: {_status.state}; PID {_status.pid}; log: `{_status.log_path}`"
    except Exception as exc:
        generation_result = safe_text(exc)
    mo.md(generation_result)
    return


@app.cell
def _(mo):
    inspect_run_id = mo.ui.text(label="Run ID to inspect", full_width=True)
    manifest_refresh = mo.ui.run_button(label="Refresh manifest and all job logs")
    mo.vstack([mo.md("## 10. Live manifest metrics"), inspect_run_id, manifest_refresh])
    return inspect_run_id, manifest_refresh


@app.cell
def _(
    artifact_root,
    inspect_run_id,
    manifest_refresh,
    mo,
    read_json_redacted,
    resolve_run_directory,
    safe_text,
    supervisor,
    tail_log,
):
    manifest_display = {"status": "Enter a run ID and click refresh."}
    log_display = ""
    if manifest_refresh.value:
        try:
            logs = []
            for job_status in supervisor.list_statuses():
                logs.append(f"### {job_status.name} — PID {job_status.pid} ({job_status.state})\nLog: `{job_status.log_path}`\n```text\n{tail_log(job_status.log_path)}\n```")
            log_display = "\n".join(logs)
            if inspect_run_id.value.strip():
                inspected_run_dir = resolve_run_directory(artifact_root, inspect_run_id.value)
                manifest_display = read_json_redacted(inspected_run_dir / "run_manifest.json")
        except Exception as exc:
            manifest_display = {"error": safe_text(exc)}
    mo.vstack([mo.json(manifest_display), mo.md(log_display)])
    return


@app.cell
def _(mo):
    dataset_run_id = mo.ui.text(label="Completed run ID", full_width=True)
    dataset_run = mo.ui.run_button(label="Convert and validate dataset")
    mo.vstack([mo.md("## 11. Dataset conversion and validation"), dataset_run_id, dataset_run])
    return dataset_run, dataset_run_id


@app.cell
def _(config_path, dataset_run, dataset_run_id, deployment_environment, mo, repo_root, runtime_python, safe_text, supervisor):
    dataset_result = "Conversion writes and validates run-scoped dataset artifacts."
    if dataset_run.value:
        try:
            _status = supervisor.start(
                "prepare-dataset",
                [runtime_python, "-m", "src.mini.prepare_dataset", "--config", config_path, "--run-id", dataset_run_id.value.strip()],
                cwd=repo_root,
                environment=deployment_environment,
            )
            dataset_result = f"Started PID {_status.pid}; log: `{_status.log_path}`"
        except Exception as exc:
            dataset_result = safe_text(exc)
    mo.md(dataset_result)
    return


@app.cell
def _(mo):
    export_run_id = mo.ui.text(label="Run ID to export", full_width=True)
    export_destination = mo.ui.text(label="Absolute persistent destination", full_width=True)
    export_preview = mo.ui.run_button(label="Preview checklist and exact command")
    export_run = mo.ui.run_button(label="Explicitly export with rsync")
    mo.vstack(
        [
            mo.md("## 12. Artifact export checklist"),
            mo.md("Nothing uploads automatically. Confirm the destination and command before export."),
            export_run_id,
            export_destination,
            mo.hstack([export_preview, export_run]),
        ]
    )
    return export_destination, export_preview, export_run, export_run_id


@app.cell
def _(
    artifact_checklist,
    artifact_root,
    command_text,
    export_command,
    export_destination,
    export_preview,
    export_run,
    export_run_id,
    mo,
    repo_root,
    resolve_run_directory,
    safe_text,
    supervisor,
):
    export_result = {"status": "Choose a run and an absolute persistent destination."}
    if (export_preview.value or export_run.value) and export_run_id.value.strip():
        try:
            source_run_dir = resolve_run_directory(artifact_root, export_run_id.value)
            _command = export_command(source_run_dir, export_destination.value)
            export_result = {"checklist": artifact_checklist(source_run_dir), "command": command_text(_command)}
            if export_run.value:
                _status = supervisor.start("export-generation-artifacts", _command, cwd=repo_root)
                export_result["started"] = {"pid": _status.pid, "log": _status.log_path}
        except Exception as exc:
            export_result = {"error": safe_text(exc)}
    mo.json(export_result)
    return


if __name__ == "__main__":
    app.run()
