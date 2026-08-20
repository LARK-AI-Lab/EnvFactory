from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from src.mini.catalog import CatalogReport, CatalogServer
from src.mini.config import load_config
from src.mini.evaluate import (
    DecodingSettings,
    EvaluationItem,
    ModelReply,
    bootstrap_success_interval,
    calculate_metrics,
    evaluate_candidate,
    evaluate_item,
    parse_tool_output,
    prepare_evaluation_suite,
    redact_secrets,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"


class FakeClient:
    def __init__(self, replies: list[str]):
        self.replies = list(replies)

    async def complete(self, messages, settings):
        assert messages[0]["role"] == "system"
        assert settings.temperature == 0.0
        content = self.replies.pop(0)
        return ModelReply(
            content=content,
            model="fake-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            latency_seconds=0.25,
        )


class FakeSession:
    instances: list["FakeSession"] = []

    def __init__(self, initial, label):
        self.initial = json.loads(json.dumps(initial))
        self.state = json.loads(json.dumps(initial))
        self.label = label
        self.closed = False
        self.calls = []
        self.__class__.instances.append(self)

    async def start(self):
        return self.state == self.initial

    async def call(self, name, arguments):
        self.calls.append((name, arguments))
        self.state["Tiny"]["value"] = arguments["value"]
        return True, "updated"

    async def save(self):
        return json.loads(json.dumps(self.state))

    async def close(self):
        self.closed = True


def _settings() -> DecodingSettings:
    return DecodingSettings(
        temperature=0.0,
        top_p=1.0,
        presence_penalty=0.0,
        max_tokens=128,
        seed=42,
        enable_thinking=False,
    )


def _item() -> EvaluationItem:
    schema = {
        "type": "function",
        "function": {
            "name": "Tiny-set_value",
            "description": "Set a value",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
                "additionalProperties": False,
            },
        },
    }
    return EvaluationItem(
        item_id="seed-7-node-0",
        seed=7,
        node_index=0,
        messages=(
            {"role": "system", "content": "tools"},
            {"role": "user", "content": "Set the value to 1"},
        ),
        initial_scenario={"Tiny": {"value": 0}},
        reference_final_scenario={"Tiny": {"value": 1}},
        tool_schemas={"Tiny-set_value": schema},
        reference_tool_names=("Tiny-set_value",),
    )


def test_tool_output_parser_is_strict_about_xml_and_json() -> None:
    parsed, calls = parse_tool_output(
        '<think>short</think><tool_call>{"name":"Tiny-set_value","arguments":{"value":1}}</tool_call>'
    )
    assert parsed is True
    assert calls == [{"name": "Tiny-set_value", "arguments": {"value": 1}}]
    assert parse_tool_output("Finished.") == (True, [])
    assert parse_tool_output('<tool_call>{"name":"Tiny-set_value"}</tool_call>') == (False, [])
    assert parse_tool_output('<tool_call>{"name":"Tiny-set_value","arguments":{}}') == (
        False,
        [],
    )


def test_executable_item_uses_fresh_state_and_scores_selected_reference() -> None:
    FakeSession.instances.clear()
    client = FakeClient(
        [
            '<tool_call>{"name":"Tiny-set_value","arguments":{"value":1}}</tool_call>',
            "Done.",
        ]
    )
    result = asyncio.run(
        evaluate_item(
            _item(), client, _settings(), max_turns=4, session_factory=FakeSession
        )
    )
    assert result.task_success is True
    assert result.exact_tool_sequence is True
    assert result.final_scenario_exact is True
    assert result.response_attempts == result.parsed_responses == 2
    assert result.tool_calls == result.valid_tool_names == 1
    assert result.valid_argument_schemas == result.execution_successes == 1
    assert result.token_usage["total_tokens"] == 30
    assert len(FakeSession.instances) == 1
    assert FakeSession.instances[0].closed is True


def test_wrong_arguments_are_not_executed_and_are_classified() -> None:
    FakeSession.instances.clear()
    result = asyncio.run(
        evaluate_item(
            _item(),
            FakeClient(
                [
                    '<tool_call>{"name":"Tiny-set_value","arguments":{"value":"bad"}}</tool_call>'
                ]
            ),
            _settings(),
            max_turns=2,
            session_factory=FakeSession,
        )
    )
    assert result.task_success is False
    assert "wrong_arguments" in result.failure_categories
    assert "final_state_mismatch" in result.failure_categories
    assert result.valid_tool_names == 1
    assert result.valid_argument_schemas == result.execution_successes == 0
    assert FakeSession.instances[0].calls == []
    assert FakeSession.instances[0].closed is True


def test_metrics_have_explicit_denominators_and_deterministic_bootstrap() -> None:
    successful = asyncio.run(
        evaluate_item(
            _item(),
            FakeClient(
                [
                    '<tool_call>{"name":"Tiny-set_value","arguments":{"value":1}}</tool_call>',
                    "Done.",
                ]
            ),
            _settings(),
            max_turns=3,
            session_factory=FakeSession,
        )
    )
    failed = asyncio.run(
        evaluate_item(
            _item(),
            FakeClient(["<tool_call>not-json</tool_call>"]),
            _settings(),
            max_turns=3,
            session_factory=FakeSession,
        )
    )
    metrics = calculate_metrics(
        [successful, failed], bootstrap_samples=200, confidence=0.95, seed=11
    )
    assert metrics["sample_count"] == 2
    assert metrics["rates"]["task_success"] == {
        "numerator": 1,
        "denominator": 2,
        "value": 0.5,
    }
    assert metrics["rates"]["structured_output_parse"]["denominator"] == 3
    assert metrics["failure_counts"]["parse"] == 1
    assert bootstrap_success_interval(
        [True, False], samples=200, confidence=0.95, seed=11
    ) == metrics["task_success_bootstrap_interval"]


