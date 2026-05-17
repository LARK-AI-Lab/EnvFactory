"""Environment generation module for MCP tools.

This module provides the EnvGen pipeline for generating complete MCP tool
implementations with validation and revision cycles.
"""

from dataclasses import dataclass
from typing import Optional

from src.gen import GenConfig


@dataclass
class EnvGenConfig(GenConfig):
    """Configuration class for EnvGen (Environment Generation).

    Contains all configuration fields specific to the EnvGen pipeline,
    including tool generation, scenario generation, validation, and revision.

    Inherits shared fields (model_name, temperature, log_folder, etc.) from GenConfig.
    """

    # Model overrides for specific EnvGen subtasks
    schema_gen_model: Optional[str] = "claude"
    """Schema generation model, uses model_name if None"""

    tool_gen_model: Optional[str] = "claude"
    """Tool generation model, uses model_name if None"""

    # Scenario generation settings
    n_scenarios: int = 4
    """Number of test scenarios to generate"""

    # Validation and revision settings
    max_revisions: int = 3
    """Maximum revision count for validation-revision loop"""

    max_concurrent_scenarios: int = 3
    """Maximum number of scenarios to validate concurrently"""

    quick_validate: bool = False
    """Whether to enable quick validation (skip some checks)"""

    # Parallel processing settings
    max_concurrent_files: int = 3
    """Maximum number of metadata files to process concurrently"""

    # Checkpoint and intermediate results
    save_intermediate: bool = True
    """Whether to save intermediate results (checkpoints)"""

    intermediate_dir: str = "envs/intermediate"
    """Directory for saving intermediate results"""

    enable_resume: bool = False
    """Whether to support checkpoint resume for interrupted generations"""

    # Logging and debugging
    enable_detailed_logging: bool = True
    """Whether to enable detailed logging"""

    # Execution settings
    agent_timeout: int = 3600
    """Agent execution timeout in seconds"""


# Import main classes for convenient access
from src.gen.env_gen.env_gen import EnvGen
from src.gen.env_gen.mcp_tool_gen import MCPToolGen, ScenarioGen
from src.gen.env_gen.validate_revise import ValidateReviseGen
from src.gen.env_gen.types import (
    ScenarioResult,
    ValidationReport,
    RevisionHistory,
    EnvGenState,
    EnvGenResult,
    CheckpointData,
)

__all__ = [
    # Configuration
    "EnvGenConfig",
    # Main classes
    "EnvGen",
    "MCPToolGen",
    "ScenarioGen",
    "ValidateReviseGen",
    # Types
    "ScenarioResult",
    "ValidationReport",
    "RevisionHistory",
    "EnvGenState",
    "EnvGenResult",
    "CheckpointData",
]
