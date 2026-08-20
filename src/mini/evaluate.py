"""Held-out, executable teacher/student evaluation for the MoLab mini pipeline."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import math
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence
from uuid import uuid4

from jsonschema import SchemaError
from jsonschema.validators import validator_for

from .artifacts import atomic_write_json, atomic_write_text
from .catalog import CatalogReport, CatalogValidationError, validate_catalog
from .config import MiniConfig, MiniConfigError, load_config
from src.utils.data_conversion import build_system_prompt, format_step


class EvaluationError(RuntimeError):
    """Raised when an evaluation input, endpoint, or artifact is unsafe."""


_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_ITEM_ID = re.compile(r"[A-Za-z0-9._-]+\Z")
_SECRET_KEY = re.compile(
    r"(?:api[_-]?key|authorization|cookie|credential|password|secret|"
    r"(?:access|auth|refresh|bearer)[_-]?token|^token$)",
    re.I,
)
_SECRET_ENV = re.compile(r"(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL)", re.I)
_TOOL_BLOCK = re.compile(r"<tool_call\s*>(.*?)</tool_call\s*>", re.I | re.S)
_TOOL_MARKER = re.compile(r"</?tool_call\b", re.I)
_TOOL_FAILURE = re.compile(r"(?: timed out after | failed:| error:)", re.I)


@dataclass(frozen=True)
class DecodingSettings:
    temperature: float
    top_p: float
    presence_penalty: float
    max_tokens: int
    seed: int
    enable_thinking: bool


@dataclass(frozen=True)
class ModelReply:
    content: str
    model: str | None
    usage: dict[str, int] | None
    latency_seconds: float


@dataclass(frozen=True)
class EvaluationItem:
    item_id: str
    seed: int
    node_index: int
    messages: tuple[dict[str, str], ...]
    initial_scenario: dict[str, Any]
    reference_final_scenario: dict[str, Any]
    tool_schemas: dict[str, dict[str, Any]]
    reference_tool_names: tuple[str, ...]
    deterministic_final_state: bool = True


@dataclass
class ItemResult:
    item_id: str
    seed: int
    node_index: int
    response_attempts: int = 0
    parsed_responses: int = 0
    tool_calls: int = 0
    valid_tool_names: int = 0
    valid_argument_schemas: int = 0
    execution_successes: int = 0
    turns: int = 0
    predicted_tool_names: list[str] = field(default_factory=list)
    exact_tool_sequence: bool = False
    final_scenario_exact: bool = False
    task_success: bool = False
    initial_state_exact: bool = False
    latencies_seconds: list[float] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    failure_categories: list[str] = field(default_factory=list)
    safe_error: str | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)


class CompletionClient(Protocol):
    async def complete(
        self, messages: Sequence[Mapping[str, str]], settings: DecodingSettings
    ) -> ModelReply: ...


class ScenarioSession(Protocol):
    async def start(self) -> bool: ...
    async def call(self, name: str, arguments: dict[str, Any]) -> tuple[bool, str]: ...
    async def save(self) -> dict[str, Any]: ...
    async def close(self) -> None: ...


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _sha256_json(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _sha256_tree(root: Path) -> str:
    if not root.is_dir():
        raise EvaluationError(f"artifact directory does not exist: {root}")
    hasher = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise EvaluationError(f"artifact directory is empty: {root}")
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        hasher.update(len(relative).to_bytes(8, "big"))
        hasher.update(relative)
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    return hasher.hexdigest()


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"{label} must be a JSON object: {path}")
    return value


def _run_root(config: MiniConfig, run_id: str) -> Path:
    if not _RUN_ID.fullmatch(run_id):
        raise EvaluationError("invalid run ID")
    runs_root = (config.artifact_root / "runs").resolve()
    root = (runs_root / run_id).resolve()
    if not root.is_relative_to(runs_root):
        raise EvaluationError("run path escapes artifact root")
    return root


def _known_secrets(config: MiniConfig) -> tuple[str, ...]:
    values = {
        value
        for name, value in os.environ.items()
        if (_SECRET_ENV.search(name) or name == config.teacher.api_key_env) and len(value) >= 8
    }
    return tuple(sorted(values, key=len, reverse=True))


def redact_secrets(value: Any, *, secrets: Sequence[str] = ()) -> Any:
    """Recursively remove secret-shaped fields and current secret values."""
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if _SECRET_KEY.search(str(key))
            else redact_secrets(child, secrets=secrets)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(child, secrets=secrets) for child in value]
    if isinstance(value, tuple):
        return [redact_secrets(child, secrets=secrets) for child in value]
    if isinstance(value, str):
        result = value
        for secret in secrets:
            result = result.replace(secret, "[REDACTED]")
        return result
    return value


def parse_tool_output(text: str) -> tuple[bool, list[dict[str, Any]]]:
    """Parse the exact XML/JSON tool-call format used for SFT conversion."""
    if not isinstance(text, str):
        return False, []
    blocks = _TOOL_BLOCK.findall(text)
    markers = _TOOL_MARKER.findall(text)
    if not blocks:
        return (not markers), []
    if len(markers) != len(blocks) * 2:
        return False, []
    calls: list[dict[str, Any]] = []
    for block in blocks:
        try:
            value = json.loads(block.strip())
        except (TypeError, json.JSONDecodeError):
            return False, []
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("name"), str)
            or not isinstance(value.get("arguments"), dict)
        ):
            return False, []
        calls.append({"name": value["name"], "arguments": value["arguments"]})
    return True, calls


def _catalog_schemas(catalog: CatalogReport) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for server in catalog.servers:
        for tool in server.metadata["tools"]:
            name = f"{server.name}-{tool['name']}"
            parameters = tool.get("input_schema") or {
                "type": "object",
                "properties": {},
            }
            try:
                validator_for(parameters).check_schema(parameters)
            except SchemaError as exc:
                raise EvaluationError(f"invalid argument schema for {name}: {exc.message}") from exc
            result[name] = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.get("description", ""),
                    "parameters": parameters,
                },
            }
    return result


def _reference_tool_names(node: Mapping[str, Any]) -> tuple[str, ...]:
    names: list[str] = []
    for step in node.get("steps") or []:
        if step.get("role") != "tool_call":
            continue
        for call in step.get("content") or []:
            names.append(str(call["name"]))
    return tuple(names)


def _validate_heldout_payload(payload: Mapping[str, Any], allowed_tools: set[str]) -> None:
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise EvaluationError("completed trajectory has no nodes")
    accepted = 0
    calls = 0
    for node in nodes:
        if not isinstance(node, Mapping):
            raise EvaluationError("completed trajectory node is not an object")
        if node.get("decision") is not True or not node.get("steps"):
            break
        accepted += 1
        servers = node.get("mcp_servers") or []
        initial = node.get("initial_scenario")
        final = node.get("final_scenario")
        if not isinstance(servers, list) or any(not isinstance(value, str) for value in servers):
            raise EvaluationError("completed trajectory server list is invalid")
        if not isinstance(initial, dict) or not set(servers).issubset(initial):
            raise EvaluationError("completed trajectory has incomplete initial scenarios")
        if not isinstance(final, dict) or any(final.get(server) is None for server in servers):
            raise EvaluationError("completed trajectory has incomplete final scenarios")
        expect_response = False
        for step in node["steps"]:
            if not isinstance(step, Mapping):
                raise EvaluationError("completed trajectory step is not an object")
            role = step.get("role")
            if expect_response:
                if role != "tool_response":
                    raise EvaluationError("completed tool calls and responses do not alternate")
                expect_response = False
            elif role == "tool_response":
                raise EvaluationError("completed tool response has no preceding call")
            elif role == "tool_call":
                content = step.get("content")
                if not isinstance(content, list) or not content:
                    raise EvaluationError("completed tool-call step is empty")
                for call in content:
                    if (
                        not isinstance(call, Mapping)
                        or call.get("name") not in allowed_tools
                        or not isinstance(call.get("arguments"), dict)
                    ):
                        raise EvaluationError("completed trajectory contains an invalid tool call")
                    calls += 1
                expect_response = True
        if expect_response:
            raise EvaluationError("completed trajectory ends before a tool response")
    if accepted == 0 or calls == 0:
        raise EvaluationError("completed trajectory has no accepted executable node")


def _history_messages(nodes: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for node in nodes:
        steps = node.get("steps") or []
        for index in range(0, len(steps) - 1, 2):
            messages.append({"role": "user", "content": format_step(steps[index]).strip()})
            messages.append(
                {"role": "assistant", "content": format_step(steps[index + 1]).strip()}
            )
    return messages


def _suite_settings(config: MiniConfig) -> dict[str, Any]:
    return {
        "temperature": config.evaluation.temperature,
        "top_p": config.evaluation.top_p,
        "presence_penalty": config.evaluation.presence_penalty,
        "max_tokens": config.evaluation.max_tokens,
        "seed": config.evaluation.seed,
        "enable_thinking": config.evaluation.enable_thinking,
        "max_turns": config.evaluation.max_turns,
    }


def prepare_evaluation_suite(
    config: MiniConfig, run_id: str, *, catalog: CatalogReport | None = None
) -> tuple[list[EvaluationItem], dict[str, Any], Path]:
    """Resolve held-out seeds and freeze a model-independent evaluation contract."""
    root = _run_root(config, run_id)
    dataset_manifest_path = root / "datasets" / "dataset_manifest.json"
    dataset_manifest = _load_json_object(dataset_manifest_path, label="dataset manifest")
    if dataset_manifest.get("source_run_id") != run_id:
        raise EvaluationError("dataset manifest belongs to a different run")
    split = dataset_manifest.get("split")
    if not isinstance(split, dict):
        raise EvaluationError("dataset manifest has no seed split")
    train_seeds = set(split.get("train_seeds") or [])
    validation_seeds = set(split.get("validation_seeds") or [])
    if not validation_seeds or train_seeds.intersection(validation_seeds):
        raise EvaluationError("evaluation requires a non-empty, leak-free validation seed split")

    catalog = catalog or validate_catalog(config)
    source = dataset_manifest.get("source")
    if not isinstance(source, dict) or source.get("catalog_sha256") != catalog.digest:
        raise EvaluationError("dataset catalog hash does not match the audited mini catalog")
    all_schemas = _catalog_schemas(catalog)
    allowed_tools = set(all_schemas)
    ranked_seeds = sorted(
        validation_seeds,
        key=lambda seed: (
            hashlib.sha256(f"evaluation:{config.evaluation.seed}:{seed}".encode("ascii")).digest(),
            seed,
        ),
    )
    selected_seeds = ranked_seeds[: config.evaluation.held_out_trajectories]
    items: list[EvaluationItem] = []
    records: list[dict[str, Any]] = []
    completed = root / "trajectories" / "completed"
    for seed in selected_seeds:
        path = completed / f"{seed}.json"
        payload = _load_json_object(path, label="held-out trajectory")
        if payload.get("seed") != seed:
            raise EvaluationError(f"trajectory seed mismatch: {path}")
        try:
            _validate_heldout_payload(payload, allowed_tools)
        except (EvaluationError, ValueError, TypeError, KeyError) as exc:
            raise EvaluationError(f"invalid held-out trajectory {path.name}: {exc}") from exc
        nodes: list[dict[str, Any]] = []
        for node in payload.get("nodes") or []:
            if not isinstance(node, dict) or node.get("decision") is not True or not node.get("steps"):
                break
            nodes.append(node)
        servers = sorted(
            {
                server
                for node in nodes
                for server in (node.get("mcp_servers") or [])
                if isinstance(server, str)
            }
        )
        schemas = {
            name: schema
            for name, schema in all_schemas.items()
            if name.partition("-")[0] in servers
        }
        user_tools = payload.get("user_tools") or []
        user_names = {
            value.get("name") for value in user_tools if isinstance(value, Mapping)
        }
        assistant_schema_map = {
            name: schema for name, schema in schemas.items() if name not in user_names
        }
        assistant_schemas = list(assistant_schema_map.values())
        system = build_system_prompt(assistant_schemas, user_tools)
        for node_index, node in enumerate(nodes):
            initial = node.get("initial_scenario")
            final = node.get("final_scenario")
            if not isinstance(initial, dict) or not isinstance(final, dict):
                raise EvaluationError(f"held-out node has no executable scenarios: {seed}:{node_index}")
            steps = node.get("steps") or []
            if not steps or steps[0].get("role") != "user":
                raise EvaluationError(f"held-out node has no initial user request: {seed}:{node_index}")
            messages = [{"role": "system", "content": system}]
            messages.extend(_history_messages(nodes[:node_index]))
            messages.append({"role": "user", "content": format_step(steps[0]).strip()})
            item_id = f"seed-{seed}-node-{node_index}"
            item = EvaluationItem(
                item_id=item_id,
                seed=seed,
                node_index=node_index,
                messages=tuple(messages),
                initial_scenario=copy.deepcopy(initial),
                reference_final_scenario=copy.deepcopy(final),
                tool_schemas=copy.deepcopy(assistant_schema_map),
                reference_tool_names=_reference_tool_names(node),
            )
            items.append(item)
            records.append(
                {
                    "item_id": item_id,
                    "seed": seed,
                    "node_index": node_index,
                    "source_file": path.relative_to(root).as_posix(),
                    "source_sha256": _sha256_file(path),
                    "prompt_sha256": _sha256_json(messages),
                    "tool_schema_sha256": _sha256_json(assistant_schema_map),
                    "initial_scenario_sha256": _sha256_json(initial),
                    "reference_final_scenario_sha256": _sha256_json(final),
                    "reference_tool_names": list(item.reference_tool_names),
                    "deterministic_final_state": True,
                }
            )
    if not items:
        raise EvaluationError("held-out validation seeds contain no accepted executable nodes")

    suite: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "dataset_manifest_sha256": _sha256_file(dataset_manifest_path),
        "dataset_source_run_sha256": dataset_manifest.get("source_run_sha256"),
        "catalog_sha256": catalog.digest,
        "selection": {
            "source": "dataset_manifest.split.validation_seeds",
            "algorithm": "sha256_rank_v1",
            "requested_trajectories": config.evaluation.held_out_trajectories,
            "selected_trajectories": len(selected_seeds),
            "selected_seeds": selected_seeds,
            "train_seed_overlap": sorted(train_seeds.intersection(selected_seeds)),
        },
        "decoding": _suite_settings(config),
        "task_count": len(items),
        "items": records,
    }
    suite["contract_sha256"] = _sha256_json(suite)
    evaluation_dir = root / "evaluation"
    suite_path = evaluation_dir / "suite.json"
    if suite_path.exists():
        existing = _load_json_object(suite_path, label="evaluation suite")
        if existing != suite:
            raise EvaluationError(
                "evaluation suite already exists with a different contract; use a new run ID"
            )
    else:
        atomic_write_json(suite_path, suite, overwrite=False)
    return items, suite, suite_path


def _arguments_valid(schema: Mapping[str, Any], arguments: Mapping[str, Any]) -> bool:
    parameters = schema.get("function", {}).get("parameters", {})
    validator = validator_for(parameters)(parameters)
    return not any(validator.iter_errors(arguments))


class MCPScenarioSession:
    """One fresh set of stateful MCP clients for one evaluation item."""

    def __init__(self, initial_scenario: Mapping[str, Any], session_label: str):
        from src.manager.mcp_client_manager import MCPManager

        self.manager = MCPManager
        self.initial = copy.deepcopy(dict(initial_scenario))
        nonce = uuid4().hex
        self.client_ids = {
            server: f"{server}-eval-{session_label}-{nonce}" for server in self.initial
        }

    async def start(self) -> bool:
        scenarios = {
            self.client_ids[server]: copy.deepcopy(scenario)
            for server, scenario in self.initial.items()
        }
        responses = await self.manager.aload_scenarios(scenarios, check=True)
        if not all(isinstance(value, str) and "Successfully" in value for value in responses.values()):
            return False
        return await self.save() == self.initial

    async def call(self, name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
        server = name.partition("-")[0]
        client_id = self.client_ids.get(server)
        if client_id is None:
            return False, f"{name} error: server is outside this evaluation item"
        response = await self.manager.acall_tool(client_id, name, arguments)
        return not bool(_TOOL_FAILURE.search(response)), response

    async def save(self) -> dict[str, Any]:
        return await self.manager.asave_all_scenarios(list(self.client_ids.values()))

    async def close(self) -> None:
        await asyncio.gather(
            *(self.manager.aclose_client(value) for value in self.client_ids.values()),
            return_exceptions=True,
        )


class OpenAIHTTPClient:
    """Small OpenAI-compatible client that does not expose the API key in artifacts."""

    def __init__(
        self, *, base_url: str, api_key: str, model: str, timeout_seconds: float
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _request(self, path: str, payload: object | None = None) -> dict[str, Any]:
        body = None
        headers = {"Authorization": f"Bearer {self.api_key}"}
        method = "GET"
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
            method = "POST"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                value = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise EvaluationError(f"model endpoint returned HTTP {exc.code} for {path}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, TimeoutError):
                raise TimeoutError("model endpoint request timed out") from exc
            raise EvaluationError(f"model endpoint request failed for {path}: {type(exc).__name__}") from exc
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise EvaluationError(f"model endpoint returned invalid JSON for {path}") from exc
        if not isinstance(value, dict):
            raise EvaluationError(f"model endpoint returned a non-object for {path}")
        return value

    def _completion_payload(
        self, messages: Sequence[Mapping[str, str]], settings: DecodingSettings
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [dict(message) for message in messages],
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "presence_penalty": settings.presence_penalty,
            "max_tokens": settings.max_tokens,
            "seed": settings.seed,
            "chat_template_kwargs": {"enable_thinking": settings.enable_thinking},
        }

    async def complete(
        self, messages: Sequence[Mapping[str, str]], settings: DecodingSettings
    ) -> ModelReply:
        started = time.perf_counter()
        response = await asyncio.to_thread(
            self._request, "/chat/completions", self._completion_payload(messages, settings)
        )
        latency = time.perf_counter() - started
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EvaluationError("chat completion has no message content") from exc
        if not isinstance(content, str):
            raise EvaluationError("chat completion message content is not text")
        usage_value = response.get("usage")
        usage = None
        if isinstance(usage_value, dict):
            usage = {
                key: int(usage_value[key])
                for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                if isinstance(usage_value.get(key), int)
            }
        model = response.get("model") if isinstance(response.get("model"), str) else None
        return ModelReply(content=content, model=model, usage=usage, latency_seconds=latency)

    async def health(self, settings: DecodingSettings) -> dict[str, Any]:
        models = await asyncio.to_thread(self._request, "/models")
        data = models.get("data")
        model_ids = sorted(
            value["id"]
            for value in data or []
            if isinstance(value, dict) and isinstance(value.get("id"), str)
        )
        if self.model not in model_ids:
            raise EvaluationError(
                f"expected exposed model {self.model!r} is absent from /v1/models"
            )
        probe = await self.complete(
            ({"role": "user", "content": "Reply with OK."},),
            DecodingSettings(
                temperature=0.0,
                top_p=1.0,
                presence_penalty=0.0,
                max_tokens=8,
                seed=settings.seed,
                enable_thinking=False,
            ),
        )
        if probe.model != self.model:
            raise EvaluationError(
                f"health completion used {probe.model!r}, expected {self.model!r}"
            )
        return {
            "model_ids": model_ids,
            "completion_model": probe.model,
            "completion_succeeded": bool(probe.content.strip()),
        }


def _add_failure(result: ItemResult, category: str) -> None:
    if category not in result.failure_categories:
        result.failure_categories.append(category)


async def evaluate_item(
    item: EvaluationItem,
    client: CompletionClient,
    settings: DecodingSettings,
    *,
    max_turns: int,
    session_factory: Callable[[Mapping[str, Any], str], ScenarioSession] = MCPScenarioSession,
) -> ItemResult:
    """Execute one task in a fresh session and compare against its selected reference."""
    result = ItemResult(item_id=item.item_id, seed=item.seed, node_index=item.node_index)
    messages = [dict(message) for message in item.messages]
    session = session_factory(copy.deepcopy(item.initial_scenario), item.item_id)
    stopped = False
    try:
        try:
            result.initial_state_exact = await session.start()
        except TimeoutError as exc:
            _add_failure(result, "timeout")
            result.safe_error = str(exc)
            return result
        except Exception as exc:
            _add_failure(result, "execution")
            result.safe_error = f"scenario start failed: {type(exc).__name__}: {exc}"
            return result
        if not result.initial_state_exact:
            _add_failure(result, "final_state_mismatch")
            result.safe_error = "fresh MCP session did not round-trip the reference initial state"
            return result

        for _ in range(max_turns):
            result.response_attempts += 1
            result.turns += 1
            try:
                reply = await client.complete(messages, settings)
            except TimeoutError as exc:
                _add_failure(result, "timeout")
                result.safe_error = str(exc)
                break
            except Exception as exc:
                _add_failure(result, "execution")
                result.safe_error = f"model request failed: {type(exc).__name__}: {exc}"
                break
            result.latencies_seconds.append(reply.latency_seconds)
            if reply.usage:
                for key, value in reply.usage.items():
                    result.token_usage[key] = result.token_usage.get(key, 0) + value
            parsed, calls = parse_tool_output(reply.content)
            result.trace.append(
                {
                    "role": "assistant",
                    "content": reply.content,
                    "model": reply.model,
                    "latency_seconds": reply.latency_seconds,
                    "usage": reply.usage,
                    "parsed": parsed,
                }
            )
            if not parsed:
                _add_failure(result, "parse")
                break
            result.parsed_responses += 1
            if not calls:
                stopped = True
                break

            result.tool_calls += len(calls)
            responses: list[str] = []
            batch_valid = True
            for call in calls:
                name = call["name"]
                arguments = call["arguments"]
                result.predicted_tool_names.append(name)
                schema = item.tool_schemas.get(name)
                if schema is None:
                    _add_failure(result, "wrong_tool")
                    responses.append(f"Error: {name} is not an available tool.")
                    batch_valid = False
                    continue
                result.valid_tool_names += 1
                if not _arguments_valid(schema, arguments):
                    _add_failure(result, "wrong_arguments")
                    responses.append(f"Error: arguments for {name} do not match its schema.")
                    batch_valid = False
                    continue
                result.valid_argument_schemas += 1
                try:
                    succeeded, response = await session.call(name, arguments)
                except TimeoutError as exc:
                    _add_failure(result, "timeout")
                    response = f"{name} timed out: {exc}"
                    succeeded = False
                except Exception as exc:
                    _add_failure(result, "execution")
                    response = f"{name} failed: {type(exc).__name__}: {exc}"
                    succeeded = False
                if succeeded:
                    result.execution_successes += 1
                else:
                    _add_failure(result, "execution")
                    batch_valid = False
                responses.append(response)
            result.trace.append({"role": "tool_call", "content": calls})
            result.trace.append({"role": "tool_response", "content": responses})
            messages.append({"role": "assistant", "content": reply.content})
            messages.append(
                {
                    "role": "user",
                    "content": "".join(
                        f"<tool_response>\n{response}\n</tool_response>\n"
                        for response in responses
                    ),
                }
            )
            if not batch_valid:
                break
        if not stopped and result.turns >= max_turns and not result.failure_categories:
            _add_failure(result, "timeout")
            result.safe_error = "maximum evaluation turns reached"
        try:
            final_scenario = await session.save()
        except TimeoutError as exc:
            _add_failure(result, "timeout")
            result.safe_error = str(exc)
            final_scenario = {}
        except Exception as exc:
            _add_failure(result, "execution")
            result.safe_error = f"scenario save failed: {type(exc).__name__}: {exc}"
            final_scenario = {}
        result.trace.append({"role": "final_scenario", "content": final_scenario})
        result.exact_tool_sequence = tuple(result.predicted_tool_names) == item.reference_tool_names
        if item.reference_tool_names and not result.predicted_tool_names:
            _add_failure(result, "wrong_tool")
        result.final_scenario_exact = (
            item.deterministic_final_state
            and final_scenario == item.reference_final_scenario
        )
        if item.deterministic_final_state and not result.final_scenario_exact:
            _add_failure(result, "final_state_mismatch")
        result.task_success = (
            result.initial_state_exact
            and bool(result.predicted_tool_names)
            and result.final_scenario_exact
            and not any(
                category in result.failure_categories
                for category in (
                    "parse",
                    "wrong_tool",
                    "wrong_arguments",
                    "execution",
                    "timeout",
                )
            )
        )
        return result
    finally:
        try:
            await session.close()
        except Exception:
            _add_failure(result, "execution")


def _rate(numerator: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def _percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_success_interval(
    successes: Sequence[bool], *, samples: int, confidence: float, seed: int
) -> dict[str, float | int] | None:
    """Return a deterministic percentile bootstrap interval for a Bernoulli mean."""
    if not successes or samples <= 0:
        return None
    rng = random.Random(seed)
    size = len(successes)
    means = sorted(
        sum(bool(successes[rng.randrange(size)]) for _ in range(size)) / size
        for _ in range(samples)
    )
    alpha = (1.0 - confidence) / 2.0
    return {
        "confidence": confidence,
        "samples": samples,
        "lower": float(_percentile(means, alpha)),
        "upper": float(_percentile(means, 1.0 - alpha)),
    }


def calculate_metrics(
    results: Sequence[ItemResult], *, bootstrap_samples: int, confidence: float, seed: int
) -> dict[str, Any]:
    tasks = len(results)
    response_attempts = sum(value.response_attempts for value in results)
    parsed = sum(value.parsed_responses for value in results)
    calls = sum(value.tool_calls for value in results)
    latencies = [latency for value in results for latency in value.latencies_seconds]
    usage_keys = ("prompt_tokens", "completion_tokens", "total_tokens")
    usage = {key: sum(value.token_usage.get(key, 0) for value in results) for key in usage_keys}
    usage_available_tasks = sum(bool(value.token_usage) for value in results)
    failures: Counter[str] = Counter(
        category for value in results for category in set(value.failure_categories)
    )
    successes = [value.task_success for value in results]
    success_count = sum(successes)
    return {
        "sample_count": tasks,
        "rates": {
            "structured_output_parse": _rate(parsed, response_attempts),
            "valid_tool_name": _rate(sum(value.valid_tool_names for value in results), calls),
            "valid_argument_schema": _rate(
                sum(value.valid_argument_schemas for value in results), calls
            ),
            "tool_call_execution_success": _rate(
                sum(value.execution_successes for value in results), calls
            ),
            "exact_tool_sequence": _rate(
                sum(value.exact_tool_sequence for value in results), tasks
            ),
            "final_scenario_exact": _rate(
                sum(value.final_scenario_exact for value in results), tasks
            ),
            "task_success": _rate(success_count, tasks),
        },
        "task_success_bootstrap_interval": bootstrap_success_interval(
            successes, samples=bootstrap_samples, confidence=confidence, seed=seed
        ),
        "latency_seconds": {
            "count": len(latencies),
            "average": sum(latencies) / len(latencies) if latencies else None,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
            "p99": _percentile(latencies, 0.99),
        },
        "averages_per_task": {
            "tool_calls": calls / tasks if tasks else None,
            "turns": sum(value.turns for value in results) / tasks if tasks else None,
        },
        "token_usage": {
            "available_tasks": usage_available_tasks,
            "totals": usage,
            "average_total_tokens_per_available_task": (
                usage["total_tokens"] / usage_available_tasks if usage_available_tasks else None
            ),
        },
        "failure_counts": {
            name: failures.get(name, 0)
            for name in (
                "parse",
                "wrong_tool",
                "wrong_arguments",
                "execution",
                "timeout",
                "final_state_mismatch",
            )
        },
        "cross_session_state_leakage": {
            "initial_state_round_trip_failures": sum(
                not value.initial_state_exact for value in results
            ),
            "passed": all(value.initial_state_exact for value in results),
        },
    }


def _result_summary(value: ItemResult, failure_trace: str | None) -> dict[str, Any]:
    result = asdict(value)
    result.pop("trace", None)
    result["failure_trace"] = failure_trace
    return result


async def evaluate_candidate(
    *,
    config: MiniConfig,
    run_id: str,
    candidate: str,
    model: str,
    provenance: Mapping[str, Any],
    health: Mapping[str, Any],
    items: Sequence[EvaluationItem],
    suite: Mapping[str, Any],
    client: CompletionClient,
    overwrite: bool = False,
    session_factory: Callable[[Mapping[str, Any], str], ScenarioSession] = MCPScenarioSession,
) -> tuple[dict[str, Any], Path]:
    if candidate not in {"teacher", "student"}:
        raise EvaluationError("candidate must be teacher or student")
    root = _run_root(config, run_id)
    evaluation_dir = root / "evaluation"
    metrics_path = evaluation_dir / f"{candidate}_metrics.json"
    if metrics_path.exists() and not overwrite:
        raise EvaluationError(f"candidate result already exists: {metrics_path}; pass --overwrite")
    settings = DecodingSettings(
        temperature=config.evaluation.temperature,
        top_p=config.evaluation.top_p,
        presence_penalty=config.evaluation.presence_penalty,
        max_tokens=config.evaluation.max_tokens,
        seed=config.evaluation.seed,
        enable_thinking=config.evaluation.enable_thinking,
    )
    semaphore = asyncio.Semaphore(config.evaluation.workers)

    async def run_one(item: EvaluationItem) -> ItemResult:
        async with semaphore:
            return await evaluate_item(
                item,
                client,
                settings,
                max_turns=config.evaluation.max_turns,
                session_factory=session_factory,
            )

    results = await asyncio.gather(*(run_one(item) for item in items))
    secrets = _known_secrets(config)
    item_by_id = {item.item_id: item for item in items}
    summaries: list[dict[str, Any]] = []
    for result in results:
        failure_trace = None
        if result.failure_categories:
            trace_path = evaluation_dir / "traces" / "failed" / candidate / f"{result.item_id}.json"
            item = item_by_id[result.item_id]
            trace_payload = redact_secrets(
                {
                    "schema_version": 1,
                    "candidate": candidate,
                    "model": model,
                    "item_id": result.item_id,
                    "seed": result.seed,
                    "node_index": result.node_index,
                    "failure_categories": result.failure_categories,
                    "safe_error": result.safe_error,
                    "input_messages": list(item.messages),
                    "initial_scenario": item.initial_scenario,
                    "reference_final_scenario": item.reference_final_scenario,
                    "reference_tool_names": list(item.reference_tool_names),
                    "trace": result.trace,
                },
                secrets=secrets,
            )
            atomic_write_json(trace_path, trace_payload)
            failure_trace = trace_path.relative_to(evaluation_dir).as_posix()
        summaries.append(_result_summary(result, failure_trace))
    metrics = calculate_metrics(
        results,
        bootstrap_samples=config.evaluation.bootstrap_samples,
        confidence=config.evaluation.bootstrap_confidence,
        seed=config.evaluation.seed,
    )
    artifact = redact_secrets(
        {
            "schema_version": 1,
            "run_id": run_id,
            "candidate": candidate,
            "model": model,
            "suite_contract_sha256": suite["contract_sha256"],
            "decoding": asdict(settings),
            "max_turns": config.evaluation.max_turns,
            "workers": config.evaluation.workers,
            "provenance": dict(provenance),
            "health": dict(health),
            "metrics": metrics,
            "items": summaries,
        },
        secrets=secrets,
    )
    atomic_write_json(metrics_path, artifact)
    write_report(evaluation_dir)
    return artifact, metrics_path


def _format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "pass" if value else "fail"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(evaluation_dir: Path) -> Path:
    """Render the teacher and student metrics side by side from source JSON."""
    sources: dict[str, dict[str, Any] | None] = {}
    for candidate in ("teacher", "student"):
        path = evaluation_dir / f"{candidate}_metrics.json"
        sources[candidate] = _load_json_object(path, label=f"{candidate} metrics") if path.exists() else None
    lines = [
        "# MoLab mini executable evaluation",
        "",
        "Every value below is sourced from the linked candidate JSON. The immutable task and",
        "prompt contract is recorded in [suite.json](suite.json).",
        "",
        "| Metric | Teacher ([JSON](teacher_metrics.json)) | Student ([JSON](student_metrics.json)) |",
        "|---|---:|---:|",
    ]
    rate_names = (
        "structured_output_parse",
        "valid_tool_name",
        "valid_argument_schema",
        "tool_call_execution_success",
        "exact_tool_sequence",
        "final_scenario_exact",
        "task_success",
    )
    for name in rate_names:
        row = []
        for candidate in ("teacher", "student"):
            source = sources[candidate]
            rate = source["metrics"]["rates"][name] if source else None
            row.append(
                "pending"
                if rate is None
                else f"{_format_metric(rate['value'])} ({rate['numerator']}/{rate['denominator']})"
            )
        lines.append(f"| {name.replace('_', ' ')} | {row[0]} | {row[1]} |")
    for label, path in (
        ("evaluation tasks", ("sample_count",)),
        ("average model latency (seconds)", ("latency_seconds", "average")),
        ("p50 model latency (seconds)", ("latency_seconds", "p50")),
        ("p95 model latency (seconds)", ("latency_seconds", "p95")),
        ("p99 model latency (seconds)", ("latency_seconds", "p99")),
        ("average tool calls per task", ("averages_per_task", "tool_calls")),
        ("average turns per task", ("averages_per_task", "turns")),
        ("prompt tokens", ("token_usage", "totals", "prompt_tokens")),
        ("completion tokens", ("token_usage", "totals", "completion_tokens")),
        ("total tokens", ("token_usage", "totals", "total_tokens")),
    ):
        values = []
        for candidate in ("teacher", "student"):
            current: Any = sources[candidate]["metrics"] if sources[candidate] else None
            for key in path:
                current = current.get(key) if isinstance(current, dict) else None
            values.append("pending" if sources[candidate] is None else _format_metric(current))
        lines.append(f"| {label} | {values[0]} | {values[1]} |")
    interval_values = []
    for candidate in ("teacher", "student"):
        source = sources[candidate]
        interval = source["metrics"]["task_success_bootstrap_interval"] if source else None
        interval_values.append(
            "pending"
            if source is None
            else "n/a"
            if interval is None
            else f"[{interval['lower']:.4f}, {interval['upper']:.4f}] "
            f"({interval['confidence']:.0%}, {interval['samples']} resamples)"
        )
    lines.append(
        f"| task success bootstrap interval | {interval_values[0]} | {interval_values[1]} |"
    )

    lines.extend(["", "## Release gates", ""])
    teacher = sources["teacher"]
    student = sources["student"]
    if teacher and student:
        teacher_success = teacher["metrics"]["rates"]["task_success"]["value"] or 0.0
        student_rates = student["metrics"]["rates"]
        gates = {
            "student structured-output parse rate >= 95%": (
                student_rates["structured_output_parse"]["value"] or 0.0
            )
            >= 0.95,
            "student valid tool-name rate >= 98%": (
                student_rates["valid_tool_name"]["value"] or 0.0
            )
            >= 0.98,
            "student task success within 15 percentage points of teacher": (
                student_rates["task_success"]["value"] or 0.0
            )
            >= teacher_success - 0.15,
            "no cross-session state leakage": teacher["metrics"][
                "cross_session_state_leakage"
            ]["passed"]
            and student["metrics"]["cross_session_state_leakage"]["passed"],
        }
        for name, passed in gates.items():
            lines.append(f"- {'PASS' if passed else 'FAIL'}: {name}")
    else:
        lines.append("Pending both teacher and student result JSON files.")

    lines.extend(["", "## Failure counts", ""])
    lines.append("| Category | Teacher | Student |")
    lines.append("|---|---:|---:|")
    for category in (
        "parse",
        "wrong_tool",
        "wrong_arguments",
        "execution",
        "timeout",
        "final_state_mismatch",
    ):
        values = [
            "pending"
            if sources[candidate] is None
            else str(sources[candidate]["metrics"]["failure_counts"][category])
            for candidate in ("teacher", "student")
        ]
        lines.append(f"| {category.replace('_', ' ')} | {values[0]} | {values[1]} |")

    lines.extend(["", "## Representative failures", ""])
    any_failures = False
    for candidate in ("teacher", "student"):
        source = sources[candidate]
        if not source:
            continue
        failures = [item for item in source["items"] if item.get("failure_trace")][:5]
        for item in failures:
            any_failures = True
            trace = item["failure_trace"]
            categories = ", ".join(item["failure_categories"])
            lines.append(f"- {candidate}: [{item['item_id']}]({trace}) — {categories}")
    if not any_failures:
        lines.append("No failed traces have been recorded.")
    report_path = evaluation_dir / "report.md"
    atomic_write_text(report_path, "\n".join(lines) + "\n")
    return report_path


def _student_provenance(
    config: MiniConfig,
    run_id: str,
    *,
    model: str,
    serving_mode: str,
    adapter_path: str | None,
    max_lora_rank: int | None,
    merged_model_path: str | None,
    base_revision: str | None,
    merge_dtype: str | None,
) -> dict[str, Any]:
    root = _run_root(config, run_id)
    base_model = config.dataset.tokenizer_model
    if model == base_model:
        raise EvaluationError("student exposed model name must differ from the unmodified base model")
    if serving_mode == "lora":
        path = Path(adapter_path).expanduser().resolve() if adapter_path else root / "training" / "adapter"
        if not path.is_relative_to((root / "training").resolve()):
            raise EvaluationError("student adapter must be beneath the run training directory")
        adapter_config = _load_json_object(path / "adapter_config.json", label="adapter config")
        if str(adapter_config.get("peft_type", "")).upper() != "LORA":
            raise EvaluationError("student adapter config does not identify LoRA")
        rank = adapter_config.get("r")
        if not isinstance(rank, int) or rank <= 0:
            raise EvaluationError("student adapter config has no positive LoRA rank")
        if max_lora_rank is None or max_lora_rank < rank:
            raise EvaluationError("configured maximum LoRA rank is below the adapter rank")
        return {
            "serving_mode": "vllm_lora",
            "base_model": base_model,
            "base_revision": base_revision or config.dataset.tokenizer_revision or "main",
            "exposed_adapter_name": model,
            "adapter_path": path.as_posix(),
            "adapter_sha256": _sha256_tree(path),
            "adapter_rank": rank,
            "maximum_lora_rank": max_lora_rank,
        }
    if serving_mode != "merged":
        raise EvaluationError("student serving mode must be lora or merged")
    if not (merged_model_path and adapter_path and base_revision and merge_dtype):
        raise EvaluationError(
            "merged serving requires --merged-model-path, --adapter-path, --base-revision, and --merge-dtype"
        )
    merged = Path(merged_model_path).expanduser().resolve()
    adapter = Path(adapter_path).expanduser().resolve()
    if not merged.is_relative_to(root) or not adapter.is_relative_to(root):
        raise EvaluationError("merged model and adapter must be beneath the run directory")
    return {
        "serving_mode": "explicit_merge_fallback",
        "base_model": base_model,
        "base_revision": base_revision,
        "exposed_merged_model_name": model,
        "adapter_path": adapter.as_posix(),
        "adapter_sha256": _sha256_tree(adapter),
        "merge_dtype": merge_dtype,
        "merged_model_path": merged.as_posix(),
        "merged_model_sha256": _sha256_tree(merged),
    }


async def _run_cli(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    config = load_config(args.config, repo_root=args.repo_root)
    items, suite, _ = prepare_evaluation_suite(config, args.run_id)
    model = args.model or (config.teacher.model if args.candidate == "teacher" else None)
    if not model:
        raise EvaluationError("--model is required for the student candidate")
    api_key = os.environ.get(config.teacher.api_key_env)
    if not api_key:
        raise EvaluationError(
            f"required API key environment variable is absent: {config.teacher.api_key_env}"
        )
    base_url = args.base_url or config.teacher.base_url
    parsed_url = urlparse(base_url)
    if (
        parsed_url.scheme not in {"http", "https"}
        or parsed_url.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed_url.path.rstrip("/") != "/v1"
        or not parsed_url.port
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise EvaluationError("evaluation base URL must be a credential-free loopback /v1 endpoint")
    client = OpenAIHTTPClient(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout_seconds=config.evaluation.request_timeout_seconds,
    )
    settings = DecodingSettings(
        temperature=config.evaluation.temperature,
        top_p=config.evaluation.top_p,
        presence_penalty=config.evaluation.presence_penalty,
        max_tokens=config.evaluation.max_tokens,
        seed=config.evaluation.seed,
        enable_thinking=config.evaluation.enable_thinking,
    )
    health = await client.health(settings)
    if args.candidate == "teacher":
        provenance = {
            "serving_mode": "base_model",
            "configured_model": config.teacher.model,
            "exposed_model": model,
            "base_url": base_url,
            "api_key_environment": config.teacher.api_key_env,
            "api_key_present": True,
        }
    else:
        provenance = _student_provenance(
            config,
            args.run_id,
            model=model,
            serving_mode=args.student_serving_mode,
            adapter_path=args.adapter_path,
            max_lora_rank=args.max_lora_rank,
            merged_model_path=args.merged_model_path,
            base_revision=args.base_revision,
            merge_dtype=args.merge_dtype,
        )
        if health.get("completion_model") != provenance.get(
            "exposed_adapter_name", provenance.get("exposed_merged_model_name")
        ):
            raise EvaluationError("student health check did not use the declared adapter/export name")
        provenance.update(
            {
                "base_url": base_url,
                "api_key_environment": config.teacher.api_key_env,
                "api_key_present": True,
            }
        )

    from src.manager.mcp_client_manager import MCPManager

    MCPManager.init_config(config.catalog.mcp_config, overwrite=True)
    try:
        return await evaluate_candidate(
            config=config,
            run_id=args.run_id,
            candidate=args.candidate,
            model=model,
            provenance=provenance,
            health=health,
            items=items,
            suite=suite,
            client=client,
            overwrite=args.overwrite,
        )
    finally:
        await MCPManager.aclose_all_clients()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run held-out executable mini evaluation")
    parser.add_argument("--config", required=True, help="Mini pipeline TOML path")
    parser.add_argument("--run-id", required=True, help="Prepared synthesis/training run ID")
    parser.add_argument("--candidate", required=True, choices=("teacher", "student"))
    parser.add_argument("--model", help="Exact model or named adapter exposed by /v1/models")
    parser.add_argument("--base-url", help="Loopback OpenAI-compatible /v1 endpoint")
    parser.add_argument("--student-serving-mode", choices=("lora", "merged"), default="lora")
    parser.add_argument("--adapter-path")
    parser.add_argument("--max-lora-rank", type=int, default=64)
    parser.add_argument("--merged-model-path")
    parser.add_argument("--base-revision")
    parser.add_argument("--merge-dtype")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--repo-root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        artifact, path = asyncio.run(_run_cli(args))
    except (
        CatalogValidationError,
        EvaluationError,
        MiniConfigError,
        ValueError,
    ) as exc:
        print(f"evaluation failed: {exc}", file=sys.stderr)
        return 1
    metrics = artifact["metrics"]
    success = metrics["rates"]["task_success"]
    print(
        f"{artifact['candidate']} evaluation: task_success="
        f"{success['numerator']}/{success['denominator']}; metrics={path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DecodingSettings",
    "EvaluationError",
    "EvaluationItem",
    "ItemResult",
    "ModelReply",
    "OpenAIHTTPClient",
    "bootstrap_success_interval",
    "calculate_metrics",
    "evaluate_candidate",
    "evaluate_item",
    "main",
    "parse_tool_output",
    "prepare_evaluation_suite",
    "redact_secrets",
    "write_report",
]
