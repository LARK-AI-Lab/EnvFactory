from dotenv import load_dotenv
load_dotenv()

from agents import Agent, Runner

from src.gen import Gen, GenConfig
from src.utils.utils import format_tools_for_prompt
from src.gen.env_gen.prompts import (
    MCPToolGenerator_System_Prompt,
    MCPToolGenerator_User_Prompt,
    ScenarioGenerator_System_Prompt,
    ScenarioGenerator_User_Prompt
)

import os
import litellm
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class MCPToolGen(Gen):
    def __init__(self, config: Optional[GenConfig] = None, logger=None):
        """
        Initialize MCPToolGen.

        Args:
            config: Configuration object
            logger: Optional shared logger instance
        """
        super().__init__(config, logger=logger)

        # Set timeout
        from src.gen.env_gen import EnvGenConfig
        if isinstance(self.config, EnvGenConfig):
            timeout = int(os.environ.get('LITELLM_TIMEOUT', str(self.config.agent_timeout)))
        else:
            timeout = int(os.environ.get('LITELLM_TIMEOUT', '3600'))
        os.environ['LITELLM_TIMEOUT'] = str(timeout)
        litellm.request_timeout = timeout

        self.load_agents()

    def load_agents(self) -> None:
        """Load tool generator agent."""
        # Use tool_gen_model if specified, otherwise use default model
        from src.gen.env_gen import EnvGenConfig
        if isinstance(self.config, EnvGenConfig) and self.config.tool_gen_model:
            tool_model = self.get_model(self.config.tool_gen_model)
        else:
            tool_model = self.model

        self.tool_generator = Agent(
            name="MCPToolGenerator",
            instructions=MCPToolGenerator_System_Prompt,
            model=tool_model,
        )

    async def gen(
        self,
        mcp_server_name: str,
        mcp_server_description: str,
        tools: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        start_turn_idx: int = 0
    ) -> Tuple[Dict[str, Any], int]:
        """
        Generate MCP tool implementation code.

        Args:
            mcp_server_name: MCP server name
            mcp_server_description: MCP server description
            tools: List of tools with input_schema and output_schema
            conversation_id: Conversation ID for logging
            start_turn_idx: Starting turn index for logging

        Returns:
            Tuple of (Dict containing tool_code, next turn_idx)
        """
        if conversation_id is None:
            conversation_id = f"tool_gen_{mcp_server_name}"

        turn_idx = start_turn_idx

        # Format tools list (only need to do this once)
        formatted_tools = format_tools_for_prompt(tools)

        # Build user prompt (only need to do this once)
        user_prompt = MCPToolGenerator_User_Prompt.format(
            mcp_server_name=mcp_server_name,
            mcp_server_description=mcp_server_description,
            mcp_tools=formatted_tools
        )

        max_attempts = 2
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                # Call agent
                output = await Runner.run(
                    self.tool_generator,
                    input=user_prompt,
                    max_turns=self.config.max_turns
                )

                # Check if output is valid
                if output is None or not hasattr(output, 'final_output') or output.final_output is None:
                    error_msg = f"Agent output is None or invalid (attempt {attempt}/{max_attempts})"
                    if attempt < max_attempts:
                        print(f"Warning: {error_msg}, retrying...")
                        last_error = ValueError(error_msg)
                        continue
                    else:
                        raise ValueError(error_msg)

                # Log interaction
                output_json = await self.log(
                    conversation_id=conversation_id,
                    idx=turn_idx,
                    agent=self.tool_generator,
                    output=output
                )
                turn_idx += 1

                # Check if parsing succeeded
                if not output_json:
                    error_msg = f"Failed to parse structured output (attempt {attempt}/{max_attempts})"
                    if attempt < max_attempts:
                        print(f"Warning: {error_msg}, retrying...")
                        print(f"Raw output preview: {output.final_output[:200]}...")
                        last_error = ValueError(error_msg)
                        continue
                    else:
                        raise ValueError(f"{error_msg}. Raw output: {output.final_output[:500]}...")

                # Ensure output contains tool_code
                if 'tool_code' not in output_json:
                    error_msg = f"Agent output missing 'tool_code' field. Parsed keys: {list(output_json.keys())} (attempt {attempt}/{max_attempts})"
                    if attempt < max_attempts:
                        print(f"Warning: {error_msg}, retrying...")
                        if output.final_output:
                            print(f"Raw output preview: {output.final_output[:200]}...")
                        last_error = ValueError(error_msg)
                        continue
                    else:
                        raise ValueError(error_msg)

                # Success - return result and next turn_idx
                return output_json, turn_idx

            except ValueError as e:
                # If it's the last attempt, raise the error
                if attempt >= max_attempts:
                    log_name = Path(self.config.log_dump_path).name
                    self.logger.dump_log(conversation_id, log_name)
                    raise e
                # Otherwise, save error and retry
                print(f"Warning: {e}, retrying...")
                last_error = e
                continue
            except Exception as e:
                # For other exceptions, don't retry, just raise
                log_name = Path(self.config.log_dump_path).name
                self.logger.dump_log(conversation_id, log_name)
                raise RuntimeError(f"Failed to generate tool for {mcp_server_name}: {str(e)}") from e

        # If we get here, all attempts failed
        log_name = Path(self.config.log_dump_path).name
        self.logger.dump_log(conversation_id, log_name)
        if last_error:
            raise last_error
        else:
            raise RuntimeError(f"Failed to generate tool for {mcp_server_name} after {max_attempts} attempts")

    def save_tools(self, mcp_server_name: str, tool_code: str) -> Path:
        """
        Save generated tool code to file.

        Args:
            mcp_server_name: MCP server name
            tool_code: Generated tool code string

        Returns:
            Path to saved file
        """
        # Ensure tool_code is string
        if not isinstance(tool_code, str):
            raise ValueError("tool_code must be a string")

        # Build file path
        tools_dir = Path("envs/tools")
        tools_dir.mkdir(parents=True, exist_ok=True)

        file_path = tools_dir / f"{mcp_server_name}.py"

        # Write file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tool_code)
            return file_path
        except Exception as e:
            raise IOError(f"Failed to save tool file to {file_path}: {e}") from e


