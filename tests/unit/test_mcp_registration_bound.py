"""Phase 11 regression for bounded MCP catalog registration."""

from __future__ import annotations

import json
import threading
from types import SimpleNamespace

from src.manager import mcp_client_manager as manager_module


def test_catalog_registration_never_exceeds_configured_bound(monkeypatch, tmp_path):
    manager = manager_module.MCPManager
    active = 0
    peak = 0
    counter_lock = threading.Lock()

    class FakeClient:
        def __init__(self, path):
            self.path = path
            self.connected = False

        async def __aenter__(self):
            nonlocal active, peak
            with counter_lock:
                active += 1
                peak = max(peak, active)
            self.connected = True
            return self

        async def list_tools(self):
            import asyncio

            await asyncio.sleep(0.03)
            return [
                SimpleNamespace(
                    name="probe",
                    description="registration probe",
                    inputSchema={"type": "object"},
                )
            ]

        async def close(self):
            nonlocal active
            if self.connected:
                with counter_lock:
                    active -= 1
                self.connected = False

    monkeypatch.setattr(manager_module, "Client", FakeClient)
    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    f"Server{index}": {"tool_path": f"fake-{index}.py"}
                    for index in range(8)
                }
            }
        ),
        encoding="utf-8",
    )

    manager.init_config(config_path, overwrite=True)

    assert 1 <= manager.registration_concurrency <= 4
    assert peak == min(8, manager.registration_concurrency)
    assert active == 0
    assert len(manager.server_to_path_mapping) == 8

    empty_path = tmp_path / "empty.json"
    empty_path.write_text('{"mcpServers": {}}', encoding="utf-8")
    manager.init_config(empty_path, overwrite=True)
