"""Crash-safe artifact primitives used by the mini pipeline."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable


def _write_temporary(destination: Path, payload: bytes) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_write_bytes(destination: Path, payload: bytes, *, overwrite: bool = True) -> None:
    """Commit bytes from a same-directory temporary file.

    Immutable artifacts use a hard-link commit so an existing destination can
    never be replaced, including when two writers race.
    """
    destination = Path(destination)
    temporary = _write_temporary(destination, payload)
    try:
        if overwrite:
            os.replace(temporary, destination)
        else:
            os.link(temporary, destination)
            temporary.unlink()
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_text(destination: Path, value: str, *, overwrite: bool = True) -> None:
    atomic_write_bytes(destination, value.encode("utf-8"), overwrite=overwrite)


def atomic_write_json(destination: Path, value: object, *, overwrite: bool = True) -> None:
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    atomic_write_bytes(destination, payload, overwrite=overwrite)


def append_jsonl(destination: Path, value: object) -> None:
    """Append and durably flush one compact JSON event."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with destination.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(payload + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_jsonl(destination: Path) -> Iterable[dict[str, Any]]:
    """Read valid JSONL records, tolerating only a truncated final record."""
    if not destination.exists():
        return
    lines = destination.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1:
                return
            raise
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record {index + 1} is not an object")
        yield value


__all__ = [
    "append_jsonl",
    "atomic_write_bytes",
    "atomic_write_json",
    "atomic_write_text",
    "read_jsonl",
]
