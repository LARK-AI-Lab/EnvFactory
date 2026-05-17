# Server: Valorant

def valorant_list_agent_compositions_for_map(map_name: str) -> list:
    """
    Get agent compositions for a specific map.
    
    Args:
        map_name (str): Map name
        
    Returns:
        list: Each composition contains {
            "agents": list[str],
            "win_rate": float,
            "play_rate": float,
            "description": str
        }
    """
    pass

def valorant_list_agent_statistics(agent_name: str = None, map_name: str = None) -> list:
    """
    Get agent statistics and meta data.
    
    Args:
        agent_name (str): [Optional] Agent name filter
        map_name (str): [Optional] Map name filter
        
    Returns:
        list: Each statistic contains {
            "agent_name": str,
            "pick_rate": float,
            "win_rate": float,
            "avg_score": float
        }
    """
    pass

def valorant_list_agents(limit: int = None) -> list:
    """
    Get agent metadata with abilities and roles.
    
    Args:
        limit (int): [Optional] Max results
        
    Returns:
        list: Each agent contains {
            "name": str,
            "role": str,
            "abilities": list[dict],
            "description": str
        }
    """
    pass

def valorant_list_leaderboard(region: str, limit: int = None) -> list:
    """
    Get leaderboard by region (ap, br, eu, kr, latam, na).
    
    Args:
        region (str): Region code
        limit (int): [Optional] Max results
        
    Returns:
        list: Each entry contains {
            "rank": int,
            "player_name": str,
            "rating": int,
            "wins": int,
            "rank_tier": str
        }
    """
    pass

def valorant_list_maps(limit: int = None) -> list:
    """
    Get map metadata.
    
    Args:
        limit (int): [Optional] Max results
        
    Returns:
        list: Each map contains {
            "name": str,
            "description": str,
            "location": str,
            "site_count": int
        }
    """
    pass

def valorant_list_player_matches(player_name: str, region: str = None, limit: int = None) -> list:
    """
    Get player match history.
    
    Args:
        player_name (str): Player name
        region (str): [Optional] Region code
        limit (int): [Optional] Max results
        
    Returns:
        list: Each match contains {
            "match_id": str,
            "map": str,
            "agent": str,
            "result": str,
            "score": str,
            "created_at": str
        }
    """
    pass

