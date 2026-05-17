import json
import os
import re
import aiofiles
from abc import ABC, abstractmethod
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv

from agents import Agent, SQLiteSession, ModelSettings, RunContextWrapper, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from agents.items import MessageOutputItem, ToolCallItem, ToolCallOutputItem, ReasoningItem
from agents.result import RunResult

from src.manager.mcp_client_manager import MCPManager
from src.utils.logger import StructuredLogger
from src.utils.utils import parse_structured_output

load_dotenv()
set_tracing_disabled(True)

PROVIDER_MAPPING = {
    "deepseek": ("DEEPSEEK_MODEL", "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL"),
    "kimi": ("KIMI_MODEL", "KIMI_API_KEY", "KIMI_BASE_URL"),
    "qwen": ("QWEN_MODEL", "QWEN_API_KEY", "QWEN_BASE_URL"),
    "glm": ("GLM_MODEL", "GLM_API_KEY", "GLM_BASE_URL"),
    "gemini": ("GEMINI_MODEL", "GEMINI_API_KEY", "GEMINI_BASE_URL"),
    "claude": ("CLAUDE_MODEL", "CLAUDE_API_KEY", "CLAUDE_BASE_URL"),
    "openai": ("OPENAI_MODEL", "OPENAI_API_KEY", "OPENAI_BASE_URL"),
    "mimo": ("MIMO_MODEL", "MIMO_API_KEY", "MIMO_BASE_URL"),
    "minimax": ("MINIMAX_MODEL", "MINIMAX_API_KEY", "MINIMAX_BASE_URL"),
}


@dataclass
class GenConfig:

    # Basic model configuration
    model_name: str = "kimi"
    """Default model name"""

    temperature: float = 1.0
    """Model temperature parameter"""

    top_p: float = 0.95
    """Model top_p parameter"""

    presence_penalty: float = 1.5
    """Model presence penalty parameter"""

    # Shared fields
    max_turns: int = 50
    """Maximum conversation turns"""

    log_folder: str = "log/log.jsonl"
    """Log output path"""

    enable_log_thinking_content: bool = True
    """If enabled, thinking content will be logged"""

    enable_dump_token_usage: bool = False
    """If enabled, dump token usage"""

    usage_dump_path: str = "log/usage.jsonl"
    """Path to dump token usage result"""

    log_dump_path: str = "log/log.jsonl"
    """Path to dump conversation logs"""


class GenContextManager:
    """Context manager for managing agent sessions and prompts."""
    
    def __init__(self):
        self.prompts: Dict[str, Dict[str, list]] = {}
        self.sessions: Dict[str, Dict[str, SQLiteSession]] = {}

    def add_prompt(self, agent: str, request_id: str, new_prompt: str):
        """Add prompt to context."""
        if agent not in self.prompts:
            self.prompts[agent] = {}
        
        if request_id not in self.prompts[agent]:
            self.prompts[agent][request_id] = []

        self.prompts[agent][request_id].append(new_prompt)

    def get_prompt(self, agent: str, request_id: str) -> Optional[str]:
        """Get the latest prompt."""
        try:
            return self.prompts[agent][request_id][-1]
        except (KeyError, IndexError):
            return None

    def get_session(self, agent: str, session_id: str) -> SQLiteSession:
        """Get or create session."""
        if agent not in self.sessions:
            self.sessions[agent] = {}
        
        if session_id in self.sessions[agent]:
            session = self.sessions[agent][session_id]
        else:
            session = SQLiteSession(session_id=session_id)
            self.sessions[agent][session_id] = session
        
        return session
    
    async def dump_session(self, agent: str, session_id: str) -> Optional[List[dict]]:
        """Dump session content."""
        if agent not in self.sessions:
            return None
        
        if session_id not in self.sessions[agent]:
            return None
        
        session = self.sessions[agent][session_id]
        messages = []
        items = await session.get_items()
        for item in items:
            role = item.get("role")
            if role == "user":
                messages.append({'content': item['content'], 'role': item['role']})
            elif role == "assistant":
                messages.append({'content': item['content']['text'], 'role': item['role']})

        return messages
    
    def close_session(self, session_id: str) -> None:
        """Close and delete session."""
        for agent_name, agent_sessions in self.sessions.items():
            if session_id in agent_sessions:
                try:
                    agent_sessions[session_id].close()
                except Exception:
                    pass
                del self.sessions[agent_name][session_id]


