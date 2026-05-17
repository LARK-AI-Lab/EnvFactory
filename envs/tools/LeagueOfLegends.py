from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Champion(BaseModel):
    """Represents a League of Legends champion."""
    name: str = Field(..., description="Champion name")
    title: str = Field(..., description="Champion title")
    roles: List[str] = Field(default=[], description="Champion roles")
    difficulty: int = Field(..., ge=1, le=10, description="Difficulty rating 1-10")

class Item(BaseModel):
    """Represents an in-game item."""
    item_id: int = Field(..., ge=0, description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    gold: int = Field(..., ge=0, description="Gold cost")
    stats: Dict[str, Any] = Field(default={}, description="Item stats")

class ProPlayer(BaseModel):
    """Represents a professional player."""
    pro_player_name: str = Field(..., description="Player name")
    riot_id: str = Field(..., description="Riot ID")
    team: str = Field(..., description="Team name")
    region: str = Field(..., description="Competitive region")

class EsportsMatch(BaseModel):
    """Represents an esports match."""
    match_id: str = Field(..., description="Match ID")
    league: str = Field(..., description="League name")
    team1: str = Field(..., description="First team")
    team2: str = Field(..., description="Second team")
    scheduled_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Scheduled time in ISO format")
    status: str = Field(..., description="Match status")

class TeamStanding(BaseModel):
    """Represents team standings."""
    rank: int = Field(..., ge=1, description="Team rank")
    team_name: str = Field(..., description="Team name")
    wins: int = Field(..., ge=0, description="Number of wins")
    losses: int = Field(..., ge=0, description="Number of losses")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage")

class LeagueScenario(BaseModel):
    """Main scenario model for League of Legends data."""
    champions: Dict[str, Champion] = Field(default={}, description="Champion data")
    items: Dict[int, Item] = Field(default={}, description="Item data")
    pro_players: Dict[str, ProPlayer] = Field(default={}, description="Pro player data")
    esports_schedule: List[EsportsMatch] = Field(default=[], description="Esports schedule")
    team_standings: Dict[str, List[TeamStanding]] = Field(default={}, description="Team standings by league")
    champion_stats: Dict[str, Dict[str, Any]] = Field(default={}, description="Champion statistics")
    summoner_profiles: Dict[str, Dict[str, Any]] = Field(default={}, description="Summoner profiles")
    match_history: Dict[str, List[Dict[str, Any]]] = Field(default={}, description="Match history")
    discounted_skins: List[Dict[str, Any]] = Field(default=[], description="Discounted skins")
    regionMap: Dict[str, str] = Field(default={
        "kr": "Korea", "na": "North America", "euw": "Europe West", "eune": "Europe Nordic",
        "br": "Brazil", "lan": "Latin America North", "las": "Latin America South", "oce": "Oceania",
        "ru": "Russia", "tr": "Turkey", "jp": "Japan", "sg": "Singapore", "th": "Thailand",
        "vn": "Vietnam", "ph": "Philippines", "tw": "Taiwan", "default": "North America"
    }, description="Region mapping")

Scenario_Schema = [Champion, Item, ProPlayer, EsportsMatch, TeamStanding, LeagueScenario]

# Section 2: Class
class LeagueOfLegendsAPI:
    def __init__(self):
        """Initialize League of Legends API with empty state."""
        self.champions: Dict[str, Champion] = {}
        self.items: Dict[int, Item] = {}
        self.pro_players: Dict[str, ProPlayer] = {}
        self.esports_schedule: List[EsportsMatch] = []
        self.team_standings: Dict[str, List[TeamStanding]] = {}
        self.champion_stats: Dict[str, Dict[str, Any]] = {}
        self.summoner_profiles: Dict[str, Dict[str, Any]] = {}
        self.match_history: Dict[str, List[Dict[str, Any]]] = {}
        self.discounted_skins: List[Dict[str, Any]] = []
        self.regionMap: Dict[str, str] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = LeagueScenario(**scenario)
        self.champions = model.champions
        self.items = model.items
        self.pro_players = model.pro_players
        self.esports_schedule = model.esports_schedule
        self.team_standings = model.team_standings
        self.champion_stats = model.champion_stats
        self.summoner_profiles = model.summoner_profiles
        self.match_history = model.match_history
        self.discounted_skins = model.discounted_skins
        self.regionMap = model.regionMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "champions": {name: champ.model_dump() for name, champ in self.champions.items()},
            "items": {item_id: item.model_dump() for item_id, item in self.items.items()},
            "pro_players": {name: player.model_dump() for name, player in self.pro_players.items()},
            "esports_schedule": [match.model_dump() for match in self.esports_schedule],
            "team_standings": {league: [team.model_dump() for team in teams] for league, teams in self.team_standings.items()},
            "champion_stats": self.champion_stats,
            "summoner_profiles": self.summoner_profiles,
            "match_history": self.match_history,
            "discounted_skins": self.discounted_skins,
            "regionMap": self.regionMap
        }

    def lol_get_champion_analysis(self, champion_name: str, lane: Optional[str] = None, region: Optional[str] = None) -> dict:
        """Retrieve detailed champion statistics and analysis."""
        if champion_name not in self.champion_stats:
            return {"champion_name": champion_name, "win_rate": 0, "pick_rate": 0, "ban_rate": 0, "builds": [], "counters": [], "synergies": []}
        
        stats = self.champion_stats[champion_name]
        return {
            "champion_name": champion_name,
            "win_rate": stats.get("win_rate", 0),
            "pick_rate": stats.get("pick_rate", 0),
            "ban_rate": stats.get("ban_rate", 0),
            "builds": stats.get("builds", []),
            "counters": stats.get("counters", []),
            "synergies": stats.get("synergies", [])
        }

    def lol_get_champion_synergies(self, champion_name: str, lane: Optional[str] = None) -> dict:
        """Retrieve champion synergy information."""
        if champion_name not in self.champion_stats:
            return {"champion_name": champion_name, "synergies": []}
        
        stats = self.champion_stats[champion_name]
        return {
            "champion_name": champion_name,
            "synergies": stats.get("synergies", [])
        }

    def lol_get_lane_matchup_guide(self, lane: str, champion_name: str, enemy_champion: Optional[str] = None) -> dict:
        """Retrieve lane matchup guide."""
        if champion_name not in self.champion_stats:
            return {"lane": lane, "champion_name": champion_name, "matchups": []}
        
        stats = self.champion_stats[champion_name]
        return {
            "lane": lane,
            "champion_name": champion_name,
            "matchups": stats.get("matchups", {}).get(lane, [])
        }

    def lol_list_champion_details(self, champion_names: List[str]) -> dict:
        """Retrieve detailed champion information."""
        champions = []
        for name in champion_names[:10]:
            if name in self.champions:
                champ = self.champions[name]
                champions.append({
                    "name": champ.name,
                    "title": champ.title,
                    "roles": champ.roles,
                    "difficulty": champ.difficulty,
                    "abilities": self.champion_stats.get(name, {}).get("abilities", []),
                    "tips": self.champion_stats.get(name, {}).get("tips", []),
                    "lore": self.champion_stats.get(name, {}).get("lore", ""),
                    "stats": self.champion_stats.get(name, {}).get("stats", {})
                })
        return {"champions": champions}

    def lol_list_champion_leaderboard(self, lane: Optional[str] = None, region: Optional[str] = None, tier: Optional[str] = None, limit: Optional[int] = None) -> dict:
        """Retrieve champion leaderboard rankings."""
        leaderboard = []
        for name, stats in self.champion_stats.items():
            if "leaderboard" in stats:
                entry = {
                    "rank": stats["leaderboard"].get("rank", 0),
                    "champion_name": name,
                    "win_rate": stats.get("win_rate", 0),
                    "pick_rate": stats.get("pick_rate", 0),
                    "ban_rate": stats.get("ban_rate", 0)
                }
                leaderboard.append(entry)
        
        leaderboard.sort(key=lambda x: x["rank"])
        if limit:
            leaderboard = leaderboard[:limit]
        
        return {"leaderboard": leaderboard}

    def lol_list_champions(self, limit: Optional[int] = None) -> dict:
        """Retrieve list of all champions."""
        champions = []
        for name, champ in self.champions.items():
            champions.append({
                "name": champ.name,
                "title": champ.title,
                "roles": champ.roles,
                "difficulty": champ.difficulty
            })
        
        if limit:
            champions = champions[:limit]
        
        return {"champions": champions}

    def lol_list_lane_meta_champions(self, lane: str, region: Optional[str] = None, tier: Optional[str] = None) -> dict:
        """Retrieve current meta champions for a specific lane."""
        meta_champions = []
        for name, stats in self.champion_stats.items():
            if "meta" in stats and lane in stats["meta"]:
                meta_champions.append({
                    "champion_name": name,
                    "tier": stats["meta"][lane].get("tier", "C"),
                    "win_rate": stats.get("win_rate", 0),
                    "pick_rate": stats.get("pick_rate", 0),
                    "ban_rate": stats.get("ban_rate", 0),
                    "kda": stats["meta"][lane].get("kda", 0)
                })
        
        return {"lane": lane, "champions": meta_champions}

    def lol_get_summoner_game_detail(self, summoner_name: str, game_id: str, region: str) -> dict:
        """Retrieve detailed game information."""
        key = f"{summoner_name}:{region}"
        if key not in self.match_history:
            return {"game_id": game_id, "game_mode": "", "duration": 0, "players": []}
        
        for match in self.match_history[key]:
            if match.get("game_id") == game_id:
                return {
                    "game_id": game_id,
                    "game_mode": match.get("game_mode", ""),
                    "duration": match.get("duration", 0),
                    "players": match.get("players", [])
                }
        
        return {"game_id": game_id, "game_mode": "", "duration": 0, "players": []}

    def lol_get_summoner_profile(self, summoner_name: str, region: str) -> dict:
        """Retrieve summoner profile information."""
        key = f"{summoner_name}:{region}"
        if key not in self.summoner_profiles:
            return {
                "summoner_name": summoner_name,
                "rank": "",
                "tier": "",
                "lp": 0,
                "win_rate": 0,
                "champion_pool": []
            }
        
        return self.summoner_profiles[key]

    def lol_list_summoner_matches(self, summoner_name: str, region: str, limit: Optional[int] = None) -> dict:
        """Retrieve recent match history for a summoner."""
        key = f"{summoner_name}:{region}"
        if key not in self.match_history:
            return {"matches": []}
        
        matches = self.match_history[key]
        if limit:
            matches = matches[:limit]
        
        return {"matches": matches}

    def lol_list_discounted_skins(self, limit: Optional[int] = None) -> dict:
        """Retrieve currently discounted champion skins."""
        skins = self.discounted_skins
        if limit:
            skins = skins[:limit]
        
        return {"skins": skins}

    def lol_list_items(self, limit: Optional[int] = None) -> dict:
        """Retrieve list of all in-game items."""
        items = []
        for item_id, item in self.items.items():
            items.append({
                "item_id": item.item_id,
                "name": item.name,
                "description": item.description,
                "gold": item.gold,
                "stats": item.stats
            })
        
        if limit:
            items = items[:limit]
        
        return {"items": items}

    def lol_get_pro_player_riot_id(self, pro_player_name: str) -> dict:
        """Retrieve Riot ID and team information for a professional player."""
        if pro_player_name not in self.pro_players:
            return {
                "pro_player_name": pro_player_name,
                "riot_id": "",
                "team": "",
                "region": ""
            }
        
        player = self.pro_players[pro_player_name]
        return {
            "pro_player_name": player.pro_player_name,
            "riot_id": player.riot_id,
            "team": player.team,
            "region": player.region
        }

    def lol_esports_list_schedules(self, league: Optional[str] = None, region: Optional[str] = None, limit: Optional[int] = None) -> dict:
        """Retrieve upcoming esports match schedules."""
        schedules = []
        for match in self.esports_schedule:
            if league and match.league != league:
                continue
            if region and match.region != region:
                continue
            
            schedules.append({
                "match_id": match.match_id,
                "league": match.league,
                "team1": match.team1,
                "team2": match.team2,
                "scheduled_time": match.scheduled_time,
                "status": match.status
            })
        
        if limit:
            schedules = schedules[:limit]
        
        return {"schedules": schedules}

    def lol_esports_list_team_standings(self, league: str, region: Optional[str] = None) -> dict:
        """Retrieve team standings for an esports league."""
        if league not in self.team_standings:
            return {"standings": []}
        
        standings = []
        for team in self.team_standings[league]:
            standings.append({
                "rank": team.rank,
                "team_name": team.team_name,
                "wins": team.wins,
                "losses": team.losses,
                "win_rate": team.win_rate
            })
        
        return {"standings": standings}

