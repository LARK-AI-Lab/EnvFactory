import unittest

from src.rewards.tool_reward import compute_score
from src.tools.tool_parser import get_tool_parser

REFERENCE = [
    {"name": "Calendar-search_events", "arguments": {"query": "sync", "max_results": 10}, "masked_arguments": ["max_results"]},
    {"name": "Calendar-delete_event", "arguments": {"event_id": "e1"}},
    {"name": "Calendar-delete_event", "arguments": {"event_id": "e1"}},
]


class ToolRewardTest(unittest.TestCase):
    def score(self, calls, failed=0, state=None):
        return compute_score(calls, failed, state or {}, REFERENCE, {"Calendar": {"events": {}}}, tau=0.5)

    def test_masked_arguments_and_repeated_reference_calls(self):
        calls = [
            {"name": "Calendar-delete_event", "arguments": {"event_id": "e1"}},
            {"name": "Calendar-search_events", "arguments": {"query": "sync"}},
            {"name": "Calendar-delete_event", "arguments": {"event_id": "e1"}},
        ]
        self.assertEqual(self.score(calls, state={"Calendar": {"events": {}}})["score"], 1.0)
        # Each reference call needs its own solution call.
        self.assertEqual(self.score(calls[:2])["trace_score"], 0.0)

    def test_penalties_and_state_component(self):
        calls = [
            {"name": "Calendar-search_events", "arguments": {"query": "sync"}},
            {"name": "Calendar-delete_event", "arguments": {"event_id": "e1"}},
            {"name": "Calendar-delete_event", "arguments": {"event_id": "e1"}},
            {"name": "Calendar-list_events", "arguments": {}},
        ]
        result = self.score(calls, failed=2, state={"Calendar": {"events": {"e2": {}}}})
        self.assertEqual(result["state_score"], 0.0)
        self.assertAlmostEqual(result["penalty"], 0.15)
        self.assertAlmostEqual(result["score"], 0.35)


class ToolParserTest(unittest.TestCase):
    def test_malformed_block_keeps_its_position_and_reasoning_is_ignored(self):
        text = (
            '<think>maybe <tool_call>{"name": "X-y", "arguments": {}}</tool_call></think>\n\n'
            '<tool_call>\n{bad}\n</tool_call>\n'
            '<tool_call>\n{"name": "Calendar-list_events", "arguments": {"max_results": 2}}\n</tool_call>'
        )
        calls = get_tool_parser("qwen3").extract_tool_calls(text)
        self.assertEqual(len(calls), 2)
        self.assertIsNotNone(calls[0].error)
        self.assertEqual((calls[1].name, calls[1].arguments, calls[1].error), ("Calendar-list_events", {"max_results": 2}, None))

    def test_xml_values_follow_the_schema_types(self):
        tools = [{"type": "function", "function": {"name": "Calendar-list_events", "parameters": {"properties": {
            "max_results": {"anyOf": [{"type": "integer"}, {"type": "null"}]}, "calendar_id": {"type": "string"},
        }}}}]
        text = (
            "<tool_call>\n<function=Calendar-list_events>\n<parameter=max_results>\n5\n</parameter>\n"
            "<parameter=calendar_id>\n007\n</parameter>\n</function>\n</tool_call>"
        )
        [call] = get_tool_parser("qwen3_coder").extract_tool_calls(text, tools)
        self.assertEqual(call.arguments, {"max_results": 5, "calendar_id": "007"})


if __name__ == "__main__":
    unittest.main()
