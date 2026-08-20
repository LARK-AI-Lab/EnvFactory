import asyncio
import json
import logging
import os
import threading
import warnings
from concurrent.futures import Future as ConcurrentFuture
from pathlib import Path
from typing import Any, Coroutine, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.exceptions import ToolError

load_dotenv()

logger = logging.getLogger(__name__)


class MCPConfigurationError(RuntimeError):
    """Raised when the global MCP manager cannot be configured safely."""


def _env_flag_enabled(name: str) -> bool:
    """Return whether an environment flag contains a conventional true value."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _env_timeout(name: str, default: float) -> float:
    """Load a positive timeout from the environment."""
    value = float(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _env_bounded_int(name: str, default: int, *, maximum: int) -> int:
    """Load a positive operational concurrency limit with a hard safety cap."""
    value = int(os.getenv(name, str(default)))
    if value <= 0 or value > maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")
    return value


class MCPClientManager:
    """Manage MCP servers on a dedicated event loop.

    Stateful client IDs own independent FastMCP clients (and therefore independent
    stdio child processes). Public async methods bridge to the manager loop without
    blocking the caller's event loop. Synchronous wrappers remain for notebooks and
    legacy code.
    """

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

        self._initialized = False
        self._shutting_down = False

        self._lock = threading.Lock()
        self._shutdown_lock = threading.Lock()
        self._register_lock = asyncio.Lock()
        self._stateless_lock = asyncio.Lock()
        self._client_create_lock = asyncio.Lock()
        # Retained as a compatibility attribute. Stateful sessions no longer share
        # base stdio transports because doing so also shares mutable server state.
        self._base_client_lock = asyncio.Lock()

        self.registration_timeout = _env_timeout(
            "MCP_REGISTRATION_TIMEOUT_SECONDS", 120
        )
        self.connection_timeout = _env_timeout("MCP_CONNECTION_TIMEOUT_SECONDS", 30)
        self.load_scenario_timeout = _env_timeout(
            "MCP_LOAD_SCENARIO_TIMEOUT_SECONDS", 120
        )
        self.tool_call_timeout = _env_timeout("MCP_TOOL_CALL_TIMEOUT_SECONDS", 30)
        self.shutdown_timeout = _env_timeout("MCP_SHUTDOWN_TIMEOUT_SECONDS", 10)
        self.batch_concurrency = max(1, int(os.getenv("MCP_BATCH_CONCURRENCY", "4")))
        # Catalog registration briefly starts one stdio process tree per server.
        # MoLab has four CPUs and constrained host RAM, so even an environment
        # override remains capped at four concurrent registrations.
        self.registration_concurrency = _env_bounded_int(
            "MCP_REGISTRATION_CONCURRENCY", 2, maximum=4
        )
        self._registration_semaphore = asyncio.Semaphore(
            self.registration_concurrency
        )

        self.clients: Dict[str, dict] = {}
        self.stateless_clients: Dict[str, Client] = {}
        self._base_clients: Dict[str, Client] = {}
        self.server_to_path_mapping: Dict[str, str] = {}
        self.tools: Dict[str, dict] = {}

        self._loop = asyncio.new_event_loop()
        self._loop_ready = threading.Event()
        self._loop_thread = threading.Thread(
            target=self._run_loop,
            name="envfactory-mcp-loop",
            daemon=True,
        )
        self._loop_thread.start()
        if not self._loop_ready.wait(timeout=5):
            raise RuntimeError("MCP manager event loop failed to start")
        self._bootstrapped = True

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.call_soon(self._loop_ready.set)
        self._loop.run_forever()

    def _ensure_running(self) -> None:
        if self._shutting_down or not self._loop.is_running():
            raise RuntimeError("MCP manager event loop is not running")

    def _log_timeout(
        self,
        operation: str,
        timeout: float,
        client_id: Optional[str],
        server_name: Optional[str],
    ) -> None:
        if server_name is None and client_id:
            server_name = client_id.split("-", 1)[0]
        logger.warning(
            "MCP operation timed out operation=%s timeout_seconds=%s client_id=%s server=%s",
            operation,
            timeout,
            client_id,
            server_name,
        )

    async def _submit(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        timeout: float,
        operation: str,
        client_id: Optional[str] = None,
        server_name: Optional[str] = None,
    ) -> Any:
        """Submit work to the manager loop without blocking an async caller."""
        self._ensure_running()
        try:
            caller_loop = asyncio.get_running_loop()
        except RuntimeError:
            coroutine.close()
            raise RuntimeError("_submit() requires an asynchronous caller") from None

        if caller_loop is self._loop:
            # Internal manager-loop code should normally call its coroutine directly.
            # Supporting this case avoids ever falling back to a synchronous wrapper.
            try:
                return await asyncio.wait_for(coroutine, timeout=timeout)
            except TimeoutError:
                self._log_timeout(operation, timeout, client_id, server_name)
                if client_id:
                    await self._close_client_on_loop(client_id)
                raise

        future: ConcurrentFuture = asyncio.run_coroutine_threadsafe(
            coroutine, self._loop
        )
        wrapped = asyncio.wrap_future(future)
        try:
            return await asyncio.wait_for(asyncio.shield(wrapped), timeout=timeout)
        except TimeoutError:
            self._log_timeout(operation, timeout, client_id, server_name)
            future.cancel()
            if client_id and self._loop.is_running():
                cleanup = asyncio.run_coroutine_threadsafe(
                    self._close_client_on_loop(client_id), self._loop
                )
                try:
                    await asyncio.wait_for(
                        asyncio.wrap_future(cleanup), timeout=self.shutdown_timeout
                    )
                except Exception:
                    cleanup.cancel()
                    logger.exception(
                        "Failed to clean up timed-out MCP client client_id=%s",
                        client_id,
                    )
            raise
        except asyncio.CancelledError:
            future.cancel()
            raise

    def _run_sync(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        timeout: float,
        operation: str,
        client_id: Optional[str] = None,
        server_name: Optional[str] = None,
    ) -> Any:
        """Run manager-loop work for a synchronous compatibility caller."""
        if threading.current_thread() is self._loop_thread:
            coroutine.close()
            raise RuntimeError(
                f"{operation} cannot use a synchronous MCP API on the manager loop"
            )
        self._ensure_running()
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            self._log_timeout(operation, timeout, client_id, server_name)
            future.cancel()
            if client_id and self._loop.is_running():
                cleanup = asyncio.run_coroutine_threadsafe(
                    self._close_client_on_loop(client_id), self._loop
                )
                try:
                    cleanup.result(timeout=self.shutdown_timeout)
                except Exception:
                    cleanup.cancel()
                    logger.exception(
                        "Failed to clean up timed-out MCP client client_id=%s",
                        client_id,
                    )
            raise

    async def _connect_client(self, client: Client) -> None:
        """Connect through FastMCP's supported async context-manager API."""
        try:
            await asyncio.wait_for(
                client.__aenter__(), timeout=self.connection_timeout
            )
        except BaseException:
            try:
                await client.close()
            except Exception:
                logger.debug("Failed to close partially connected MCP client", exc_info=True)
            raise

    def init_config(self, config_path, overwrite=False):
        """Initialize the manager from an MCP config file."""
        if self._initialized and not overwrite:
            return None
        if not config_path:
            raise MCPConfigurationError(
                "MCP configuration is missing. Set MCP_CONFIG_PATH or set "
                "SKIP_MCP_AUTO_INIT=true and register servers explicitly."
            )

        resolved_path = Path(config_path).expanduser().resolve()
        if not resolved_path.is_file():
            raise MCPConfigurationError(
                f"MCP configuration file does not exist: {resolved_path}"
            )
        try:
            with resolved_path.open("r", encoding="utf-8") as file:
                config = json.load(file)
        except json.JSONDecodeError as exc:
            raise MCPConfigurationError(
                f"MCP configuration is not valid JSON: {resolved_path}"
            ) from exc
        if not isinstance(config.get("mcpServers"), dict):
            raise MCPConfigurationError(
                f"MCP configuration must contain an 'mcpServers' object: {resolved_path}"
            )

        server_count = max(1, len(config["mcpServers"]))
        return self._run_sync(
            self._init_config_on_loop(config, overwrite),
            timeout=self.registration_timeout * server_count,
            operation="configuration initialization",
        )

    def register_mcp_server(
        self,
        server_name: str,
        tool_path: str,
        is_stateless: bool = False,
        timeout: Optional[float] = None,
    ):
        """Synchronously register one MCP server on the manager event loop."""
        if not server_name or not isinstance(server_name, str):
            raise ValueError("server_name must be a non-empty string")
        if not tool_path or not isinstance(tool_path, str):
            raise ValueError("tool_path must be a non-empty string")
        timeout = self.registration_timeout if timeout is None else timeout
        return self._run_sync(
            self.register_mcp_server_async(server_name, tool_path, is_stateless),
            timeout=timeout,
            operation="server registration",
            server_name=server_name,
        )

    def register_MCP_server(self, *args, **kwargs):
        """Deprecated compatibility alias for :meth:`register_mcp_server`."""
        warnings.warn(
            "register_MCP_server() is deprecated; use register_mcp_server()",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.register_mcp_server(*args, **kwargs)

    async def _init_config_on_loop(self, config: dict, overwrite: bool = False):
        if self._initialized and not overwrite:
            return
        if overwrite:
            await self._clear_registered_servers_on_loop()

        servers = config["mcpServers"]
        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict) or not server_config.get("tool_path"):
                raise MCPConfigurationError(
                    f"MCP server '{server_name}' must define a non-empty tool_path"
                )

        tasks = [
            asyncio.wait_for(
                self.register_mcp_server_async(
                    server_name,
                    server_config["tool_path"],
                    server_config.get("stateless", False),
                ),
                timeout=self.registration_timeout,
            )
            for server_name, server_config in servers.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        failures = [result for result in results if isinstance(result, BaseException)]
        if failures:
            await self._clear_registered_servers_on_loop()
            raise MCPConfigurationError(
                "MCP auto-initialization failed; no servers were retained"
            ) from failures[0]
        self._initialized = True

    async def register_mcp_server_async(
        self, server_name: str, tool_path: str, is_stateless: bool = False
    ):
        """Register a server; this coroutine must execute on the manager loop."""
        async with self._registration_semaphore:
            client = Client(tool_path)
            retained = False
            try:
                await self._connect_client(client)
                tools = await asyncio.wait_for(
                    client.list_tools(), timeout=self.registration_timeout
                )
                schemas = [
                    (
                        f"{server_name}-{tool.name}",
                        {
                            "type": "function",
                            "function": {
                                "name": f"{server_name}-{tool.name}",
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        },
                    )
                    for tool in tools
                ]

                async with self._register_lock:
                    await self._close_server_sessions_on_loop(server_name)
                    old_stateless = self.stateless_clients.pop(server_name, None)
                    if old_stateless is not None:
                        await old_stateless.close()
                    with self._lock:
                        prefix = f"{server_name}-"
                        for name in [name for name in self.tools if name.startswith(prefix)]:
                            self.tools.pop(name, None)
                        self.server_to_path_mapping[server_name] = tool_path
                        for tool_name, schema in schemas:
                            self.tools[tool_name] = schema
                        if is_stateless:
                            self.stateless_clients[server_name] = client
                            retained = True
            finally:
                if not retained:
                    await client.close()

    async def _clear_registered_servers_on_loop(self):
        await self._close_all_clients_on_loop()
        with self._lock:
            stateless_clients = list(self.stateless_clients.values())
            base_clients = list(self._base_clients.values())
            self.stateless_clients.clear()
            self._base_clients.clear()
            self.server_to_path_mapping.clear()
            self.tools.clear()
        await asyncio.gather(
            *[client.close() for client in stateless_clients + base_clients],
            return_exceptions=True,
        )
        self._initialized = False

    def filter_tools(self, servers: Optional[List[str]] = None) -> List[dict]:
        """Filter tools by allowed server names."""
        with self._lock:
            if servers is None:
                return list(self.tools.values())
            allowed = frozenset(servers)
            return [
                schema
                for name, schema in self.tools.items()
                if (parts := name.partition("-"))[0] in allowed
                and parts[2] not in self._excluded_tools
            ]

    @staticmethod
    def is_valid_client_id(client_id) -> bool:
        """Check if client_id uses '<server>-<request>' format."""
        if not isinstance(client_id, str):
            return False
        hyphen_idx = client_id.find("-")
        return 0 < hyphen_idx < len(client_id) - 1

    async def _get_or_create_client_on_loop(self, client_id: str) -> Tuple[Client, bool]:
        """Get or create a session. This always executes on the manager loop."""
        if not self.is_valid_client_id(client_id):
            raise ValueError("client_id must use '<server>-<request>' format")
        server_name = client_id.split("-", 1)[0]

        async with self._client_create_lock:
            with self._lock:
                info = self.clients.get(client_id)
                if info is not None:
                    return info["client"], info["status"]
                stateless = self.stateless_clients.get(server_name)
                tool_path = self.server_to_path_mapping.get(server_name)
            if stateless is not None:
                return stateless, True
            if tool_path is None:
                raise MCPConfigurationError(
                    f"MCP server '{server_name}' is not registered. Set MCP_CONFIG_PATH "
                    "to a valid configuration or register the server explicitly."
                )

            client = Client(tool_path)
            await self._connect_client(client)
            with self._lock:
                self.clients[client_id] = {
                    "client": client,
                    "status": False,
                    "server": server_name,
                    "operation_lock": asyncio.Lock(),
                }
            return client, False

    def get_client(self, client_id: str) -> Tuple[Client, bool]:
        """Synchronous compatibility wrapper for session lookup/creation."""
        return self._run_sync(
            self._get_or_create_client_on_loop(client_id),
            timeout=self.connection_timeout,
            operation="session connection",
            client_id=client_id,
        )

    def _set_status_on_loop(self, client_id: str) -> None:
        with self._lock:
            if client_id in self.clients:
                self.clients[client_id]["status"] = True

    def set_status(self, client_id: str):
        """Mark a session initialized from synchronous legacy code."""
        async def set_status_on_loop():
            self._set_status_on_loop(client_id)

        return self._run_sync(
            set_status_on_loop(),
            timeout=self.connection_timeout,
            operation="session status update",
            client_id=client_id,
        )

    async def _call_tool_on_loop(
        self,
        client_id: str,
        tool_name: str,
        tool_args: dict | str,
        timeout: Optional[float] = None,
    ) -> str:
        client, _ = await self._get_or_create_client_on_loop(client_id)
        short_name = tool_name.split("-", 1)[-1]
        args = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
        if not isinstance(args, dict):
            raise TypeError("tool_args must decode to a dictionary")

        server_name = client_id.split("-", 1)[0]
        with self._lock:
            info = self.clients.get(client_id)
            is_stateless = server_name in self.stateless_clients
        operation_lock = self._stateless_lock if is_stateless else info["operation_lock"]
        async with operation_lock:
            result = await asyncio.wait_for(
                client.call_tool(short_name, args),
                timeout=self.tool_call_timeout if timeout is None else timeout,
            )
        return ",".join(
            item.text for item in result.content if hasattr(item, "text")
        )

    async def _load_scenario_on_loop(
        self, client_id: str, scenario: Optional[dict] = None, check: bool = False
    ) -> str:
        _, initialized = await self._get_or_create_client_on_loop(client_id)
        if initialized or scenario is None:
            return "Client already initialized. Skipping..."

        result = await asyncio.wait_for(
            self._call_tool_on_loop(
                client_id,
                "load_scenario",
                {"scenario": scenario},
                timeout=self.load_scenario_timeout,
            ),
            timeout=self.load_scenario_timeout,
        )
        if check:
            saved = await self._call_tool_on_loop(client_id, "save_scenario", {})
            try:
                if json.loads(saved) == scenario:
                    self._set_status_on_loop(client_id)
            except (TypeError, json.JSONDecodeError):
                pass
        else:
            self._set_status_on_loop(client_id)
        return result

    async def aload_scenario(
        self, client_id: str, scenario: dict | None = None, check: bool = False
    ) -> str:
        """Load one scenario without blocking the caller's event loop."""
        return await self._submit(
            self._load_scenario_on_loop(client_id, scenario, check),
            timeout=self.connection_timeout
            + self.load_scenario_timeout
            + (self.tool_call_timeout if check else 0),
            operation="scenario load",
            client_id=client_id,
        )

    async def aload_scenarios(
        self, scenarios_by_client: Dict[str, dict], check: bool = False
    ) -> Dict[str, str]:
        """Load scenarios concurrently with manager-wide bounded concurrency."""
        async def load_all_on_loop() -> Dict[str, str]:
            semaphore = asyncio.Semaphore(self.batch_concurrency)

            async def load_one(client_id: str, scenario: dict):
                async with semaphore:
                    try:
                        return client_id, await self._load_scenario_on_loop(
                            client_id, scenario, check
                        )
                    except TimeoutError:
                        self._log_timeout(
                            "scenario load",
                            self.load_scenario_timeout,
                            client_id,
                            None,
                        )
                        await self._close_client_on_loop(client_id)
                        raise

            try:
                pairs = await asyncio.gather(
                    *(
                        load_one(client_id, scenario)
                        for client_id, scenario in scenarios_by_client.items()
                    )
                )
                return dict(pairs)
            except BaseException:
                await asyncio.gather(
                    *(
                        self._close_client_on_loop(client_id)
                        for client_id in scenarios_by_client
                    ),
                    return_exceptions=True,
                )
                raise

        count = max(1, len(scenarios_by_client))
        return await self._submit(
            load_all_on_loop(),
            timeout=(
                self.connection_timeout
                + self.load_scenario_timeout
                + (self.tool_call_timeout if check else 0)
            )
            * count,
            operation="batch scenario load",
        )

    def load_scenario(
        self, client_id: str, scenario: Optional[dict] = None, check: bool = False
    ):
        """Synchronous compatibility wrapper for :meth:`aload_scenario`."""
        return self._run_sync(
            self._load_scenario_on_loop(client_id, scenario, check),
            timeout=self.connection_timeout
            + self.load_scenario_timeout
            + (self.tool_call_timeout if check else 0),
            operation="scenario load",
            client_id=client_id,
        )

    async def acall_tool(
        self, client_id: str, tool_name: str, tool_args: dict | str
    ) -> str:
        """Execute one tool call without blocking the caller's event loop."""
        if "load_scenario" in tool_name:
            scenario = (
                tool_args.get("scenario", tool_args)
                if isinstance(tool_args, dict)
                else json.loads(tool_args)
            )
            return await self.aload_scenario(client_id, scenario)
        try:
            return await self._submit(
                self._call_tool_on_loop(client_id, tool_name, tool_args),
                timeout=self.connection_timeout + self.tool_call_timeout,
                operation="tool call",
                client_id=client_id,
            )
        except TimeoutError:
            return f"{tool_name} timed out after {self.tool_call_timeout:g} seconds"
        except ToolError as exc:
            return f"{tool_name} failed: {exc}"
        except Exception as exc:
            return f"{tool_name} error: {exc}"

    def call_tool(self, client_id: str, tool_name: str, tool_args):
        """Synchronous compatibility wrapper for :meth:`acall_tool`."""
        if "load_scenario" in tool_name:
            scenario = (
                tool_args.get("scenario", tool_args)
                if isinstance(tool_args, dict)
                else json.loads(tool_args)
            )
            return self.load_scenario(client_id, scenario)
        try:
            return self._run_sync(
                self._call_tool_on_loop(client_id, tool_name, tool_args),
                timeout=self.connection_timeout + self.tool_call_timeout,
                operation="tool call",
                client_id=client_id,
            )
        except TimeoutError:
            return f"{tool_name} timed out after {self.tool_call_timeout:g} seconds"
        except ToolError as exc:
            return f"{tool_name} failed: {exc}"
        except Exception as exc:
            return f"{tool_name} error: {exc}"

    async def _save_all_scenarios_on_loop(
        self, client_ids: List[str]
    ) -> Dict[str, Optional[dict]]:
        semaphore = asyncio.Semaphore(self.batch_concurrency)

        async def save_one(client_id: str) -> Tuple[str, Optional[dict]]:
            server = client_id.split("-", 1)[0]
            async with semaphore:
                try:
                    result = await self._call_tool_on_loop(
                        client_id, "save_scenario", {}
                    )
                    return server, json.loads(result)
                except TimeoutError:
                    self._log_timeout(
                        "scenario save",
                        self.tool_call_timeout,
                        client_id,
                        server,
                    )
                    await self._close_client_on_loop(client_id)
                    return server, None
                except Exception:
                    logger.exception(
                        "Failed to save MCP scenario client_id=%s server=%s",
                        client_id,
                        server,
                    )
                    return server, None

        return dict(await asyncio.gather(*(save_one(cid) for cid in client_ids)))

    async def asave_all_scenarios(
        self, client_ids: List[str]
    ) -> Dict[str, dict | None]:
        """Save scenarios concurrently with bounded concurrency."""
        count = max(1, len(client_ids))
        return await self._submit(
            self._save_all_scenarios_on_loop(client_ids),
            timeout=(self.connection_timeout + self.tool_call_timeout) * count,
            operation="batch scenario save",
        )

    def save_all_scenario(
        self, client_id_list: List[str]
    ) -> Dict[str, Optional[dict]]:
        """Deprecated singular-name compatibility wrapper."""
        return self._run_sync(
            self._save_all_scenarios_on_loop(client_id_list),
            timeout=(self.connection_timeout + self.tool_call_timeout)
            * max(1, len(client_id_list)),
            operation="batch scenario save",
        )

    def save_all_scenarios(
        self, client_ids: List[str]
    ) -> Dict[str, Optional[dict]]:
        """Synchronous plural alias matching :meth:`asave_all_scenarios`."""
        return self.save_all_scenario(client_ids)

    async def _close_client_on_loop(self, client_id: str) -> None:
        with self._lock:
            info = self.clients.pop(client_id, None)
        if info is not None:
            await info["client"].close()

    async def _close_server_sessions_on_loop(self, server_name: str) -> None:
        with self._lock:
            client_ids = [
                client_id
                for client_id, info in self.clients.items()
                if info.get("server") == server_name
            ]
        await asyncio.gather(
            *(self._close_client_on_loop(client_id) for client_id in client_ids),
            return_exceptions=True,
        )

    async def aclose_client(self, client_id: str) -> None:
        """Close and untrack one stateful session deterministically."""
        await self._submit(
            self._close_client_on_loop(client_id),
            timeout=self.shutdown_timeout,
            operation="client close",
            client_id=client_id,
        )

    async def _close_stateless_client_on_loop(self, server_name: str) -> None:
        with self._lock:
            client = self.stateless_clients.pop(server_name, None)
        if client is not None:
            await client.close()

    def close_client(
        self,
        client_id: Optional[str] = None,
        server_name: Optional[str] = None,
    ):
        """Synchronous compatibility wrapper for deterministic client close."""
        if client_id:
            self._run_sync(
                self._close_client_on_loop(client_id),
                timeout=self.shutdown_timeout,
                operation="client close",
                client_id=client_id,
            )
        if server_name:
            return self._run_sync(
                self._close_stateless_client_on_loop(server_name),
                timeout=self.shutdown_timeout,
                operation="stateless client close",
                server_name=server_name,
            )
        return None

    async def _close_all_clients_on_loop(self) -> None:
        with self._lock:
            clients = [info["client"] for info in self.clients.values()]
            self.clients.clear()
        await asyncio.gather(
            *(client.close() for client in clients), return_exceptions=True
        )

    async def _close_all_base_clients_on_loop(self) -> None:
        async with self._base_client_lock:
            clients = list(self._base_clients.values())
            self._base_clients.clear()
        await asyncio.gather(
            *(client.close() for client in clients), return_exceptions=True
        )

    def close_all_clients(self):
        """Close all tracked stateful clients."""
        return self._run_sync(
            self._close_all_clients_on_loop(),
            timeout=self.shutdown_timeout,
            operation="all-clients close",
        )

    async def aclose_all_clients(self) -> None:
        """Asynchronously close every tracked stateful session."""
        await self._submit(
            self._close_all_clients_on_loop(),
            timeout=self.shutdown_timeout,
            operation="all-clients close",
        )

    async def _shutdown_on_loop(self) -> None:
        await self._close_all_clients_on_loop()
        with self._lock:
            stateless = list(self.stateless_clients.values())
            self.stateless_clients.clear()
        await asyncio.gather(
            *(client.close() for client in stateless), return_exceptions=True
        )
        await self._close_all_base_clients_on_loop()

    def shutdown(self, timeout: Optional[float] = None):
        """Idempotently close connections and stop the manager event loop."""
        timeout = self.shutdown_timeout if timeout is None else timeout
        with self._shutdown_lock:
            if self._shutting_down or not self._loop.is_running():
                return
            self._shutting_down = True
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._shutdown_on_loop(), self._loop
                )
                future.result(timeout=timeout)
            finally:
                self._loop.call_soon_threadsafe(self._loop.stop)
                if threading.current_thread() is not self._loop_thread:
                    self._loop_thread.join(timeout=timeout)

    def __del__(self):
        try:
            self.shutdown()
        except Exception:
            pass


MCPManager = MCPClientManager()
mcp_config_path = os.environ.get("MCP_CONFIG_PATH")
if _env_flag_enabled("SKIP_MCP_AUTO_INIT"):
    logger.debug("Skipping MCP auto-initialization")
elif mcp_config_path:
    MCPManager.init_config(mcp_config_path)
else:
    logger.debug("MCP_CONFIG_PATH is unset; servers must be registered explicitly")
