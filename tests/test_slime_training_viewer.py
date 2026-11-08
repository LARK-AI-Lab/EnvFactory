import json

from src.app.slime_training_viewer import LogReader, create_app


def record(kind, index, values):
    return f"(Actor pid=123) [2026-10-23 12:00:00] INFO - {kind} {index}: {values!r}\n"


def test_merges_scalar_records_without_confusing_steps_or_missing_values(tmp_path):
    path = tmp_path / "run.log"
    path.write_text(
        "(Actor pid=123)   bf16 .............. True\n"
        "  reward_tau .............. 0.5\n"
        "  api_key .............. do-not-display\n"
        + record("perf", 2, {"perf/rollout_time": 100.0})
        + record("reward components", 2, {"rollout/trace_score": .25, "rollout/state_score": .5})
        + record("rollout", 2, {"rollout/raw_reward": .7})
        + record("step", 4, {"train/loss": .02})
        + record("step", 5, {"train/loss": .03})
        + record("eval", 0, {"eval/bfcl_v3": .43})
    )
    reader = LogReader()
    first = reader.read(path)
    assert first["config"] == {"bf16": "True", "reward_tau": "0.5"}
    row, = first["series"]["rollout"]
    assert row["id"] == 2
    assert row["values"] == {"perf/rollout_time": 100., "rollout/trace_score": .25,
                             "rollout/state_score": .5, "rollout/raw_reward": .7}
    assert [r["id"] for r in first["series"]["train"]] == [4, 5]
    assert first["series"]["eval"][0]["id"] == 0
    assert reader.read(path)["bytes_read"] == 0


def test_appended_partial_records_and_file_rotation(tmp_path):
    path = tmp_path / "run.log"
    line = record("step", 1, {"train/loss": .1})
    path.write_text(line[:-3])
    reader = LogReader()
    assert not reader.read(path)["series"]["train"]
    with path.open("a") as stream:
        stream.write(line[-3:])
    result = reader.read(path)
    assert result["bytes_read"] == 3
    assert result["series"]["train"][0]["values"]["train/loss"] == .1
    # Replacement can be larger than the previous log; inode identity matters.
    replacement = tmp_path / "replacement"
    replacement.write_text(record("step", 7, {"train/loss": .3, "train/grad_norm": .8}))
    replacement.replace(path)
    assert [r["id"] for r in reader.read(path)["series"]["train"]] == [7]
    path.write_text("")
    assert not reader.read(path)["series"]["train"]


def test_nonfinite_metrics_are_flagged_and_code_is_not_evaluated(tmp_path):
    path = tmp_path / "run.log"
    path.write_text(record("step", 0, {"train/loss": float("nan"), "train/grad_norm": float("inf"),
                                      "train/negative": -float("inf"), "train/ess_ratio": .2})
                    + "INFO - step 1: {'train/loss': __import__('os').getcwd()}\n")
    result = LogReader().read(path)
    assert len(result["nonfinite"]) == 3
    assert result["series"]["train"][0]["values"]["train/loss"] is None
    assert result["series"]["train"][0]["values"]["train/ess_ratio"] == .2
    assert result["unparsed_records"] == 1
    json.dumps(result, allow_nan=False)


def test_routes_only_read_discovered_logs_and_start_without_dumps(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "run.log").write_text(record("rollout", 0, {"rollout/raw_reward": .6}))
    (logs / "rollout_data").mkdir()
    # A corrupt dump must have no bearing on this viewer.
    (logs / "rollout_data" / "0.pt").write_bytes(b"not a torch dump")
    outside = tmp_path / "outside.log"
    outside.write_text("private")
    (logs / "outside.log").symlink_to(outside)
    client = create_app([logs]).test_client()
    assert client.get("/").status_code == 200
    assert [r["id"] for r in client.get("/api/runs").json["runs"]] == ["0/run.log"]
    assert client.get("/api/run?run=0/run.log").json["series"]["rollout"][0]["values"]["rollout/raw_reward"] == .6
    for name in ["0/../outside.log", "0/outside.log", str(outside), "missing"]:
        assert client.get("/api/run", query_string={"run": name}).status_code == 404
    assert client.get("/api/run?run=0/run.log").json["bytes_read"] == 0


