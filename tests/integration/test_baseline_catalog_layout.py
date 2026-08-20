from __future__ import annotations

from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MINI_SERVERS = (
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
@pytest.mark.parametrize("server", MINI_SERVERS)
def test_mini_server_sources_and_metadata_exist(server: str) -> None:
    assert (REPOSITORY_ROOT / "envs" / "tools" / f"{server}.py").is_file()
    assert (REPOSITORY_ROOT / "envs" / "metadata" / f"{server}_metadata.json").is_file()
