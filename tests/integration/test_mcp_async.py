"""Phase 2 integration tests for the non-blocking MCP API."""

import asyncio
import json
from pathlib import Path

import pytest

from src.manager.mcp_client_manager import MCPManager


ROOT = Path(__file__).resolve().parents[2]
CALCULATOR = ROOT / "envs" / "tools" / "Calculator.py"
SLOW_MCP = ROOT / "tests" / "fixtures" / "SlowMCP.py"


@pytest.fixture(scope="module", autouse=True)
def registered_phase2_servers():
    MCPManager.register_mcp_server("Calculator", str(CALCULATOR))
    MCPManager.register_mcp_server("SlowMCP", str(SLOW_MCP))
    yield
    MCPManager.close_all_clients()


@pytest.mark.integration
def test_slow_mcp_call_does_not_block_callers_event_loop():
    async def exercise():
        client_id = "SlowMCP-ticker"
        ticks = 0
        done = asyncio.Event()

        async def ticker():
            nonlocal ticks
            while not done.is_set():
                ticks += 1
                await asyncio.sleep(0.01)

        ticker_task = asyncio.create_task(ticker())
        try:
            result = await MCPManager.acall_tool(
                client_id, "SlowMCP-slow", {"delay_seconds": 0.3}
            )
        finally:
            done.set()
            await ticker_task
            await MCPManager.aclose_client(client_id)

        assert json.loads(result)["slept"] == pytest.approx(0.3)
        assert ticks >= 10

    asyncio.run(exercise())


@pytest.mark.integration
def test_four_calculator_sessions_are_isolated():
    async def assert_isolation():
        client_ids = [f"Calculator-four-{index}" for index in range(4)]
        try:
            await MCPManager.aload_scenarios(
                {
                    client_id: {
                        "history": [{"expression": str(index), "result": index}]
                    }
                    for index, client_id in enumerate(client_ids)
                }
            )
            await asyncio.gather(
                *(
                    MCPManager.acall_tool(
                        client_id,
                        "Calculator-calculate",
                        {"expression": f"{index} + 10"},
                    )
                    for index, client_id in enumerate(client_ids)
                )
            )
            raw = await asyncio.gather(
                *(
                    MCPManager.acall_tool(client_id, "save_scenario", {})
                    for client_id in client_ids
                )
            )
            histories = [json.loads(value)["history"] for value in raw]
            for index, history in enumerate(histories):
                assert history == [
                    {"expression": str(index), "result": index},
                    {"expression": f"{index} + 10", "result": index + 10},
                ]
        finally:
            await asyncio.gather(
                *(MCPManager.aclose_client(client_id) for client_id in client_ids)
            )

    asyncio.run(assert_isolation())


@pytest.mark.integration
def test_timed_out_call_does_not_poison_next_session():
    async def exercise():
        original_timeout = MCPManager.tool_call_timeout
        timed_out_client = "SlowMCP-timeout"
        next_client = "SlowMCP-after-timeout"
        try:
            MCPManager.tool_call_timeout = 0.05
            result = await MCPManager.acall_tool(
                timed_out_client,
                "SlowMCP-slow",
                {"delay_seconds": 0.5},
            )
            assert "timed out" in result
            assert timed_out_client not in MCPManager.clients

            MCPManager.tool_call_timeout = 2
            assert await MCPManager.acall_tool(
                next_client, "SlowMCP-ping", {}
            ) == "pong"
        finally:
            MCPManager.tool_call_timeout = original_timeout
            await asyncio.gather(
                MCPManager.aclose_client(timed_out_client),
                MCPManager.aclose_client(next_client),
                return_exceptions=True,
            )

    asyncio.run(exercise())
