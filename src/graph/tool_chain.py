from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json
import copy

from src.graph.tool_node import Tool

@dataclass
class ToolQueryNode:
    raw_tool_call: list[Tool]
    initial_scenario: dict = None
    steps: list[dict] = field(default_factory=list) # Trajectory
    query: str = None
    user_intent: str = None
    final_scenario: dict = None
    decision: bool = None
    accuracy: float = None
    pass_k_trace: dict[int, list] = field(default_factory=dict)
    pass_k_scenario: dict[int, dict] = field(default_factory=dict)
    pass_k_decision: dict[int, bool] = field(default_factory=dict)
    last_state: Enum = None
    _mcp_servers: list[str] = None

    @property
    def mcp_servers(self) -> list[str]:
        if self._mcp_servers is None:
            classes = set()
            for tool in self.raw_tool_call:
                class_name = tool.name.split("-")[0]
                classes.add(class_name)
            self._mcp_servers = list(classes)
        return self._mcp_servers

    def __str__(self):
        turn_desc = ""
        for step in self.steps:
            if step['role'] == 'user':
                turn_desc += f"- User: {step['content']}\n"
            elif step['role'] == 'assistant':
                turn_desc += f"- Assistant: {step['content']}\n"
            elif step['role'] == 'tool_call':
                turn_desc += f"- Tool Call: {step['content']}\n"
            elif step['role'] == 'tool_response':
                turn_desc += f"- Tool Response: {step['content']}\n"
            else:
                pass
        return turn_desc

    def deepcopy(self) -> "ToolQueryNode":
        return copy.deepcopy(self)
    
    def save(self) -> dict:
        result = {
            "raw_tool_call": [],
            "initial_scenario": self.initial_scenario,
            "steps": self.steps,
            "query": self.query,
            "final_scenario": self.final_scenario,
            "decision": self.decision,
            "accuracy": self.accuracy,
            "pass_k_trace": self.pass_k_trace,
            "pass_k_scenario": self.pass_k_scenario,
            "pass_k_decision": self.pass_k_decision,
            "mcp_servers": self._mcp_servers,
        }

        return result

    @classmethod
    def load(cls, data: dict) -> "ToolQueryNode":
        return cls(
            raw_tool_call=[],
            initial_scenario=data.get("initial_scenario"),
            steps=data.get("steps"),
            query=data.get("query"),
            final_scenario=data.get("final_scenario"),
            decision=data.get("decision"),
            accuracy=data.get("accuracy"),
            pass_k_trace=data.get("pass_k_trace", {}),
            pass_k_scenario=data.get("pass_k_scenario", {}),
            pass_k_decision=data.get("pass_k_decision", {}),
            _mcp_servers=data.get("mcp_servers"),
        )


class ToolQueryChain:
    def __init__(self, init_tool_chain: list[Tool], seed: int = None):
        self.init_tool_chain = init_tool_chain
        self.tool_chain = []
        self.seed = seed
        self.create_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.scenario = None
        self.user_tools = None
        self.user_profile = None
        self._mcp_servers = None

    def __len__(self):
        return len(self.tool_chain)

    def __getitem__(self, idx: int):
        return self.tool_chain[idx]

    def __setitem__(self, idx: int, tool_node: ToolQueryNode):
        self.tool_chain[idx] = tool_node

    def deepcopy(self) -> "ToolQueryChain":
        return copy.deepcopy(self)

    def reset_node(self, turn_idx: int):
        self.tool_chain[turn_idx] = ToolQueryNode(
            raw_tool_call = self.tool_chain[turn_idx].raw_tool_call,
            initial_scenario = self.tool_chain[turn_idx].initial_scenario,
            _mcp_servers = self.tool_chain[turn_idx]._mcp_servers,
        )

    def update_node(self, turn_idx: int, **kwargs):
        node = self.tool_chain[turn_idx]
        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)
    
    def get_conversation(self, turn_idx: int, show_history: bool = True) -> str:
        """
        Args:
            turn_idx (int): The current turn index.
            show_history (bool): Whether to show history conversation.
        """
        conversation = ""
    
        for i in range(len(self.tool_chain)):
            node = self.tool_chain[i]

            if i < turn_idx and show_history: # History
                conversation += f"[Turn {i+1}] (Previous)\n"
                conversation += f"{str(node)}\n"
            elif i == turn_idx: # Current
                conversation += f"[Turn {i+1}] (Current)\n"
                if len(node.steps) == 0:
                    for j, tool in enumerate(node.raw_tool_call):
                        conversation += f"- Target Tool Name {j+1}: {tool.name}\n"
                else:
                    conversation += f"{str(node)}\n"

        return conversation.strip()

    @property
    def mcp_servers(self) -> list[str]:
        if self._mcp_servers is None:
            classes = set()
            # First, try to get from init_tool_chain (original behavior)
            if self.init_tool_chain:
                for tool in self.init_tool_chain:
                    classes.add(tool.server)
            # If that yields nothing, fall back to tool_chain nodes
            elif self.tool_chain:
                for node in self.tool_chain:
                    if hasattr(node, 'mcp_servers') and node.mcp_servers:
                        classes.update(node.mcp_servers)
            self._mcp_servers = list(classes)
        return self._mcp_servers

    @property
    def trace(self) -> str:
        trace = ""
        for i, tool in enumerate(self.init_tool_chain):
            trace += f"## Tool {i}\n"
            trace += f"{str(tool)}\n"
        return trace
 
    def save(self, path: str) -> None:
        """Save the entire ToolQueryChain as a single JSON object"""
        chain_data = {
            "nodes": [node.save() for node in self.tool_chain],
            "seed": self.seed,
        }
        chain_data["scenario"] = self.scenario
        chain_data["user_tools"] = self.user_tools
        chain_data["user_profile"] = self.user_profile
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(chain_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, source: str | dict) -> "ToolQueryChain":
        # Load from file or dict
        if isinstance(source, str):
            with open(source, "r", encoding="utf-8") as f:
                chain_data = json.load(f)
        elif isinstance(source, dict):
            chain_data = source
        else:
            raise TypeError("Source must be a file path (str) or dictionary (dict)")

        # Extract data
        tool_chain_nodes = [
            ToolQueryNode.load(node_data) for node_data in chain_data["nodes"]
        ]
        
        # Create and initialize instance
        instance = cls.__new__(cls)
        instance.init_tool_chain = []
        instance.tool_chain = tool_chain_nodes
        instance.scenario = chain_data.get("scenario")
        instance.user_tools = chain_data.get("user_tools")
        instance.user_profile = chain_data.get("user_profile")
        instance.seed = chain_data.get("seed")
        instance.create_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        instance._mcp_servers = chain_data.get("mcp_servers")
        
        return instance