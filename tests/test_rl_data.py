import json
import tempfile
import unittest

from src.tools.tool_manager import ToolManager
from src.utils.data_process import _rl_row, rl_row_fingerprint, verify_rl_rows

CONFIG = "configs/mcp_server.json"
EVENT = {"summary": "Sync", "start_time": "2025-01-02T10:00:00", "end_time": "2025-01-02T11:00:00"}
CREATE = {"name": "Calendar-create_event", "arguments": EVENT}
FAILING = {"name": "Calendar-create_event", "arguments": {"summary": "x"}}  # Missing required times.


def row(calls, final_state):
    return _rl_row([{"role": "user", "content": "Add the sync."}], calls, ["Calendar"], {"Calendar": {}}, {"Calendar": final_state})


class VerifyRlRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = ToolManager(CONFIG).create_client("Calendar", {})
        cls.empty = client.state()
        client.call_tool("create_event", EVENT)
        cls.one_event = client.state()
        client.call_tool("create_event", {**EVENT, "summary": "Duplicate"})
        cls.two_events = client.state()

    def test_final_state_becomes_what_the_reference_calls_produce(self):
        # Synthesis stored a duplicate create that the filtered label no longer contains.
        [kept] = verify_rl_rows([row([CREATE], self.two_events)], CONFIG)
        self.assertEqual(kept["metadata"]["final_state"], {"Calendar": self.one_event})
        self.assertEqual(kept["metadata"]["initial_state"], {"Calendar": {}})

    def test_failed_reference_call_drops_the_row_only_when_the_stored_state_disagrees(self):
        # A failing lookup can be the right answer; a failing write that synthesis saw succeed cannot.
        self.assertEqual(len(verify_rl_rows([row([FAILING], self.empty)], CONFIG)), 1)
        self.assertEqual(verify_rl_rows([row([FAILING], self.one_event)], CONFIG), [])

    def test_listed_rows_are_dropped(self):
        listed = row([CREATE], self.one_event)
        with tempfile.NamedTemporaryFile("w", suffix=".json") as f:
            json.dump({"rows": [rl_row_fingerprint(listed)]}, f)
            f.flush()
            self.assertEqual(verify_rl_rows([listed, row([CREATE, CREATE], self.two_events)], CONFIG, f.name)[0]["label"],
                             json.dumps([CREATE, CREATE]))


if __name__ == "__main__":
    unittest.main()
