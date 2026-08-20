from __future__ import annotations

import json

import pytest

from src.mini.artifacts import append_jsonl, atomic_write_json, read_jsonl
from src.mini.manifest import RunLock, RunLockError, RunManifest
from src.mini.synthesize import deterministic_seeds


def _manifest() -> RunManifest:
    return RunManifest.create(
        run_id="unit-run",
        config_sha256="c" * 64,
        graph_sha256="g" * 64,
        catalog_sha256="a" * 64,
        teacher_model="teacher",
        target_trajectories=2,
        seeds=[11, 22],
        git_commit="abc1234",
        git_dirty=False,
    )


def test_manifest_round_trip_and_seed_invariants(tmp_path) -> None:
    path = tmp_path / "run_manifest.json"
    manifest = _manifest()
    manifest.state = "running"
    manifest.completed_seeds = [11]
    manifest.pending_seeds = [22]
    manifest.attempts_by_seed["11"] = 1
    manifest.checkpoint(path)

    loaded = RunManifest.load(path)
    assert loaded == manifest
    assert loaded.completed_seeds == [11]
    assert loaded.attempts_by_seed == {"11": 1, "22": 0}

    value = loaded.model_dump(mode="json")
    value["failed_seeds"] = [11]
    with pytest.raises(ValueError, match="both completed and failed"):
        RunManifest.model_validate(value)


def test_immutable_atomic_json_refuses_overwrite(tmp_path) -> None:
    path = tmp_path / "completed" / "1.json"
    atomic_write_json(path, {"attempt": 1}, overwrite=False)
    with pytest.raises(FileExistsError):
        atomic_write_json(path, {"attempt": 2}, overwrite=False)
    assert json.loads(path.read_text(encoding="utf-8")) == {"attempt": 1}


def test_jsonl_reader_tolerates_only_truncated_final_line(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    append_jsonl(path, {"event": 1})
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"event":')
    assert list(read_jsonl(path)) == [{"event": 1}]

    path.write_text('{"broken":\n{"event":2}\n', encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        list(read_jsonl(path))


def test_live_and_stale_run_locks_require_explicit_recovery(tmp_path) -> None:
    path = tmp_path / "run.lock"
    with RunLock(path):
        with pytest.raises(RunLockError, match="live PID"):
            RunLock(path).acquire()

    path.write_text('{"pid": 2147483647}\n', encoding="utf-8")
    with pytest.raises(RunLockError, match="recover-stale-lock"):
        RunLock(path).acquire()
    with RunLock(path, recover_stale=True):
        assert path.exists()
    assert not path.exists()


def test_seed_namespace_is_deterministic_ordered_and_unique() -> None:
    first = deterministic_seeds(42, 100)
    assert first == deterministic_seeds(42, 100)
    assert first != deterministic_seeds(43, 100)
    assert len(first) == len(set(first)) == 100
