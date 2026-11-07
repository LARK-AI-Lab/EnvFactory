"""Qwen3 (Hermes JSON) tool-call parsing for policy output, the format of the EnvFactory SFT data.

``<tool_call>{"name": "Calendar-list_events", "arguments": {"max_results": 5}}</tool_call>``

A block that cannot be parsed stays in the call list as a ``ToolCall`` with ``error``
set, so its observation keeps its position among the batch's tool responses and the
reward can count it as a format failure.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

TOOL_CALL_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)


@dataclass
class ToolCall:
    name: str
    arguments: dict = field(default_factory=dict)
    error: str | None = None


def extract_tool_calls(text: str) -> list[ToolCall]:
    """Calls in the visible answer; anything inside the reasoning block is ignored."""
    calls = []
    for block in TOOL_CALL_RE.findall(text.split("</think>", 1)[-1]):
        try:
            payload = json.loads(block)
            name, arguments = payload["name"], payload.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise ValueError("'name' must be a string and 'arguments' a JSON object")
            calls.append(ToolCall(name=name, arguments=arguments))
        except Exception as e:
            calls.append(ToolCall(name="", error=f"Invalid tool call format: {e}. Raw content: {block.strip()}"))
    return calls