# Section 3: MCP Tools
mcp = FastMCP(name="LeagueOfLegends")
api = LeagueOfLegendsAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the League of Legends API.
    
    Args:
        scenario (dict): Scenario dictionary matching LeagueScenario schema.
    
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
    """
    Save current League of Legends state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def lol_get_champion_analysis(champion_name: str, lane: Optional[str] = None, region: Optional[str] = None) -> dict:
    """
    Retrieve detailed champion statistics including win/pick/ban rates, optimal builds, counters, and synergies.
    
    Args:
        champion_name (str): The name of the champion to analyze.
        lane (str) [Optional]: The lane position to filter by.
        region (str) [Optional]: The server region code to filter by.
    
    Returns:
        champion_analysis (dict): Detailed champion statistics and analysis.
    """
    try:
        if not champion_name or not isinstance(champion_name, str):
            raise ValueError("Champion name must be a non-empty string")
        return api.lol_get_champion_analysis(champion_name, lane, region)
    except Exception as e:
        raise e

@mcp.tool()
def lol_get_champion_synergies(champion_name: str, lane: Optional[str] = None) -> dict:
    """
    Retrieve champion synergy information showing which champions pair well together.
    
    Args:
        champion_name (str): The name of the champion to analyze.
        lane (str) [Optional]: The lane position to filter by.
    
    Returns:
        synergies (dict): Champion synergy information.
    """
    try:
        if not champion_name or not isinstance(champion_name, str):
            raise ValueError("Champion name must be a non-empty string")
        return api.lol_get_champion_synergies(champion_name, lane)
    except Exception as e:
        raise e

@mcp.tool()
def lol_get_lane_matchup_guide(lane: str, champion_name: str, enemy_champion: Optional[str] = None) -> dict:
    """
    Retrieve lane matchup guide providing win rates and difficulty ratings.
    
    Args:
        lane (str): The lane position for the matchup analysis.
        champion_name (str): The name of the champion to analyze.
        enemy_champion (str) [Optional]: Specific enemy champion to analyze against.
    
    Returns:
        matchup_guide (dict): Lane matchup information.
    """
    try:
        if not lane or not isinstance(lane, str):
            raise ValueError("Lane must be a non-empty string")
        if not champion_name or not isinstance(champion_name, str):
            raise ValueError("Champion name must be a non-empty string")
        return api.lol_get_lane_matchup_guide(lane, champion_name, enemy_champion)
    except Exception as e:
        raise e

@mcp.tool()
def lol_list_champion_details(champion_names: List[str]) -> dict:
    """
    Retrieve detailed champion information including abilities, tips, lore, and stats.
    
    Args:
        champion_names (List[str]): List of champion names to retrieve details for (max 10).
    
    Returns:
        champion_details (dict): Detailed information for requested champions.
    """
    try:
        if not isinstance(champion_names, list) or len(champion_names) == 0:
            raise ValueError("Champion names must be a non-empty list")
        if len(champion_names) > 10:
            raise ValueError("Maximum 10 champions can be requested at once")
        return api.lol_list_champion_details(champion_names)
    except Exception as e:
        raise e

@mcp.tool()
def lol_list_champion_leaderboard(lane: Optional[str] = None, region: Optional[str] = None, tier: Optional[str] = None, limit: Optional[int] = None) -> dict:
    """
    Retrieve champion leaderboard rankings with performance metrics.
    
    Args:
        lane (str) [Optional]: Lane position to filter by.
        region (str) [Optional]: Server region code to filter by.
        tier (str) [Optional]: Competitive tier to filter by.
        limit (int) [Optional]: Maximum number of results.
    
    Returns:
        leaderboard (dict): Ranked list of champions.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.lol_list_champion_leaderboard(lane, region, tier, limit)
    except Exception as e:
        raise e

