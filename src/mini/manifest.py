"""Versioned run manifests and exclusive run locks for mini synthesis."""

from __future__ import annotations

import errno
import importlib.metadata
import json
import os
import platform
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .artifacts import atomic_write_json


RunState = Literal["created", "running", "interrupted", "completed", "failed"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _package_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


class RunManifest(BaseModel):
    """Complete, secret-free checkpoint for one synthesis run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    run_id: str
    state: RunState = "created"
    created_at: str
    updated_at: str
    completed_at: str | None = None
    git_commit: str | None = None
    git_dirty: bool = False
    config_sha256: str
    graph_sha256: str
    catalog_sha256: str
    python_version: str
    platform: str
    torch_version: str | None = None
    cuda_version: str | None = None
    vllm_version: str | None = None
    gpu_name: str | None = None
    gpu_vram_bytes: int | None = None
    host_ram_bytes: int | None = None
    cpu_count: int | None = None
    teacher_model: str
    teacher_revision: str | None = None
    student_model: str | None = None
    student_revision: str | None = None
    target_trajectories: int = Field(gt=0)
    seeds: list[int]
    completed_seeds: list[int] = Field(default_factory=list)
    failed_seeds: list[int] = Field(default_factory=list)
    pending_seeds: list[int] = Field(default_factory=list)
    attempts_by_seed: dict[str, int] = Field(default_factory=dict)
    failure_summary: dict[str, int] = Field(default_factory=dict)
    attempted_count: int = Field(default=0, ge=0)
    retried_count: int = Field(default=0, ge=0)
    valid_count: int = Field(default=0, ge=0)
    started_monotonic_seconds: float
    elapsed_seconds: float = Field(default=0, ge=0)
    trajectory_rate_per_hour: float = Field(default=0, ge=0)
    peak_gpu_memory_bytes: int | None = None
    peak_host_rss_bytes: int | None = None
    dataset_counts: dict[str, int] = Field(default_factory=dict)
    training_summary: dict[str, Any] = Field(default_factory=dict)
    evaluation_summary: dict[str, Any] = Field(default_factory=dict)

    @field_validator("seeds", "completed_seeds", "failed_seeds", "pending_seeds")
    @classmethod
    def unique_seeds(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("seed lists must not contain duplicates")
        return value

    @model_validator(mode="after")
    def validate_seed_partition(self) -> "RunManifest":
        seed_set = set(self.seeds)
        for label, values in (
            ("completed", self.completed_seeds),
            ("failed", self.failed_seeds),
            ("pending", self.pending_seeds),
        ):
            unknown = set(values).difference(seed_set)
            if unknown:
                raise ValueError(f"{label}_seeds contains unknown seeds: {sorted(unknown)}")
        if set(self.completed_seeds).intersection(self.failed_seeds):
            raise ValueError("a seed cannot be both completed and failed")
        return self

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        config_sha256: str,
        graph_sha256: str,
        catalog_sha256: str,
        teacher_model: str,
        target_trajectories: int,
        seeds: list[int],
        git_commit: str | None,
        git_dirty: bool,
        environment: dict[str, Any] | None = None,
    ) -> "RunManifest":
        environment = environment or {}
        packages = environment.get("packages", {})
        torch = packages.get("torch", {}) if isinstance(packages, dict) else {}
        gpu = environment.get("gpu", {})
        resources = environment.get("resources", {})
        now = utc_now()
        return cls(
            run_id=run_id,
            created_at=now,
            updated_at=now,
            git_commit=git_commit,
            git_dirty=git_dirty,
            config_sha256=config_sha256,
            graph_sha256=graph_sha256,
            catalog_sha256=catalog_sha256,
            python_version=platform.python_version(),
            platform=platform.platform(),
            torch_version=torch.get("version") or _package_version("torch"),
            cuda_version=torch.get("compiled_cuda_version"),
            vllm_version=(packages.get("vllm", {}) or {}).get("version")
            if isinstance(packages, dict)
            else _package_version("vllm"),
            gpu_name=gpu.get("name") if isinstance(gpu, dict) else None,
            gpu_vram_bytes=gpu.get("total_vram_bytes") if isinstance(gpu, dict) else None,
            host_ram_bytes=resources.get("host_ram_bytes")
            if isinstance(resources, dict)
            else None,
            cpu_count=resources.get("cpu_count") if isinstance(resources, dict) else os.cpu_count(),
            teacher_model=teacher_model,
            target_trajectories=target_trajectories,
            seeds=seeds,
            pending_seeds=list(seeds),
            attempts_by_seed={str(seed): 0 for seed in seeds},
            started_monotonic_seconds=time.monotonic(),
        )

    def checkpoint(self, path: Path) -> None:
        self.updated_at = utc_now()
        self.elapsed_seconds = max(0.0, time.monotonic() - self.started_monotonic_seconds)
        self.trajectory_rate_per_hour = (
            len(self.completed_seeds) * 3600 / self.elapsed_seconds
            if self.elapsed_seconds > 0
            else 0.0
        )
        atomic_write_json(path, self.model_dump(mode="json"))

    @classmethod
    def load(cls, path: Path) -> "RunManifest":
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid run manifest {path}: {exc}") from exc


class RunLockError(RuntimeError):
    """Raised when a run already has a live or unrecovered stale writer."""


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError as exc:
        return exc.errno == errno.EPERM
    return True


class RunLock:
    """Advisory exclusive-create lock containing diagnosable writer metadata."""

    def __init__(self, path: Path, *, recover_stale: bool = False):
        self.path = Path(path)
        self.recover_stale = recover_stale
        self.acquired = False
        self.lock_id = uuid.uuid4().hex

    def acquire(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                try:
                    record = json.loads(self.path.read_text(encoding="utf-8"))
                    pid = int(record.get("pid", -1))
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    pid = -1
                if _process_is_alive(pid):
                    raise RunLockError(f"run is already locked by live PID {pid}")
                if not self.recover_stale:
                    raise RunLockError(
                        "run lock appears stale; inspect it and pass --recover-stale-lock to replace it"
                    )
                try:
                    self.path.unlink()
                except FileNotFoundError:
                    pass
                self.recover_stale = False
                continue
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(
                    {
                        "pid": os.getpid(),
                        "started_at": utc_now(),
                        "hostname": socket.gethostname(),
                        "python": sys.executable,
                        "lock_id": self.lock_id,
                    },
                    handle,
                    sort_keys=True,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.acquired = True
            return self

    def release(self) -> None:
        if self.acquired:
            try:
                record = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                record = {}
            # Never remove a lock that was replaced while this process ran.
            if record.get("lock_id") == self.lock_id:
                self.path.unlink(missing_ok=True)
            self.acquired = False

    def __enter__(self) -> "RunLock":
        return self.acquire()

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.release()


__all__ = ["RunLock", "RunLockError", "RunManifest", "RunState", "utc_now"]
