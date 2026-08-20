from __future__ import annotations

from pathlib import Path

import pytest

from src.mini.config import MiniConfigError, discover_repo_root, load_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"


def _modified_config(tmp_path: Path, old: str, new: str) -> Path:
    contents = CONFIG_PATH.read_text(encoding="utf-8")
    assert old in contents
    path = tmp_path / "pipeline.toml"
    path.write_text(contents.replace(old, new, 1), encoding="utf-8")
    return path


def test_load_config_is_strict_typed_and_repository_relative(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config("configs/mini/pipeline.toml", repo_root=REPOSITORY_ROOT)

    assert config.repo_root == REPOSITORY_ROOT
    assert config.config_path == CONFIG_PATH
    assert config.schema_version == 1
    assert config.generation.workers == 4
    assert config.dataset.train_ratio == pytest.approx(0.9)
    assert config.artifact_root == REPOSITORY_ROOT / "artifacts" / "mini"
    assert config.catalog.mcp_config == REPOSITORY_ROOT / "configs" / "mini" / "mcp_server.json"
    assert config.graph.embedding_cache == REPOSITORY_ROOT / "artifacts" / "mini" / "cache" / "embeddings.sqlite3"


def test_unknown_keys_fail_fast(tmp_path: Path) -> None:
    path = _modified_config(
        tmp_path,
        'base_url = "http://127.0.0.1:8000/v1"',
        'base_url = "http://127.0.0.1:8000/v1"\nunknown_setting = true',
    )
    with pytest.raises(MiniConfigError, match="unknown_setting"):
        load_config(path, repo_root=REPOSITORY_ROOT)


def test_duplicate_catalog_servers_are_rejected(tmp_path: Path) -> None:
    path = _modified_config(
        tmp_path,
        '"MovieRecommender", "Retail", "Telecom", "Weather"',
        '"MovieRecommender", "Retail", "Telecom", "Calculator"',
    )
    with pytest.raises(MiniConfigError, match="duplicates.*Calculator"):
        load_config(path, repo_root=REPOSITORY_ROOT)


def test_only_deployment_fields_allow_environment_expansion(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MINI_TEST_MODEL", "changed-model")
    path = _modified_config(
        tmp_path,
        'model = "Qwen/Qwen3-14B"',
        'model = "${MINI_TEST_MODEL}"',
    )
    with pytest.raises(MiniConfigError, match="structural field 'teacher.model'"):
        load_config(path, repo_root=REPOSITORY_ROOT)


def test_allowed_deployment_environment_override(tmp_path: Path, monkeypatch) -> None:
    artifact_root = tmp_path / "shared-artifacts"
    monkeypatch.setenv("ENVFACTORY_MINI_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("ENVFACTORY_MINI_TEACHER_BASE_URL", "http://127.0.0.1:8123/v1")
    monkeypatch.setenv("ENVFACTORY_MINI_EMBEDDING_DEVICE", "cuda:0")
    config = load_config(CONFIG_PATH)
    assert config.artifact_root == artifact_root
    assert config.graph.path == artifact_root / "graph" / "graph.pkl"
    assert config.graph.manifest_path == artifact_root / "graph" / "manifest.json"
    assert config.graph.embedding_cache == artifact_root / "cache" / "embeddings.sqlite3"
    assert config.graph.user_provided_cache == artifact_root / "cache" / "user_provided.sqlite3"
    assert config.teacher.base_url == "http://127.0.0.1:8123/v1"
    assert config.graph.embedding_device == "cuda:0"


def test_repository_root_discovery_and_override_validation(tmp_path: Path) -> None:
    assert discover_repo_root() == REPOSITORY_ROOT
    with pytest.raises(MiniConfigError, match="not an EnvFactory repository root"):
        discover_repo_root(tmp_path)


def test_teacher_endpoint_must_remain_loopback(tmp_path: Path) -> None:
    path = _modified_config(
        tmp_path,
        'base_url = "http://127.0.0.1:8000/v1"',
        'base_url = "https://models.example.test:8000/v1"',
    )
    with pytest.raises(MiniConfigError, match="loopback"):
        load_config(path, repo_root=REPOSITORY_ROOT)