def extract_pydantic_models(tool_code: str) -> str:
    """
    Extract Section 1 (Pydantic models) from tool code.

    Args:
        tool_code: Full tool implementation code

    Returns:
        String containing only Section 1 (Pydantic models) up to Scenario_Schema line
    """
    lines = tool_code.split('\n')
    section1_lines = []
    found_section1 = False

    for line in lines:
        # Check if we've found Section 1 marker
        if '# Section 1:' in line or '# Section 1 ' in line:
            found_section1 = True

        if found_section1:
            section1_lines.append(line)
            # Stop when we find Section 2 or Scenario_Schema assignment
            if '# Section 2:' in line or '# Section 2 ' in line:
                # Remove the Section 2 line
                section1_lines.pop()
                break
            # Also check for Scenario_Schema assignment (this marks the end of Section 1)
            if 'Scenario_Schema' in line and '=' in line:
                break

    # If we didn't find Section 1 marker, try to find Scenario_Schema directly
    if not found_section1:
        for line in lines:
            section1_lines.append(line)
            if 'Scenario_Schema' in line and '=' in line:
                break

    return '\n'.join(section1_lines)


def extract_mcp_tools(tool_code: str) -> str:
    """
    Extract Section 3 (MCP Tools) from tool code.

    Args:
        tool_code: Full tool implementation code

    Returns:
        String containing only Section 3 (MCP Tools) from Section 3 marker to Section 4 marker
    """
    lines = tool_code.split('\n')
    section3_lines = []
    found_section3 = False

    for line in lines:
        # Check if we've found Section 3 marker
        if '# Section 3:' in line or '# Section 3 ' in line:
            found_section3 = True

        if found_section3:
            section3_lines.append(line)
            # Stop when we find Section 4
            if '# Section 4:' in line or '# Section 4 ' in line:
                # Remove the Section 4 line
                section3_lines.pop()
                break

    # If we didn't find Section 3 marker, try to find from FastMCP creation
    if not found_section3:
        for i, line in enumerate(lines):
            if 'FastMCP' in line and '=' in line:
                # Start from this line
                for j in range(i, len(lines)):
                    section3_lines.append(lines[j])
                    if '# Section 4:' in lines[j] or '# Section 4 ' in lines[j]:
                        section3_lines.pop()
                        break
                break

    return '\n'.join(section3_lines)


