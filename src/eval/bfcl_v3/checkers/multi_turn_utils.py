"""BFCL multi-turn execution utils with isolated per-grading state."""

from __future__ import annotations

import ast
import copy
import importlib
import inspect
import json
from typing import Any

from src.eval.bfcl_v3.checkers.executable_backend_config import (
    CLASS_FILE_PATH_MAPPING,
    STATELESS_CLASSES,
)


def execute_multi_turn_func_call(
    func_call_list: list[str],
    initial_config: dict,
    involved_classes: list[str],
    registry: dict[str, Any],
    long_context: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    """Execute python call strings against backend instances in registry."""
    class_method_name_mapping: dict[str, str] = {}
    involved_instances: dict[str, Any] = {}
    for class_name in involved_classes:
        if class_name not in registry:
            class_ = getattr(importlib.import_module(CLASS_FILE_PATH_MAPPING[class_name]), class_name)
            instance = class_()
            if class_name not in STATELESS_CLASSES:
                instance._load_scenario(copy.deepcopy(initial_config.get(class_name, {})), long_context=long_context)
            registry[class_name] = instance
        involved_instances[class_name] = registry[class_name]
        for method_name, _ in inspect.getmembers(registry[class_name], predicate=inspect.ismethod):
            if not method_name.startswith("_"):
                class_method_name_mapping[method_name] = class_name

    execution_results = []
    for func_call in func_call_list:
        try:
            class_name, method_name, args, kwargs = _parse_method_call(func_call, class_method_name_mapping)
            result = getattr(registry[class_name], method_name)(*args, **kwargs)
            if isinstance(result, dict):
                # Some functions return values json cannot encode (e.g. mpmath's mpf).
                try:
                    result = json.dumps(result)
                except (TypeError, ValueError):
                    result = str(result)
            elif not isinstance(result, str):
                result = str(result)
            execution_results.append(result)
        except Exception as e:
            execution_results.append(f"Error during execution: {str(e)}")
    return execution_results, involved_instances


def is_empty_execute_response(input_list: list) -> bool:
    return len(input_list) == 0 or (len(input_list) == 1 and len(input_list[0]) == 0)


def _parse_method_call(
    function_call_string: str,
    method_to_class: dict[str, str],
) -> tuple[str, str, list[Any], dict[str, Any]]:
    """Parse one BFCL call without executing model-provided Python code."""
    expression = ast.parse(function_call_string, mode="eval").body
    if not isinstance(expression, ast.Call):
        raise ValueError("Expected a function call")

    qualified_class = None
    if isinstance(expression.func, ast.Name):
        method_name = expression.func.id
    elif isinstance(expression.func, ast.Attribute) and isinstance(expression.func.value, ast.Name):
        qualified_class = expression.func.value.id
        method_name = expression.func.attr
    else:
        raise ValueError("Only direct environment method calls are allowed")

    class_name = method_to_class.get(method_name)
    if class_name is None:
        raise NameError(f"name '{method_name}' is not defined")  # Upstream's eval() error text.
    if qualified_class is not None and qualified_class != class_name:
        raise ValueError(f"Function '{method_name}' does not belong to '{qualified_class}'")

    args = [ast.literal_eval(arg) for arg in expression.args]
    kwargs = {}
    for keyword in expression.keywords:
        if keyword.arg is None:
            raise ValueError("Expanded keyword arguments are not allowed")
        kwargs[keyword.arg] = ast.literal_eval(keyword.value)
    return class_name, method_name, args, kwargs
