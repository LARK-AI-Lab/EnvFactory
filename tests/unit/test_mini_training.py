from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from src.mini.config import load_config
from src.mini.training import (
    TrainingProfileError,
    render_training_profile,
    verify_training_output,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _training_fixture(tmp_path: Path):
    config = load_config(
        REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml",
        repo_root=REPOSITORY_ROOT,
    ).model_copy(update={"artifact_root": (tmp_path / "artifacts" / "mini").resolve()})
    run_id = "phase8-test"
    dataset_dir = config.artifact_root / "runs" / run_id / "datasets"
    dataset_dir.mkdir(parents=True)
    train_path = dataset_dir / "sft_train.json"
    validation_path = dataset_dir / "sft_validation.json"
    train_path.write_text('[{"instruction":"train","input":"","output":"ok"}]\n')
    validation_path.write_text(
        '[{"instruction":"validation","input":"","output":"ok"}]\n'
    )
    manifest = {
        "schema_version": 1,
        "source_run_id": run_id,
        "source_run_sha256": "a" * 64,
        "tokenizer": {"model": config.dataset.tokenizer_model},
        "quality": {"maximum_sequence_tokens": config.dataset.maximum_sequence_tokens},
        "gates": {
            "zero_seed_overlap": True,
            "fit_rate_at_least_95_percent": True,
        },
        "files": {
            train_path.name: _hash(train_path),
            validation_path.name: _hash(validation_path),
        },
    }
    (dataset_dir / "dataset_manifest.json").write_text(json.dumps(manifest))
    return config, run_id


def test_shared_template_has_phase8_lora_semantics() -> None:
    values = yaml.safe_load(
        (REPOSITORY_ROOT / "configs" / "mini" / "llamafactory_sft.yaml").read_text()
    )
    assert values["finetuning_type"] == "lora"
    assert values["lora_target"] == "all"
    assert values["cutoff_len"] == 8192
    assert values["overwrite_cache"] is False
    assert values["preprocessing_num_workers"] == 3
    assert values["dataloader_num_workers"] == 2
    assert values["bf16"] is True
    assert values["gradient_checkpointing"] is True
    assert values["overwrite_output_dir"] is False
    assert values["save_only_model"] is False
    assert values["report_to"] == "tensorboard"
    assert values["per_device_train_batch_size"] * values["gradient_accumulation_steps"] == 16


def test_render_full_profile_is_run_scoped_and_writes_dataset_registry(tmp_path: Path) -> None:
    config, run_id = _training_fixture(tmp_path)
    result = render_training_profile(config, run_id)

    values = yaml.safe_load(result.yaml_path.read_text())
    run_root = (config.artifact_root / "runs" / run_id).resolve()
    assert result.output_dir == run_root / "training" / "checkpoints"
    assert Path(values["dataset_dir"]).resolve() == run_root / "datasets"
    assert Path(values["output_dir"]).resolve() == result.output_dir
    assert Path(values["logging_dir"]).resolve().is_relative_to(run_root)
    assert values["dataset"] == "env_factory_mini_train"
    assert values["eval_dataset"] == "env_factory_mini_validation"
    assert values["resume_from_checkpoint"] is None
    assert values["overwrite_output_dir"] is False
    assert values["report_to"] == "tensorboard"
    assert values["per_device_train_batch_size"] == 2
    assert values["gradient_accumulation_steps"] == 8
    assert "__RUN_" not in result.yaml_path.read_text()

    registry = json.loads(result.dataset_info_path.read_text())
    assert set(registry) == {
        "env_factory_mini_train",
        "env_factory_mini_validation",
    }
    assert registry["env_factory_mini_train"]["file_name"] == "sft_train.json"
    assert registry["env_factory_mini_validation"]["file_name"] == "sft_validation.json"
    assert registry["env_factory_mini_train"]["formatting"] == "alpaca"


def test_smoke_memory_probe_and_resume_profiles_encode_bounded_jobs(tmp_path: Path) -> None:
    config, run_id = _training_fixture(tmp_path)
    smoke = render_training_profile(config, run_id, profile="smoke", per_device_batch_size=1)
    assert smoke.values["model_name_or_path"] == "Qwen/Qwen3-4B"
    assert smoke.values["max_steps"] == 20
    assert smoke.values["save_steps"] == 10
    assert smoke.values["gradient_accumulation_steps"] == 16

    probe = render_training_profile(config, run_id, profile="memory-probe")
    assert probe.values["model_name_or_path"] == "Qwen/Qwen3-8B"
    assert probe.values["max_steps"] == 1
    assert probe.values["per_device_train_batch_size"] == 2
    assert probe.values["report_to"] == "none"

    checkpoint = smoke.output_dir / "checkpoint-20"
    checkpoint.mkdir(parents=True)
    (checkpoint / "trainer_state.json").write_text('{"global_step":20}')
    (checkpoint / "optimizer.pt").write_bytes(b"optimizer")
    (checkpoint / "scheduler.pt").write_bytes(b"scheduler")
    (checkpoint / "adapter_config.json").write_text('{"peft_type":"LORA"}')
    (checkpoint / "adapter_model.safetensors").write_bytes(b"adapter")
    resume = render_training_profile(config, run_id, profile="resume-check")
    assert resume.values["resume_from_checkpoint"] == checkpoint.as_posix()
    assert resume.values["max_steps"] == 21
    assert resume.values["overwrite_output_dir"] is False


def test_render_rejects_dataset_tampering_and_untrusted_resume_path(tmp_path: Path) -> None:
    config, run_id = _training_fixture(tmp_path)
    dataset_dir = config.artifact_root / "runs" / run_id / "datasets"
    (dataset_dir / "sft_train.json").write_text("[]")
    with pytest.raises(TrainingProfileError, match="hash mismatch"):
        render_training_profile(config, run_id)

    config, run_id = _training_fixture(tmp_path / "second")
    outside = tmp_path / "checkpoint-10"
    outside.mkdir()
    (outside / "trainer_state.json").write_text('{"global_step":10}')
    with pytest.raises(TrainingProfileError, match="beneath the run directory"):
        render_training_profile(
            config,
            run_id,
            profile="resume-check",
            resume_from_checkpoint=outside,
        )


def test_verify_training_output_checks_loss_resume_and_promotes_adapter(tmp_path: Path) -> None:
    config, run_id = _training_fixture(tmp_path)
    rendered = render_training_profile(config, run_id)
    checkpoint = rendered.output_dir / "checkpoint-20"
    checkpoint.mkdir(parents=True)
    (checkpoint / "trainer_state.json").write_text(
        json.dumps({"global_step": 20, "log_history": [{"loss": 1.25}, {"eval_loss": 1.1}]})
    )
    (checkpoint / "optimizer.pt").write_bytes(b"optimizer")
    (checkpoint / "scheduler.pt").write_bytes(b"scheduler")
    (checkpoint / "adapter_config.json").write_text('{"peft_type":"LORA"}')
    (checkpoint / "adapter_model.safetensors").write_bytes(b"adapter")
    (rendered.output_dir / "adapter_config.json").write_text('{"peft_type":"LORA"}')
    (rendered.output_dir / "adapter_model.safetensors").write_bytes(b"adapter")

    summary = verify_training_output(
        config,
        run_id,
        output_dir=rendered.output_dir,
        minimum_step=20,
        previous_step=19,
        promote_adapter=True,
    )
    assert summary["global_step"] == 20
    assert summary["finite_loss_records"] == 2
    assert summary["resume_advanced"] is True
    adapter_dir = config.artifact_root / "runs" / run_id / "training" / "adapter"
    assert (adapter_dir / "adapter_config.json").is_file()
    assert (adapter_dir / "adapter_model.safetensors").read_bytes() == b"adapter"

    with pytest.raises(TrainingProfileError, match="did not advance"):
        verify_training_output(
            config,
            run_id,
            output_dir=rendered.output_dir,
            previous_step=20,
        )


def test_verify_rejects_nonfinite_loss_and_current_secret(tmp_path: Path, monkeypatch) -> None:
    config, run_id = _training_fixture(tmp_path)
    rendered = render_training_profile(config, run_id)
    checkpoint = rendered.output_dir / "checkpoint-1"
    checkpoint.mkdir(parents=True)
    state_path = checkpoint / "trainer_state.json"
    (checkpoint / "optimizer.pt").write_bytes(b"optimizer")
    (checkpoint / "scheduler.pt").write_bytes(b"scheduler")
    (checkpoint / "adapter_config.json").write_text('{"peft_type":"LORA"}')
    (checkpoint / "adapter_model.safetensors").write_bytes(b"adapter")
    state_path.write_text('{"global_step":1,"log_history":[{"loss":NaN}]}')
    with pytest.raises(TrainingProfileError, match="non-finite"):
        verify_training_output(config, run_id, output_dir=rendered.output_dir)

    state_path.write_text('{"global_step":1,"log_history":[{"loss":1.0}]}')
    secret = "phase8-secret-value"
    monkeypatch.setenv("PHASE8_API_TOKEN", secret)
    (rendered.output_dir / "trainer.log").write_text(f"accidental={secret}\n")
    with pytest.raises(TrainingProfileError, match="secret found"):
        verify_training_output(config, run_id, output_dir=rendered.output_dir)