def test_candidate_artifacts_and_side_by_side_report_are_source_linked(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH).model_copy(update={"artifact_root": tmp_path / "artifacts"})
    run_id = "candidate-report"
    suite = {"contract_sha256": "contract-123"}

    async def run_candidate(candidate: str):
        return await evaluate_candidate(
            config=config,
            run_id=run_id,
            candidate=candidate,
            model=f"{candidate}-model",
            provenance={"serving_mode": "test"},
            health={"completion_model": f"{candidate}-model"},
            items=[_item()],
            suite=suite,
            client=FakeClient(
                [
                    '<tool_call>{"name":"Tiny-set_value","arguments":{"value":1}}</tool_call>',
                    "Done.",
                ]
            ),
            session_factory=FakeSession,
        )

    teacher, teacher_path = asyncio.run(run_candidate("teacher"))
    student, student_path = asyncio.run(run_candidate("student"))
    assert teacher_path.is_file() and student_path.is_file()
    assert teacher["metrics"]["token_usage"]["totals"]["total_tokens"] == 30
    assert student["metrics"]["rates"]["task_success"]["value"] == 1.0
    report = (teacher_path.parent / "report.md").read_text(encoding="utf-8")
    assert "Teacher ([JSON](teacher_metrics.json))" in report
    assert "Student ([JSON](student_metrics.json))" in report
    assert "task success bootstrap interval" in report
    assert "PASS: no cross-session state leakage" in report


def _catalog(tmp_path: Path) -> CatalogReport:
    metadata = {
        "class_name": "Tiny",
        "tools": [
            {
                "name": "set_value",
                "description": "Set value",
                "input_schema": {
                    "type": "object",
                    "properties": {"value": {"type": "integer"}},
                    "required": ["value"],
                },
            }
        ],
    }
    server = CatalogServer(
        name="Tiny",
        metadata_path=tmp_path / "Tiny_metadata.json",
        tool_path=tmp_path / "Tiny.py",
        metadata=metadata,
        metadata_tool_names=("set_value",),
        registered_tool_names=("set_value", "load_scenario", "save_scenario"),
    )
    return CatalogReport(servers=(server,), digest="tiny-catalog")


def test_suite_uses_only_validation_seeds_and_is_immutable(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH).model_copy(update={"artifact_root": tmp_path / "artifacts"})
    run_id = "evaluation-suite"
    root = config.artifact_root / "runs" / run_id
    completed = root / "trajectories" / "completed"
    completed.mkdir(parents=True)
    trajectory = {
        "seed": 7,
        "scenario": "test",
        "user_tools": None,
        "nodes": [
            {
                "raw_tool_call": ["Tiny-set_value"],
                "initial_scenario": {"Tiny": {"value": 0}},
                "final_scenario": {"Tiny": {"value": 1}},
                "query": "Set value",
                "decision": True,
                "mcp_servers": ["Tiny"],
                "steps": [
                    {"role": "user", "content": "Set value"},
                    {
                        "role": "tool_call",
                        "content": [
                            {"name": "Tiny-set_value", "arguments": {"value": 1}}
                        ],
                    },
                    {"role": "tool_response", "content": ["updated"]},
                    {"role": "assistant", "content": "Done"},
                ],
            }
        ],
    }
    (completed / "7.json").write_text(json.dumps(trajectory), encoding="utf-8")
    dataset_dir = root / "datasets"
    dataset_dir.mkdir()
    manifest = {
        "source_run_id": run_id,
        "source_run_sha256": "source",
        "source": {"catalog_sha256": "tiny-catalog"},
        "split": {"train_seeds": [3], "validation_seeds": [7]},
    }
    (dataset_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    items, suite, path = prepare_evaluation_suite(config, run_id, catalog=_catalog(tmp_path))
    assert suite["selection"]["selected_seeds"] == [7]
    assert suite["selection"]["train_seed_overlap"] == []
    assert suite["task_count"] == len(items) == 1
    assert path.is_file()
    assert prepare_evaluation_suite(config, run_id, catalog=_catalog(tmp_path))[1] == suite

    manifest["split"]["validation_seeds"] = [9]
    (dataset_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    with pytest.raises(Exception, match="held-out trajectory"):
        prepare_evaluation_suite(config, run_id, catalog=_catalog(tmp_path))


def test_failed_trace_redaction_removes_keys_and_current_values() -> None:
    value = {
        "api_key": "visible",
        "nested": {"message": "prefix super-secret-value suffix", "token_count": 3},
    }
    redacted = redact_secrets(value, secrets=("super-secret-value",))
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["message"] == "prefix [REDACTED] suffix"
    assert redacted["nested"]["token_count"] == 3
