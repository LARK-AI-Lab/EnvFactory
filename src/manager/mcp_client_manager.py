import asyncio
import json
import logging
import os
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.exceptions import ToolError

load_dotenv()

class MCPClientManager:
    """Manages multiple concurrent MCP servers with connection pooling for performance."""

    _instance = None
    _cls_lock = threading.Lock()
    _excluded_tools = frozenset({"load_scenario", "save_scenario"})

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._cls_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_bootstrapped", False):
            return

        self._bootstrapped = True
        self._initialized = False

        self._lock = threading.Lock()
        self._register_lock = asyncio.Lock()
        self._stateless_lock = asyncio.Lock()
        self._base_client_lock = asyncio.Lock()
        self.load_scenario_timeout = float(os.getenv("MCP_LOAD_SCENARIO_TIMEOUT_SECONDS", "120"))

        self.clients: Dict[str, dict] = {}
        self.stateless_clients: Dict[str, Client] = {}
        self._base_clients: Dict[str, Client] = {}
        self.server_to_path_mapping: Dict[str, str] = {}
        self.tools: Dict[str, dict] = {}

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _ensure_base_client(self, server_name: str) -> Client:
        """Get or create a connected base client for transport reuse."""
        async with self._base_client_lock:
            if server_name in self._base_clients:
                return self._base_clients[server_name]

            client = Client(self.server_to_path_mapping[server_name])
            await client._connect()
            self._base_clients[server_name] = client
            return client

    async def _spawn_session(self, server_name: str) -> Client:
        """Create a new session client sharing the base transport."""
        base = await self._ensure_base_client(server_name)
        return base.new()

    def init_config(self, config_path, overwrite=False):
        """Initialize manager from MCP config file."""
        if self._initialized and not overwrite:
            return

        with open(Path(config_path).resolve(), "r", encoding="utf-8") as f:
            config = json.load(f)

        future = asyncio.run_coroutine_threadsafe(
            self._init_config_async(config, overwrite),
            self._loop,
        )
        return future.result(timeout=120)

    async def _init_config_async(self, config: dict, overwrite: bool = False):
        """Async initialization of all configured servers."""
        if self._initialized and not overwrite:
            return

        if overwrite:
            await self._close_all_clients_async()
            await self._close_all_base_clients_async()
            with self._lock:
                self.server_to_path_mapping.clear()
                self.tools.clear()

        tasks = [
            self.register_mcp_server_async(
                server_name, server_config["tool_path"],
                server_config.get("stateless", False)
            )
            for server_name, server_config in config.get("mcpServers", {}).items()
        ]
        await asyncio.gather(*tasks)
        self._initialized = True

    async def register_mcp_server_async(self, server_name: str, tool_path: str, is_stateless: bool = False):
        """Register an MCP server and extract its tool schemas."""
        client = Client(tool_path)
        await client._connect()

        tools = await client.list_tools()
        schemas = [
            (f"{server_name}-{tool.name}", {
                "type": "function",
                "function": {
                    "name": f"{server_name}-{tool.name}",
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            })
            for tool in tools
        ]

        async with self._register_lock:
            with self._lock:
                self.server_to_path_mapping[server_name] = tool_path
                for tool_name, schema in schemas:
                    self.tools[tool_name] = schema

                if is_stateless:
                    self.stateless_clients[server_name] = client
                else:
                    async with self._base_client_lock:
                        self._base_clients[server_name] = client

    def filter_tools(self, servers: Optional[List[str]] = None) -> List[dict]:
        """Filter tools by allowed server names."""
        with self._lock:
            if servers is None:
                return list(self.tools.values())

            allowed = frozenset(servers)
            result = []
            for name, schema in self.tools.items():
                server, _, short = name.partition("-")
                if server in allowed and short not in self._excluded_tools:
                    result.append(schema)
            return result

    @staticmethod
    def is_valid_client_id(client_id) -> bool:
        """Check if client_id uses '<server>-<request>' format."""
        if not isinstance(client_id, str):
            return False
        hyphen_idx = client_id.find("-")
        return 0 < hyphen_idx < len(client_id) - 1

    def get_client(self, client_id: str) -> Tuple[Client, bool]:
        """Get or create a client. Returns (client, is_initialized)."""
        assert self.is_valid_client_id(client_id), "client_id must use '<server>-<request>' format"
        server_name = client_id.split("-", 1)[0]

        with self._lock:
            if client_id in self.clients:
                info = self.clients[client_id]
                return info["client"], info["status"]

            if server_name in self.stateless_clients:
                return self.stateless_clients[server_name], True

        client = asyncio.run_coroutine_threadsafe(
            self._spawn_session(server_name), self._loop
        ).result(timeout=30)

        with self._lock:
            self.clients[client_id] = {"client": client, "status": False}
        return client, False

    def set_status(self, client_id: str):
        """Mark a session client as initialized."""
        with self._lock:
            if client_id in self.clients:
                self.clients[client_id]["status"] = True

    def load_scenario(self, client_id: str, scenario: Optional[dict] = None, check: bool = False):
        """Load a scenario into the client. Auto-initializes if successful."""
        client, initialized = self.get_client(client_id)
        if initialized or scenario is None:
            return "Client already initialized. Skipping..."

        future = asyncio.run_coroutine_threadsafe(
            self._call_tool_async("load_scenario", {"scenario": scenario}, client, client_id),
            self._loop,
        )
        result = future.result(timeout=self.load_scenario_timeout)
        if check:
            saved = self.call_tool(client_id, "save_scenario", {})
            try:
                if json.loads(saved) == scenario:
                    self.set_status(client_id)
            except Exception:
                pass
        else:
            self.set_status(client_id)

        return result

    def call_tool(self, client_id: str, tool_name: str, tool_args):
        """Execute a tool on the specified client."""
        assert self.is_valid_client_id(client_id), "client_id must use '<server>-<request>' format"

        if "load_scenario" in tool_name:
            scenario = tool_args.get("scenario", tool_args) if isinstance(tool_args, dict) else json.loads(tool_args)
            return self.load_scenario(client_id, scenario)

        client, _ = self.get_client(client_id)
        future = asyncio.run_coroutine_threadsafe(
            self._call_tool_async(tool_name, tool_args, client, client_id),
            self._loop,
        )
        try:
            return future.result(timeout=30)
        except TimeoutError:
            return f"{tool_name} timed out after 30 seconds"
        except ToolError as exc:
            return f"{tool_name} failed: {exc}"
        except Exception as exc:
            return f"{tool_name} error: {exc}"

    async def _call_tool_async(self, tool_name: str, tool_args, client: Client, client_id: str) -> str:
        """Execute tool with proper session handling."""
        short_name = tool_name.split("-", 1)[-1]
        args = json.loads(tool_args) if isinstance(tool_args, str) else tool_args

        server_name = client_id.split("-", 1)[0]
        is_stateless = server_name in self.stateless_clients

        if is_stateless:
            async with self._stateless_lock:
                result = await client.call_tool(short_name, args)
        else:
            async with client:
                result = await client.call_tool(short_name, args)

        return ",".join(item.text for item in result.content if hasattr(item, "text"))

    def save_all_scenario(self, client_id_list: List[str]) -> Dict[str, Optional[dict]]:
        """Save scenarios from all specified clients."""
        future = asyncio.run_coroutine_threadsafe(
            self._save_all_scenario_async(client_id_list),
            self._loop,
        )
        return future.result(timeout=60)

    async def _save_all_scenario_async(self, client_id_list: List[str]) -> Dict[str, Optional[dict]]:
        """Async batch scenario save."""
        async def save_one(cid: str) -> Tuple[str, Optional[dict]]:
            server = cid.split("-", 1)[0]
            try:
                client, _ = self.get_client(cid)
                result = await self._call_tool_async("save_scenario", {}, client, cid)
                return server, json.loads(result)
            except Exception:
                return server, None

        results = await asyncio.gather(*[save_one(cid) for cid in client_id_list])
        return dict(results)

    def close_client(self, client_id: Optional[str] = None, server_name: Optional[str] = None):
        """Remove a session from tracking. Actual cleanup is automatic."""
        if client_id:
            with self._lock:
                self.clients.pop(client_id, None)

        if server_name:
            future = asyncio.run_coroutine_threadsafe(
                self._close_stateless_client(server_name),
                self._loop,
            )
            return future.result(timeout=10)

    async def _close_stateless_client(self, server_name: str):
        """Close a stateless client."""
        with self._lock:
            client = self.stateless_clients.pop(server_name, None)
        if client:
            await client.close()

    async def _close_all_clients_async(self):
        """Clear all session tracking."""
        with self._lock:
            self.clients.clear()

    async def _close_base_client(self, server_name: str):
        """Close a base client and remove from pool."""
        async with self._base_client_lock:
            client = self._base_clients.pop(server_name, None)
            if client:
                await client.close()

    async def _close_all_base_clients_async(self):
        """Close all base clients (for shutdown)."""
        async with self._base_client_lock:
            clients = list(self._base_clients.values())
            self._base_clients.clear()

        await asyncio.gather(*[c.close() for c in clients], return_exceptions=True)

    def close_all_clients(self):
        """Close all tracked clients."""
        future = asyncio.run_coroutine_threadsafe(
            self._close_all_clients_async(),
            self._loop,
        )
        return future.result(timeout=30)

    def shutdown(self, timeout: int = 5):
        """Gracefully shutdown all connections and the event loop."""
        if not self._loop.is_running():
            return

        asyncio.run_coroutine_threadsafe(
            self._close_all_base_clients_async(), self._loop
        ).result(timeout=timeout)

        self.close_all_clients()

        self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join(timeout=timeout)

    def __del__(self):
        try:
            self.shutdown()
        except Exception:
            pass


MCPManager = MCPClientManager()
mcp_config_path = os.environ.get("MCP_CONFIG_PATH")
if mcp_config_path:
    MCPManager.init_config(mcp_config_path)