@mcp.tool()
def lol_list_champions(limit: Optional[int] = None) -> dict:
    """
    Retrieve list of all League of Legends champions with basic metadata.
    
    Args:
        limit (int) [Optional]: Maximum number of results.
    
    Returns:
        champions (dict): List of champion metadata.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.lol_list_champions(limit)
    except Exception as e:
        raise e

@mcp.tool()
def lol_list_lane_meta_champions(lane: str, region: Optional[str] = None, tier: Optional[str] = None) -> dict:
    """
    Retrieve current meta champions for a specific lane with tier rankings and statistics.
    
    Args:
        lane (str): The lane position to analyze.
        region (str) [Optional]: Server region code to filter by.
        tier (str) [Optional]: Competitive tier to filter by.
    
    Returns:
        meta_champions (dict): Meta champions for the specified lane.
    """
    try:
        if not lane or not isinstance(lane, str):
            raise ValueError("Lane must be a non-empty string")
        return api.lol_list_lane_meta_champions(lane, region, tier)
    except Exception as e:
        raise e

@mcp.tool()
def lol_get_summoner_game_detail(summoner_name: str, game_id: str, region: str) -> dict:
    """
    Retrieve detailed information for a specific game including all players' data.
    
    Args:
        summoner_name (str): The summoner's display name.
        game_id (str): The unique game match identifier.
        region (str): The server region code.
    
    Returns:
        game_details (dict): Detailed game information.
    """
    try:
        if not summoner_name or not isinstance(summoner_name, str):
            raise ValueError("Summoner name must be a non-empty string")
        if not game_id or not isinstance(game_id, str):
            raise ValueError("Game ID must be a non-empty string")
        if not region or not isinstance(region, str):
            raise ValueError("Region must be a non-empty string")
        return api.lol_get_summoner_game_detail(summoner_name, game_id, region)
    except Exception as e:
        raise e

@mcp.tool()
def lol_get_summoner_profile(summoner_name: str, region: str) -> dict:
    """
    Retrieve summoner profile information including rank, tier, and champion pool.
    
    Args:
        summoner_name (str): The summoner's display name.
        region (str): The server region code.
    
    Returns:
        profile (dict): Summoner profile information.
    """
    try:
        if not summoner_name or not isinstance(summoner_name, str):
            raise ValueError("Summoner name must be a non-empty string")
        if not region or not isinstance(region, str):
            raise ValueError("Region must be a non-empty string")
        return api.lol_get_summoner_profile(summoner_name, region)
    except Exception as e:
        raise e

@mcp.tool()
def lol_list_summoner_matches(summoner_name: str, region: str, limit: Optional[int] = None) -> dict:
    """
    Retrieve recent match history for a summoner with per-game statistics.
    
    Args:
        summoner_name (str): The summoner's display name.
        region (str): The server region code.
        limit (int) [Optional]: Maximum number of results.
    
    Returns:
        matches (dict): List of recent matches.
    """
    try:
        if not summoner_name or not isinstance(summoner_name, str):
            raise ValueError("Summoner name must be a non-empty string")
        if not region or not isinstance(region, str):
            raise ValueError("Region must be a non-empty string")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.lol_list_summoner_matches(summoner_name, region, limit)
    except Exception as e:
        raise e

@mcp.tool()
def lol_list_discounted_skins(limit: Optional[int] = None) -> dict:
    """
    Retrieve currently discounted champion skins with pricing information.
    
    Args:
        limit (int) [Optional]: Maximum number of results.
    
    Returns:
        skins (dict): List of discounted skins.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.lol_list_discounted_skins(limit)
    except Exception as e:
        raise e

