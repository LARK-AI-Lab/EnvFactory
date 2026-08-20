from __future__ import annotations

from pathlib import Path

import pytest

from src.mini.build_graph import dry_run, main
from src.mini.config import load_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs" / "mini" / "pipeline.toml"


@pytest.mark.integration
def test_graph_dry_run_validates_all_inputs_without_writing(capsys) -> None:
    config = load_config(CONFIG_PATH)
    graph_existed = config.graph.path.exists()
    manifest_existed = config.graph.manifest_path.exists()

    report, unmet = dry_run(config)
    assert report.server_count == 8
    assert report.metadata_tool_count == 55
    assert unmet == [
        "teacher classification endpoint "
        "(Qwen/Qwen3-14B at http://127.0.0.1:8000/v1)"
    ]
    assert config.graph.path.exists() is graph_existed
    assert config.graph.manifest_path.exists() is manifest_existed

    assert main(["--config", str(CONFIG_PATH), "--dry-run"]) == 0
    output = capsys.readouterr()
    assert "graph dry run passed: 8 servers, 55 tools" in output.out
    assert "unmet live dependencies: teacher classification endpoint" in output.out
    assert output.err == ""
