import ast
import importlib
import inspect
import json
import unittest
from types import SimpleNamespace

from src.eval.bfcl_v3.bfcl import BfclEnv, build_rows, grade
from src.eval.bfcl_v3.checkers.executable_backend_config import CLASS_FILE_PATH_MAPPING
from src.tools.tool_parser import ToolCall

ARGS = SimpleNamespace(eval_max_context_len=40960, eval_max_response_len=8192, rollout_max_response_len=8192)
PARAMS = {
    name: [p for p in inspect.signature(fn).parameters if p != "self"]
    for cls, module in CLASS_FILE_PATH_MAPPING.items()
    for name, fn in inspect.getmembers(getattr(importlib.import_module(module), cls), inspect.isfunction)
}


def as_tool_call(call: str) -> ToolCall:
    """A ground-truth call as the policy emits it: keyword arguments in JSON."""
    node = ast.parse(call, mode="eval").body
    arguments = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords}
    arguments.update(zip(PARAMS[node.func.id], (ast.literal_eval(arg) for arg in node.args)))
    return ToolCall(name=node.func.id, arguments=json.loads(json.dumps(arguments)))


class BfclTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = build_rows()

    def play(self, row, turns):
        metadata = json.loads(json.dumps(row["metadata"]))
        env = BfclEnv(ARGS, metadata)
        for i, calls in enumerate(turns):
            if i:
                self.assertIsNotNone(env.next_user_turn())
            env.call_tools(calls)
        metadata.update(env.result())
        return grade(metadata, row["label"])

    def test_reference_calls_pass_every_task(self):
        for row in self.rows:
            turns = [[as_tool_call(call) for call in turn] for turn in json.loads(row["label"])]
            self.assertEqual(self.play(row, turns), 1.0, row["metadata"]["bfcl_id"])

    def test_stopping_before_the_last_user_turn_fails(self):
        row = next(r for r in self.rows if len(json.loads(r["label"])) > 1)
        turns = [[as_tool_call(call) for call in turn] for turn in json.loads(row["label"])]
        self.assertEqual(self.play(row, turns[:-1]), 0.0)

    def test_held_out_functions_are_hidden_until_announced(self):
        row = next(r for r in self.rows if r["metadata"]["bfcl_category"] == "multi_turn_miss_func")
        advertised = {tool["function"]["name"] for tool in row["metadata"]["tools"]}
        announced = [turn[0]["content"] for turn in row["metadata"]["user_turns"] if "I have updated some more functions" in turn[0]["content"]]
        self.assertTrue(announced)
        self.assertFalse(any(f"'name': '{name}'" in announced[0] for name in advertised))


if __name__ == "__main__":
    unittest.main()
