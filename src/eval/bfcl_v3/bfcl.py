"""BFCL v3 multi-turn evaluation for the slime rollout (ported from ToolAgent).

Rows follow upstream's Qwen function-calling protocol: no system prompt, the involved
classes' function docs as tools (with the Python language hint), one scripted user turn
after another, and held-out functions announced in a user message. Executed calls are
replayed by upstream's state and response checkers; a task scores 1 only if every turn passes.

Build the eval file once (``run_grpo.sh`` adds it when present)::

    python -m src.eval.bfcl_v3.bfcl data/bfcl_v3_val.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.eval.bfcl_v3.checkers.executable_backend_config import CLASS_FILE_PATH_MAPPING
from src.eval.bfcl_v3.checkers.multi_turn_checker import multi_turn_checker
from src.eval.bfcl_v3.checkers.multi_turn_utils import execute_multi_turn_func_call

BENCHMARK = "bfcl_v3"
DATA_DIR = Path(__file__).resolve().parent / "data"
CATEGORIES = ("multi_turn_base", "multi_turn_miss_func", "multi_turn_miss_param", "multi_turn_long_context")
# Upstream force-quits a task after this many executed steps within one user turn.
MAXIMUM_STEP_LIMIT = 20
ANNOUNCEMENT = "{functions}\nI have updated some more functions you can choose from. What about now?"
LANGUAGE_HINT = " Note that the provided function is in Python 3 syntax."


def _read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _function_docs(class_name: str) -> list[dict]:
    return _read_jsonl(DATA_DIR / "multi_turn_func_doc" / f"{CLASS_FILE_PATH_MAPPING[class_name].rsplit('.', 1)[-1]}.json")


def build_row(entry: dict, category: str, ground_truth: list[list[str]]) -> dict:
    """One slime eval row: the first user turn as prompt, later turns scripted in metadata."""
    classes = list(entry["involved_classes"])
    docs = {doc["name"]: doc for class_name in classes for doc in _function_docs(class_name)}
    missed = entry.get("missed_function") or {}
    held_out = {name for names in missed.values() for name in names}
    questions = entry["question"]
    user_turns = [
        [{"role": "user", "content": ANNOUNCEMENT.format(functions=[docs[name] for name in missed[str(i)]])}]
        if missed.get(str(i)) else questions[i]
        for i in range(1, len(questions))
    ]
    # Upstream appends the hint after removing held-out docs, so announced functions lack it.
    tools = [
        {"type": "function", "function": {**doc, "description": doc["description"] + LANGUAGE_HINT}}
        for name, doc in docs.items() if name not in held_out
    ]
    return {
        "prompt": questions[0],
        "label": json.dumps(ground_truth),
        "metadata": {
            "benchmark": BENCHMARK,
            "bfcl_id": entry["id"],
            "bfcl_category": category,
            "involved_classes": classes,
            "initial_config": entry.get("initial_config") or {},
            "tools": tools,
            "user_turns": user_turns,
        },
    }


def build_rows(categories=CATEGORIES) -> list[dict]:
    rows = []
    for category in categories:
        answers = {item["id"]: item["ground_truth"] for item in _read_jsonl(DATA_DIR / "possible_answer" / f"{category}.json")}
        rows.extend(build_row(entry, category, answers[entry["id"]]) for entry in _read_jsonl(DATA_DIR / f"{category}.json"))
    return rows


def _bfcl_repr(value: Any) -> str:
    """An argument in BFCL ground-truth style (single-quoted strings)."""
    if isinstance(value, list):
        return "[" + ", ".join(_bfcl_repr(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{_bfcl_repr(k)}: {_bfcl_repr(v)}" for k, v in value.items()) + "}"
    return repr(value)


def call_string(name: str, arguments: dict) -> str:
    return f"{name}({', '.join(f'{key}={_bfcl_repr(value)}' for key, value in arguments.items())})"


class BfclEnv:
    """One BFCL task: executes calls on upstream's backend classes and records them per user turn."""

    per_call_budget = True  # Upstream bounds each model call, not the whole episode.
    max_steps = MAXIMUM_STEP_LIMIT + 1  # The step after the limit ends the task, like upstream's force-quit.

    def __init__(self, args, metadata: dict):
        self.metadata = metadata
        self.tool_schemas = metadata["tools"]
        self.max_context_len = args.eval_max_context_len
        self.max_response_len = args.eval_max_response_len or args.rollout_max_response_len
        self.long_context = "long_context" in metadata["bfcl_category"]
        self._instances: dict[str, Any] = {}
        self.turn_calls: list[list[str]] = [[]]

    def call_tools(self, tool_calls: list) -> list[str]:
        """Upstream executes any public method of the involved classes, advertised or not."""
        results = []
        for call in tool_calls:
            call_str = call_string(call.name, call.arguments)
            [result], _ = execute_multi_turn_func_call(
                [call_str], self.metadata["initial_config"], self.metadata["involved_classes"],
                self._instances, long_context=self.long_context,
            )
            self.turn_calls[-1].append(call_str)
            results.append(result)
        return results

    def next_user_turn(self) -> list[dict] | None:
        if not self.metadata["user_turns"]:
            return None
        self.turn_calls.append([])
        return self.metadata["user_turns"].pop(0)

    def result(self) -> dict:
        return {"bfcl_turn_calls": self.turn_calls}


def grade(metadata: dict, label: str) -> float:
    """1.0 when every user turn passes upstream's state and execution-response checks."""
    ground_truth = json.loads(label)
    turn_calls = metadata["bfcl_turn_calls"]
    if len(turn_calls) != len(ground_truth):  # Upstream: multi_turn:force_terminated.
        return 0.0
    entry = {
        "id": metadata["bfcl_id"],
        "initial_config": metadata["initial_config"],
        "involved_classes": metadata["involved_classes"],
    }
    result = multi_turn_checker([[calls] for calls in turn_calls], ground_truth, entry, metadata["bfcl_category"], "envfactory")
    return float(result["valid"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write the BFCL v3 multi-turn eval set as slime JSONL.")
    parser.add_argument("output")
    parser.add_argument("--categories", nargs="+", default=list(CATEGORIES))
    cli = parser.parse_args()
    rows = build_rows(cli.categories)
    with open(cli.output, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"✅ Saved {len(rows)} BFCL v3 rows to {cli.output}")
