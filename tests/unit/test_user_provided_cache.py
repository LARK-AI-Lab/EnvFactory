from __future__ import annotations

import json
from types import SimpleNamespace

from src.graph.tool_node import Parameter, Tool
from src.mini.classification import (
    CachedUserProvidedClassifier,
    TeacherUserProvidedClassifier,
    classification_prompt_hash,
)


class FakeClassifier:
    identity = "fake-classifier:v1"
    settings = {"seed": 42, "thinking": False}

    def __init__(self):
        self.calls = []

    def classify(self, parameters, param_to_tool_map=None):
        self.calls.append(list(parameters))
        return [parameter.name != "derived_id" for parameter in parameters]


def _tool() -> Tool:
    return Tool(
        {
            "server": "Calendar",
            "name": "Calendar-create_event",
            "description": "Create an event.",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
        }
    )


def test_classification_hash_normalizes_whitespace() -> None:
    tool = _tool()
    first = Parameter(" title ", "A   readable\n title", " string ")
    second = Parameter("title", "A readable title", "string")
    assert classification_prompt_hash(first, tool) == classification_prompt_hash(second, tool)


def test_classification_cache_deduplicates_and_persists(tmp_path) -> None:
    tool = _tool()
    first = Parameter("title", "Readable title", "string")
    duplicate = Parameter("title", "Readable title", "string")
    derived = Parameter("derived_id", "Returned by a prior tool", "string")
    mapping = {first: tool, duplicate: tool, derived: tool}
    fake = FakeClassifier()
    cached = CachedUserProvidedClassifier(fake, tmp_path / "classifications.sqlite3")
    assert cached.classify([first, duplicate, derived], mapping) == [True, True, False]
    assert len(fake.calls) == 1
    assert len(fake.calls[0]) == 2

    fresh = FakeClassifier()
    persisted = CachedUserProvidedClassifier(fresh, tmp_path / "classifications.sqlite3")
    assert persisted.classify([derived, first], mapping) == [False, True]
    assert fresh.calls == []
    assert persisted.hits == 2


def test_teacher_uses_seed_json_schema_and_disables_thinking() -> None:
    captured = {}

    class Completions:
        def create(self, **kwargs):
            captured.update(kwargs)
            content = json.dumps({"classifications": [True]})
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    classifier = TeacherUserProvidedClassifier(
        base_url="http://127.0.0.1:8000/v1",
        api_key="local-test-key",
        model="teacher",
        seed=73,
        client=client,
    )
    assert classifier.classify([Parameter("title", "Event title", "string")]) == [True]
    assert captured["temperature"] == 0.0
    assert captured["seed"] == 73
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False


def test_teacher_batches_independent_parameter_classifications() -> None:
    batch_sizes = []

    class Completions:
        def create(self, **kwargs):
            size = kwargs["response_format"]["json_schema"]["schema"]["properties"][
                "classifications"
            ]["minItems"]
            batch_sizes.append(size)
            content = json.dumps({"classifications": [True] * size})
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    classifier = TeacherUserProvidedClassifier(
        base_url="http://127.0.0.1:8000/v1",
        api_key="local-test-key",
        model="teacher",
        seed=73,
        batch_size=2,
        client=client,
    )
    parameters = [Parameter(f"value_{index}", "User-provided value", "string") for index in range(5)]

    assert classifier.classify(parameters) == [True] * 5
    assert batch_sizes == [2, 2, 1]
