"""Lightweight Slime configs and training dynamics; never opens rollout dumps.

    python src/app/slime_training_viewer.py --port 5005
    python src/app/slime_training_viewer.py --log-root /path/to/training_runs

By default reads the sibling ``training_runs`` directory. Each
``<root>/<run>/training.log`` is one Slurm-submitted run (``sbatch --output``);
bare ``<root>/*.log`` files are single-log runs; auxiliary logs are not runs.
Only recorded launch arguments and scalar log records are displayed: missing
metrics stay missing, and the current checkout's config is never substituted.
"""

import argparse
import ast
import math
import os
import re
import subprocess
import threading
import time
from collections import Counter, OrderedDict
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request

_PROJECT = Path(__file__).resolve().parents[2]
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_ARG = re.compile(r"(?:^|\s)([A-Za-z_]\w*)\s+\.{2,}\s+(.*?)\s*$")
_METRIC = re.compile(r" - (reward components|rollout|eval|step|perf) (\d+): (\{.*\})\s*$")
_TIME = re.compile(r"\[(\d{4}-\d\d-\d\d [^\]]+)\]")
_TIMER = re.compile(r" - Timer (\w+) (start|end)(?: \(elapsed: ([\d.]+)s\))?")
_PROCESS = re.compile(r"\(([^)]+pid=\d+)\)")
_CHECKPOINT = re.compile(r"(successfully saved checkpoint from|saving checkpoint at) iteration\s+(\d+)")
_SENSITIVE = re.compile(r"password|secret|api_key|access_token|credential", re.I)
_KINDS = {"reward components": "rollout", "perf": "rollout", "rollout": "rollout",
          "eval": "eval", "step": "train"}
_JOB_END = re.compile(r"^Job ['\"][^'\"]+['\"] (succeeded|failed|was stopped|was interrupted)(?:[.!\s].*)?$")
_CLI_PREFIX = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d[,.]\d+)\s+(?:SUCC|ERR|WARN|INFO)\s+cli\.py:\d+\s+--\s+")
# slurmstepd's record of scancel, time limit or preemption.
_SLURM_CANCEL = re.compile(r"\*\*\* (JOB \d+ ON \S+ CANCELLED AT (\S+)(?: DUE TO [^*]*?)?) \*\*\*")
_AUXILIARY = re.compile(r"(?:^|[_.-])(?:monitor|supervisor|observer|audit|prelaunch|startup|validation|process_data)(?:$|[_.-])", re.I)


def _status(entry, line, stamp):
    """Report recorded phases and explicit Ray/Slurm outcomes, never liveness."""
    prefix = _CLI_PREFIX.match(line)
    if prefix:
        stamp = stamp or prefix[1].replace(",", ".")
        line = line[prefix.end():]
    terminal = _JOB_END.fullmatch(line.strip())
    if terminal:
        state = {"succeeded": "complete", "failed": "failed",
                 "was stopped": "aborted", "was interrupted": "aborted"}[terminal[1]]
        entry["status"] = {"state": state, "terminal": True, "time": stamp,
                           "evidence": line.strip()[:300]}
        return
    if entry["status"]["terminal"]:
        return
    # A Ray outcome recorded before the allocation ends keeps precedence.
    cancelled = _SLURM_CANCEL.search(line)
    if cancelled:
        entry["status"] = {"state": "aborted", "terminal": True,
                           "time": stamp or cancelled[2].replace("T", " "),
                           "evidence": "Slurm " + cancelled[1]}
        return
    timer = _TIMER.search(line) if stamp else None
    state = None
    evidence = ""
    if timer:
        stage, action, _ = timer.groups()
        if stage in {"train", "actor_train", "ref_log_probs", "log_probs", "data_preprocess"}:
            state = "training" if stage != "train" or action == "start" else "running"
        elif stage == "update_weights":
            state = "syncing" if action == "start" else "running"
        elif stage == "save_model":
            state = "saving" if action == "start" else "running"
        if state:
            evidence = timer[0].removeprefix(" - ")
    if " - Runtime eval:" in line or re.match(r"^(?:\([^)]*pid=\d+\)\s*)?Eval [\w.-]+:\s*\d+%\|", line):
        state, evidence = "evaluating", "Evaluation progress recorded"
    elif re.match(r"^(?:\([^)]*pid=\d+\)\s*)?Rollout generation:\s*\d+%\|", line):
        state, evidence = "rollout", "Rollout generation progress recorded"
    elif stamp and (match := _METRIC.search(line)):
        if match[1] in {"step", "rollout"}:
            state, evidence = "training", "Trainer metrics recorded"
        elif match[1] == "eval":
            state, evidence = "running", "Evaluation results recorded"
    elif line.startswith("Running entrypoint for job "):
        state, evidence = "preparing", "Ray job entrypoint started"
    if state:
        entry["status"] = {"state": state, "terminal": False, "time": stamp or entry["last_time"],
                           "evidence": evidence}
        entry["phase"] = entry["status"]


