import unittest

from src.tools.tool_manager import ToolManager

TICKET_STATE = {
    "users": {"alice": {"username": "alice", "password": "pw", "is_staff": False}},
    "current_time": "2025-01-01 00:00:00",
}
EVENT = {"summary": "Sync", "start_time": "2025-01-02T10:00:00", "end_time": "2025-01-02T11:00:00"}


class ToolManagerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = ToolManager("configs/mcp_server.json")

    def test_clients_of_one_environment_do_not_share_state(self):
        first = self.manager.create_client("Calendar", {})
        second = self.manager.create_client("Calendar", {})
        first.call_tool("create_event", EVENT)
        self.assertEqual(len(first.state()["events"]), len(second.state()["events"]) + 1)

    def test_module_globals_rebound_by_tools_stay_per_client(self):
        # TicketManagementSystem keeps its session token in a module-level `global`.
        first = self.manager.create_client("TicketManagementSystem", TICKET_STATE)
        second = self.manager.create_client("TicketManagementSystem", TICKET_STATE)
        first.call_tool("login", {"username": "alice", "password": "pw"})
        self.assertIn('"is_authenticated": true', first.call_tool("check_login_status", {}))
        self.assertIn('"is_authenticated": false', second.call_tool("check_login_status", {}))

    def test_arguments_are_validated_like_fastmcp(self):
        client = self.manager.create_client("Calendar", {})
        self.assertIn('"event_id"', client.call_tool("list_events", {"max_results": "1"}))
        error = client.call_tool("create_event", {"summary": "x"})
        self.assertTrue(error.startswith("Calendar-create_event failed: Error executing tool create_event:"), error)

    def test_scenario_tools_are_hidden_from_the_policy(self):
        names = {schema["function"]["name"] for schema in self.manager.filter_tools(["Calendar"])}
        self.assertIn("Calendar-create_event", names)
        self.assertFalse(names & {"Calendar-load_scenario", "Calendar-save_scenario"})
        client = self.manager.create_client("Calendar", {})
        self.assertEqual(client.call_tool("load_scenario", {"scenario": {}}), "Unknown tool 'Calendar-load_scenario'.")

    def test_replaying_calls_reproduces_state_without_reusing_ids(self):
        # The reward compares final states, so generated ids must not depend on randomness.
        def run(initial):
            client = self.manager.create_client("TickTick", initial)
            client.call_tool("ticktick_create_project", {"name": "Q4"})
            return client.state()

        first = run({})
        self.assertEqual(first, run({}))
        # A later turn starts from the earlier final state; its new project must get a fresh id.
        second = run(first)
        self.assertEqual(len(second["projects"]), 2)
        self.assertLessEqual(first["projects"].keys(), second["projects"].keys())


if __name__ == "__main__":
    unittest.main()
