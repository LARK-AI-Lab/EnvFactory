"""Shared pytest configuration for EnvFactory's test suites."""

import os


# Tests register isolated fake servers explicitly and must never auto-start the
# repository-wide MCP catalog during collection.
os.environ.setdefault("SKIP_MCP_AUTO_INIT", "true")