class _NonfiniteNames(ast.NodeTransformer):
    def visit_Name(self, node):
        return ast.Constant(float(node.id)) if node.id in {"nan", "inf"} else node


def _numbers(text):
    """Literal scalar dict, accepting logged nan/inf without evaluating code."""
    tree = _NonfiniteNames().visit(ast.parse(text, mode="eval"))
    values = ast.literal_eval(tree)
    if not isinstance(values, dict):
        return {}
    return {k: v for k, v in values.items()
            if isinstance(k, str) and isinstance(v, (int, float))}


def _duration(start, end):
    try:
        seconds = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
        return seconds if seconds >= 0 else None
    except (TypeError, ValueError):
        return None


def _event(entry, stage, start="", source="", **fields):
    event = {"stage": stage, "start": start, "end": "", "seconds": None,
             "rollout_id": None, "source": source, "derived_start": False, **fields}
    entry["timeline"].append(event)
    return event


def _finish(event, end, seconds=None):
    event["end"] = end
    event["seconds"] = seconds if seconds is not None else _duration(event["start"], end)


def _assign_training(entry, event, index):
    event["rollout_id"] = index
    for child in entry["timeline"]:
        if (child["source"] == event["source"] and child["stage"] in {"actor_train", "log_probs", "ref_log_probs"}
                and event["start"] <= child["start"]
                and (not event["end"] or child["start"] <= event["end"])):
            child["rollout_id"] = index


def _timing(entry, line, stamp):
    """Keep explicit intervals; never infer evaluation duration from log gaps."""
    process = _PROCESS.search(line)
    source = process[1] if process else ""
    timer = _TIMER.search(line)
    checkpoint = _CHECKPOINT.search(line)
    if timer:
        stage, action, elapsed = timer.groups()
        if action == "start":
            event = _event(entry, stage, stamp, source)
            if stage in {"actor_train", "log_probs", "ref_log_probs"}:
                parent = next((e for e in reversed(entry["timeline"]) if e["stage"] == "train"
                               and e["source"] == source and not e["end"]), None)
                if parent is not None:
                    event["rollout_id"] = parent["rollout_id"]
        else:
            candidates = [e for e in entry["timeline"] if e["stage"] == stage and not e["end"]
                          and (not source or e["source"] == source)]
            # Some Ray timer-end lines omit their actor prefix. Pair only when
            # unique, so concurrent ranks cannot produce invented intervals.
            event = candidates[0] if len(candidates) == 1 else _event(entry, stage, source=source)
            _finish(event, stamp, float(elapsed) if elapsed else None)
    elif " - Runtime eval:" in line:
        _event(entry, "eval", stamp, source)
    elif checkpoint:
        action, index = checkpoint.groups()
        if action.startswith("saving"):
            _event(entry, "checkpoint", stamp, source, rollout_id=int(index))
        else:
            event = next((e for e in reversed(entry["timeline"]) if e["stage"] == "checkpoint"
                          and e["rollout_id"] == int(index) and not e["end"]), None)
            _finish(event if event is not None else _event(entry, "checkpoint", rollout_id=int(index)), stamp)


def _metric_timing(entry, kind, index, values, stamp, source):
    if kind == "eval":
        event = next((e for e in reversed(entry["timeline"]) if e["stage"] == "eval"
                      and not e["end"] and e["source"] == source), None)
        event = event if event is not None else _event(entry, "eval", source=source)
        event["rollout_id"] = index
        _finish(event, stamp)
    for metric, stage in (("perf/rollout_time", "rollout"), ("perf/train_time", "train")):
        seconds = values.get(metric)
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            continue
        # Prefer the trainer's explicit interval. Perf records can follow the
        # timer end in the next second; don't create a duplicate interval.
        event = next((e for e in reversed(entry["timeline"]) if e["stage"] == stage
                      and e["source"] == source and e["end"]
                      and (e["rollout_id"] == index or
                           (e["rollout_id"] is None and (gap := _duration(e["end"], stamp)) is not None
                            and gap <= 2))), None)
        if event is None:
            try:
                start = (datetime.fromisoformat(stamp) - timedelta(seconds=seconds)).isoformat(sep=" ", timespec="seconds")
            except (ValueError, OverflowError):
                start = ""
            event = _event(entry, stage, start, source, derived_start=bool(start))
            _finish(event, stamp, seconds)
        event["rollout_id"] = index
        if stage == "train" and event["start"]:
            _assign_training(entry, event, index)


