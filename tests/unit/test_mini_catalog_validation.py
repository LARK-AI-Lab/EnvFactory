from __future__ import annotations

from pathlib import Path

import pytest

from src.mini.catalog import (
    CatalogValidationError,
    _load_json,
    _metadata_tool_names,
    _repo_file,
    _validate_no_http_client_imports,
)


def test_duplicate_json_server_names_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"mcpServers":{"Same":{},"Same":{}}}', encoding="utf-8")
    with pytest.raises(CatalogValidationError, match="duplicate JSON key: Same"):
        _load_json(path)


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ({"class_name": "Wrong", "tools": [{"name": "ok"}]}, "class_name mismatch"),
        ({"class_name": "Expected", "tools": []}, "empty tool list"),
        (
            {"class_name": "Expected", "tools": [{"name": "same"}, {"name": "same"}]},
            "duplicate tools",
        ),
    ],
)
def test_invalid_metadata_is_rejected(metadata: dict, message: str) -> None:
    with pytest.raises(CatalogValidationError, match=message):
        _metadata_tool_names(metadata, "Expected")


def test_http_client_import_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "Unsafe.py"
    path.write_text("import requests\n", encoding="utf-8")
    with pytest.raises(CatalogValidationError, match="requests"):
        _validate_no_http_client_imports(path)


def test_missing_and_escaping_repository_paths_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(CatalogValidationError, match="does not exist"):
        _repo_file(tmp_path, "missing.py", label="tool")
    with pytest.raises(CatalogValidationError, match="escapes repository root"):
        _repo_file(tmp_path, "../outside.py", label="tool")
