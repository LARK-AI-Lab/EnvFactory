"""Phase 1 regression tests for core initialization and sampling behavior."""

import asyncio
import json
import os
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import networkx as nx
import pytest

from src.gen import Gen, ModelConfigurationError
from src.gen.env_gen import EnvGenConfig
from src.gen.mcp_schema_gen import SchemaGen
from src.gen.query_gen import QueryGenConfig, QueryGenContext
from src.gen.query_gen import query_gen_non_conv as non_conv_module
from src.gen.query_gen.query_gen_non_conv import QueryGenNonConv
from src.graph.sampler import RandomWalkSampler
from src.graph.tool_graph import ToolGraph
from src.graph.tool_node import Tool
from src.manager.llm_client_manager import LLMClientManager, LLMConfigurationError
from src.manager.mcp_client_manager import MCPManager


ROOT = Path(__file__).resolve().parents[2]


def test_register_mcp_server_sync_wrapper(monkeypatch):
    calls = []

    async def fake_register(server_name, tool_path, is_stateless=False):
        calls.append((server_name, tool_path, is_stateless))
        return "registered"

    monkeypatch.setattr(MCPManager, "register_mcp_server_async", fake_register)

    result = MCPManager.register_mcp_server(
        "Calendar",
        "envs/tools/Calendar.py",
        is_stateless=True,
    )

    assert result == "registered"
    assert calls == [("Calendar", "envs/tools/Calendar.py", True)]


def test_skip_auto_init():
    env = os.environ.copy()
    env["SKIP_MCP_AUTO_INIT"] = "true"
    env["MCP_CONFIG_PATH"] = str(ROOT / "does-not-exist.json")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from src.manager.mcp_client_manager import MCPManager; "
                "print(MCPManager._initialized)"
            ),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.stdout.strip() == "False"


def test_missing_mcp_config_fails_clearly():
    env = os.environ.copy()
    env.pop("MCP_CONFIG_PATH", None)
    env["SKIP_MCP_AUTO_INIT"] = "false"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from src.manager.mcp_client_manager import MCPManager; "
                "MCPManager.get_client('Calendar-request')"
            ),
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert "MCP server 'Calendar' is not registered" in result.stderr
    assert "MCP_CONFIG_PATH" in result.stderr


def test_agent_initialization_occurs_once(monkeypatch):
    calls = []

    monkeypatch.setattr(Gen, "get_model", lambda self, model_name=None: object())
    monkeypatch.setattr(SchemaGen, "load_agents", lambda self: calls.append(self))

    SchemaGen(config=EnvGenConfig())

    assert len(calls) == 1


def test_query_configs_are_not_mutated_across_runs(monkeypatch):
    shared_config = QueryGenConfig(enable_user_tool_use=True)

    def generator(classification):
        instance = object.__new__(QueryGenNonConv)
        instance.config = shared_config
        instance.user_tools = {}
        instance.user_tool_use_enabled = shared_config.enable_user_tool_use
        instance.user_tool_classifier = SimpleNamespace(name="classifier")
        instance.context_manager = SimpleNamespace(get_session=lambda **_: object())

        async def fake_log(**_):
            return {"user_tools": classification}

        instance.log = fake_log
        return instance

    async def fake_run(*_, **__):
        return object()

    monkeypatch.setattr(non_conv_module.Runner, "run", fake_run)
    monkeypatch.setitem(MCPManager.tools, "Weather-user_tool", object())
    first = generator([])
    second = generator(
        [{"name": "Weather-user_tool", "description": "available to the user"}]
    )
    first_context = QueryGenContext(
        config=shared_config,
        tool_graph=SimpleNamespace(),
        tool_chain=SimpleNamespace(user_tools=None),
        idx=0,
        conversation_id="phase-1-first",
    )
    second_context = QueryGenContext(
        config=shared_config,
        tool_graph=SimpleNamespace(),
        tool_chain=SimpleNamespace(user_tools=None),
        idx=0,
        conversation_id="phase-1-second",
    )

    async def classify_concurrently():
        await asyncio.gather(
            first.classify_tools(first_context),
            second.classify_tools(second_context),
        )

    asyncio.run(classify_concurrently())

    assert first.user_tool_use_enabled is False
    assert second.user_tool_use_enabled is True
    assert shared_config.enable_user_tool_use is True


def _sampling_graph() -> ToolGraph:
    tools = [
        Tool(
            {
                "server": "Weather",
                "name": f"Weather-tool-{index}",
                "description": "test tool",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
            }
        )
        for index in range(5)
    ]
    graph = nx.DiGraph()
    graph.add_nodes_from(tools)
    for index, tool in enumerate(tools):
        graph.add_edge(tool, tools[(index + 1) % len(tools)])
        graph.add_edge(tool, tools[(index + 2) % len(tools)])
    tool_graph = ToolGraph(graph=graph)
    tool_graph.server_to_tools = {"Weather": tools}
    return tool_graph


def _sample_names(tool_graph: ToolGraph, seed: int) -> tuple[str, ...]:
    chain = tool_graph.sample(RandomWalkSampler(), max_nodes=8, seed=seed)
    return tuple(tool.name for tool in chain.init_tool_chain)


def test_graph_sampling_is_reproducible_under_concurrency():
    tool_graph = _sampling_graph()
    with ThreadPoolExecutor(max_workers=8) as pool:
        samples = list(pool.map(lambda _: _sample_names(tool_graph, 73), range(64)))

    assert len(set(samples)) == 1

    script = textwrap.dedent(
        """
        import json
        import networkx as nx
        from src.graph.sampler import RandomWalkSampler
        from src.graph.tool_graph import ToolGraph
        from src.graph.tool_node import Tool

        tools = [Tool({
            "server": "Weather",
            "name": f"Weather-tool-{index}",
            "description": "test tool",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
        }) for index in range(5)]
        graph = nx.DiGraph()
        graph.add_nodes_from(tools)
        for index, tool in enumerate(tools):
            graph.add_edge(tool, tools[(index + 1) % len(tools)])
            graph.add_edge(tool, tools[(index + 2) % len(tools)])
        tool_graph = ToolGraph(graph=graph)
        tool_graph.server_to_tools = {"Weather": tools}
        chain = tool_graph.sample(RandomWalkSampler(), max_nodes=8, seed=73)
        print(json.dumps([tool.name for tool in chain.init_tool_chain]))
        """
    )
    env = os.environ.copy()
    env["SKIP_MCP_AUTO_INIT"] = "true"
    process_samples = [
        json.loads(
            subprocess.check_output(
                [sys.executable, "-c", script],
                cwd=ROOT,
                env=env,
                text=True,
                timeout=30,
            )
        )
        for _ in range(2)
    ]

    assert process_samples[0] == process_samples[1] == list(samples[0])


def test_missing_model_configuration_fails_before_network(monkeypatch):
    for name in (
        "OPENAI_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "CHAT_MODEL",
        "CHAT_API_KEY",
        "CHAT_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    generator = SimpleNamespace(config=SimpleNamespace(model_name="openai"))
    with pytest.raises(ModelConfigurationError, match="OPENAI_MODEL"):
        Gen.get_model(generator)

    client = LLMClientManager()
    with pytest.raises(LLMConfigurationError, match="CHAT_API_KEY"):
        client.inference("hello")
    assert client.chat_client is None
    assert client._executor is None