class LogReader:
    """Small per-log cache; refresh consumes only appended complete lines."""

    def __init__(self):
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def read(self, path):
        with self.lock:
            stat = path.stat()
            entry = self.cache.get(path)
            identity = (stat.st_dev, stat.st_ino)
            if (entry is None or entry["identity"] != identity
                    or stat.st_size < entry["offset"]
                    or (stat.st_size == entry["offset"] and stat.st_mtime_ns != entry["mtime"])):
                entry = {"identity": identity, "offset": 0, "pending": b"", "mtime": None,
                         "config": {}, "rows": {kind: {} for kind in ("rollout", "eval", "train")},
                         "nonfinite": {}, "unparsed_records": 0, "timeline": [], "last_time": "",
                         "status": {"state": "unknown", "terminal": False, "time": "",
                                    "evidence": "No stage or terminal outcome recorded"},
                         "phase": {"state": "unknown", "terminal": False, "time": "",
                                   "evidence": "No stage recorded"}}
            with path.open("rb") as stream:
                stream.seek(entry["offset"])
                # Bound this refresh to the stat snapshot even while the trainer
                # appends. New bytes are consumed on the next refresh.
                appended = stream.read(stat.st_size - entry["offset"])
                entry["offset"] = stream.tell()
            lines = re.split(b"[\r\n]", entry["pending"] + appended)
            entry["pending"] = lines.pop()
            for raw in lines:
                self._line(entry, _ANSI.sub("", raw.decode("utf-8", errors="replace")))
            entry["mtime"] = stat.st_mtime_ns
            self.cache[path] = entry
            self.cache.move_to_end(path)
            while len(self.cache) > 8:
                self.cache.popitem(last=False)
            return {"config": dict(entry["config"]), "status": dict(entry["status"]),
                    "phase": dict(entry["phase"]),
                    "series": {kind: [dict(rows[i], values=dict(rows[i]["values"])) for i in sorted(rows)]
                               for kind, rows in entry["rows"].items()},
                    "nonfinite": list(entry["nonfinite"].values()),
                    "timeline": sorted((dict(event) for event in entry["timeline"]),
                                       key=lambda event: event["start"] or event["end"]),
                    "unparsed_records": entry["unparsed_records"],
                    "bytes_read": len(appended), "size": stat.st_size,
                    "modified": stat.st_mtime, "path": str(path)}

    @staticmethod
    def _line(entry, line):
        stamp_match = _TIME.search(line)
        stamp = stamp_match[1] if stamp_match else ""
        if stamp:
            entry["last_time"] = max(entry["last_time"], stamp)
        _status(entry, line, stamp)
        if stamp:
            _timing(entry, line, stamp)
        argument = _ARG.search(line)
        if argument and not _SENSITIVE.search(argument[1]):
            entry["config"][argument[1]] = argument[2]
        match = _METRIC.search(line)
        if not match:
            return
        try:
            values = _numbers(match[3])
        except (ValueError, SyntaxError, TypeError, RecursionError):
            entry["unparsed_records"] += 1
            return
        kind, index = _KINDS[match[1]], int(match[2])
        process = _PROCESS.search(line)
        source = process[1] if process else ""
        if stamp and match[1] in {"eval", "perf"}:
            _metric_timing(entry, kind, index, values, stamp, source)
        if stamp and match[1] == "rollout":
            parent = next((e for e in reversed(entry["timeline"]) if e["stage"] == "train"
                           and e["source"] == source and not e["end"]), None)
            if parent is not None:
                _assign_training(entry, parent, index)
        row = entry["rows"][kind].setdefault(index, {"id": index, "time": "", "values": {}})
        if stamp:
            row["time"] = stamp
        for key, value in values.items():
            if not math.isfinite(value):
                entry["nonfinite"][(kind, index, key)] = {"kind": kind, "id": index, "metric": key}
                value = None
            row["values"][key] = value


def _tail_status(path):
    """The run list reads only each log's tail, where terminal outcomes land."""
    entry = {"last_time": "", "status": {"state": "unknown", "terminal": False,
                                        "time": "", "evidence": "No outcome recorded"}}
    try:
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 131072))
            tail = stream.read(131072).decode("utf-8", errors="replace")
        for line in re.split(r"[\r\n]", tail)[:-1]:
            line = _ANSI.sub("", line)
            stamp = _TIME.search(line)
            _status(entry, line, stamp[1] if stamp else "")
    except OSError:
        pass
    return entry["status"]


