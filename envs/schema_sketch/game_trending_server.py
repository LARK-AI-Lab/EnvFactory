# Server: GameTrending

def get_steam_trending_games(limit: int = 5) -> dict:
    """
    Get real trending games from Steam platform with live data from multiple sources. Returns games that are currently trending based on various metrics including recent sales, player activity, and community engagement.
    
    Args:
        limit (int): [Optional] Maximum number of trending games to return. Default is 5, range from 1 to 10.
        
    Returns:
        dict: A dictionary containing games (list of dicts), each game contains app_id (int), name (str), current_players (int), price (dict with amount (float), discount_percent (int)).
    """
    pass

def get_steam_most_played(limit: int = 5) -> dict:
    """
    Get real-time most played games from Steam with live player statistics from SteamCharts. Returns games ranked by current player count.
    
    Args:
        limit (int): [Optional] Maximum number of most played games to return. Default is 5, range from 1 to 10.
        
    Returns:
        dict: A dictionary containing games (list of dicts), each game contains app_id (int), name (str), current_players (int). 
    """
    pass

def get_epic_free_games(include_upcoming: bool = True) -> dict:
    """
    Get current and upcoming free games from Epic Games Store with real promotion data. Returns games that are currently free or will be free soon.
    
    Args:
        include_upcoming (bool): [Optional] Whether to include upcoming free games. Default is True. If False, only returns currently free games.
        
    Returns:
        dict: A dictionary containing current_games (list of dicts) and upcoming_games (list of dicts if include_upcoming is True), each game contains app_id (int), name (str). 
    """
    pass

def get_epic_trending_games(limit: int = 5) -> dict:
    """
    Get trending games from Epic Games Store. Returns games that are currently trending based on sales, player activity, and community engagement.
    
    Args:
        limit (int): [Optional] Maximum number of trending games to return. Default is 5, range from 1 to 10.
        
    Returns:
        dict: A dictionary containing games (list of dicts), each game contains app_id (int), name (str), price (dict with amount (float), discount_percent (int)), current_players (int).
    """
    pass

def get_app_id(game_name: str, platform: str = None) -> dict:
    """
    Get app_id for a game by its name. Searches across Steam and Epic Games Store to find matching games.
    
    Args:
        game_name (str): The name of the game to search for.
        platform (str): [Optional] Filter by platform: "steam" or "epic". If not provided, searches both platforms.
        
    Returns:
        dict: A dictionary containing matches (list of dicts), each match contains app_id (int), name (str), platform (str), store_url (str). 
    """
    pass

def get_game_details(app_id: int) -> dict:
    """
    Get comprehensive details about a specific game from Steam or Epic Games Store. Provides detailed information including description, screenshots, videos, system requirements, and community data.
    
    Args:
        app_id (int): Application ID from get_steam_trending_games, get_steam_most_played, get_epic_free_games, get_epic_trending_games, or get_app_id.
        
    Returns:
        dict: A dictionary containing app_id (int), name (str), description (str), price (dict with amount (float), discount_percent (int)), store_url (str), rating (float), platform (str).
    """
    pass

