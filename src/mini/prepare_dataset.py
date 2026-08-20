"""Deterministic, leak-free SFT dataset preparation for mini runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .artifacts import atomic_write_json, atomic_write_text
from .catalog import CatalogReport, CatalogValidationError, validate_catalog
from .config import MiniConfig, MiniConfigError, load_config
from .manifest import RunManifest
from src.utils.data_conversion import iter_sft_samples, validate_steps


class DatasetPreparationError(RuntimeError):
    """Raised when source data or tokenizer behavior violates the dataset contract."""


class DatasetGateError(DatasetPreparationError):
    """Raised after diagnostics are written when a release gate does not pass."""


@dataclass(frozen=True)
class PreparedDataset:
    manifest_path: Path
    all_path: Path
    train_path: Path
    validation_path: Path
    inspection_path: Path
    dataset_info_path: Path
    training_profile_path: Path
    manifest: dict[str, Any]


@dataclass(frozen=True)
class _TrajectoryInfo:
    seed: int
    path: Path
    tool_calls: int
    servers: tuple[str, ...]


class _AtomicJsonArrayWriter:
    """Stream a compact JSON array to a same-directory atomic replacement."""

    def __init__(self, destination: Path):
        self.destination = destination
        self.temporary: Path | None = None
        self.handle = None
        self.first = True

    def __enter__(self) -> "_AtomicJsonArrayWriter":
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(
            prefix=f".{self.destination.name}.", suffix=".tmp", dir=self.destination.parent
        )
        self.temporary = Path(name)
        self.handle = os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")
        self.handle.write("[")
        return self

    def write(self, value: Mapping[str, Any]) -> None:
        if self.handle is None:
            raise RuntimeError("JSON writer is not open")
        if not self.first:
            self.handle.write(",")
        json.dump(value, self.handle, ensure_ascii=False, separators=(",", ":"))
        self.first = False

    def __exit__(self, exc_type, exc, traceback) -> None:
        assert self.handle is not None and self.temporary is not None
        try:
            if exc_type is None:
                self.handle.write("]\n")
                self.handle.flush()
                os.fsync(self.handle.fileno())
            self.handle.close()
            if exc_type is None:
                os.replace(self.temporary, self.destination)
        finally:
            self.temporary.unlink(missing_ok=True)


_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SEED_FILE = re.compile(r"([0-9]+)\.json\Z")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DatasetPreparationError(f"cannot read trajectory {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DatasetPreparationError(f"trajectory root must be an object: {path}")
    return value


def _tool_schemas(catalog: CatalogReport) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for server in catalog.servers:
        for tool in server.metadata["tools"]:
            full_name = f"{server.name}-{tool['name']}"
            schemas[full_name] = {
                "type": "function",
                "function": {
                    "name": full_name,
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema") or {
                        "type": "object",
                        "properties": {},
                    },
                },
            }
    return schemas


def _accepted_nodes(payload: Mapping[str, Any]):
    for node in payload.get("nodes") or []:
        if not isinstance(node, Mapping) or node.get("decision") is not True or not node.get("steps"):
            break
        yield node


def _validate_conversion_values(
    payload: Mapping[str, Any], allowed_tools: set[str]
) -> tuple[int, tuple[str, ...], Counter[str], Counter[str]]:
    tool_calls = 0
    servers: set[str] = set()
    role_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    accepted = list(_accepted_nodes(payload))
    if not accepted:
        raise DatasetPreparationError("trajectory has no accepted node")
    for node_index, node in enumerate(accepted):
        node_servers = node.get("mcp_servers") or []
        if not isinstance(node_servers, list) or any(not isinstance(item, str) for item in node_servers):
            raise DatasetPreparationError("mcp_servers must be a list of strings")
        servers.update(node_servers)
        initial = node.get("initial_scenario")
        final = node.get("final_scenario")
        if not isinstance(initial, dict) or not set(node_servers).issubset(initial):
            raise DatasetPreparationError("trajectory has incomplete initial scenarios")
        if not isinstance(final, dict) or any(final.get(server) is None for server in node_servers):
            raise DatasetPreparationError("trajectory has incomplete final scenarios")
        steps = node["steps"]
        if len(steps) % 2:
            raise DatasetPreparationError("trajectory contains an incomplete input/output pair")
        if any(not isinstance(step, Mapping) for step in steps):
            raise DatasetPreparationError("trajectory steps must be objects")
        validate_steps(steps, node_index)
        for step_index, step in enumerate(steps):
            role = step.get("role")
            role_counts[str(role)] += 1
            if role == "tool_call":
                if step_index + 1 >= len(steps) or steps[step_index + 1].get("role") != "tool_response":
                    raise DatasetPreparationError("tool call has no immediately paired response")
                for call in step.get("content") or []:
                    if not isinstance(call, Mapping):
                        raise DatasetPreparationError("tool-call JSON value must be an object")
                    name = call.get("name")
                    arguments = call.get("arguments")
                    if name not in allowed_tools:
                        raise DatasetPreparationError(f"invalid tool name {name!r}")
                    if not isinstance(arguments, dict):
                        raise DatasetPreparationError(
                            f"tool-call arguments for {name!r} must be a JSON object"
                        )
                    try:
                        json.dumps(arguments, ensure_ascii=False, allow_nan=False)
                    except (TypeError, ValueError) as exc:
                        raise DatasetPreparationError(
                            f"malformed tool-call JSON arguments for {name!r}: {exc}"
                        ) from exc
                    tool_calls += 1
                    tool_counts[str(name)] += 1
            elif role == "tool_response":
                if step_index == 0 or steps[step_index - 1].get("role") != "tool_call":
                    raise DatasetPreparationError("tool response has no immediately paired call")
                content = step.get("content")
                if not isinstance(content, list) or any(not isinstance(item, str) for item in content):
                    raise DatasetPreparationError("tool_response content must be a list of strings")
            elif role in {"user", "assistant"} and not isinstance(step.get("content"), str):
                raise DatasetPreparationError(f"{role} content must be a string")
    if not servers:
        raw_servers = payload.get("mcp_servers") or []
        if isinstance(raw_servers, list):
            servers.update(item for item in raw_servers if isinstance(item, str))
    if tool_calls == 0:
        raise DatasetPreparationError("trajectory contains no tool calls")
    return tool_calls, tuple(sorted(servers)), role_counts, tool_counts


def deterministic_split(
    seeds: Sequence[int], *, train_ratio: float, split_seed: int
) -> tuple[set[int], set[int]]:
    """Split whole trajectories using a stable hash rank, never global RNG state."""
    unique = sorted(set(seeds))
    if len(unique) != len(seeds):
        raise DatasetPreparationError("trajectory seeds are not unique")
    ranked = sorted(
        unique,
        key=lambda seed: (
            hashlib.sha256(f"{split_seed}:{seed}".encode("ascii")).digest(),
            seed,
        ),
    )
    train_count = math.floor(len(ranked) * train_ratio)
    if len(ranked) >= 2:
        train_count = min(max(train_count, 1), len(ranked) - 1)
    train = set(ranked[:train_count])
    return train, set(ranked[train_count:])


def _sample_messages(sample: Mapping[str, Any]) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": str(sample["system"])}]
    history = sample.get("history") or []
    for pair in history:
        if not isinstance(pair, list) or len(pair) != 2:
            raise DatasetPreparationError("SFT history entries must be two-item lists")
        messages.extend(
            (
                {"role": "user", "content": str(pair[0])},
                {"role": "assistant", "content": str(pair[1])},
            )
        )
    prompt = str(sample["instruction"])
    if sample.get("input"):
        prompt += "\n" + str(sample["input"])
    messages.append({"role": "user", "content": prompt})
    messages.append({"role": "assistant", "content": str(sample["output"])})
    return messages


def count_sample_tokens(tokenizer: Any, sample: Mapping[str, Any]) -> int:
    """Apply the student chat template to the complete supervised sequence."""
    try:
        token_ids = tokenizer.apply_chat_template(
            _sample_messages(sample), tokenize=True, add_generation_prompt=False
        )
    except Exception as exc:
        raise DatasetPreparationError(f"student tokenizer chat template failed: {exc}") from exc
    if isinstance(token_ids, Mapping):
        token_ids = token_ids.get("input_ids")
    if hasattr(token_ids, "tolist"):
        token_ids = token_ids.tolist()
    if isinstance(token_ids, list) and token_ids and isinstance(token_ids[0], list):
        if len(token_ids) != 1:
            raise DatasetPreparationError("tokenizer returned an unexpected batch")
        token_ids = token_ids[0]
    if not isinstance(token_ids, list):
        raise DatasetPreparationError("tokenizer chat template did not return token IDs")
    return len(token_ids)


def _load_tokenizer(config: MiniConfig) -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise DatasetPreparationError(
            "transformers is required for exact dataset token counts; use the MoLab runtime "
            "environment from requirements-molab.txt"
        ) from exc
    kwargs: dict[str, Any] = {"use_fast": True, "trust_remote_code": False}
    if config.dataset.tokenizer_revision:
        kwargs["revision"] = config.dataset.tokenizer_revision
    try:
        tokenizer = AutoTokenizer.from_pretrained(config.dataset.tokenizer_model, **kwargs)
    except Exception as exc:
        raise DatasetPreparationError(
            f"cannot load student tokenizer {config.dataset.tokenizer_model!r}: {exc}"
        ) from exc
    if not getattr(tokenizer, "chat_template", None):
        raise DatasetPreparationError("student tokenizer does not define a chat template")
    return tokenizer


def _resolved_tokenizer_revision(config: MiniConfig, tokenizer: Any) -> str | None:
    init_kwargs = getattr(tokenizer, "init_kwargs", {})
    if isinstance(init_kwargs, dict):
        resolved = init_kwargs.get("_commit_hash") or init_kwargs.get("revision")
        if resolved:
            return str(resolved)
        for value in init_kwargs.values():
            if not isinstance(value, (str, os.PathLike)):
                continue
            parts = Path(value).parts
            try:
                snapshot_index = parts.index("snapshots")
            except ValueError:
                continue
            if snapshot_index + 1 < len(parts):
                candidate = parts[snapshot_index + 1]
                if re.fullmatch(r"[0-9a-fA-F]{7,64}", candidate):
                    return candidate.lower()
    return config.dataset.tokenizer_revision


def _percentiles(histogram: Mapping[int, int]) -> dict[str, int | None]:
    count = sum(histogram.values())
    if not count:
        return {name: None for name in ("min", "p50", "p90", "p95", "p99", "max")}
    ordered = sorted(histogram)

    def nearest(percent: float) -> int:
        target = max(1, math.ceil(percent * count))
        cumulative = 0
        for value in ordered:
            cumulative += histogram[value]
            if cumulative >= target:
                return value
        return ordered[-1]

    return {
        "min": ordered[0],
        "p50": nearest(0.50),
        "p90": nearest(0.90),
        "p95": nearest(0.95),
        "p99": nearest(0.99),
        "max": ordered[-1],
    }


def _source_run_hash(manifest: RunManifest, trajectories: Sequence[_TrajectoryInfo]) -> str:
    hasher = hashlib.sha256()
    stable_run = {
        "schema_version": manifest.schema_version,
        "run_id": manifest.run_id,
        "config_sha256": manifest.config_sha256,
        "graph_sha256": manifest.graph_sha256,
        "catalog_sha256": manifest.catalog_sha256,
        "teacher_model": manifest.teacher_model,
        "teacher_revision": manifest.teacher_revision,
        "target_trajectories": manifest.target_trajectories,
        "seeds": manifest.seeds,
    }
    hasher.update(
        json.dumps(stable_run, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    for item in trajectories:
        hasher.update(f"\n{item.seed}:".encode("ascii"))
        hasher.update(bytes.fromhex(_sha256_file(item.path)))
    return hasher.hexdigest()


def _inspection_report(records: Sequence[dict[str, Any]]) -> str:
    lines = [
        "# Deterministic dataset inspection samples",
        "",
        "Previews are whitespace-normalized and truncated; training data remains unchanged.",
        "",
    ]
    for index, record in enumerate(records, 1):
        lines.extend(
            (
                f"## {index}. seed {record['seed']} / sample {record['sample_index']} ({record['split']})",
                "",
                f"- Tokens: {record['tokens']}",
                f"- Servers: {', '.join(record['servers'])}",
                f"- Instruction: {record['instruction_preview']}",
                f"- Output: {record['output_preview']}",
                "",
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def _preview(value: Any, limit: int = 240) -> str:
    compact = " ".join(str(value).split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def prepare_dataset(
    config: MiniConfig,
    run_id: str,
    *,
    tokenizer: Any | None = None,
    catalog: CatalogReport | None = None,
) -> PreparedDataset:
    """Validate, split, tokenize, and atomically materialize one run's SFT data."""
    if not _RUN_ID.fullmatch(run_id):
        raise DatasetPreparationError("invalid run ID")
    run_root = (config.artifact_root / "runs" / run_id).resolve()
    if not run_root.is_relative_to((config.artifact_root / "runs").resolve()):
        raise DatasetPreparationError("run path escapes artifact root")
    manifest_path = run_root / "run_manifest.json"
    if not manifest_path.is_file():
        raise DatasetPreparationError(f"run manifest does not exist: {manifest_path}")
    manifest = RunManifest.load(manifest_path)
    if manifest.run_id != run_id:
        raise DatasetPreparationError("run manifest ID does not match requested run")

    catalog = catalog or validate_catalog(config)
    if manifest.catalog_sha256 != catalog.digest:
        raise DatasetPreparationError("run catalog hash does not match the audited mini catalog")
    schemas = _tool_schemas(catalog)
    allowed_tools = set(schemas)

    completed_dir = run_root / "trajectories" / "completed"
    if not completed_dir.is_dir():
        raise DatasetPreparationError(f"completed trajectory directory does not exist: {completed_dir}")
    paths: list[tuple[int, Path]] = []
    ignored_json_files: list[str] = []
    ignored_temporary_files: list[str] = []
    for path in completed_dir.iterdir():
        if not path.is_file():
            continue
        match = _SEED_FILE.fullmatch(path.name)
        if match:
            paths.append((int(match.group(1)), path))
        elif path.suffix == ".tmp" or ".tmp" in path.suffixes:
            ignored_temporary_files.append(path.name)
        elif path.suffix == ".json":
            ignored_json_files.append(path.name)
    paths.sort(key=lambda item: item[0])
    if not paths:
        raise DatasetPreparationError("run has no completed numeric-seed trajectories")
    if len({seed for seed, _ in paths}) != len(paths):
        raise DatasetPreparationError("completed trajectory filenames contain duplicate numeric seeds")

    run_seeds = set(manifest.seeds)
    unknown_seeds = [seed for seed, _ in paths if seed not in run_seeds]
    if unknown_seeds:
        raise DatasetPreparationError(f"completed trajectories contain seeds outside the run: {unknown_seeds}")

    source_infos: list[_TrajectoryInfo] = []
    trajectory_infos: list[_TrajectoryInfo] = []
    insufficient: list[dict[str, int]] = []
    role_distribution: Counter[str] = Counter()
    tool_distribution: Counter[str] = Counter()
    server_combinations: Counter[str] = Counter()
    for seed, path in paths:
        payload = _load_json_object(path)
        if payload.get("seed") != seed:
            raise DatasetPreparationError(f"trajectory filename/seed mismatch: {path.name}")
        try:
            calls, servers, roles, tools = _validate_conversion_values(payload, allowed_tools)
        except (ValueError, TypeError, KeyError) as exc:
            raise DatasetPreparationError(f"invalid completed trajectory {path.name}: {exc}") from exc
        if any(server not in config.catalog.servers for server in servers):
            raise DatasetPreparationError(f"trajectory {path.name} references a server outside the catalog")
        role_distribution.update(roles)
        tool_distribution.update(tools)
        server_combinations["+".join(servers)] += 1
        info = _TrajectoryInfo(seed, path, calls, servers)
        source_infos.append(info)
        if calls < config.dataset.minimum_tool_calls:
            insufficient.append({"seed": seed, "tool_calls": calls})
            continue
        trajectory_infos.append(info)
    if not trajectory_infos:
        raise DatasetPreparationError("no trajectory meets dataset.minimum_tool_calls")

    train_seeds, validation_seeds = deterministic_split(
        [item.seed for item in trajectory_infos],
        train_ratio=config.dataset.train_ratio,
        split_seed=config.dataset.split_seed,
    )
    if train_seeds.intersection(validation_seeds):
        raise DatasetPreparationError("internal error: train/validation trajectory leakage")

    tokenizer = tokenizer or _load_tokenizer(config)
    if not callable(getattr(tokenizer, "apply_chat_template", None)):
        raise DatasetPreparationError("tokenizer must provide apply_chat_template")
    resolved_tokenizer_revision = _resolved_tokenizer_revision(config, tokenizer)
    dataset_dir = run_root / "datasets"
    all_path = dataset_dir / "sft_all.json"
    train_path = dataset_dir / "sft_train.json"
    validation_path = dataset_dir / "sft_validation.json"
    dataset_manifest_path = dataset_dir / "dataset_manifest.json"
    inspection_path = dataset_dir / "inspection_report.md"

    sample_counts: Counter[str] = Counter()
    server_sample_distribution: Counter[str] = Counter()
    token_length_histogram: Counter[int] = Counter()
    over_cutoff: list[dict[str, int]] = []
    inspection_candidates: list[tuple[bytes, dict[str, Any]]] = []
    with ExitStack() as stack:
        all_writer = stack.enter_context(_AtomicJsonArrayWriter(all_path))
        train_writer = stack.enter_context(_AtomicJsonArrayWriter(train_path))
        validation_writer = stack.enter_context(_AtomicJsonArrayWriter(validation_path))
        for info in trajectory_infos:
            payload = _load_json_object(info.path)
            assistant_tools = [
                schema
                for name, schema in schemas.items()
                if name.partition("-")[0] in info.servers
            ]
            split = "train" if info.seed in train_seeds else "validation"
            split_writer = train_writer if split == "train" else validation_writer
            for sample_index, sample in enumerate(
                iter_sft_samples(payload, assistant_tools, enable_think=True)
            ):
                tokens = count_sample_tokens(tokenizer, sample)
                sample_counts["candidate"] += 1
                if tokens > config.dataset.maximum_sequence_tokens:
                    over_cutoff.append(
                        {"seed": info.seed, "sample_index": sample_index, "tokens": tokens}
                    )
                    continue
                all_writer.write(sample)
                split_writer.write(sample)
                sample_counts["retained"] += 1
                sample_counts[split] += 1
                token_length_histogram[tokens] += 1
                for server in info.servers:
                    server_sample_distribution[server] += 1
                inspection = {
                    "seed": info.seed,
                    "sample_index": sample_index,
                    "split": split,
                    "tokens": tokens,
                    "servers": list(info.servers),
                    "instruction_preview": _preview(sample["instruction"]),
                    "output_preview": _preview(sample["output"]),
                }
                rank = hashlib.sha256(
                    f"{config.dataset.split_seed}:{info.seed}:{sample_index}".encode("ascii")
                ).digest()
                inspection_candidates.append((rank, inspection))
                inspection_candidates.sort(key=lambda item: item[0])
                del inspection_candidates[20:]

    candidate_count = sample_counts["candidate"]
    retained_count = sample_counts["retained"]
    fit_rate = retained_count / candidate_count if candidate_count else 0.0
    yield_rate = len(paths) / len(manifest.seeds) if manifest.seeds else 0.0
    server_shares = {
        server: count / retained_count if retained_count else 0.0
        for server, count in sorted(server_sample_distribution.items())
    }
    imbalanced = {server: share for server, share in server_shares.items() if share > 0.35}
    gates = {
        "zero_invalid_tool_names": True,
        "zero_malformed_tool_call_json": True,
        "zero_seed_overlap": not bool(train_seeds.intersection(validation_seeds)),
        "fit_rate_at_least_95_percent": fit_rate >= 0.95,
        "generation_yield_at_least_80_percent": yield_rate >= 0.80,
        "server_share_at_most_35_percent_or_accepted": (
            not imbalanced or config.dataset.allow_server_imbalance
        ),
    }
    source_hash = _source_run_hash(manifest, source_infos)
    selected_inspection = [
        value for _, value in sorted(inspection_candidates, key=lambda item: item[0])[:20]
    ]
    dataset_manifest: dict[str, Any] = {
        "schema_version": 1,
        "source_run_id": run_id,
        "source_run_sha256": source_hash,
        "source": {
            "config_sha256": manifest.config_sha256,
            "graph_sha256": manifest.graph_sha256,
            "catalog_sha256": manifest.catalog_sha256,
            "target_trajectories": len(manifest.seeds),
            "completed_trajectory_files": len(paths),
        },
        "tokenizer": {
            "model": config.dataset.tokenizer_model,
            "requested_revision": config.dataset.tokenizer_revision,
            "resolved_revision": resolved_tokenizer_revision,
            "chat_template_sha256": _sha256_bytes(
                str(getattr(tokenizer, "chat_template", "")).encode("utf-8")
            ),
        },
        "split": {
            "algorithm": "sha256_rank_v1",
            "seed": config.dataset.split_seed,
            "train_ratio": config.dataset.train_ratio,
            "validation_ratio": config.dataset.validation_ratio,
            "train_seeds": sorted(train_seeds),
            "validation_seeds": sorted(validation_seeds),
        },
        "counts": {
            "source_trajectories": len(paths),
            "retained_trajectories": len(trajectory_infos),
            "train_trajectories": len(train_seeds),
            "validation_trajectories": len(validation_seeds),
            "candidate_samples": candidate_count,
            "retained_samples": retained_count,
            "train_samples": sample_counts["train"],
            "validation_samples": sample_counts["validation"],
            "over_cutoff_samples": len(over_cutoff),
            "failed_artifacts_excluded": len(list((run_root / "trajectories" / "failed").glob("*.json"))),
            "temporary_artifacts_excluded": len(ignored_temporary_files),
        },
        "exclusions": {
            "insufficient_tool_calls": insufficient,
            "over_cutoff": over_cutoff,
            "ignored_temporary_files": sorted(ignored_temporary_files),
            "ignored_non_numeric_json_files": sorted(ignored_json_files),
        },
        "distributions": {
            "roles": dict(sorted(role_distribution.items())),
            "tools": dict(sorted(tool_distribution.items())),
            "server_combinations": dict(sorted(server_combinations.items())),
            "server_sample_counts": dict(sorted(server_sample_distribution.items())),
            "server_sample_shares": server_shares,
            "token_lengths": _percentiles(token_length_histogram),
        },
        "quality": {
            "generation_yield": yield_rate,
            "pre_cutoff_fit_rate": fit_rate,
            "maximum_sequence_tokens": config.dataset.maximum_sequence_tokens,
            "minimum_tool_calls": config.dataset.minimum_tool_calls,
            "imbalanced_servers": imbalanced,
            "server_imbalance_accepted": bool(
                imbalanced and config.dataset.allow_server_imbalance
            ),
        },
        "gates": gates,
        "files": {
            "sft_all.json": _sha256_file(all_path),
            "sft_train.json": _sha256_file(train_path),
            "sft_validation.json": _sha256_file(validation_path),
        },
        "inspection_samples": selected_inspection,
    }
    atomic_write_json(dataset_manifest_path, dataset_manifest)
    atomic_write_text(inspection_path, _inspection_report(selected_inspection))

    failed_gates = [name for name, passed in gates.items() if not passed]
    if failed_gates:
        raise DatasetGateError(
            "dataset gates failed (diagnostics were written): " + ", ".join(failed_gates)
        )
    manifest.dataset_counts = {
        "trajectories": len(trajectory_infos),
        "all": retained_count,
        "train": sample_counts["train"],
        "validation": sample_counts["validation"],
        "excluded_over_cutoff": len(over_cutoff),
    }
    manifest.student_model = config.dataset.tokenizer_model
    manifest.student_revision = resolved_tokenizer_revision
    manifest.checkpoint(manifest_path)
    # A successful conversion is the only supported source for training
    # profiles. Import locally to keep conversion helpers independently usable.
    from .training import render_training_profile

    training_profile = render_training_profile(config, run_id, profile="full")
    return PreparedDataset(
        manifest_path=dataset_manifest_path,
        all_path=all_path,
        train_path=train_path,
        validation_path=validation_path,
        inspection_path=inspection_path,
        dataset_info_path=training_profile.dataset_info_path,
        training_profile_path=training_profile.yaml_path,
        manifest=dataset_manifest,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare deterministic MoLab mini SFT data")
    parser.add_argument("--config", required=True, help="Mini pipeline TOML path")
    parser.add_argument("--run-id", required=True, help="Synthesis run identifier")
    parser.add_argument("--repo-root", help="Explicit EnvFactory repository root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        config = load_config(args.config, repo_root=args.repo_root)
        result = prepare_dataset(config, args.run_id)
    except (
        CatalogValidationError,
        DatasetPreparationError,
        MiniConfigError,
        ValueError,
    ) as exc:
        print(f"dataset preparation failed: {exc}", file=os.sys.stderr)
        return 1
    counts = result.manifest["counts"]
    print(
        f"dataset {args.run_id}: train={counts['train_samples']}, "
        f"validation={counts['validation_samples']}, "
        f"excluded_over_cutoff={counts['over_cutoff_samples']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DatasetGateError",
    "DatasetPreparationError",
    "PreparedDataset",
    "count_sample_tokens",
    "deterministic_split",
    "main",
    "prepare_dataset",
]