class SlurmQueue:
    """Map each of the user's queued jobs' stdout path to its id and state; 30-second cache."""

    _WIDTH = 24

    def __init__(self):
        self.cached = None
        self.lock = threading.Lock()

    def __call__(self):
        with self.lock:
            if self.cached and time.monotonic() - self.cached[0] < 30:
                return self.cached[1]
            width = self._WIDTH
            try:
                # Fixed-width fields: STDOUT is last, so paths may hold spaces.
                output = subprocess.run(
                    ["squeue", "--me", "--noheader", f"--Format=JobID:{width},State:{width},STDOUT:4096"],
                    capture_output=True, text=True, timeout=10, check=True,
                ).stdout
                jobs = {}
                for line in output.splitlines():
                    stdout = line[2 * width:].strip()
                    if stdout:
                        jobs[os.path.realpath(stdout)] = {"id": line[:width].strip(),
                                                          "state": line[width:2 * width].strip()}
                result = {"jobs": jobs, "checked_at": time.time(), "error": ""}
            except (OSError, subprocess.SubprocessError):
                result = {"jobs": None, "checked_at": time.time(), "error": "Slurm queue is unavailable"}
            self.cached = (time.monotonic(), result)
            return result


def _lifecycle(item, recorded, queue):
    """Keep lifecycle separate from the last recorded training phase."""
    def result(state, evidence, source, stamp="", **extra):
        return {"state": state, "terminal": state in {"complete", "failed", "interrupted"},
                "evidence": evidence, "source": source, "time": stamp, **extra}

    if recorded["terminal"]:
        state = "interrupted" if recorded["state"] == "aborted" else recorded["state"]
        return result(state, recorded["evidence"], "log", recorded["time"])
    if not item["slurm"]:
        return result("unknown", "No terminal outcome recorded; this log has no Slurm job", "unverified")
    jobs = queue.get("jobs")
    if jobs is None:
        return result("unknown", "No terminal outcome recorded; Slurm queue is unavailable", "unverified")
    job = jobs.get(str(item["path"]))
    if job:
        state = "running" if job["state"] in {"RUNNING", "COMPLETING"} else "pending"
        return result(state, f"Slurm job {job['id']}: {job['state']}", "slurm",
                      checked_at=queue["checked_at"])
    return result("interrupted", "Slurm job is no longer queued; no successful exit recorded", "slurm",
                  checked_at=queue["checked_at"])


def create_app(log_roots=None, queue=None):
    app = Flask(__name__)
    roots = [Path(p).expanduser().resolve() for p in
             (log_roots if log_roots is not None else [_PROJECT.parent / "training_runs"])]
    reader = LogReader()
    queue = queue or SlurmQueue()

    def allowed(path):
        return path.is_file() and not path.is_symlink() and any(
            path.resolve().is_relative_to(root) for root in roots)

    def experiments():
        found, claimed = [], set()
        for i, root in enumerate(roots):
            candidates = [*root.glob("*/training.log"),
                          *(p for p in root.glob("*.log") if not _AUXILIARY.search(p.stem))]
            for path in candidates:
                if not allowed(path) or path.resolve() in claimed:
                    continue
                claimed.add(path.resolve())
                # sbatch --output writes a run directory's training.log; a root
                # may itself be one run directory.
                slurm = path.name == "training.log"
                found.append({"id": f"{i}/{path.relative_to(root)}", "path": path.resolve(), "slurm": slurm,
                              "name": path.resolve().parent.name if slurm else path.stem})
        names = Counter(item["name"] for item in found)
        for item in found:
            item["label"] = item["name"]
            if names[item["name"]] > 1:
                item["label"] += " · " + str(item["path"].parent)
            item["root"] = str(item["path"].parent)
            item["modified"] = item["path"].stat().st_mtime
        return sorted(found, key=lambda item: item["modified"], reverse=True)

    def lifecycle(item, recorded):
        return _lifecycle(item, recorded, queue() if item["slurm"] and not recorded["terminal"] else {})

    def public(item):
        return {k: item[k] for k in ("id", "name", "label", "root", "modified")}

    @app.get("/")
    def index():
        return render_template("slime_training_viewer.html", roots=[str(p) for p in roots])

    @app.get("/api/runs")
    def runs():
        response = jsonify({"runs": [
            {**public(item), "status": lifecycle(item, _tail_status(item["path"]))}
            for item in experiments()]})
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/run")
    def run():
        selected = next((item for item in experiments() if item["id"] == request.args.get("run")), None)
        if selected is None:
            return jsonify({"error": "Experiment not found"}), 404
        started = time.perf_counter()
        try:
            payload = reader.read(selected["path"])
        except OSError as error:
            return jsonify({"error": str(error)}), 500
        payload["parse_ms"] = round((time.perf_counter() - started) * 1000, 2)
        payload["status"] = lifecycle(selected, payload["status"])
        response = jsonify({"run": public(selected), **payload})
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-root", action="append",
                        help="Directory of run directories, a run directory, or a directory of .log files; repeatable")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5005)
    args = parser.parse_args()
    create_app(args.log_root).run(host=args.host, port=args.port)