def test_timeline_pairs_stages_and_keeps_evaluation_separate(tmp_path):
    def line(message, stamp, actor="Actor pid=123"):
        return f"({actor}) [2026-10-23 {stamp}] INFO - {message}\n"

    path = tmp_path / "run.log"
    path.write_text(
        line("Timer train start", "12:00:00")
        + line("Timer ref_log_probs start", "12:00:00")
        + "[2026-10-23 12:01:00] timer.py:32 - Timer ref_log_probs end (elapsed: 60.1s)\n"
        + line("rollout 2: {'rollout/raw_reward': 0.7}", "12:01:00")
        + line("Timer actor_train start", "12:01:00")
        + line("Timer actor_train end (elapsed: 120.1s)", "12:03:00")
        + line("Timer train end (elapsed: 180.2s)", "12:03:00")
        + line("perf 2: {'perf/train_time': 180.23}", "12:03:01")
        + line("Timer update_weights start", "12:03:01")
        + line("Timer update_weights end (elapsed: 1.1s)", "12:03:02")
        + line("Runtime eval: 800 samples for bfcl_v3", "12:03:05", "Manager pid=456")
        + line("eval 2: {'eval/bfcl_v3': 0.42}", "12:23:05", "Manager pid=456")
        + line("perf 3: {'perf/rollout_time': 90.5}", "12:25:00", "Manager pid=456")
        + line("saving checkpoint at iteration 2 to /models", "12:26:00.100000")
        + line("successfully saved checkpoint from iteration 2 to /models", "12:26:15.200000")
        + line("Timer train start", "12:27:00")
    )
    reader = LogReader()
    data = reader.read(path)
    train = [e for e in data["timeline"] if e["stage"] == "train"]
    assert len(train) == 2  # No duplicate when perf arrives one second later.
    assert train[0]["rollout_id"] == 2 and train[0]["seconds"] == 180.2
    assert train[1]["end"] == "" and train[1]["seconds"] is None
    eval_event, = [e for e in data["timeline"] if e["stage"] == "eval"]
    assert eval_event["rollout_id"] == 2 and eval_event["seconds"] == 1200
    assert eval_event["start"] == "2026-10-23 12:03:05"
    generated, = [e for e in data["timeline"] if e["stage"] == "rollout"]
    assert generated["rollout_id"] == 3 and generated["seconds"] == 90.5
    assert generated["derived_start"] is True
    checkpoint, = [e for e in data["timeline"] if e["stage"] == "checkpoint"]
    assert checkpoint["seconds"] == 15.1
    nested = [e for e in data["timeline"] if e["stage"] in {"actor_train", "ref_log_probs"}]
    assert [e["rollout_id"] for e in nested] == [2, 2]
    assert reader.read(path)["timeline"] == data["timeline"]
    with path.open("a") as stream:
        stream.write(line("Timer train end (elapsed: 60.0s)", "12:28:00")
                     + line("perf 4: {'perf/train_time': 60.0}", "12:28:00"))
    updated = reader.read(path)
    train = [e for e in updated["timeline"] if e["stage"] == "train"]
    assert len(train) == 2 and train[1]["rollout_id"] == 4
    assert train[1]["seconds"] == 60 and train[1]["end"] == "2026-10-23 12:28:00"


def test_timeline_does_not_invent_missing_or_ambiguous_boundaries(tmp_path):
    path = tmp_path / "run.log"
    path.write_text(record("eval", 0, {"eval/bfcl_v3": .43})
                    + "(Actor pid=1) [2026-10-23 12:01:00] timer.py:24 - Timer train start\n"
                    + "(Actor pid=2) [2026-10-23 12:01:00] timer.py:24 - Timer train start\n"
                    + "[2026-10-23 12:02:00] timer.py:32 - Timer train end (elapsed: 60.0s)\n")
    events = LogReader().read(path)["timeline"]
    assert events[0]["stage"] == "eval"
    assert events[0]["start"] == "" and events[0]["seconds"] is None
    train = [e for e in events if e["stage"] == "train"]
    assert len(train) == 3
    assert sum(not e["end"] for e in train) == 2
    assert next(e for e in train if e["end"])["start"] == ""


