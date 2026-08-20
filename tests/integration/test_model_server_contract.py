from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.mini.config import load_config
from src.mini.doctor import check_model_health


pytestmark = [pytest.mark.integration, pytest.mark.model]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_live_model_server_contract() -> None:
    if os.environ.get("RUN_MINI_MODEL_TESTS") != "1":
        pytest.skip("set RUN_MINI_MODEL_TESTS=1 with the configured local vLLM server running")
    config = load_config(REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml")
    health = check_model_health(config, timeout=30)
    assert health["healthy"] is True
    assert health["configured_max_model_len"] == 16384
