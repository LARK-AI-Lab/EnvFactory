from dataclasses import dataclass
from enum import Enum

from src.gen import GenConfig
from src.graph.tool_chain import ToolQueryChain
from src.graph.tool_graph import ToolGraph

@dataclass
class QueryGenConfig(GenConfig):
    pass_k: int = 4
    """Pass@k sampling parameter for query solver"""

    max_iterations: int = 8
    """Max iterations for QueryGen"""

    max_retry: int = 4
    """Max retry limit for QueryGen"""

    max_solve_iterations: int = 8
    """Max iterations of solving query"""

    max_refine_iterations: int = 1
    """Max iterations of refining query"""

    max_interaction_iterations: int = 5
    """Max iterations of user-assistant interactions"""

    enable_split_turns: bool = True
    """If enabled, the planner will split turns"""

    enable_query_refinement: bool = False
    """If enabled, the generated query will be refined"""

    enable_user_interaction: bool = False
    """If enabled, the user interaction will be enabled"""

    enable_user_tool_use: bool = False
    """If enabled, the user may call tools when assist explicitly request"""

    enable_user_verification: bool = False
    """If enabled, the user response will be verified"""

    enable_filteration: bool = False
    """In enabled, the selector will filter out redundant or unnessary steps"""

    save_folder: str = "data/"
    """Folder to save tool chain"""

    def __post_init__(self):
        if self.enable_user_tool_use:
            self.enable_user_interaction = True


@dataclass
class QueryGenContext:
    config: QueryGenConfig
    tool_graph: ToolGraph
    tool_chain: ToolQueryChain
    idx: int
    conversation_id: str
    k: int = 0
    user_knowledge: str = None
    user_tools: dict = None


class QueryGenState(Enum):
    Preparing = "preparing"
    Starting = "starting"
    Generating = "generating"
    Refining = "refining"
    Solving = "solving"
    Terminated = "terminated"


class QueryGen:
    """Router class for query generation"""
    def __init__(self, tool_graph: ToolGraph, config: QueryGenConfig = QueryGenConfig()):
        self.config = config
        self.tool_graph = tool_graph

        # Initialize the appropriate implementation based on config
        if config.enable_user_interaction:
            from src.gen.query_gen.query_gen_conv import QueryGenConv
            self._impl = QueryGenConv(tool_graph=tool_graph, config=config)
        else:
            from src.gen.query_gen.query_gen_non_conv import QueryGenNonConv
            self._impl = QueryGenNonConv(tool_graph=tool_graph, config=config)
    
    def __getattr__(self, name):
        """
        Delegate all attribute access to the underlying implementation.
        This allows QueryGen to behave exactly like the selected implementation.
        """
        return getattr(self._impl, name)
    
    async def gen(self, tool_chain: ToolQueryChain | str) -> ToolQueryChain:
        return await self._impl.gen(tool_chain)
