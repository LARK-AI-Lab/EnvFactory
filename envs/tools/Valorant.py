from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Agent(BaseModel):
    """Represents a Valorant agent."""
    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role (Duelist, Controller, Initiator, Sentinel)")
    description: str = Field(..., description="Agent background and playstyle description")
    abilities: List[Dict[str, Any]] = Field(default=[], description="Agent abilities list")

class Map(BaseModel):
    """Represents a Valorant map."""
    name: str = Field(..., description="Map name")
    description: str = Field(..., description="Map layout and strategic characteristics")
    location: str = Field(..., description="In-game lore location")
    site_count: int = Field(..., ge=1, le=3, description="Number of bomb sites")

class PlayerMatch(BaseModel):
    """Represents a player's match history entry."""
    match_id: str = Field(..., description="Unique match identifier")
    map: str = Field(..., description="Map name")
    agent: str = Field(..., description="Agent used by player")
    result: str = Field(..., description="Match outcome (Victory, Defeat, Draw)")
    score: str = Field(..., description="Final round score")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Match timestamp in ISO 8601 format")

class LeaderboardEntry(BaseModel):
    """Represents a leaderboard entry."""
    rank: int = Field(..., ge=1, description="Player rank position")
    player_name: str = Field(..., description="Player display name")
    rating: int = Field(..., ge=0, description="Competitive rating points")
    wins: int = Field(..., ge=0, description="Total competitive wins")
    rank_tier: str = Field(..., description="Competitive rank tier")

class AgentComposition(BaseModel):
    """Represents an agent team composition."""
    agents: List[str] = Field(..., description="List of agent names")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage")
    play_rate: float = Field(..., ge=0, le=100, description="Play rate percentage")
    description: str = Field(..., description="Composition strengths and strategy")

class AgentStats(BaseModel):
    """Represents agent performance statistics."""
    agent_name: str = Field(..., description="Agent name")
    pick_rate: float = Field(..., ge=0, le=100, description="Pick rate percentage")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage")
    avg_score: float = Field(..., ge=0, description="Average combat score")

class ValorantScenario(BaseModel):
    """Main scenario model for Valorant game data."""
    agents: Dict[str, Agent] = Field(default={}, description="Agent metadata")
    maps: Dict[str, Map] = Field(default={}, description="Map metadata")
    player_matches: Dict[str, List[PlayerMatch]] = Field(default={}, description="Player match history")
    leaderboards: Dict[str, List[LeaderboardEntry]] = Field(default={}, description="Regional leaderboards")
    agent_compositions: Dict[str, List[AgentComposition]] = Field(default={}, description="Map-specific agent compositions")
    agent_statistics: Dict[str, AgentStats] = Field(default={}, description="Agent performance statistics")

Scenario_Schema = [Agent, Map, PlayerMatch, LeaderboardEntry, AgentComposition, AgentStats, ValorantScenario]

# Section 2: Class
class ValorantAPI:
    def __init__(self):
        """Initialize Valorant API with empty state."""
        self.agents: Dict[str, Agent] = {}
        self.maps: Dict[str, Map] = {}
        self.player_matches: Dict[str, List[PlayerMatch]] = {}
        self.leaderboards: Dict[str, List[LeaderboardEntry]] = {}
        self.agent_compositions: Dict[str, List[AgentComposition]] = {}
        self.agent_statistics: Dict[str, AgentStats] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = ValorantScenario(**scenario)
        self.agents = model.agents
        self.maps = model.maps
        self.player_matches = model.player_matches
        self.leaderboards = model.leaderboards
        self.agent_compositions = model.agent_compositions
        self.agent_statistics = model.agent_statistics

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "agents": {name: agent.model_dump() for name, agent in self.agents.items()},
            "maps": {name: map_.model_dump() for name, map_ in self.maps.items()},
            "player_matches": {player: [match.model_dump() for match in matches] for player, matches in self.player_matches.items()},
            "leaderboards": {region: [entry.model_dump() for entry in entries] for region, entries in self.leaderboards.items()},
            "agent_compositions": {map_name: [comp.model_dump() for comp in comps] for map_name, comps in self.agent_compositions.items()},
            "agent_statistics": {name: stats.model_dump() for name, stats in self.agent_statistics.items()}
        }

    def list_agents(self, limit: Optional[int] = None) -> dict:
        """Retrieve metadata for Valorant agents."""
        agents_list = list(self.agents.values())
        if limit:
            agents_list = agents_list[:limit]
        return {"agents": [agent.model_dump() for agent in agents_list]}

    def list_maps(self, limit: Optional[int] = None) -> dict:
        """Retrieve metadata for Valorant maps."""
        maps_list = list(self.maps.values())
        if limit:
            maps_list = maps_list[:limit]
        return {"maps": [map_.model_dump() for map_ in maps_list]}

    def list_player_matches(self, player_name: str, region: Optional[str] = None, limit: Optional[int] = None) -> dict:
        """Retrieve match history for a specific player."""
        matches = self.player_matches.get(player_name, [])
        if region:
            matches = [match for match in matches if match.map in self.maps]
        if limit:
            matches = matches[:limit]
        return {"matches": [match.model_dump() for match in matches]}

    def list_leaderboard(self, region: str, limit: Optional[int] = None) -> dict:
        """Retrieve competitive leaderboard for a region."""
        entries = self.leaderboards.get(region, [])
        if limit:
            entries = entries[:limit]
        return {"leaderboard": [entry.model_dump() for entry in entries]}

    def list_agent_compositions_for_map(self, map_name: str) -> dict:
        """Retrieve recommended agent compositions for a specific map."""
        compositions = self.agent_compositions.get(map_name, [])
        return {"compositions": [comp.model_dump() for comp in compositions]}

    def list_agent_statistics(self, agent_name: Optional[str] = None, map_name: Optional[str] = None) -> dict:
        """Retrieve performance statistics for agents."""
        stats_list = []
        if agent_name:
            if agent_name in self.agent_statistics:
                stats_list = [self.agent_statistics[agent_name]]
        else:
            stats_list = list(self.agent_statistics.values())
        
        if map_name and map_name in self.maps:
            pass
        
        return {"statistics": [stats.model_dump() for stats in stats_list]}

