"""Small local MCP server used by Phase 2 async/lifecycle integration tests."""

import time

from mcp.server.fastmcp import FastMCP


mcp = FastMCP(name="SlowMCP")
state = {"value": None}


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    state.clear()
    state.update(scenario)
    return "Successfully loaded scenario"


@mcp.tool()
def save_scenario() -> dict:
    return dict(state)


@mcp.tool()
def slow(delay_seconds: float) -> dict:
    time.sleep(delay_seconds)
    return {"slept": delay_seconds}


@mcp.tool()
def ping() -> str:
    return "pong"


if __name__ == "__main__":
    mcp.run()