class Gen(ABC):
    """
    Unified generator base class supporting QueryGen and EnvGen and their submodules.
    
    Provides:
    - Unified model configuration and initialization
    - Unified logging
    - Context management
    - Tool validation and execution (required by QueryGen)
    """
    
    def __init__(self, config: Optional[GenConfig] = None, logger: Optional[StructuredLogger] = None):
        """
        Initialize generator base class.
        
        Args:
            config: Configuration object, uses default if None
            logger: Optional shared logger instance, creates new one if None
        """
        self.config = config or GenConfig()
        self.context_manager = GenContextManager()
        self.logger = logger or StructuredLogger(log_folder=self.config.log_folder)
        self.model = self.get_model(self.config.model_name)
        self.model_settings = ModelSettings(
            temperature = self.config.temperature,
            top_p = self.config.top_p,
            presence_penalty = self.config.presence_penalty,
        )
        self.load_agents()

    def host_local_model(self, model_name: str) -> LitellmModel:
        '''Host a local model, currently only support vLLM and SGLang (with optional numeric suffix)'''
        
        # Match pattern: vllm or sglang followed by optional digits
        match = re.match(r'^(vllm|sglang)(\d*)$', model_name.lower())
        if not match:
            raise ValueError(f"Unsupported model: {model_name}. Only vLLM and SGLang are supported.")
        
        base_name, suffix = match.groups()
        suffix = suffix or ''  # Handle empty suffix case
        
        # Construct environment variable names
        base_url = os.environ.get(f'{base_name.upper()}_BASE_URL{suffix}')
        api_key = os.environ.get(f'{base_name.upper()}_API_KEY{suffix}')
        model = os.environ.get(f"{base_name.upper()}_MODEL{suffix}")
        
        if not all([base_url, api_key, model]):
            raise ValueError(
                f"Missing environment variables for {model_name}. "
                f"Expected: {base_name.upper()}_BASE_URL{suffix}, "
                f"{base_name.upper()}_API_KEY{suffix}, "
                f"{base_name.upper()}_MODEL{suffix}"
            )
        
        return LitellmModel(
            model=f"openai/{model}",
            api_key=api_key,
            base_url=base_url,
        )

    def get_model(self, model_name: Optional[str] = None) -> LitellmModel:
        """Get LiteLLM model instance based on model name."""
        model_name = model_name or self.config.model_name

        # Host local models
        if "sglang" in model_name or "vllm" in model_name:
            return self.host_local_model(model_name)

        if model_name not in PROVIDER_MAPPING:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(PROVIDER_MAPPING.keys())}")

        model_env, api_key_env, base_url_env = PROVIDER_MAPPING[model_name]
        model = os.environ.get(model_env)
        api_key = os.environ.get(api_key_env)
        base_url = os.environ.get(base_url_env)

        if not all([model, api_key, base_url]):
            missing = [name for name, val in [("model", model), ("api_key", api_key), ("base_url", base_url)] if not val]
            raise ValueError(f"Missing environment variables for {model_name}: {missing}")

        return LitellmModel(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    @abstractmethod
    def load_agents(self) -> None:
        """Load and initialize agents, must be implemented by subclasses."""
        pass

    async def dump_token_usage(self, output: RunResult, agent: Agent):
        usage = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": output.last_agent.model.model,
            "prompt_tokens": output.raw_responses[0].usage.input_tokens,
            "completion_tokens": output.raw_responses[0].usage.output_tokens,
            "total_tokens": output.raw_responses[0].usage.total_tokens,
            "agent_name": agent.name,
        }
        
        async with aiofiles.open(self.config.usage_dump_path, 'a', encoding='utf-8') as f:
            await f.write(json.dumps(usage, ensure_ascii=False) + '\n')

    async def log(
        self, conversation_id: str, idx: int, agent: Agent, output: RunResult, context: RunContextWrapper = None
    ) -> Dict[str, Any]:
        """Unified logging method for agent interactions"""
        # Dump token usage
        if self.config.enable_dump_token_usage:
            await self.dump_token_usage(output, agent)

        # Extract user input
        if isinstance(output.input, list):
            user_input = output.input[-1]['content']
        else:
            user_input = output.input

        # Extract detailed message flow
        messages = [{"user": user_input}]
        think = None
        for item in output.new_items:
            if isinstance(item, MessageOutputItem):
                messages.append({
                    "assistant": item.raw_item.content[0].text
                })
            elif isinstance(item, ReasoningItem):
                think = item.raw_item.summary[0].text
                messages.append({
                    "think": think
                })
            elif isinstance(item, ToolCallItem):
                messages.append({
                    "tool_call": {
                        "name": item.raw_item.name,
                        "arguments": item.raw_item.arguments,
                    }
                })
            elif isinstance(item, ToolCallOutputItem):
                messages.append({
                    "tool_response": item.raw_item['output']
                })


        # Parse the output
        output_json = parse_structured_output(output.final_output)

        # Take care of reasoning content
        if think and not output_json.get('think'):
            output_json['think'] = think

        # Get system prompt
        if isinstance(agent.instructions, str):
            system_prompt = agent.instructions
        elif callable(agent.instructions):
            system_prompt = agent.instructions(context=output.context_wrapper, agent=agent)
        else:
            system_prompt = "Error"
            
        # Unified log format
        content = {
            "agent": f"{agent.name}_{context.k}" if context else agent.name,
            "system": system_prompt,
            "user": user_input,
            "assistant_think": output_json.get('think') if self.config.enable_log_thinking_content else "",
            "assistant": output_json['non_think'],
        }
        await self.logger.add_log(conversation_id, idx, content)

        # Parse and return structured output
        return output_json

    def validate(self, initial_scenario: dict, tool_calls: list[dict]) -> dict:
        """
        Validate tool call sequence (used by QueryGen).
        
        Args:
            initial_scenario: Initial scenario configuration
            tool_calls: List of tool calls
            
        Returns:
            Dictionary containing tool calls, responses, and final scenario
        """
        tool_trace = {"tool_calls": [], "tool_responses": [], "final_scenario": {}}
        if len(tool_calls) == 0:
            return tool_trace

        request_id = uuid4().hex  # Create temporary request_id
        client_ids = set()

        # Load scenario
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id}"
            client_ids.add(client_id)
            tool_response = MCPManager.load_scenario(
                scenario=scenario,
                client_id=client_id,
            )
            assert "Successfully" in tool_response

        # Call tools
        for tool_call in tool_calls:
            tool_class = tool_call['name'].split("-")[0]
            client_id = f"{tool_class}-{request_id}"
            client_ids.add(client_id)
            tool_response = MCPManager.call_tool(
                tool_name=tool_call['name'],
                tool_args=tool_call['arguments'],
                client_id=client_id,
            )
            tool_trace["tool_calls"].append(tool_call)
            tool_trace['tool_responses'].append(tool_response)
        
        # Save scenario
        final_scenario = {}
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id}"
            tool_response = MCPManager.call_tool(
                client_id=client_id,
                tool_name="save_scenario",
                tool_args={},
            )
            final_scenario[mcp_server] = json.loads(tool_response)
        tool_trace['final_scenario'] = final_scenario

        # Close clients
        for client_id in list(client_ids):
            MCPManager.close_client(client_id)

        return tool_trace

    def execute(self, tool_calls: list[dict] | dict, request_id: str) -> list:
        """
        Execute tool call sequence (used by QueryGen).
        
        Args:
            tool_calls: List of tool calls
            request_id: Request ID
            
        Returns:
            List of tool responses
        """
        if isinstance(tool_calls, dict):
            tool_calls = [tool_calls]

        tool_responses = []
        for tool_call in tool_calls:
            try:
                tool_class = tool_call['name'].split("-")[0]
                tool_response = MCPManager.call_tool(
                    tool_name=tool_call['name'],
                    tool_args=tool_call['arguments'],
                    client_id=f"{tool_class}-{request_id}",
                )
                tool_responses.append(tool_response)
            except Exception as e:
                err_msg = f"Invalid tool: {tool_call}: {repr(e)}.\n"
                tool_responses.append(err_msg)

        return tool_responses


# Backward compatibility imports
# These imports maintain backward compatibility for code using the old locations.
# New code should import from src.gen.env_gen directly.
from src.gen.env_gen.types import (
    ScenarioResult as _ScenarioResult,
    ValidationReport as _ValidationReport,
    RevisionHistory as _RevisionHistory,
    EnvGenState as _EnvGenState,
    EnvGenResult as _EnvGenResult,
    CheckpointData as _CheckpointData,
)

# Re-export for backward compatibility with deprecation warning
ScenarioResult = _ScenarioResult
ValidationReport = _ValidationReport
RevisionHistory = _RevisionHistory
EnvGenState = _EnvGenState
EnvGenResult = _EnvGenResult
CheckpointData = _CheckpointData