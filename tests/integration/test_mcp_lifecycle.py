"""Phase 2 stress tests for MCP client and child-process cleanup."""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest

from src.manager.mcp_client_manager import MCPManager


ROOT = Path(__file__).resolve().parents[2]
CALCULATOR = ROOT / "envs" / "tools" / "Calculator.py"


def _child_pids() -> set[int]:
    return {child.pid for child in psutil.Process().children(recursive=True)}


def _wait_for_child_baseline(baseline: set[int], timeout: float = 15) -> set[int]:
    deadline = time.monotonic() + timeout
    current = _child_pids()
    while not current.issubset(baseline) and time.monotonic() < deadline:
        time.sleep(0.05)
        current = _child_pids()
    return current


@pytest.fixture(scope="module", autouse=True)
def registered_calculator():
    MCPManager.register_mcp_server("Calculator", str(CALCULATOR))
    yield
    MCPManager.close_all_clients()


@pytest.mark.integration
def test_closing_100_sessions_returns_clients_and_processes_to_baseline():
    baseline_clients = len(MCPManager.clients)
    baseline_children = _child_pids()

    async def exercise():
        for batch_start in range(0, 100, 10):
            client_ids = [
                f"Calculator-lifecycle-{index}"
                for index in range(batch_start, batch_start + 10)
            ]
            await MCPManager.aload_scenarios(
                {client_id: {"history": []} for client_id in client_ids}
            )
            await asyncio.gather(
                *(MCPManager.aclose_client(client_id) for client_id in client_ids)
            )

    asyncio.run(exercise())

    assert len(MCPManager.clients) == baseline_clients
    remaining_children = _wait_for_child_baseline(baseline_children)
    assert remaining_children.issubset(baseline_children)


@pytest.mark.integration
def test_shutdown_is_idempotent_in_fresh_process():
    script = """
from src.manager.mcp_client_manager import MCPManager
MCPManager.register_mcp_server('Calculator', r'%s')
MCPManager.shutdown()
MCPManager.shutdown()
print('shutdown-ok')
""" % str(CALCULATOR)
    environment = os.environ.copy()
    environment["SKIP_MCP_AUTO_INIT"] = "true"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.stdout.strip() == "shutdown-ok"
