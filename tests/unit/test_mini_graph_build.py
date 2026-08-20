from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from src.graph.tool_node import Parameter
from src.mini.build_graph import build_graph
from src.mini.catalog import CatalogReport, CatalogServer
from src.mini.config import load_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"


class StableEmbeddingBackend:
    identity = "stable:test-embedding"

    def __init__(self, *, fail=False):
        self.calls = []
        self.fail = fail

    def encode(self, texts):
        if self.fail:
            raise AssertionError("warm graph build must not compute embeddings")
        self.calls.append(list(texts))
        rows = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            row = np.frombuffer(digest[:16], dtype=np.uint8).astype(np.float32) - 127.5
            rows.append(row)
        return np.stack(rows)


class AlwaysUserProvided:
    identity = "stable:test-classifier"
    settings = {
        "temperature": 0.0,
        "seed": 42,
        "thinking": False,
        "response_format": "json_schema",
    }

    def __init__(self, *, fail=False):
        self.calls = 0
        self.fail = fail

    def classify(self, parameters, param_to_tool_map=None):
        if self.fail:
            raise AssertionError("warm graph build must not classify parameters")
        self.calls += 1
        return [True] * len(parameters)


def _metadata() -> dict:
    return {
        "class_name": "Tiny",
        "description": "Tiny test server",
        "tools": [
            {
                "name": "first",
                "description": "First tool",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "A query"}
                    },
                    "required": ["query"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "first_result": {"type": "string", "description": "First result"}
                    },
                },
            },
            {
                "name": "second",
                "description": "Second tool",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "A topic"}
                    },
                    "required": ["topic"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "second_result": {"type": "string", "description": "Second result"}
                    },
                },
            },
        ],
    }


def _config_and_catalog(tmp_path):
    artifact_root = tmp_path / "artifacts"
    config = load_config(CONFIG_PATH)
    graph_config = config.graph.model_copy(
        update={
            "path": artifact_root / "graph" / "graph.pkl",
            "manifest_path": artifact_root / "graph" / "manifest.json",
            "embedding_cache": artifact_root / "cache" / "embeddings.sqlite3",
            "user_provided_cache": artifact_root / "cache" / "user.sqlite3",
        }
    )
    config = config.model_copy(update={"artifact_root": artifact_root, "graph": graph_config})

    fixture_dir = tmp_path / "inputs"
    fixture_dir.mkdir()
    metadata_path = fixture_dir / "Tiny_metadata.json"
    tool_path = fixture_dir / "Tiny.py"
    metadata = _metadata()
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    tool_path.write_text("# graph hash fixture\n", encoding="utf-8")
    server = CatalogServer(
        name="Tiny",
        metadata_path=metadata_path,
        tool_path=tool_path,
        metadata=metadata,
        metadata_tool_names=("first", "second"),
        registered_tool_names=("first", "second", "load_scenario", "save_scenario"),
    )
    return config, CatalogReport(servers=(server,), digest="fixture-catalog-sha256")


def test_parameter_hash_matches_identity_equality() -> None:
    first = Parameter("same", "first", "string")
    second = Parameter("same", "second", "string")
    assert first is not second
    assert first != second
    assert len({first, second}) == 2


def test_graph_manifest_and_warm_build_use_no_live_computation(tmp_path) -> None:
    config, catalog = _config_and_catalog(tmp_path)
    embedding = StableEmbeddingBackend()
    classifier = AlwaysUserProvided()
    result = build_graph(
        config,
        catalog=catalog,
        embedding_backend=embedding,
        user_classifier=classifier,
    )

    assert result.cached is False
    assert result.manifest["counts"]["tools"] == 2
    assert result.manifest["sampling_validation_seeds"] == 100
    assert result.manifest["inputs"]["settings"]["enable_parameter_merge"] is False
    assert result.manifest["inputs"]["settings"]["enable_llm_edges"] is False
    assert result.manifest["inputs"]["settings"]["classifier_settings"]["thinking"] is False
    assert result.manifest["output_sha256"] == hashlib.sha256(
        config.graph.path.read_bytes()
    ).hexdigest()
    assert config.graph.manifest_path.is_file()
    assert classifier.calls == 1
    assert len(embedding.calls) == 1
    # Merge-only name/description vectors are not requested in the default mode.
    assert all(": " in text for text in embedding.calls[0])
    parameters = [node for node in result.graph.graph.nodes if isinstance(node, Parameter)]
    assert all(parameter._embedding is not None for parameter in parameters)
    assert all(parameter._name_embedding is None for parameter in parameters)
    assert all(parameter._description_embedding is None for parameter in parameters)

    warm = build_graph(
        config,
        catalog=catalog,
        embedding_backend=StableEmbeddingBackend(fail=True),
        user_classifier=AlwaysUserProvided(fail=True),
    )
    assert warm.cached is True
    assert warm.manifest["output_sha256"] == result.manifest["output_sha256"]
