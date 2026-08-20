"""Strict, repository-relative configuration for the MoLab mini pipeline."""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator


class MiniConfigError(ValueError):
    """Raised when mini configuration cannot be loaded safely."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CatalogConfig(_StrictModel):
    mcp_config: Path
    metadata_dir: Path
    servers: list[str]

    @field_validator("servers")
    @classmethod
    def validate_servers(cls, servers: list[str]) -> list[str]:
        if not servers:
            raise ValueError("catalog.servers must not be empty")
        if any(not server.strip() for server in servers):
            raise ValueError("catalog.servers contains an empty server name")
        duplicates = sorted({server for server in servers if servers.count(server) > 1})
        if duplicates:
            raise ValueError(f"catalog.servers contains duplicates: {', '.join(duplicates)}")
        return servers


class GraphConfig(_StrictModel):
    path: Path
    manifest_path: Path
    embedding_backend: Literal["sentence_transformers", "http"]
    embedding_model: str
    embedding_device: str
    embedding_batch_size: int = Field(gt=0)
    embedding_cache: Path
    enable_parameter_merge: bool
    enable_llm_edges: bool
    classify_user_provided: bool
    user_provided_classifier: Literal["teacher"]
    user_provided_cache: Path


class TeacherConfig(_StrictModel):
    provider: str
    model: str
    fallback_model: str
    base_url: str
    api_key_env: str
    max_model_len: int = Field(gt=0)
    gpu_memory_utilization: float = Field(gt=0, le=1)
    max_num_seqs: int = Field(gt=0)

    @field_validator("provider", "model", "fallback_model", "base_url", "api_key_env")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("teacher string settings must not be empty")
        return value

    @field_validator("api_key_env")
    @classmethod
    def validate_api_key_environment_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("teacher.api_key_env must be an environment-variable name, not a secret")
        return value

    @field_validator("base_url")
    @classmethod
    def validate_loopback_endpoint(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ValueError("teacher.base_url must use an HTTP(S) loopback address")
        if parsed.username or parsed.password or not parsed.port:
            raise ValueError("teacher.base_url must contain a port and no credentials")
        if parsed.path.rstrip("/") != "/v1" or parsed.query or parsed.fragment:
            raise ValueError("teacher.base_url must end at the /v1 API root")
        return value.rstrip("/")


class GenerationConfig(_StrictModel):
    mode: Literal["sft_non_conv"]
    target_trajectories: int = Field(gt=0)
    workers: int = Field(gt=0, le=4)
    pass_k: int = Field(gt=0)
    max_nodes: int = Field(gt=0)
    max_servers: int = Field(gt=0)
    max_iterations: int = Field(gt=0)
    max_solve_iterations: int = Field(gt=0)
    max_attempts_per_seed: int = Field(gt=0)
    enable_query_refinement: bool
    enable_user_interaction: bool
    enable_user_tool_use: bool
    enable_filteration: bool
    manifest_flush_every: int = Field(gt=0)


class DatasetConfig(_StrictModel):
    train_ratio: float = Field(gt=0, lt=1)
    validation_ratio: float = Field(gt=0, lt=1)
    split_seed: int
    minimum_tool_calls: int = Field(ge=1)
    maximum_sequence_tokens: int = Field(gt=0)
    tokenizer_model: str = "Qwen/Qwen3-8B"
    tokenizer_revision: str | None = None
    allow_server_imbalance: bool = False

    @field_validator("tokenizer_model")
    @classmethod
    def validate_tokenizer_model(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("dataset.tokenizer_model must not be empty")
        return value

    @field_validator("tokenizer_revision")
    @classmethod
    def validate_tokenizer_revision(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("dataset.tokenizer_revision must be null or non-empty")
        return value

    @model_validator(mode="after")
    def validate_ratios(self) -> "DatasetConfig":
        if abs(self.train_ratio + self.validation_ratio - 1.0) > 1e-9:
            raise ValueError("dataset train_ratio and validation_ratio must sum to 1")
        return self


class EvaluationConfig(_StrictModel):
    held_out_trajectories: int = Field(gt=0)
    workers: int = Field(gt=0, le=4)
    max_turns: int = Field(gt=0)
    temperature: float = Field(default=0.0, ge=0, le=2)
    top_p: float = Field(default=1.0, gt=0, le=1)
    presence_penalty: float = Field(default=0.0, ge=-2, le=2)
    max_tokens: int = Field(default=2048, gt=0)
    seed: int = 42
    request_timeout_seconds: float = Field(default=120.0, gt=0)
    bootstrap_samples: int = Field(default=2000, ge=0)
    bootstrap_confidence: float = Field(default=0.95, gt=0, lt=1)
    enable_thinking: bool = False


class MiniConfig(_StrictModel):
    schema_version: Literal[1]
    run_seed: int
    artifact_root: Path
    catalog: CatalogConfig
    graph: GraphConfig
    teacher: TeacherConfig
    generation: GenerationConfig
    dataset: DatasetConfig
    evaluation: EvaluationConfig

    _repo_root: Path = PrivateAttr()
    _config_path: Path = PrivateAttr()

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    @property
    def config_path(self) -> Path:
        return self._config_path


_PATH_FIELDS = {
    ("artifact_root",),
    ("catalog", "mcp_config"),
    ("catalog", "metadata_dir"),
    ("graph", "path"),
    ("graph", "manifest_path"),
    ("graph", "embedding_cache"),
    ("graph", "user_provided_cache"),
}
_ARTIFACT_PATH_FIELDS = {
    ("graph", "path"),
    ("graph", "manifest_path"),
    ("graph", "embedding_cache"),
    ("graph", "user_provided_cache"),
}

# Only machine/deployment values may be injected. Experiment structure remains
# in the checked-in TOML and secrets remain indirect through api_key_env.
_DEPLOYMENT_OVERRIDES = {
    "ENVFACTORY_MINI_ARTIFACT_ROOT": ("artifact_root",),
    "ENVFACTORY_MINI_EMBEDDING_DEVICE": ("graph", "embedding_device"),
    "ENVFACTORY_MINI_TEACHER_BASE_URL": ("teacher", "base_url"),
    "ENVFACTORY_MINI_TEACHER_API_KEY_ENV": ("teacher", "api_key_env"),
}
_EXPANDABLE_FIELDS = set(_DEPLOYMENT_OVERRIDES.values())
_ENV_REFERENCE = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|\{[^}]+\})|%[^%]+%")


def discover_repo_root(repo_root: str | Path | None = None) -> Path:
    """Find the repository from this package, or validate an explicit override."""
    candidate = Path(repo_root).expanduser() if repo_root is not None else Path(__file__).resolve().parents[2]
    candidate = candidate.resolve()
    if not (candidate / "src" / "mini").is_dir() or not (candidate / "setup.py").is_file():
        raise MiniConfigError(f"not an EnvFactory repository root: {candidate}")
    return candidate


def _get_nested(values: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = values
    for component in path:
        if not isinstance(current, dict) or component not in current:
            return None
        current = current[component]
    return current


def _set_nested(values: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    current = values
    for component in path[:-1]:
        nested = current.get(component)
        if not isinstance(nested, dict):
            return
        current = nested
    if path[-1] in current:
        current[path[-1]] = value


def _walk_strings(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_strings(child, (*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, (*path, str(index)))
    elif isinstance(value, str):
        yield path, value


def _apply_environment(values: dict[str, Any]) -> None:
    for variable, path in _DEPLOYMENT_OVERRIDES.items():
        override = os.environ.get(variable)
        if override is not None:
            _set_nested(values, path, override)

    for path, value in list(_walk_strings(values)):
        if not _ENV_REFERENCE.search(value):
            continue
        if path not in _EXPANDABLE_FIELDS:
            dotted = ".".join(path)
            raise MiniConfigError(f"environment expansion is not allowed for structural field '{dotted}'")
        expanded = os.path.expandvars(value)
        if _ENV_REFERENCE.search(expanded):
            raise MiniConfigError(f"unresolved environment reference in {'.'.join(path)}")
        _set_nested(values, path, expanded)


def _rebase_artifact_paths(values: dict[str, Any], declared_artifact_root: object) -> None:
    """Keep configured graph outputs beneath a deployment artifact-root override."""
    if "ENVFACTORY_MINI_ARTIFACT_ROOT" not in os.environ:
        return
    if not isinstance(declared_artifact_root, str):
        return
    resolved_artifact_root = _get_nested(values, ("artifact_root",))
    if not isinstance(resolved_artifact_root, str):
        return
    old_root = Path(declared_artifact_root)
    new_root = Path(resolved_artifact_root)
    for path in _ARTIFACT_PATH_FIELDS:
        raw_value = _get_nested(values, path)
        if not isinstance(raw_value, str):
            continue
        try:
            relative = Path(raw_value).relative_to(old_root)
        except ValueError as exc:
            dotted = ".".join(path)
            raise MiniConfigError(
                f"cannot rebase {dotted}; configured path is outside artifact_root"
            ) from exc
        _set_nested(values, path, str(new_root / relative))


def _resolve_paths(values: dict[str, Any], repo_root: Path) -> None:
    for path in _PATH_FIELDS:
        raw_value = _get_nested(values, path)
        if not isinstance(raw_value, str):
            continue
        candidate = Path(raw_value).expanduser()
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        _set_nested(values, path, candidate.resolve())


def load_config(config_path: str | Path, *, repo_root: str | Path | None = None) -> MiniConfig:
    """Load a strict mini TOML config with all relative paths rooted at the repo."""
    root = discover_repo_root(repo_root)
    path = Path(config_path).expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_file():
        raise MiniConfigError(f"mini configuration file does not exist: {path}")

    try:
        with path.open("rb") as handle:
            values = tomllib.load(handle)
        declared_artifact_root = values.get("artifact_root")
        _apply_environment(values)
        _rebase_artifact_paths(values, declared_artifact_root)
        _resolve_paths(values, root)
        config = MiniConfig.model_validate(values)
    except MiniConfigError:
        raise
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        raise MiniConfigError(f"invalid mini configuration {path}: {exc}") from exc

    config._repo_root = root
    config._config_path = path
    return config


__all__ = [
    "CatalogConfig",
    "DatasetConfig",
    "EvaluationConfig",
    "GenerationConfig",
    "GraphConfig",
    "MiniConfig",
    "MiniConfigError",
    "TeacherConfig",
    "discover_repo_root",
    "load_config",
]