# Section 3: MCP Tools
mcp = FastMCP(name="Valorant")
api = ValorantAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the Valorant API.
    
    Args:
        scenario (dict): Scenario dictionary matching ValorantScenario schema.
    
    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current Valorant state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def valorant_list_agents(limit: Optional[int] = None) -> dict:
    """Retrieve metadata for Valorant agents including roles, abilities, and descriptions.
    
    Args:
        limit (int): [Optional] Maximum number of agent records to return.
    
    Returns:
        agents (list): List of agents with metadata and ability information.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("Limit must be a positive integer")
        return api.list_agents(limit)
    except Exception as e:
        raise e

@mcp.tool()
def valorant_list_maps(limit: Optional[int] = None) -> dict:
    """Retrieve metadata for Valorant maps including descriptions, locations, and site information.
    
    Args:
        limit (int): [Optional] Maximum number of map records to return.
    
    Returns:
        maps (list): List of maps with metadata.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("Limit must be a positive integer")
        return api.list_maps(limit)
    except Exception as e:
        raise e

@mcp.tool()
def valorant_list_player_matches(player_name: str, region: Optional[str] = None, limit: Optional[int] = None) -> dict:
    """Retrieve the match history for a specific Valorant player.
    
    Args:
        player_name (str): Display name of the player.
        region (str): [Optional] Region code to filter matches by.
        limit (int): [Optional] Maximum number of match records to return.
    
    Returns:
        matches (list): List of matches from the player's match history.
    """
    try:
        if not player_name or not isinstance(player_name, str):
            raise ValueError("Player name must be a non-empty string")
        if region is not None and not isinstance(region, str):
            raise ValueError("Region must be a string")
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("Limit must be a positive integer")
        return api.list_player_matches(player_name, region, limit)
    except Exception as e:
        raise e

@mcp.tool()
def valorant_list_leaderboard(region: str, limit: Optional[int] = None) -> dict:
    """Retrieve the competitive leaderboard rankings for a specific Valorant region.
    
    Args:
        region (str): Region code (ap, br, eu, kr, latam, na).
        limit (int): [Optional] Maximum number of leaderboard entries to return.
    
    Returns:
        leaderboard (list): List of ranked player entries for the region.
    """
    try:
        if not region or not isinstance(region, str):
            raise ValueError("Region must be a non-empty string")
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("Limit must be a positive integer")
        return api.list_leaderboard(region, limit)
    except Exception as e:
        raise e

@mcp.tool()
def valorant_list_agent_compositions_for_map(map_name: str) -> dict:
    """Retrieve recommended agent team compositions for a specific Valorant map.
    
    Args:
        map_name (str): Name of the Valorant map.
    
    Returns:
        compositions (list): List of agent team compositions with performance metrics.
    """
    try:
        if not map_name or not isinstance(map_name, str):
            raise ValueError("Map name must be a non-empty string")
        return api.list_agent_compositions_for_map(map_name)
    except Exception as e:
        raise e

@mcp.tool()
def valorant_list_agent_statistics(agent_name: Optional[str] = None, map_name: Optional[str] = None) -> dict:
    """Retrieve performance statistics and meta data for Valorant agents.
    
    Args:
        agent_name (str): [Optional] Specific agent to filter statistics for.
        map_name (str): [Optional] Map to filter agent statistics for.
    
    Returns:
        statistics (list): List of agent performance statistics.
    """
    try:
        if agent_name is not None and not isinstance(agent_name, str):
            raise ValueError("Agent name must be a string")
        if map_name is not None and not isinstance(map_name, str):
            raise ValueError("Map name must be a string")
        return api.list_agent_statistics(agent_name, map_name)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()