class ScenarioGen(Gen):
    """
    Scenario generator for MCP tools.

    Generates diverse test scenarios with varying complexity levels
    to thoroughly validate tool implementations.
    """

    def __init__(self, config: Optional[GenConfig] = None, logger=None):
        """
        Initialize scenario generator.

        Args:
            config: Configuration object
            logger: Optional shared logger instance
        """
        super().__init__(config, logger=logger)
        self.load_agents()

    def load_agents(self) -> None:
        """Load scenario generator agent."""
        from src.gen.env_gen import EnvGenConfig
        if isinstance(self.config, EnvGenConfig) and self.config.tool_gen_model:
            tool_model = self.get_model(self.config.tool_gen_model)
        else:
            tool_model = self.model
        self.scenario_generator = Agent(
            name="ScenarioGenerator",
            instructions=ScenarioGenerator_System_Prompt,
            model=tool_model,
        )

    async def generate_scenarios(
        self,
        mcp_server_name: str,
        tool_code: str,
        n_scenarios: Optional[int] = None,
        conversation_id: Optional[str] = None,
        start_turn_idx: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Generate n test scenarios for MCP tool validation.

        Args:
            mcp_server_name: Name of the MCP server
            tool_code: Full implementation code
            n_scenarios: Number of scenarios to generate (uses config default if None)
            conversation_id: Conversation ID for logging
            start_turn_idx: Starting turn index for logging

        Returns:
            Tuple of (List of scenario dictionaries, next turn_idx), each scenario containing:
                - scenario_id: Unique identifier
                - complexity_level: simple/medium/complex/boundary
                - description: What this scenario tests
                - scenario_data: Complete scenario dictionary

        Raises:
            ValueError: If scenario generation fails or output is invalid
        """
        from src.gen.env_gen import EnvGenConfig
        if n_scenarios is None:
            if isinstance(self.config, EnvGenConfig):
                n_scenarios = self.config.n_scenarios
            else:
                n_scenarios = 4  # default

        if conversation_id is None:
            conversation_id = f"scenario_gen_{mcp_server_name}"

        turn_idx = start_turn_idx

        # Extract only Section 1 (Pydantic models) from tool_code
        pydantic_models_code = extract_pydantic_models(tool_code)

        user_prompt = ScenarioGenerator_User_Prompt.format(
            mcp_server_name=mcp_server_name,
            tool_code=pydantic_models_code,
            n_scenarios=n_scenarios
        )

        last_error = None
        for attempt in range(2):
            try:
                output = await Runner.run(
                    self.scenario_generator,
                    input=user_prompt,
                    max_turns=self.config.max_turns
                )

                output_json = await self.log(
                    conversation_id=conversation_id,
                    idx=turn_idx,
                    agent=self.scenario_generator,
                    output=output
                )
                turn_idx += 1

                if 'scenarios' not in output_json:
                    raise ValueError(f"Missing 'scenarios' field. Keys: {list(output_json.keys())}")

                scenarios = output_json['scenarios']
                # Handle case where scenarios is a JSON string instead of a list
                # This can happen when parse_structured_output fails to parse nested JSON
                if isinstance(scenarios, str):
                    # Clean the string: remove markdown code blocks if present
                    cleaned = scenarios.strip()
                    # Remove markdown code block markers (```json or ```)
                    if cleaned.startswith('```'):
                        lines = cleaned.split('\n')
                        # Remove first line if it's a code block marker
                        if lines[0].strip().startswith('```'):
                            lines = lines[1:]
                        # Remove last line if it's a code block marker
                        if lines and lines[-1].strip() == '```':
                            lines = lines[:-1]
                        cleaned = '\n'.join(lines).strip()

                    # Try to parse as JSON
                    try:
                        scenarios = json.loads(cleaned)
                    except json.JSONDecodeError:
                        # Try to extract JSON from the string (find outermost [])
                        try:
                            start_index = cleaned.find('[')
                            end_index = cleaned.rfind(']')
                            if start_index != -1 and end_index != -1 and end_index > start_index:
                                json_str = cleaned[start_index:end_index+1]
                                scenarios = json.loads(json_str)
                            else:
                                raise ValueError(
                                    f"Scenarios is a string but cannot extract valid JSON. "
                                    f"First 200 chars: {cleaned[:200]}"
                                )
                        except (json.JSONDecodeError, ValueError) as e:
                            raise ValueError(
                                f"Scenarios is a string but not valid JSON: {str(e)[:200]}. "
                                f"Content preview: {cleaned}"
                            ) from e

                if not isinstance(scenarios, list):
                    raise ValueError(f"Scenarios must be a list, got {type(scenarios).__name__}: {scenarios}")
                if len(scenarios) == 0:
                    raise ValueError("No scenarios generated")

                # Validate structure
                required_fields = ['scenario_id', 'complexity_level', 'scenario_data']
                valid_levels = ['simple', 'medium', 'complex', 'boundary']
                for i, scenario in enumerate(scenarios):
                    if not isinstance(scenario, dict):
                        raise ValueError(f"Scenario {i} must be a dict")
                    for field in required_fields:
                        if field not in scenario:
                            raise ValueError(f"Scenario {i} missing field: {field}")
                    if scenario['complexity_level'] not in valid_levels:
                        raise ValueError(f"Invalid complexity_level: {scenario['complexity_level']}")
                    if not isinstance(scenario['scenario_data'], dict):
                        raise ValueError(f"scenario_data must be a dict")

                return scenarios, turn_idx

            except Exception as e:
                last_error = e
                if attempt == 0:
                    print(f"  ⚠ Retrying... ({str(e)[:100]})")
                else:
                    raise ValueError(f"Scenario generation failed after 2 attempts: {str(e)}") from e

        raise ValueError(f"Scenario generation failed: {str(last_error)}") from last_error

    def get_scenarios_by_complexity(
        self,
        scenarios: List[Dict[str, Any]],
        complexity_level: str
    ) -> List[Dict[str, Any]]:
        """
        Filter scenarios by complexity level.

        Args:
            scenarios: List of scenario dictionaries
            complexity_level: Target complexity level

        Returns:
            Filtered list of scenarios
        """
        return [
            s for s in scenarios
            if s['complexity_level'] == complexity_level
        ]

    def get_scenario_by_id(
        self,
        scenarios: List[Dict[str, Any]],
        scenario_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific scenario by ID.

        Args:
            scenarios: List of scenario dictionaries
            scenario_id: Target scenario ID

        Returns:
            Scenario dictionary or None if not found
        """
        for scenario in scenarios:
            if scenario['scenario_id'] == scenario_id:
                return scenario
        return None

    def save_scenarios(
        self,
        scenarios: List[Dict[str, Any]],
        file_path: str
    ) -> None:
        """
        Save scenarios to a JSON file.

        Args:
            scenarios: List of scenario dictionaries
            file_path: Path to save file
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, indent=2, ensure_ascii=False)

    def load_scenarios(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load scenarios from a JSON file.

        Args:
            file_path: Path to scenarios file

        Returns:
            List of scenario dictionaries
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            scenarios = json.load(f)

        # Validate structure
        if not isinstance(scenarios, list):
            raise ValueError("Loaded data must be a list of scenarios")

        return scenarios
