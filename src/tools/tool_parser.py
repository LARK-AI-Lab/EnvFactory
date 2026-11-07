"""Tool-call parsers for policy output.

A block that cannot be parsed stays in the call list as a ``ToolCall`` with ``error``
set, so its observation keeps its position among the batch's tool responses and the
reward can count it as a format failure.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict = field(default_factory=dict)
    error: str | None = None


def _action_text(text: str) -> str:
    """Drop the reasoning block; tool calls only count in the visible answer."""
    return text.split("</think>", 1)[-1]


class Qwen3ToolParser:
    """Hermes JSON calls used by Qwen3 and the EnvFactory SFT data.

    ``<tool_call>{"name": "Calendar-list_events", "arguments": {"max_results": 5}}</tool_call>``
    """

    tool_call_regex = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)

    def extract_tool_calls(self, text: str, tools: list[dict] | None = None) -> list[ToolCall]:
        calls = []
        for block in self.tool_call_regex.findall(_action_text(text)):
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


class Qwen3CoderToolParser:
    """XML calls used by Qwen3.5 / Qwen3-Coder; values are typed through the tool schemas.

    ``<tool_call><function=Calendar-list_events><parameter=max_results>5</parameter></function></tool_call>``
    """

    tool_call_regex = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
    function_regex = re.compile(r"<function=(.*?)</function>|<function=(.*)$", re.DOTALL)
    parameter_regex = re.compile(r"<parameter=(.*?)(?:</parameter>|(?=<parameter=)|(?=</function>)|$)", re.DOTALL)
    string_types = frozenset({"string", "str", "text", "varchar", "char", "enum"})

    @classmethod
    def _schema_type(cls, schema: dict):
        """A property's ``type``, or the member types of a pydantic ``anyOf`` (e.g. Optional[int])."""
        if schema.get("type") is not None:
            return schema["type"]
        types = []
        for member in schema.get("anyOf") or schema.get("oneOf") or []:
            member_type = member.get("type") if isinstance(member, dict) else None
            types.extend(member_type if isinstance(member_type, list) else [member_type] if member_type else [])
        return types or None

    @classmethod
    def _coerce(cls, value: str, schema_type):
        if value.lower() == "null":
            return None
        if isinstance(schema_type, (list, tuple)):
            for member in (s for s in schema_type if str(s).lower() != "null"):
                coerced = cls._coerce(value, member)
                if str(member).lower() in cls.string_types or not isinstance(coerced, str):
                    return coerced
            return value
        kind = str(schema_type or "").strip().lower()
        if kind in cls.string_types:
            return value
        if kind.startswith("int"):
            try:
                return int(value)
            except ValueError:
                return value
        if kind.startswith(("num", "float")):
            try:
                number = float(value)
                return int(number) if number.is_integer() else number
            except ValueError:
                return value
        if kind in ("boolean", "bool"):
            return value.strip().lower() == "true"
        try:
            return json.loads(value)
        except ValueError:
            pass
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    def extract_tool_calls(self, text: str, tools: list[dict] | None = None) -> list[ToolCall]:
        param_types = {}
        for tool in tools or []:
            fn = tool.get("function", tool)
            properties = (fn.get("parameters") or {}).get("properties") or {}
            param_types[fn.get("name")] = {key: self._schema_type(value) for key, value in properties.items()}

        calls = []
        for block in self.tool_call_regex.findall(_action_text(text)):
            functions = [g1 or g2 for g1, g2 in self.function_regex.findall(block.strip())]
            if not functions:
                calls.append(ToolCall(name="", error=f"Invalid tool call format: missing <function=...>. Raw content: {block.strip()}"))
            for function in functions:
                if ">" not in function:
                    calls.append(ToolCall(name="", error=f"Invalid tool call format: unterminated function name. Raw content: {block.strip()}"))
                    continue
                name, body = function.split(">", 1)
                name = name.strip()
                schema = param_types.get(name, {})
                arguments = {}
                for match in self.parameter_regex.findall(body):
                    if ">" not in match:
                        continue
                    key, value = match.split(">", 1)
                    value = value.removeprefix("\n").removesuffix("\n")
                    arguments[key.strip()] = self._coerce(value, schema.get(key.strip()))
                calls.append(ToolCall(name=name, arguments=arguments))
        return calls


TOOL_PARSERS = {
    "qwen3": Qwen3ToolParser,
    "hermes": Qwen3ToolParser,
    "qwen3_coder": Qwen3CoderToolParser,
}


def get_tool_parser(name: str):
    if name not in TOOL_PARSERS:
        raise ValueError(f"Unknown tool format '{name}'. Available: {sorted(TOOL_PARSERS)}.")
    return TOOL_PARSERS[name]()
