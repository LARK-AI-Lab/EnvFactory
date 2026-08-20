"""Run-scoped LlamaFactory LoRA profiles and checkpoint verification."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from .artifacts import atomic_write_json, atomic_write_text
from .config import MiniConfig, MiniConfigError, load_config


class TrainingProfileError(RuntimeError):
    """Raised when a training profile or output violates the mini contract."""


@dataclass(frozen=True)
class RenderedTrainingProfile:
    dataset_info_path: Path
    yaml_path: Path
    profile_manifest_path: Path
    output_dir: Path
    values: dict[str, Any]


_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_CHECKPOINT = re.compile(r"checkpoint-([0-9]+)\Z")
_PLACEHOLDER = re.compile(r"__RUN_[A-Z0-9_]+__")
_SECRET_NAME = re.compile(r"(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)
_TEXT_OUTPUT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".yaml", ".yml"}
_ADAPTER_FILES = (
    "adapter_config.json",
    "adapter_model.safetensors",
    "adapter_model.bin",
    "README.md",
)
_RESUME_FILES = ("trainer_state.json", "optimizer.pt", "scheduler.pt", "adapter_config.json")


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _run_root(config: MiniConfig, run_id: str) -> Path:
    if not _RUN_ID.fullmatch(run_id):
        raise TrainingProfileError("invalid run ID")
    runs_root = (config.artifact_root / "runs").resolve()
    run_root = (runs_root / run_id).resolve()
    if not run_root.is_relative_to(runs_root):
        raise TrainingProfileError("run path escapes artifact root")
    return run_root


def _confined_path(path: str | Path, root: Path, *, label: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise TrainingProfileError(f"{label} must be beneath the run directory")
    return resolved


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TrainingProfileError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TrainingProfileError(f"{label} must be a JSON object: {path}")
    return value


def _validate_dataset(config: MiniConfig, run_root: Path, run_id: str) -> tuple[Path, dict[str, Any]]:
    dataset_dir = run_root / "datasets"
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest = _load_json_object(manifest_path, label="dataset manifest")
    if manifest.get("source_run_id") != run_id:
        raise TrainingProfileError("dataset manifest belongs to a different run")
    gates = manifest.get("gates")
    if not isinstance(gates, dict) or not gates or not all(value is True for value in gates.values()):
        raise TrainingProfileError("all dataset release gates must pass before rendering training")
    tokenizer = manifest.get("tokenizer")
    if not isinstance(tokenizer, dict) or tokenizer.get("model") != config.dataset.tokenizer_model:
        raise TrainingProfileError("dataset tokenizer model does not match the configured student")
    quality = manifest.get("quality")
    if not isinstance(quality, dict) or quality.get("maximum_sequence_tokens") != config.dataset.maximum_sequence_tokens:
        raise TrainingProfileError("dataset cutoff does not match the configured student cutoff")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise TrainingProfileError("dataset manifest has no file hashes")
    for name in ("sft_train.json", "sft_validation.json"):
        path = dataset_dir / name
        expected = files.get(name)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise TrainingProfileError(f"dataset manifest has no valid hash for {name}")
        if not path.is_file() or _sha256_file(path) != expected:
            raise TrainingProfileError(f"dataset file hash mismatch: {name}")
    return dataset_dir, manifest


def dataset_info() -> dict[str, Any]:
    """Return the two local Alpaca dataset entries used by LlamaFactory."""
    columns = {
        "prompt": "instruction",
        "query": "input",
        "response": "output",
        "history": "history",
        "system": "system",
    }
    return {
        "env_factory_mini_train": {
            "file_name": "sft_train.json",
            "formatting": "alpaca",
            "columns": dict(columns),
        },
        "env_factory_mini_validation": {
            "file_name": "sft_validation.json",
            "formatting": "alpaca",
            "columns": dict(columns),
        },
    }


def _load_template(config: MiniConfig) -> tuple[Path, dict[str, Any]]:
    path = config.repo_root / "configs" / "mini" / "llamafactory_sft.yaml"
    try:
        values = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise TrainingProfileError(f"cannot load LlamaFactory template {path}: {exc}") from exc
    if not isinstance(values, dict):
        raise TrainingProfileError("LlamaFactory template must be a YAML mapping")
    return path, values


def _latest_checkpoint(output_dir: Path) -> tuple[Path, int] | None:
    candidates: list[tuple[int, Path]] = []
    if output_dir.is_dir():
        for path in output_dir.iterdir():
            match = _CHECKPOINT.fullmatch(path.name)
            if match and path.is_dir():
                candidates.append((int(match.group(1)), path.resolve()))
    if not candidates:
        return None
    step, path = max(candidates)
    return path, step


def _validate_resume_checkpoint(checkpoint: Path) -> None:
    missing = [name for name in _RESUME_FILES if not (checkpoint / name).is_file()]
    has_adapter = any((checkpoint / name).is_file() for name in _ADAPTER_FILES if name.startswith("adapter_model."))
    if not has_adapter:
        missing.append("adapter_model.safetensors|adapter_model.bin")
    if missing:
        raise TrainingProfileError(
            "checkpoint is incomplete for trainer resume: " + ", ".join(missing)
        )


def render_training_profile(
    config: MiniConfig,
    run_id: str,
    *,
    profile: str = "full",
    per_device_batch_size: int = 2,
    resume_from_checkpoint: str | Path | None = None,
) -> RenderedTrainingProfile:
    """Render one trusted run-specific LlamaFactory YAML without starting training."""
    if profile not in {"full", "smoke", "memory-probe", "resume-check"}:
        raise TrainingProfileError(f"unsupported training profile: {profile}")
    if per_device_batch_size not in {1, 2}:
        raise TrainingProfileError("per-device batch size must be 1 or 2")
    run_root = _run_root(config, run_id)
    dataset_dir, data_manifest = _validate_dataset(config, run_root, run_id)
    template_path, values = _load_template(config)
    training_dir = run_root / "training"
    output_names = {
        "full": "checkpoints",
        "smoke": "smoke",
        "memory-probe": f"memory-probe-batch-{per_device_batch_size}",
        "resume-check": "smoke",
    }
    output_dir = training_dir / output_names[profile]
    tensorboard_dir = training_dir / "tensorboard" / profile

    values.update(
        {
            "model_name_or_path": config.dataset.tokenizer_model,
            "model_revision": config.dataset.tokenizer_revision or "main",
            "dataset_dir": dataset_dir.as_posix(),
            "output_dir": output_dir.as_posix(),
            "logging_dir": tensorboard_dir.as_posix(),
            "cutoff_len": config.dataset.maximum_sequence_tokens,
            "per_device_train_batch_size": per_device_batch_size,
            "gradient_accumulation_steps": 16 // per_device_batch_size,
            "seed": config.run_seed,
            "data_seed": config.dataset.split_seed,
        }
    )
    if profile == "smoke":
        values.update(
            {
                "model_name_or_path": "Qwen/Qwen3-4B",
                "model_revision": "main",
                "max_steps": 20,
                "save_steps": 10,
                "eval_strategy": "steps",
                "eval_steps": 10,
            }
        )
    elif profile == "memory-probe":
        values.update(
            {
                "max_steps": 1,
                "save_steps": 1,
                "do_eval": False,
                "eval_strategy": "no",
                "report_to": "none",
            }
        )
        values.pop("eval_steps", None)
    elif profile == "resume-check":
        values.update(
            {
                "model_name_or_path": "Qwen/Qwen3-4B",
                "model_revision": "main",
                "save_steps": 1,
                "eval_strategy": "steps",
                "eval_steps": 1,
            }
        )

    if resume_from_checkpoint is not None:
        checkpoint = _confined_path(resume_from_checkpoint, output_dir, label="resume checkpoint")
        match = _CHECKPOINT.fullmatch(checkpoint.name)
        if not match or not checkpoint.is_dir():
            raise TrainingProfileError("resume checkpoint is not a trusted checkpoint-N directory")
        _validate_resume_checkpoint(checkpoint)
        step = int(match.group(1))
        values["resume_from_checkpoint"] = checkpoint.as_posix()
        if profile == "resume-check":
            values["max_steps"] = step + 1
    elif profile == "resume-check":
        latest = _latest_checkpoint(output_dir)
        if latest is None:
            raise TrainingProfileError("resume-check requires an existing smoke checkpoint")
        _validate_resume_checkpoint(latest[0])
        values["resume_from_checkpoint"] = latest[0].as_posix()
        values["max_steps"] = latest[1] + 1
    else:
        values["resume_from_checkpoint"] = None

    if values["gradient_accumulation_steps"] * values["per_device_train_batch_size"] != 16:
        raise TrainingProfileError("training profile does not produce effective batch size 16")
    rendered = yaml.safe_dump(values, sort_keys=False, allow_unicode=True)
    unresolved = sorted(set(_PLACEHOLDER.findall(rendered)))
    if unresolved:
        raise TrainingProfileError(f"unresolved training path placeholders: {', '.join(unresolved)}")
    for key in ("dataset_dir", "output_dir", "logging_dir"):
        _confined_path(values[key], run_root, label=key)

    dataset_info_path = dataset_dir / "dataset_info.json"
    yaml_names = {
        "full": "resolved_llamafactory.yaml",
        "smoke": "resolved_llamafactory_smoke.yaml",
        "memory-probe": f"resolved_llamafactory_memory_probe_batch_{per_device_batch_size}.yaml",
        "resume-check": "resolved_llamafactory_resume_check.yaml",
    }
    yaml_path = training_dir / yaml_names[profile]
    manifest_names = {
        "full": "profile_manifest.json",
        "smoke": "profile_manifest_smoke.json",
        "memory-probe": f"profile_manifest_memory_probe_batch_{per_device_batch_size}.json",
        "resume-check": "profile_manifest_resume_check.json",
    }
    arguments_names = {
        "full": "resolved_training_arguments.json",
        "smoke": "resolved_training_arguments_smoke.json",
        "memory-probe": f"resolved_training_arguments_memory_probe_batch_{per_device_batch_size}.json",
        "resume-check": "resolved_training_arguments_resume_check.json",
    }
    profile_manifest_path = training_dir / manifest_names[profile]
    arguments_path = training_dir / arguments_names[profile]
    atomic_write_json(dataset_info_path, dataset_info())
    atomic_write_text(yaml_path, rendered)
    atomic_write_json(arguments_path, values)
    profile_manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "profile": profile,
        "template": template_path.relative_to(config.repo_root).as_posix(),
        "template_sha256": _sha256_file(template_path),
        "dataset_manifest_sha256": _sha256_file(dataset_dir / "dataset_manifest.json"),
        "dataset_source_run_sha256": data_manifest.get("source_run_sha256"),
        "dataset_info_sha256": _sha256_file(dataset_info_path),
        "resolved_yaml": yaml_path.name,
        "resolved_yaml_sha256": _sha256_file(yaml_path),
        "resolved_arguments": arguments_path.name,
        "resolved_arguments_sha256": _sha256_file(arguments_path),
        "output_dir": output_dir.as_posix(),
        "effective_batch_size": 16,
        "resume_from_checkpoint": values.get("resume_from_checkpoint"),
    }
    atomic_write_json(profile_manifest_path, profile_manifest)
    return RenderedTrainingProfile(
        dataset_info_path=dataset_info_path,
        yaml_path=yaml_path,
        profile_manifest_path=profile_manifest_path,
        output_dir=output_dir,
        values=values,
    )


def _finite_losses(trainer_state: Mapping[str, Any]) -> list[float]:
    losses: list[float] = []
    history = trainer_state.get("log_history")
    if not isinstance(history, list):
        return losses
    for record in history:
        if not isinstance(record, Mapping):
            continue
        for key in ("loss", "eval_loss", "train_loss"):
            value = record.get(key)
            if isinstance(value, (int, float)):
                number = float(value)
                if not math.isfinite(number):
                    raise TrainingProfileError(f"trainer state contains non-finite {key}")
                losses.append(number)
    return losses


def _scan_for_current_secrets(root: Path) -> None:
    secrets = {
        value
        for name, value in os.environ.items()
        if _SECRET_NAME.search(name) and len(value) >= 8
    }
    if not secrets or not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _TEXT_OUTPUT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if any(secret in content for secret in secrets):
            raise TrainingProfileError(f"current environment secret found in training output: {path}")


def _copy_adapter_files(output_dir: Path, adapter_dir: Path) -> list[str]:
    names = [name for name in _ADAPTER_FILES if (output_dir / name).is_file()]
    if "adapter_config.json" not in names or not any(name.startswith("adapter_model.") for name in names):
        raise TrainingProfileError("training output has no complete LoRA adapter")
    adapter_config = _load_json_object(output_dir / "adapter_config.json", label="adapter config")
    if str(adapter_config.get("peft_type", "")).upper() != "LORA":
        raise TrainingProfileError("adapter config does not identify a LoRA adapter")
    adapter_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in names:
        source = output_dir / name
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{name}.", suffix=".tmp", dir=adapter_dir
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, adapter_dir / name)
        finally:
            temporary.unlink(missing_ok=True)
        copied.append(name)
    return copied


def _version_report() -> dict[str, Any]:
    packages = {}
    for name in ("llamafactory", "torch", "transformers", "peft", "trl", "accelerate"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    cuda_version = None
    try:
        import torch

        cuda_version = torch.version.cuda
    except ImportError:
        pass
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
        "cuda_version": cuda_version,
    }


def verify_training_output(
    config: MiniConfig,
    run_id: str,
    *,
    output_dir: str | Path,
    minimum_step: int = 1,
    previous_step: int | None = None,
    promote_adapter: bool = False,
) -> dict[str, Any]:
    """Verify finite losses, checkpoint progress, adapter integrity, and secret hygiene."""
    run_root = _run_root(config, run_id)
    resolved_output = _confined_path(output_dir, run_root / "training", label="training output")
    latest = _latest_checkpoint(resolved_output)
    if latest is None:
        raise TrainingProfileError("training output has no checkpoint-N directory")
    checkpoint, directory_step = latest
    _validate_resume_checkpoint(checkpoint)
    state = _load_json_object(checkpoint / "trainer_state.json", label="trainer state")
    global_step = state.get("global_step")
    if not isinstance(global_step, int) or global_step < minimum_step:
        raise TrainingProfileError(f"trainer global step has not reached {minimum_step}")
    if global_step != directory_step:
        raise TrainingProfileError("checkpoint directory and trainer global step disagree")
    if previous_step is not None and global_step <= previous_step:
        raise TrainingProfileError("resumed training did not advance beyond the saved step")
    losses = _finite_losses(state)
    if not losses:
        raise TrainingProfileError("trainer state contains no finite loss values")
    _scan_for_current_secrets(run_root / "training")
    copied: list[str] = []
    if promote_adapter:
        copied = _copy_adapter_files(resolved_output, run_root / "training" / "adapter")
    summary = {
        "schema_version": 1,
        "run_id": run_id,
        "output_dir": resolved_output.as_posix(),
        "latest_checkpoint": checkpoint.as_posix(),
        "global_step": global_step,
        "finite_loss_records": len(losses),
        "minimum_loss": min(losses),
        "maximum_loss": max(losses),
        "resume_advanced": previous_step is None or global_step > previous_step,
        "adapter_files": copied,
        "dataset_manifest_sha256": _sha256_file(run_root / "datasets" / "dataset_manifest.json"),
    }
    training_root = run_root / "training"
    dataset_manifest = _load_json_object(
        run_root / "datasets" / "dataset_manifest.json", label="dataset manifest"
    )
    tokenizer_metadata = dataset_manifest.get("tokenizer")
    if not isinstance(tokenizer_metadata, dict):
        raise TrainingProfileError("dataset manifest has no tokenizer metadata")
    atomic_write_json(training_root / "tokenizer_metadata.json", tokenizer_metadata)
    atomic_write_json(training_root / "version_report.json", _version_report())
    atomic_write_json(training_root / "training_summary.json", summary)
    run_manifest_path = run_root / "run_manifest.json"
    if run_manifest_path.is_file():
        from .manifest import RunManifest

        run_manifest = RunManifest.load(run_manifest_path)
        run_manifest.training_summary = summary
        run_manifest.checkpoint(run_manifest_path)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render or verify mini LoRA training artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser("render", help="Render a run-specific LlamaFactory YAML")
    render.add_argument("--config", required=True)
    render.add_argument("--run-id", required=True)
    render.add_argument(
        "--profile", choices=("full", "smoke", "memory-probe", "resume-check"), default="full"
    )
    render.add_argument("--per-device-batch-size", type=int, choices=(1, 2), default=2)
    render.add_argument("--resume-from-checkpoint")
    render.add_argument("--repo-root")
    verify = subparsers.add_parser("verify", help="Verify checkpoint, loss, and adapter artifacts")
    verify.add_argument("--config", required=True)
    verify.add_argument("--run-id", required=True)
    verify.add_argument("--output-dir", required=True)
    verify.add_argument("--minimum-step", type=int, default=1)
    verify.add_argument("--previous-step", type=int)
    verify.add_argument("--promote-adapter", action="store_true")
    verify.add_argument("--repo-root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        config = load_config(args.config, repo_root=args.repo_root)
        if args.command == "render":
            result = render_training_profile(
                config,
                args.run_id,
                profile=args.profile,
                per_device_batch_size=args.per_device_batch_size,
                resume_from_checkpoint=args.resume_from_checkpoint,
            )
            print(f"training profile: {result.yaml_path}")
        else:
            summary = verify_training_output(
                config,
                args.run_id,
                output_dir=args.output_dir,
                minimum_step=args.minimum_step,
                previous_step=args.previous_step,
                promote_adapter=args.promote_adapter,
            )
            print(
                f"training verified: step={summary['global_step']}, "
                f"finite_losses={summary['finite_loss_records']}"
            )
    except (MiniConfigError, TrainingProfileError, ValueError) as exc:
        print(f"training profile failed: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "RenderedTrainingProfile",
    "TrainingProfileError",
    "dataset_info",
    "render_training_profile",
    "verify_training_output",
]