def test_status_tracks_recorded_phases_without_claiming_liveness(tmp_path):
    path = tmp_path / "run.log"
    path.write_text("Running entrypoint for job run-1: python train.py\n")
    reader = LogReader()
    assert reader.read(path)["status"]["state"] == "preparing"
    for message, expected in [
        ("Runtime eval: 800 samples for bfcl_v3", "evaluating"),
        ("eval 0: {'eval/bfcl_v3': 0.43}", "running"),
        ("Rollout generation:   0%|          | 0/2048 [00:00<?, ?it/s]", "rollout"),
        ("Timer train start", "training"),
        ("Timer train end (elapsed: 60.0s)", "running"),
        ("Timer update_weights start", "syncing"),
    ]:
        with path.open("a") as stream:
            prefix = "" if message.startswith("Rollout generation:") else "[2026-10-23 12:00:00] INFO - "
            stream.write(prefix + message + "\n")
        status = reader.read(path)["status"]
        assert status["state"] == expected
        assert status["terminal"] is False
    # Neither incidental errors nor completion of every optimizer step prove exit.
    with path.open("a") as stream:
        stream.write("Traceback (most recent call last):\nCUDA out of memory\n"
                     "First rollout sample: Job 'other' failed\n"
                     + record("step", 39, {"train/loss": .1}))
    assert reader.read(path)["status"]["state"] == "training"


def test_status_requires_explicit_terminal_job_outcomes(tmp_path):
    reader = LogReader()
    for outcome, state in [("succeeded", "complete"), ("failed. Status message: process exited", "failed"),
                           ("was stopped", "aborted"), ("was interrupted", "aborted")]:
        path = tmp_path / (outcome + ".log")
        path.write_text(f"Job 'run-1' {outcome}\n" + record("step", 0, {"train/loss": .1}))
        status = reader.read(path)["status"]
        assert status["state"] == state and status["terminal"] is True
        assert status["evidence"].startswith("Job 'run-1'")
    path = tmp_path / "submitted.log"
    path.write_text("Job 'run-1' submitted successfully\n")
    assert reader.read(path)["status"]["state"] == "unknown"


def test_ray_cli_prefixes_and_ansi_terminal_outcomes(tmp_path):
    for level, outcome, state in [("SUCC", "succeeded", "complete"),
                                   ("ERR", "failed", "failed"),
                                   ("WARN", "was stopped", "aborted")]:
        path = tmp_path / f"{level}.log"
        path.write_text(record("step", 0, {"train/loss": .1})
                        + f"2026-11-04 18:24:54,067\t{level} cli.py:75 -- "
                        + f"\x1b[32mJob 'run-1' {outcome}\x1b[39m\n")
        status = LogReader().read(path)["status"]
        assert status["state"] == state and status["terminal"]
        assert status["time"] == "2026-11-04 18:24:54.067"


def test_slurm_cancellation_is_terminal_unless_ray_already_succeeded(tmp_path):
    cancel = "slurmstepd: error: *** JOB 809564 ON ACD1-27 CANCELLED AT 2026-11-08T02:43:14 ***\n"
    path = tmp_path / "cancelled.log"
    path.write_text(record("step", 3, {"train/loss": .1}) + cancel)
    status = LogReader().read(path)["status"]
    assert status["state"] == "aborted" and status["terminal"]
    assert status["time"] == "2026-11-08 02:43:14"
    assert status["evidence"] == "Slurm JOB 809564 ON ACD1-27 CANCELLED AT 2026-11-08T02:43:14"
    timed_out = tmp_path / "timeout.log"
    timed_out.write_text(cancel.replace(" ***", " DUE TO TIME LIMIT ***"))
    assert LogReader().read(timed_out)["status"]["state"] == "aborted"
    finished = tmp_path / "finished.log"
    finished.write_text("Job 'raysubmit_1' succeeded\n" + cancel)
    assert LogReader().read(finished)["status"]["state"] == "complete"


def run_dir(root, name, text=None):
    directory = root / name
    directory.mkdir()
    path = directory / "training.log"
    path.write_text(record("step", 0, {"train/loss": .1}) if text is None else text)
    return path


