from __future__ import annotations

from pathlib import Path

import pytest

from src.mini.catalog import LIFECYCLE_TOOLS, main, validate_catalog
from src.mini.config import load_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"
EXPECTED_SERVERS = (
    "Calculator",
    "Calendar",
    "CampusCard",
    "HotelBooking",
    "MovieRecommender",
    "Retail",
    "Telecom",
    "Weather",
)


@pytest.mark.integration
def test_exact_mini_catalog_has_55_registered_metadata_tools() -> None:
    report = validate_catalog(load_config(CONFIG_PATH))

    assert tuple(server.name for server in report.servers) == EXPECTED_SERVERS
    assert report.server_count == 8
    assert report.metadata_tool_count == 55
    assert len(report.digest) == 64
    for server in report.servers:
        assert LIFECYCLE_TOOLS.issubset(server.registered_tool_names)
        assert set(server.metadata_tool_names) == set(server.registered_tool_names) - LIFECYCLE_TOOLS


@pytest.mark.integration
def test_catalog_digest_and_cli_are_deterministic(capsys) -> None:
    config = load_config(CONFIG_PATH)
    first = validate_catalog(config)
    second = validate_catalog(config)
    assert first.digest == second.digest

    exit_code = main(["--config", str(CONFIG_PATH), "--check"])
    output = capsys.readouterr()
    assert exit_code == 0
    assert "catalog check passed: 8 servers, 55 metadata tools" in output.out
    assert first.digest in output.out
    assert output.err == ""
