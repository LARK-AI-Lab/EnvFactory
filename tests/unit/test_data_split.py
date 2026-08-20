from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mini.catalog import CatalogReport, CatalogServer
from src.mini.config import load_config
from src.mini.manifest import RunManifest
from src.mini.prepare_dataset import (
    DatasetGateError,
    DatasetPreparationError,
    deterministic_split,
    prepare_dataset,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"


class FakeTokenizer:
    chat_template = "fake-qwen-chat-template-v1"
    init_kwargs = {"_commit_hash": "tokenizer-commit-abc123"}

    def __init__(self):
        self.messages: list[list[dict[str, str]]] = []

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is True
        assert add_generation_prompt is False
        self.messages.append(messages)
        return list(range(128))


class OneLongSampleTokenizer(FakeTokenizer):
    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        result = super().apply_chat_template(
            messages, tokenize=tokenize, add_generation_prompt=add_generation_prompt
        )
        if len(self.messages) == 1:
            return list(range(9000))
        return result


def _catalog(tmp_path: Path) -> CatalogReport:
    servers = []
    for server_name, tool_name in (
        ("Calculator", "calculate"),
        ("Calendar", "list_events"),
        ("Weather", "get_weather"),
    ):
        metadata = {
            "class_name": server_name,
            "tools": [
                {
                    "name": tool_name,
                    "description": f"Test {tool_name}",
                    "input_schema": {
                        "type": "object",
                        "properties": {"value": {"type": "integer"}},
                        "required": ["value"],
                    },
                }
            ],
        }
        servers.append(
            CatalogServer(
                name=server_name,
                metadata_path=tmp_path / f"{server_name}_metadata.json",
                tool_path=tmp_path / f"{server_name}.py",
                metadata=metadata,
                metadata_tool_names=(tool_name,),
                registered_tool_names=(tool_name, "load_scenario", "save_scenario"),
            )
        )
    return CatalogReport(servers=tuple(servers), digest="catalog-phase7")


def _trajectory(seed: int, server: str, tool: str, *, arguments=None) -> dict:
    full_name = f"{server}-{tool}"
    return {
        "seed": seed,
        "scenario": "test",
        "user_tools": None,
        "user_profile": None,
        "sampled_tool_names": [full_name],
        "mcp_servers": [server],
        "nodes": [
            {
                "raw_tool_call": [full_name],
                "initial_scenario": {server: {"value": 0}},
                "final_scenario": {server: {"value": 1}},
                "query": f"Run seed {seed}",
                "decision": True,
                "accuracy": 1.0,
                "pass_k_trace": {},
                "pass_k_scenario": {},
                "pass_k_decision": {},
                "mcp_servers": [server],
                "steps": [
                    {"role": "user", "content": f"Run seed {seed}"},
                    {
                        "role": "tool_call",
                        "content": [
                            {
                                "name": full_name,
                                "arguments": {"value": seed} if arguments is None else arguments,
                            }
                        ],
                    },
                    {"role": "tool_response", "content": [f"result {seed}"]},
                    {"role": "assistant", "content": f"Finished {seed}"},
                ],
            }
        ],
    }


def _run_fixture(tmp_path: Path, *, malformed_arguments: bool = False):
    config = load_config(CONFIG_PATH).model_copy(update={"artifact_root": tmp_path / "artifacts"})
    catalog = _catalog(tmp_path)
    run_id = "phase7-test"
    run_root = config.artifact_root / "runs" / run_id
    completed = run_root / "trajectories" / "completed"
    failed = run_root / "trajectories" / "failed"
    completed.mkdir(parents=True)
    failed.mkdir(parents=True)
    seeds = [30, 2, 11, 7, 19, 5]
    assignments = (
        ("Calculator", "calculate"),
        ("Calendar", "list_events"),
        ("Weather", "get_weather"),
        ("Calculator", "calculate"),
        ("Calendar", "list_events"),
        ("Weather", "get_weather"),
    )
    for index, (seed, (server, tool)) in enumerate(zip(seeds, assignments, strict=True)):
        arguments = "not-an-object" if malformed_arguments and index == 0 else None
        value = _trajectory(seed, server, tool, arguments=arguments)
        (completed / f"{seed}.json").write_text(json.dumps(value), encoding="utf-8")
    (completed / ".2.json.partial.tmp").write_text("{", encoding="utf-8")
    (failed / "999.json").write_text("{}", encoding="utf-8")

    manifest = RunManifest.create(
        run_id=run_id,
        config_sha256="config-phase7",
        graph_sha256="graph-phase7",
        catalog_sha256=catalog.digest,
        teacher_model=config.teacher.model,
        target_trajectories=len(seeds),
        seeds=seeds,
        git_commit="abc1234",
        git_dirty=False,
    )
    manifest.state = "completed"
    manifest.completed_seeds = list(seeds)
    manifest.pending_seeds = []
    manifest.valid_count = len(seeds)
    manifest.checkpoint(run_root / "run_manifest.json")
    return config, catalog, run_id


def test_deterministic_split_is_whole_trajectory_and_order_independent() -> None:
    first = deterministic_split([9, 1, 5, 3], train_ratio=0.5, split_seed=42)
    second = deterministic_split([3, 5, 1, 9], train_ratio=0.5, split_seed=42)
    assert first == second
    assert first[0].isdisjoint(first[1])
    assert first[0] | first[1] == {1, 3, 5, 9}


def test_prepare_dataset_is_deterministic_streamed_and_leak_free(tmp_path) -> None:
    config, catalog, run_id = _run_fixture(tmp_path)
    tokenizer = FakeTokenizer()
    result = prepare_dataset(config, run_id, tokenizer=tokenizer, catalog=catalog)

    manifest = result.manifest
    assert result.dataset_info_path.is_file()
    assert result.training_profile_path.is_file()
    assert result.training_profile_path.name == "resolved_llamafactory.yaml"
    assert manifest["counts"] == {
        "source_trajectories": 6,
        "retained_trajectories": 6,
        "train_trajectories": 5,
        "validation_trajectories": 1,
        "candidate_samples": 12,
        "retained_samples": 12,
        "train_samples": 10,
        "validation_samples": 2,
        "over_cutoff_samples": 0,
        "failed_artifacts_excluded": 1,
        "temporary_artifacts_excluded": 1,
    }
    train_seeds = set(manifest["split"]["train_seeds"])
    validation_seeds = set(manifest["split"]["validation_seeds"])
    assert train_seeds.isdisjoint(validation_seeds)
    assert train_seeds | validation_seeds == {2, 5, 7, 11, 19, 30}
    assert manifest["tokenizer"]["resolved_revision"] == "tokenizer-commit-abc123"
    assert manifest["distributions"]["token_lengths"]["p95"] == 128
    assert all(manifest["gates"].values())

    all_samples = json.loads(result.all_path.read_text(encoding="utf-8"))
    train_samples = json.loads(result.train_path.read_text(encoding="utf-8"))
    validation_samples = json.loads(result.validation_path.read_text(encoding="utf-8"))
    assert len(all_samples) == len(train_samples) + len(validation_samples) == 12
    assert all(
        set(sample) == {"instruction", "input", "output", "system", "history"}
        for sample in all_samples
    )
    assert [sample["instruction"] for sample in all_samples[::2]] == [
        "Run seed 2",
        "Run seed 5",
        "Run seed 7",
        "Run seed 11",
        "Run seed 19",
        "Run seed 30",
    ]
    assert tokenizer.messages[0][0]["role"] == "system"
    assert tokenizer.messages[0][-1]["role"] == "assistant"

    tracked = [
        result.manifest_path,
        result.all_path,
        result.train_path,
        result.validation_path,
        result.inspection_path,
    ]
    before = {path.name: path.read_bytes() for path in tracked}
    rerun = prepare_dataset(config, run_id, tokenizer=FakeTokenizer(), catalog=catalog)
    after = {path.name: path.read_bytes() for path in tracked}
    assert before == after
    assert rerun.manifest == manifest


def test_prepare_dataset_rejects_malformed_tool_call_arguments(tmp_path) -> None:
    config, catalog, run_id = _run_fixture(tmp_path, malformed_arguments=True)
    with pytest.raises(DatasetPreparationError, match="arguments.*JSON object"):
        prepare_dataset(config, run_id, tokenizer=FakeTokenizer(), catalog=catalog)
    assert not (config.artifact_root / "runs" / run_id / "datasets").exists()


def test_over_cutoff_samples_are_recorded_before_fit_gate_failure(tmp_path) -> None:
    config, catalog, run_id = _run_fixture(tmp_path)
    with pytest.raises(DatasetGateError, match="fit_rate_at_least_95_percent"):
        prepare_dataset(config, run_id, tokenizer=OneLongSampleTokenizer(), catalog=catalog)

    dataset_dir = config.artifact_root / "runs" / run_id / "datasets"
    manifest = json.loads((dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["counts"]["candidate_samples"] == 12
    assert manifest["counts"]["retained_samples"] == 11
    assert manifest["exclusions"]["over_cutoff"] == [
        {"sample_index": 0, "seed": 2, "tokens": 9000}
    ]
    assert manifest["gates"]["fit_rate_at_least_95_percent"] is False
    assert len(json.loads((dataset_dir / "sft_all.json").read_text(encoding="utf-8"))) == 11


def test_server_imbalance_requires_an_explicit_configured_acceptance(tmp_path) -> None:
    config, catalog, run_id = _run_fixture(tmp_path)
    completed = config.artifact_root / "runs" / run_id / "trajectories" / "completed"
    for path in completed.glob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        seed = value["seed"]
        path.write_text(
            json.dumps(_trajectory(seed, "Calculator", "calculate")), encoding="utf-8"
        )

    with pytest.raises(DatasetGateError, match="server_share_at_most_35_percent"):
        prepare_dataset(config, run_id, tokenizer=FakeTokenizer(), catalog=catalog)

    accepted_dataset = config.dataset.model_copy(update={"allow_server_imbalance": True})
    accepted_config = config.model_copy(update={"dataset": accepted_dataset})
    result = prepare_dataset(
        accepted_config, run_id, tokenizer=FakeTokenizer(), catalog=catalog
    )
    assert result.manifest["quality"]["imbalanced_servers"] == {"Calculator": 1.0}
    assert result.manifest["quality"]["server_imbalance_accepted"] is True
    assert result.manifest["gates"]["server_share_at_most_35_percent_or_accepted"] is True
