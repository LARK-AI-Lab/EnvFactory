from __future__ import annotations

import ast
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_supported_python_runtime() -> None:
    assert sys.version_info >= (3, 12)


def test_package_declares_supported_python_runtime() -> None:
    setup_tree = ast.parse((REPOSITORY_ROOT / "setup.py").read_text(encoding="utf-8"))
    setup_calls = [
        node
        for node in ast.walk(setup_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setup"
    ]

    assert len(setup_calls) == 1
    python_requires = next(
        keyword.value
        for keyword in setup_calls[0].keywords
        if keyword.arg == "python_requires"
    )
    assert isinstance(python_requires, ast.Constant)
    assert python_requires.value == ">=3.12"
