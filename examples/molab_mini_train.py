"""MoLab training/evaluation notebook. Run with ``marimo edit examples/molab_mini_train.py``."""

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    import os
    import time
    from pathlib import Path

    import marimo as mo
    import yaml

    from src.mini.notebook import (
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
        yaml,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # EnvFactory Mini — training and evaluation

    **GPU exclusivity is mandatory.** Stop vLLM and verify VRAM release
    before training. Stop training before launching a teacher or student
    evaluation endpoint. Never enter credentials in this notebook: use
    protected environment variables. MoLab notebooks may be
    public-but-unlisted, and notebook storage must be treated as ephemeral.
    """)
    return


@app.cell
def _(Path, mo, time):
    default_repo = str(Path(__file__).resolve().parents[1])
    train_repo_input = mo.ui.text(value=default_repo, label="Repository root", full_width=True)
    train_artifact_input = mo.ui.text(
        value=str(Path(default_repo) / "artifacts" / "mini"),
        label="Persistent artifact root",
        full_width=True,
    )
    train_session_started = time.monotonic()
    mo.vstack([mo.md("## 1. Session paths and clock"), train_repo_input, train_artifact_input])
    return train_artifact_input, train_repo_input, train_session_started


@app.cell
def _(
    NotebookProcessSupervisor,
    Path,
    mo,
    session_clock,
    train_artifact_input,
    train_repo_input,
    train_session_started,
):
    train_repo_root = Path(train_repo_input.value).expanduser().resolve()
    train_artifact_root = Path(train_artifact_input.value).expanduser().resolve()
    train_config_path = train_repo_root / "configs" / "mini" / "pipeline.toml"
    train_python = train_repo_root / ".venv-mini-train" / "bin" / "python"
    runtime_python_for_eval = train_repo_root / ".venv-mini-runtime" / "bin" / "python"
    llamafactory_cli = train_repo_root / ".venv-mini-train" / "bin" / "llamafactory-cli"
    train_deployment_environment = {"ENVFACTORY_MINI_ARTIFACT_ROOT": str(train_artifact_root)}
    train_supervisor = NotebookProcessSupervisor(train_artifact_root)
    train_clock = session_clock(train_session_started)
    clock_text = f"Session elapsed: **{train_clock['elapsed_hours']:.2f} h**. " + (
        "⚠️ The 10.5-hour warning threshold has passed; checkpoint/export now."
        if train_clock["warning"]
        else "Warning begins at 10.5 hours."
    )
    mo.md(clock_text)
    return (
        llamafactory_cli,
        runtime_python_for_eval,
        train_artifact_root,
        train_config_path,
        train_deployment_environment,
        train_python,
        train_repo_root,
        train_supervisor,
    )


@app.cell
def _(mo):
    train_doctor_run = mo.ui.run_button(label="Run training doctor and check server PIDs")
    train_doctor_refresh = mo.ui.run_button(label="Refresh doctor status and report")
    mo.vstack([mo.md("## 2. Doctor report and vLLM-stopped verification"), mo.hstack([train_doctor_run, train_doctor_refresh])])
    return train_doctor_refresh, train_doctor_run


@app.cell
def _(
    mo,
    os,
    safe_text,
    tail_log,
    train_artifact_root,
    train_config_path,
    train_doctor_run,
    train_doctor_refresh,
    train_deployment_environment,
    train_python,
    train_repo_root,
    train_supervisor,
):
    train_doctor_result = {"status": "Run this check before every training launch."}
    train_doctor_report = ""
    live_server_pids = []
    if train_doctor_run.value or train_doctor_refresh.value:
        for pid_path in train_artifact_root.glob("runs/*/logs/model_server.pid"):
            try:
                server_pid = int(pid_path.read_text(encoding="utf-8").strip())
                os.kill(server_pid, 0)
                live_server_pids.append({"pid": server_pid, "path": str(pid_path)})
            except (OSError, ValueError):
                continue
    if train_doctor_run.value:
        try:
            _status = train_supervisor.start(
                "train-doctor",
                [train_python, "-m", "src.mini.doctor", "--config", train_config_path, "--environment-profile", "train", "--without-model", "--json"],
                cwd=train_repo_root,
                environment=train_deployment_environment,
            )
            train_doctor_result = {
                "doctor_pid": _status.pid,
                "doctor_log": _status.log_path,
                "live_model_servers": live_server_pids,
                "gpu_exclusive": not live_server_pids,
            }
        except Exception as exc:
            train_doctor_result = {"error": safe_text(exc)}
    if train_doctor_refresh.value:
        try:
            _status = train_supervisor.status("train-doctor")
            if _status is None:
                train_doctor_result = {"status": "No training doctor job has been launched."}
            else:
                train_doctor_result = {
                    "state": _status.state,
                    "pid": _status.pid,
                    "log": _status.log_path,
                    "return_code": _status.return_code,
                    "live_model_servers": live_server_pids,
                    "gpu_exclusive": not live_server_pids,
                }
                train_doctor_report = f"```text\n{tail_log(_status.log_path, lines=240)}\n```"
        except Exception as exc:
            train_doctor_result = {"error": safe_text(exc)}
    mo.vstack([mo.json(train_doctor_result), mo.md(train_doctor_report)])
    return


@app.cell
def _(mo):
    selected_run_input = mo.ui.text(label="Prepared run ID", full_width=True)
    select_run = mo.ui.run_button(label="Load selected run")
    mo.vstack([mo.md("## 3. Dataset and run selection"), selected_run_input, select_run])
    return select_run, selected_run_input


@app.cell
def _(
    mo,
    resolve_run_directory,
    safe_text,
    select_run,
    selected_run_input,
    train_artifact_root,
):
    selected_run_dir = None
    run_selection_result = {"status": "Enter a run ID and load it."}
    if selected_run_input.value.strip():
        try:
            selected_run_dir = resolve_run_directory(train_artifact_root, selected_run_input.value)
            if select_run.value and not selected_run_dir.is_dir():
                raise FileNotFoundError(f"run does not exist: {selected_run_dir}")
            run_selection_result = {
                "run_id": selected_run_dir.name,
                "run_directory": str(selected_run_dir),
                "exists": selected_run_dir.is_dir(),
            }
        except Exception as exc:
            run_selection_result = {"error": safe_text(exc)}
    mo.json(run_selection_result)
    return (selected_run_dir,)


@app.cell
def _(json, mo, read_json_redacted, safe_text, selected_run_dir):
    dataset_inspection = {"status": "Load a run to inspect its dataset manifest and one shape-only sample."}
    if selected_run_dir is not None:
        try:
            dataset_manifest = read_json_redacted(selected_run_dir / "datasets" / "dataset_manifest.json")
            sample_path = selected_run_dir / "datasets" / "sft_train.json"
            sample_payload = json.loads(sample_path.read_text(encoding="utf-8"))
            first_sample = sample_payload[0] if sample_payload else {}
            dataset_inspection = {
                "manifest": dataset_manifest,
                "sample_shape": {
                    "fields": sorted(first_sample),
                    "field_lengths": {key: len(str(value)) for key, value in first_sample.items()},
                },
            }
        except Exception as exc:
            dataset_inspection = {"error": safe_text(exc)}
    mo.vstack([mo.md("## 4. Dataset manifest and sample inspection"), mo.json(dataset_inspection)])
    return


@app.cell
def _(mo, redact, safe_text, selected_run_dir, train_repo_root, yaml):
    training_preview = {"status": "Load a run to preview training configuration."}
    try:
        shared_yaml_path = train_repo_root / "configs" / "mini" / "llamafactory_sft.yaml"
        shared_yaml = redact(yaml.safe_load(shared_yaml_path.read_text(encoding="utf-8")))
        training_preview = {"shared_template_read_only": shared_yaml}
        if selected_run_dir is not None:
            resolved_candidates = sorted((selected_run_dir / "training").glob("resolved_llamafactory*.yaml"))
            training_preview["resolved_run_files"] = [str(path) for path in resolved_candidates]
            training_preview["resolved_non_secret_paths"] = {
                "dataset_dir": str(selected_run_dir / "datasets"),
                "training_dir": str(selected_run_dir / "training"),
                "adapter_dir": str(selected_run_dir / "training" / "adapter"),
            }
    except Exception as exc:
        training_preview = {"error": safe_text(exc)}
    mo.vstack(
        [
            mo.md("## 5. Training configuration preview"),
            mo.json(training_preview),
            mo.md("The shared YAML is never modified; render commands create run-specific YAML files."),
        ]
    )
    return


@app.cell
def _(mo):
    smoke_batch = mo.ui.dropdown(options={"Batch 2": 2, "Batch 1": 1}, value="Batch 2", label="Per-device batch")
    render_smoke = mo.ui.run_button(label="Render 20-step smoke YAML")
    start_smoke = mo.ui.run_button(label="Start smoke training")
    verify_smoke = mo.ui.run_button(label="Verify 20-step smoke checkpoint")
    stop_smoke = mo.ui.run_button(label="Gracefully stop smoke training")
    mo.vstack([mo.md("## 6. Smoke training"), smoke_batch, mo.hstack([render_smoke, start_smoke, verify_smoke, stop_smoke])])
    return render_smoke, smoke_batch, start_smoke, stop_smoke, verify_smoke


@app.cell
def _(
    llamafactory_cli,
    mo,
    render_smoke,
    safe_text,
    selected_run_dir,
    smoke_batch,
    start_smoke,
    stop_smoke,
    train_config_path,
    train_deployment_environment,
    train_python,
    train_repo_root,
    train_supervisor,
    verify_smoke,
):
    smoke_result = "Render first, inspect the run-scoped YAML, then launch."
    try:
        if selected_run_dir is None and (render_smoke.value or start_smoke.value or verify_smoke.value):
            raise ValueError("load a prepared run first")
        if render_smoke.value:
            _status = train_supervisor.start(
                "render-smoke",
                [train_python, "-m", "src.mini.training", "render", "--config", train_config_path, "--run-id", selected_run_dir.name, "--profile", "smoke", "--per-device-batch-size", str(smoke_batch.value)],
                cwd=train_repo_root,
                environment=train_deployment_environment,
            )
            smoke_result = f"Render PID {_status.pid}; log: `{_status.log_path}`"
        if start_smoke.value:
            smoke_yaml = selected_run_dir / "training" / "resolved_llamafactory_smoke.yaml"
            _status = train_supervisor.start("training-smoke", [llamafactory_cli, "train", smoke_yaml], cwd=train_repo_root, environment=train_deployment_environment)
            smoke_result = f"Training PID {_status.pid}; streaming log: `{_status.log_path}`"
        if verify_smoke.value:
            _status = train_supervisor.start(
                "verify-smoke",
                [train_python, "-m", "src.mini.training", "verify", "--config", train_config_path, "--run-id", selected_run_dir.name, "--output-dir", selected_run_dir / "training" / "smoke", "--minimum-step", "20"],
                cwd=train_repo_root,
                environment=train_deployment_environment,
            )
            smoke_result = f"Verification PID {_status.pid}; log: `{_status.log_path}`"
        if stop_smoke.value:
            _status = train_supervisor.stop("training-smoke", graceful_timeout_seconds=60)
            smoke_result = "No smoke job found." if _status is None else f"Stop state: {_status.state}; PID {_status.pid}"
    except Exception as exc:
        smoke_result = safe_text(exc)
    mo.md(smoke_result)
    return


@app.cell
def _(mo):
    full_batch = mo.ui.dropdown(options={"Batch 2": 2, "Batch 1": 1}, value="Batch 2", label="Per-device batch")
    resume_checkpoint = mo.ui.text(label="Optional absolute checkpoint path", full_width=True)
    render_full = mo.ui.run_button(label="Render full/resume YAML")
    start_full = mo.ui.run_button(label="Start full training or resume")
    stop_full = mo.ui.run_button(label="Gracefully stop full training")
    refresh_training_logs = mo.ui.run_button(label="Refresh training status and logs")
    mo.vstack(
        [
            mo.md("## 7. Full training and resume"),
            full_batch,
            resume_checkpoint,
            mo.hstack([render_full, start_full, stop_full, refresh_training_logs]),
        ]
    )
    return full_batch, refresh_training_logs, render_full, resume_checkpoint, start_full, stop_full


@app.cell
def _(
    Path,
    full_batch,
    llamafactory_cli,
    mo,
    refresh_training_logs,
    render_full,
    resume_checkpoint,
    safe_text,
    selected_run_dir,
    start_full,
    stop_full,
    train_config_path,
    train_deployment_environment,
    train_python,
    train_repo_root,
    train_supervisor,
    tail_log,
):
    full_result = "A resume must use a trusted checkpoint inside this run."
    training_log_display = ""
    try:
        if selected_run_dir is None and (render_full.value or start_full.value):
            raise ValueError("load a prepared run first")
        if render_full.value:
            render_command = [train_python, "-m", "src.mini.training", "render", "--config", train_config_path, "--run-id", selected_run_dir.name, "--profile", "full", "--per-device-batch-size", str(full_batch.value)]
            if resume_checkpoint.value.strip():
                _checkpoint = Path(resume_checkpoint.value).expanduser().resolve()
                _checkpoint_root = (selected_run_dir / "training" / "checkpoints").resolve()
                if _checkpoint_root not in _checkpoint.parents:
                    raise ValueError("resume checkpoint must be inside this run's training/checkpoints directory")
                render_command.extend(["--resume-from-checkpoint", _checkpoint])
            _status = train_supervisor.start("render-full", render_command, cwd=train_repo_root, environment=train_deployment_environment)
            full_result = f"Render PID {_status.pid}; log: `{_status.log_path}`"
        if start_full.value:
            full_yaml = selected_run_dir / "training" / "resolved_llamafactory.yaml"
            _status = train_supervisor.start("training-full", [llamafactory_cli, "train", full_yaml], cwd=train_repo_root, environment=train_deployment_environment)
            full_result = f"Training PID {_status.pid}; streaming log: `{_status.log_path}`"
        if stop_full.value:
            _status = train_supervisor.stop("training-full", graceful_timeout_seconds=60)
            full_result = "No full job found." if _status is None else f"Stop state: {_status.state}; PID {_status.pid}"
        if refresh_training_logs.value:
            _log_parts = []
            for _status in train_supervisor.list_statuses():
                if _status.name.startswith(("training-", "render-", "verify-")):
                    _log_parts.append(
                        f"### {_status.name} — PID {_status.pid} ({_status.state})\n"
                        f"Log: `{_status.log_path}`\n```text\n{tail_log(_status.log_path)}\n```"
                    )
            training_log_display = "\n".join(_log_parts)
    except Exception as exc:
        full_result = safe_text(exc)
    mo.vstack([mo.md(full_result), mo.md(training_log_display)])
    return


@app.cell
def _(mo):
    adapter_check = mo.ui.run_button(label="Verify checkpoint and promote adapter")
    mo.vstack([mo.md("## 8. Adapter integrity check"), adapter_check])
    return (adapter_check,)


@app.cell
def _(
    adapter_check,
    mo,
    safe_text,
    selected_run_dir,
    train_config_path,
    train_deployment_environment,
    train_python,
    train_repo_root,
    train_supervisor,
):
    adapter_result = "Verification checks loss, trainer state, LoRA files, and secret leakage."
    if adapter_check.value:
        try:
            if selected_run_dir is None:
                raise ValueError("load a trained run first")
            _status = train_supervisor.start(
                "verify-adapter",
                [train_python, "-m", "src.mini.training", "verify", "--config", train_config_path, "--run-id", selected_run_dir.name, "--output-dir", selected_run_dir / "training" / "checkpoints", "--minimum-step", "1", "--promote-adapter"],
                cwd=train_repo_root,
                environment=train_deployment_environment,
            )
            adapter_result = f"Verification PID {_status.pid}; log: `{_status.log_path}`"
        except Exception as exc:
            adapter_result = safe_text(exc)
    mo.md(adapter_result)
    return


@app.cell
def _(mo):
    evaluation_server_role = mo.ui.dropdown(options={"Teacher": "teacher", "Student LoRA": "student"}, value="Teacher", label="Endpoint role")
    evaluation_server_action = mo.ui.dropdown(options={"Start": "start", "Health": "health", "Stop": "stop"}, value="Start", label="Server action")
    evaluation_server_run = mo.ui.run_button(label="Run evaluation server action")
    mo.vstack(
        [
            mo.md("## 9. Teacher or student evaluation server"),
            evaluation_server_role,
            evaluation_server_action,
            evaluation_server_run,
        ]
    )
    return evaluation_server_action, evaluation_server_role, evaluation_server_run


@app.cell
def _(
    evaluation_server_action,
    evaluation_server_role,
    evaluation_server_run,
    mo,
    runtime_python_for_eval,
    safe_text,
    selected_run_dir,
    train_artifact_root,
    train_config_path,
    train_deployment_environment,
    train_repo_root,
    train_supervisor,
):
    evaluation_server_result = "Stop training before starting either endpoint."
    if evaluation_server_run.value:
        try:
            if selected_run_dir is None:
                raise ValueError("load a run first")
            _role = evaluation_server_role.value
            _action = evaluation_server_action.value
            server_environment = {
                **train_deployment_environment,
                "MOLAB_VLLM_RUN_DIR": str(selected_run_dir),
                "MOLAB_VLLM_CONFIG": str(train_config_path),
                "MOLAB_VLLM_PYTHON": str(runtime_python_for_eval),
                "MOLAB_VLLM_EXECUTABLE": str(train_repo_root / ".venv-mini-runtime" / "bin" / "vllm"),
            }
            if _role == "teacher":
                server_environment["MOLAB_VLLM_MODEL"] = "Qwen/Qwen3-14B"
                server_environment["MOLAB_VLLM_EXPECTED_MODEL"] = "Qwen/Qwen3-14B"
            else:
                adapter_dir = (selected_run_dir / "training" / "adapter").resolve()
                server_environment.update(
                    {
                        "MOLAB_VLLM_MODEL": "Qwen/Qwen3-8B",
                        "MOLAB_VLLM_EXPECTED_MODEL": "envfactory-mini-student",
                        "MOLAB_VLLM_LORA_MODULE": f"envfactory-mini-student={adapter_dir}",
                        "MOLAB_VLLM_MAX_LORA_RANK": "64",
                    }
                )
            _status = train_supervisor.start(
                f"evaluation-server-{_role}-{_action}",
                ["bash", train_repo_root / "src" / "serve" / "vllm_molab.sh", _action],
                cwd=train_repo_root,
                environment=server_environment,
            )
            evaluation_server_result = f"Launcher PID {_status.pid}; log: `{_status.log_path}`; server PID file: `{selected_run_dir / 'logs' / 'model_server.pid'}`"
        except Exception as exc:
            evaluation_server_result = safe_text(exc)
    mo.md(evaluation_server_result)
    return


@app.cell
def _(mo):
    evaluation_role = mo.ui.dropdown(options={"Teacher": "teacher", "Student LoRA": "student"}, value="Teacher", label="Candidate")
    evaluation_run = mo.ui.run_button(label="Run held-out executable evaluation")
    evaluation_refresh = mo.ui.run_button(label="Refresh report and logs")
    mo.vstack([mo.md("## 10. Evaluation controls and report"), evaluation_role, mo.hstack([evaluation_run, evaluation_refresh])])
    return evaluation_refresh, evaluation_role, evaluation_run


@app.cell
def _(
    evaluation_refresh,
    evaluation_role,
    evaluation_run,
    mo,
    runtime_python_for_eval,
    safe_text,
    selected_run_dir,
    tail_log,
    train_config_path,
    train_deployment_environment,
    train_repo_root,
    train_supervisor,
):
    evaluation_result = "Teacher and student must use the same frozen suite."
    report_text = ""
    try:
        if evaluation_run.value:
            if selected_run_dir is None:
                raise ValueError("load a run first")
            _role = evaluation_role.value
            _command = [runtime_python_for_eval, "-m", "src.mini.evaluate", "--config", train_config_path, "--run-id", selected_run_dir.name, "--candidate", _role]
            if _role == "teacher":
                _command.extend(["--model", "Qwen/Qwen3-14B"])
            else:
                _command.extend(["--model", "envfactory-mini-student", "--student-serving-mode", "lora", "--adapter-path", selected_run_dir / "training" / "adapter", "--max-lora-rank", "64"])
            _status = train_supervisor.start(f"evaluation-{_role}", _command, cwd=train_repo_root, environment=train_deployment_environment)
            evaluation_result = f"Evaluation PID {_status.pid}; streaming log: `{_status.log_path}`"
        if evaluation_refresh.value and selected_run_dir is not None:
            report_path = selected_run_dir / "evaluation" / "report.md"
            report_text = report_path.read_text(encoding="utf-8") if report_path.is_file() else "Report is not available yet."
            log_parts = []
            for _status in train_supervisor.list_statuses():
                if _status.name.startswith("evaluation-"):
                    log_parts.append(f"### {_status.name} — PID {_status.pid} ({_status.state})\n```text\n{tail_log(_status.log_path)}\n```")
            report_text += "\n\n" + "\n".join(log_parts)
    except Exception as exc:
        evaluation_result = safe_text(exc)
    mo.vstack([mo.md(evaluation_result), mo.md(report_text)])
    return


@app.cell
def _(mo):
    train_export_destination = mo.ui.text(label="Absolute persistent destination", full_width=True)
    train_export_preview = mo.ui.run_button(label="Preview checklist and exact command")
    train_export_run = mo.ui.run_button(label="Explicitly export with rsync")
    mo.vstack(
        [
            mo.md("## 11. Artifact export checklist"),
            mo.md("Nothing uploads automatically. Export only after checking the listed artifacts."),
            train_export_destination,
            mo.hstack([train_export_preview, train_export_run]),
        ]
    )
    return train_export_destination, train_export_preview, train_export_run


@app.cell
def _(
    artifact_checklist,
    command_text,
    export_command,
    mo,
    safe_text,
    selected_run_dir,
    train_export_destination,
    train_export_preview,
    train_export_run,
    train_repo_root,
    train_supervisor,
):
    train_export_result = {"status": "Load a run and choose an absolute persistent destination."}
    if (train_export_preview.value or train_export_run.value) and selected_run_dir is not None:
        try:
            _command = export_command(selected_run_dir, train_export_destination.value)
            train_export_result = {"checklist": artifact_checklist(selected_run_dir), "command": command_text(_command)}
            if train_export_run.value:
                _status = train_supervisor.start("export-training-artifacts", _command, cwd=train_repo_root)
                train_export_result["started"] = {"pid": _status.pid, "log": _status.log_path}
        except Exception as exc:
            train_export_result = {"error": safe_text(exc)}
    mo.json(train_export_result)
    return


if __name__ == "__main__":
    app.run()