@mcp.tool()
def lol_list_items(limit: Optional[int] = None) -> dict:
    """
    Retrieve list of all in-game items with metadata and stats.
    
    Args:
        limit (int) [Optional]: Maximum number of results.
    
    Returns:
        items (dict): List of item metadata.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.lol_list_items(limit)
    except Exception as e:
        raise e

@mcp.tool()
def lol_get_pro_player_riot_id(pro_player_name: str) -> dict:
    """
    Retrieve Riot ID and team information for a professional player.
    
    Args:
        pro_player_name (str): The professional player's name or gamertag.
    
    Returns:
        player_info (dict): Professional player information.
    """
    try:
        if not pro_player_name or not isinstance(pro_player_name, str):
            raise ValueError("Pro player name must be a non-empty string")
        return api.lol_get_pro_player_riot_id(pro_player_name)
    except Exception as e:
        raise e

@mcp.tool()
def lol_esports_list_schedules(league: Optional[str] = None, region: Optional[str] = None, limit: Optional[int] = None) -> dict:
    """
    Retrieve upcoming League of Legends esports match schedules.
    
    Args:
        league (str) [Optional]: Esports league to filter by.
        region (str) [Optional]: Server region code to filter by.
        limit (int) [Optional]: Maximum number of results.
    
    Returns:
        schedules (dict): List of upcoming esports matches.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.lol_esports_list_schedules(league, region, limit)
    except Exception as e:
        raise e

@mcp.tool()
def lol_esports_list_team_standings(league: str, region: Optional[str] = None) -> dict:
    """
    Retrieve team standings for a League of Legends esports league.
    
    Args:
        league (str): The esports league to get standings for.
        region (str) [Optional]: Server region code to filter by.
    
    Returns:
        standings (dict): Ranked list of teams in the league.
    """
    try:
        if not league or not isinstance(league, str):
            raise ValueError("League must be a non-empty string")
        return api.lol_esports_list_team_standings(league, region)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()