def test_run_directories_are_experiments_and_auxiliary_or_outside_logs_are_not(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    path = run_dir(runs, "EnvFactory-4B")
    (runs / "EnvFactory-4B" / "monitor.log").write_text("auxiliary output\n")
    for name in ["monitor.log", "process_data_20261028.log"]:
        (runs / name).write_text("auxiliary output\n")
    (runs / "no-log-yet").mkdir()
    outside = tmp_path / "private"
    outside.mkdir()
    (outside / "training.log").write_text("private")
    (runs / "linked").symlink_to(outside)
    client = create_app([runs], queue=lambda: {"jobs": {}, "checked_at": 1}).test_client()
    items = client.get("/api/runs").json["runs"]
    assert [(item["id"], item["name"]) for item in items] == [("0/EnvFactory-4B/training.log", "EnvFactory-4B")]
    assert client.get("/api/run?run=0/EnvFactory-4B/training.log").json["path"] == str(path)
    for name in ["0/linked/training.log", "0/monitor.log", "0/EnvFactory-4B/monitor.log",
                 "0/../private/training.log"]:
        assert client.get("/api/run", query_string={"run": name}).status_code == 404
    # A root may be one run directory; it keeps the directory's name.
    single = create_app([runs / "EnvFactory-4B"], queue=lambda: {"jobs": None}).test_client()
    assert [item["name"] for item in single.get("/api/runs").json["runs"]] == ["EnvFactory-4B"]


def test_lifecycle_uses_slurm_queue_and_recorded_outcomes_never_log_age(tmp_path):
    path = run_dir(tmp_path, "run-1")
    queue = {"jobs": {}, "checked_at": 1}
    client = create_app([tmp_path], queue=lambda: queue).test_client()

    def get():
        return client.get("/api/run?run=0/run-1/training.log").json

    assert get()["status"]["state"] == "interrupted"
    queue["jobs"] = None  # A failed queue query is not proof of interruption.
    assert get()["status"]["state"] == "unknown"
    queue["jobs"] = {str(tmp_path / "other" / "training.log"): {"id": "2", "state": "RUNNING"}}
    assert get()["status"]["state"] == "interrupted"
    for slurm_state, expected in [("RUNNING", "running"), ("COMPLETING", "running"),
                                  ("PENDING", "pending"), ("CONFIGURING", "pending")]:
        queue["jobs"] = {str(path): {"id": "809618", "state": slurm_state}}
        status = get()["status"]
        assert status["state"] == expected and status["source"] == "slurm"
        assert status["evidence"] == f"Slurm job 809618: {slurm_state}"
    assert get()["phase"]["state"] == "training"
    # The trainer's recorded exit outranks a job still finishing in the queue.
    with path.open("a") as stream:
        stream.write("2026-11-04 18:24:54,067\tSUCC cli.py:67 -- Job 'raysubmit_1' succeeded\n")
    payload = get()
    assert payload["status"]["state"] == "complete" and payload["status"]["source"] == "log"
    assert payload["phase"]["state"] == "training"
    assert client.get("/api/runs").json["runs"][0]["status"]["state"] == "complete"


def test_bare_log_has_unknown_liveness_without_querying_slurm(tmp_path):
    path = tmp_path / "old-experiment.log"
    path.write_text(record("step", 49, {"train/loss": .1}))

    def queue():
        raise AssertionError("bare logs have no Slurm job")

    client = create_app([tmp_path], queue=queue).test_client()
    assert client.get("/api/run?run=0/old-experiment.log").json["status"]["state"] == "unknown"
    with path.open("a") as stream:
        stream.write("2026-11-04 18:24:54,067\tSUCC cli.py:67 -- Job 'run-1' succeeded\n")
    assert client.get("/api/runs").json["runs"][0]["status"]["state"] == "complete"


def test_duplicate_run_names_remain_individually_selectable(tmp_path):
    roots = [tmp_path / "first", tmp_path / "second"]
    for index, root in enumerate(roots):
        root.mkdir()
        run_dir(root, "same-name", record("step", index, {"train/loss": index + .1}))
    client = create_app(roots, queue=lambda: {"jobs": None}).test_client()
    items = client.get("/api/runs").json["runs"]
    assert len({item["id"] for item in items}) == 2
    assert len({item["label"] for item in items}) == 2
    assert {
        client.get("/api/run", query_string={"run": item["id"]}).json["series"]["train"][0]["id"]
        for item in items
    } == {0, 1}
