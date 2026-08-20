"""Safe orchestration helpers shared by the MoLab marimo notebooks.

The notebooks deliberately contain presentation and command construction only.
Long-running work remains in the existing ``src.mini`` command-line modules and
is launched here as an observable subprocess.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import signal
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .artifacts import atomic_write_json


_JOB_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_SECRET_KEY = re.compile(r"(?:^|_)(?:authorization|cookie|password|secret|token|api_key)(?:$|_)", re.I)


class NotebookError(RuntimeError):
    """A safe, user-actionable notebook orchestration error."""


class JobAlreadyRunning(NotebookError):
    """Raised when a reactive rerun tries to replace a live job."""


@dataclass(frozen=True)
class JobStatus:
    name: str
    pid: int
    state: str
    command: list[str]
    cwd: str
    log_path: str
    started_at: str
    return_code: int | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret_values(environment: Mapping[str, str] | None = None) -> tuple[str, ...]:
    values = environment if environment is not None else os.environ
    candidates = []
    for key, value in values.items():
        if _SECRET_KEY.search(key) and not key.lower().endswith("_env") and len(value) >= 4:
            candidates.append(value)
    return tuple(sorted(set(candidates), key=len, reverse=True))


def safe_text(value: object, *, environment: Mapping[str, str] | None = None) -> str:
    """Remove currently defined secret values from notebook-visible text."""
    result = str(value)
    for secret in _secret_values(environment):
        result = result.replace(secret, "[REDACTED]")
    return result


def redact(value: Any, *, environment: Mapping[str, str] | None = None) -> Any:
    """Recursively redact secret-shaped fields and secret values."""
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = str(raw_key)
            if _SECRET_KEY.search(key) and not key.lower().endswith("_env"):
                output[key] = "[REDACTED]"
            else:
                output[key] = redact(child, environment=environment)
        return output
    if isinstance(value, list):
        return [redact(child, environment=environment) for child in value]
    if isinstance(value, tuple):
        return tuple(redact(child, environment=environment) for child in value)
    if isinstance(value, str):
        return safe_text(value, environment=environment)
    return value


def validate_run_id(run_id: str) -> str:
    candidate = run_id.strip()
    if not _RUN_ID.fullmatch(candidate) or candidate in {".", ".."}:
        raise NotebookError("run ID must contain only letters, digits, '.', '_', and '-'")
    return candidate


def resolve_run_directory(artifact_root: str | Path, run_id: str) -> Path:
    root = Path(artifact_root).expanduser().resolve()
    run_dir = (root / "runs" / validate_run_id(run_id)).resolve()
    if run_dir.parent != (root / "runs").resolve():
        raise NotebookError("run directory escaped the configured artifact root")
    return run_dir


def validate_export_destination(destination: str | Path, *, run_dir: str | Path) -> Path:
    raw = str(destination).strip()
    if not raw:
        raise NotebookError("choose an explicit artifact export destination")
    target = Path(raw).expanduser()
    if not target.is_absolute():
        raise NotebookError("artifact export destination must be an absolute path")
    target = target.resolve()
    source = Path(run_dir).resolve()
    if target == source or source in target.parents or target in source.parents:
        raise NotebookError("export destination must be separate from the run directory")
    return target


def export_command(run_dir: str | Path, destination: str | Path) -> list[str]:
    """Return the explicit, non-deleting rsync command used by both notebooks."""
    source = Path(run_dir).resolve()
    target_root = validate_export_destination(destination, run_dir=source)
    return ["rsync", "-a", "--protect-args", f"{source}/", f"{target_root / source.name}/"]


def command_text(command: Sequence[str]) -> str:
    return shlex.join([str(part) for part in command])


def session_clock(started_monotonic: float, *, warning_after_hours: float = 10.5) -> dict[str, Any]:
    elapsed = max(0.0, time.monotonic() - started_monotonic)
    return {
        "elapsed_seconds": elapsed,
        "elapsed_hours": elapsed / 3600.0,
        "warning": elapsed >= warning_after_hours * 3600,
        "warning_after_hours": warning_after_hours,
    }


def tail_log(path: str | Path, *, lines: int = 120, max_bytes: int = 256_000) -> str:
    """Read a bounded, redacted log tail for reactive display."""
    log_path = Path(path)
    if not log_path.is_file():
        return ""
    with log_path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes))
        payload = handle.read().decode("utf-8", errors="replace")
    return safe_text("\n".join(payload.splitlines()[-lines:]))


def read_json_redacted(path: str | Path) -> Any:
    source = Path(path)
    try:
        return redact(json.loads(source.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise NotebookError(safe_text(f"could not read JSON artifact {source}: {exc}")) from exc


def artifact_checklist(run_dir: str | Path) -> list[dict[str, Any]]:
    """Report the run artifacts users should persist before session end."""
    root = Path(run_dir).resolve()
    required = (
        ("run manifest", root / "run_manifest.json"),
        ("resolved config", root / "resolved_config.toml"),
        ("environment report", root / "environment.json"),
        ("generation logs", root / "logs"),
        ("completed trajectories", root / "trajectories" / "completed"),
        ("dataset manifest", root / "datasets" / "dataset_manifest.json"),
        ("training adapter", root / "training" / "adapter"),
        ("evaluation report", root / "evaluation" / "report.md"),
    )
    return [
        {"artifact": label, "path": str(path), "present": path.exists()}
        for label, path in required
    ]


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import psutil

            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except ImportError:
            pass
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class NotebookProcessSupervisor:
    """Persistent, idempotent subprocess supervisor for reactive notebooks.

    State files let a restarted notebook show a surviving subprocess. A live
    named job is never replaced, which is the last line of defense against a
    reactive dependency change relaunching expensive work.
    """

    def __init__(self, artifact_root: str | Path):
        self.artifact_root = Path(artifact_root).expanduser().resolve()
        self.state_dir = self.artifact_root / "notebook" / "jobs"
        self.log_dir = self.artifact_root / "notebook" / "logs"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._processes: dict[str, subprocess.Popen[str]] = {}
        self._handles: dict[str, Any] = {}

    @staticmethod
    def _name(name: str) -> str:
        if not _JOB_NAME.fullmatch(name):
            raise NotebookError("job name must use letters, digits, '.', '_', or '-'")
        return name

    def _state_path(self, name: str) -> Path:
        return self.state_dir / f"{self._name(name)}.json"

    def _load(self, name: str) -> JobStatus | None:
        path = self._state_path(name)
        if not path.is_file():
            return None
        try:
            return JobStatus(**json.loads(path.read_text(encoding="utf-8")))
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise NotebookError(f"invalid notebook job state {path}: {exc}") from exc

    def _save(self, status: JobStatus) -> None:
        atomic_write_json(self._state_path(status.name), asdict(status))

    def status(self, name: str) -> JobStatus | None:
        name = self._name(name)
        status = self._load(name)
        if status is None:
            return None
        process = self._processes.get(name)
        return_code = process.poll() if process is not None else None
        if status.state not in {"running", "stopping"}:
            if process is not None and return_code is not None:
                self._close_handle(name)
            return status
        alive = (
            return_code is None
            and _pid_is_alive(status.pid)
        )
        if alive:
            return JobStatus(**{**asdict(status), "state": "running", "return_code": None})
        final_state = (
            "succeeded"
            if return_code == 0
            else "failed"
            if return_code is not None
            else "exited"
        )
        finished = JobStatus(
            **{
                **asdict(status),
                "state": final_state,
                "return_code": return_code,
            }
        )
        self._save(finished)
        self._close_handle(name)
        return finished

    def list_statuses(self) -> list[JobStatus]:
        statuses: list[JobStatus] = []
        for path in sorted(self.state_dir.glob("*.json")):
            status = self.status(path.stem)
            if status is not None:
                statuses.append(status)
        return statuses

    def start(
        self,
        name: str,
        command: Sequence[str | os.PathLike[str]],
        *,
        cwd: str | Path,
        environment: Mapping[str, str] | None = None,
    ) -> JobStatus:
        name = self._name(name)
        current = self.status(name)
        if current is not None and current.state in {"running", "stopping"}:
            raise JobAlreadyRunning(f"job '{name}' is already running with PID {current.pid}")
        argv = [str(part) for part in command]
        if not argv or any(not part for part in argv):
            raise NotebookError("subprocess command contains an empty argument")
        secret_environment = os.environ.copy()
        if environment:
            secret_environment.update(environment)
        for secret in _secret_values(secret_environment):
            if any(secret in part for part in argv):
                raise NotebookError("refusing to place a secret value in subprocess arguments")
        working_directory = Path(cwd).expanduser().resolve()
        if not working_directory.is_dir():
            raise NotebookError(f"subprocess working directory does not exist: {working_directory}")
        log_path = self.log_dir / f"{name}.log"
        log_handle = log_path.open("a", encoding="utf-8", buffering=1)
        child_environment = os.environ.copy()
        if environment:
            child_environment.update({str(key): str(value) for key, value in environment.items()})
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        try:
            process = subprocess.Popen(
                argv,
                cwd=working_directory,
                env=child_environment,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=os.name != "nt",
                creationflags=creationflags,
            )
        except OSError as exc:
            log_handle.close()
            raise NotebookError(safe_text(f"could not start job '{name}': {exc}")) from exc
        self._processes[name] = process
        self._handles[name] = log_handle
        status = JobStatus(
            name=name,
            pid=process.pid,
            state="running",
            command=argv,
            cwd=str(working_directory),
            log_path=str(log_path),
            started_at=utc_now(),
        )
        self._save(status)
        return status

    def stop(self, name: str, *, graceful_timeout_seconds: float = 30.0) -> JobStatus | None:
        name = self._name(name)
        status = self.status(name)
        if status is None or status.state not in {"running", "stopping"}:
            return status
        stopping = JobStatus(**{**asdict(status), "state": "stopping"})
        self._save(stopping)
        process = self._processes.get(name)
        if process is not None and os.name == "nt":
            try:
                process.send_signal(signal.CTRL_BREAK_EVENT)
            except OSError:
                # Some non-interactive Windows hosts do not attach a console
                # to the new group. Preserve the grace interval before kill.
                pass
        else:
            self._signal(status.pid, signal.SIGTERM)
        deadline = time.monotonic() + max(0.0, graceful_timeout_seconds)
        while _pid_is_alive(status.pid) and time.monotonic() < deadline:
            if process is not None:
                try:
                    process.wait(timeout=min(0.1, max(0.01, deadline - time.monotonic())))
                except subprocess.TimeoutExpired:
                    pass
            else:
                time.sleep(0.05)
        if _pid_is_alive(status.pid):
            if process is not None:
                process.kill()
            else:
                self._signal(
                    status.pid,
                    signal.SIGKILL if hasattr(signal, "SIGKILL") else signal.SIGTERM,
                )
            if process is not None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired as exc:
                    raise NotebookError(f"job '{name}' survived graceful and forced termination") from exc
        return_code = process.poll() if process is not None else None
        stopped = JobStatus(
            **{**asdict(status), "state": "stopped", "return_code": return_code}
        )
        self._save(stopped)
        self._close_handle(name)
        return stopped

    @staticmethod
    def _signal(pid: int, requested_signal: signal.Signals) -> None:
        try:
            if os.name != "nt":
                os.killpg(pid, requested_signal)
            else:
                os.kill(pid, requested_signal)
        except ProcessLookupError:
            return
        except OSError as exc:
            raise NotebookError(f"could not signal PID {pid}: {exc}") from exc

    def _close_handle(self, name: str) -> None:
        handle = self._handles.pop(name, None)
        if handle is not None and not handle.closed:
            handle.close()


__all__ = [
    "JobAlreadyRunning",
    "JobStatus",
    "NotebookError",
    "NotebookProcessSupervisor",
    "artifact_checklist",
    "command_text",
    "export_command",
    "read_json_redacted",
    "redact",
    "resolve_run_directory",
    "safe_text",
    "session_clock",
    "tail_log",
    "validate_export_destination",
    "validate_run_id",
]
