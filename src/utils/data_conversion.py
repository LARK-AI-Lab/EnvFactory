"""Reusable, side-effect-free trajectory-to-SFT conversion helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any

from src.utils.prompts import SYSTEM_PROMPT


INPUT_ROLES = frozenset({"user", "tool_response"})
OUTPUT_ROLES = frozenset({"assistant", "tool_call"})


def format_step(step: Mapping[str, Any]) -> str:
    """Format one EnvFactory trajectory step for the Alpaca fields."""
    role = step.get("role")
    content = step.get("content", "")
    if content is None:
        raise ValueError(f"got null content for role {role!r}")
    if role in {"user", "assistant"}:
        return str(content)
    if role == "tool_response":
        if not isinstance(content, list) or any(not isinstance(item, str) for item in content):
            raise ValueError("tool_response content must be a list of strings")
        return "".join(f"<tool_response>\n{item}\n</tool_response>\n" for item in content)
    if role == "tool_call":
        if not isinstance(content, list) or not content:
            raise ValueError("tool_call content must be a non-empty list")
        rendered: list[str] = []
        for call in content:
            if not isinstance(call, Mapping):
                raise ValueError("tool_call values must be objects")
            value = {"name": call.get("name"), "arguments": call.get("arguments")}
            rendered.append(
                "<tool_call>\n"
                + json.dumps(value)
                + "\n</tool_call>\n"
            )
        return "".join(rendered)
    raise ValueError(f"unknown trajectory role: {role!r}")


def validate_steps(steps: Sequence[Mapping[str, Any]], node_idx: int) -> None:
    """Validate the input/output alternation expected by the legacy converter."""
    for index, step in enumerate(steps):
        expected = INPUT_ROLES if index % 2 == 0 else OUTPUT_ROLES
        if step.get("role") not in expected:
            raise ValueError(
                f"Node {node_idx} Step {index}: expected {sorted(expected)}, "
                f"got {step.get('role')!r}"
            )


def is_failed_tool_call(steps: Sequence[Mapping[str, Any]], output_idx: int) -> bool:
    """Return whether a tool call's paired response contains a legacy failure marker."""
    current = steps[output_idx]
    if current.get("role") != "tool_call" or output_idx + 1 >= len(steps):
        return False
    response = steps[output_idx + 1]
    if response.get("role") != "tool_response":
        return False
    content = response.get("content", [])
    return isinstance(content, list) and any(
        isinstance(item, str) and ("Fail" in item or "Error" in item) for item in content
    )


def build_system_prompt(
    assistant_tools: Iterable[Mapping[str, Any]],
    user_tools: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    """Render the stable EnvFactory system prompt without consulting MCP globals."""
    user_tools = user_tools or []
    if user_tools:
        user_text = "- Here are the actions you may instruct the user to do:\n"
        user_text += "\n".join(
            f"{tool['name']}: {tool['description']}" for tool in user_tools
        )
    else:
        user_text = ""
    tools_text = "\n".join(
        json.dumps(tool)
        for tool in assistant_tools
    )
    return SYSTEM_PROMPT.replace("{user_tools}", user_text).replace("{tools}", tools_text)


def iter_sft_samples(
    chain: Mapping[str, Any],
    assistant_tools: Sequence[Mapping[str, Any]],
    *,
    enable_think: bool = True,
) -> Iterator[dict[str, Any]]:
    """Yield one Alpaca sample per retained input/output pair in a trajectory."""
    user_tools = chain.get("user_tools") or []
    user_names = {
        tool.get("name") for tool in user_tools if isinstance(tool, Mapping)
    }
    tools = [
        tool
        for tool in assistant_tools
        if tool.get("function", {}).get("name") not in user_names
    ]
    system = build_system_prompt(tools, user_tools)
    history: list[list[str]] = []

    for node_idx, node in enumerate(chain.get("nodes") or []):
        if not isinstance(node, Mapping):
            raise ValueError(f"node {node_idx} must be an object")
        if node.get("decision") is not True or not node.get("steps"):
            break
        steps = node["steps"]
        if not isinstance(steps, list):
            raise ValueError(f"node {node_idx} steps must be a list")
        validate_steps(steps, node_idx)
        if not any(step.get("role") == "tool_call" for step in steps):
            continue

        for index in range(0, len(steps) - 1, 2):
            input_step, output_step = steps[index], steps[index + 1]
            input_text = format_step(input_step)
            output_text = format_step(output_step)
            output_type = output_step.get("type", "KEEP")
            think = ""
            if enable_think and "think" in output_step:
                think = f"<think>{output_step.get('think', '')}</think>\n\n"
            if output_type == "KEEP" and not is_failed_tool_call(steps, index + 1):
                yield {
                    "instruction": input_text.strip(),
                    "input": "",
                    "output": think + output_text,
                    "system": system,
                    "history": [pair.copy() for pair in history],
                }
            history.append([input_text, output_text])


__all__ = [
    "INPUT_ROLES",
    "OUTPUT_ROLES",
    "build_system_prompt",
    "format_step",
    "is_failed_tool_call",
    "iter_sft_samples",
    "validate_steps",
]
