from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP


# Section 1: Schema
class GamePrice(BaseModel):
    """Represents pricing information for a game."""
    amount: float = Field(..., ge=0, description="Present sale price in the store's default currency.")
    discount_percent: int = Field(..., ge=0, le=100, description="Active discount percentage (0 if none).")


class SteamGame(BaseModel):
    """Represents a Steam game entry."""
    app_id: int = Field(..., ge=0, description="The unique Steam application identifier for this game.")
    name: str = Field(..., description="The official title of the game.")
    current_players: int = Field(..., ge=0, description="Live concurrent player count on Steam.")
    price: GamePrice = Field(..., description="Current pricing and discount information.")
    description: str = Field(default="", description="Full textual description or synopsis of the game.")
    store_url: str = Field(default="", description="Direct link to the game's page on the store.")
    rating: float = Field(default=0.0, ge=0, le=100, description="Aggregate user rating on the store (scale 0-100).")
    trending_score: float = Field(default=0.0, ge=0, description="Trending momentum score for ranking.")


class EpicGame(BaseModel):
    """Represents an Epic Games Store game entry."""
    app_id: int = Field(..., ge=0, description="The unique Epic application identifier for this game.")
    name: str = Field(..., description="The official title of the game.")
    current_players: int = Field(..., ge=0, description="Live concurrent player count on Epic.")
    price: GamePrice = Field(..., description="Current pricing and discount information.")
    description: str = Field(default="", description="Full textual description or synopsis of the game.")
    store_url: str = Field(default="", description="Direct link to the game's page on the store.")
    rating: float = Field(default=0.0, ge=0, le=100, description="Aggregate user rating on the store (scale 0-100).")
    trending_score: float = Field(default=0.0, ge=0, description="Trending momentum score for ranking.")
    is_free_now: bool = Field(default=False, description="Whether the game is currently free to claim.")
    is_upcoming_free: bool = Field(default=False, description="Whether the game will be free soon.")


class GameTrendingScenario(BaseModel):
    """Main scenario model for GameTrending server."""
    steam_games: Dict[str, Any] = Field(default_factory=lambda: {
        "730": {"app_id": 730, "name": "Counter-Strike 2", "current_players": 1250000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "The next evolution of Counter-Strike, featuring updated graphics and refined gameplay.", "store_url": "https://store.steampowered.com/app/730", "rating": 85.0, "trending_score": 98.5},
        "570": {"app_id": 570, "name": "Dota 2", "current_players": 680000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "A competitive game of action and strategy, played both professionally and casually.", "store_url": "https://store.steampowered.com/app/570", "rating": 82.0, "trending_score": 92.0},
        "578080": {"app_id": 578080, "name": "PUBG: BATTLEGROUNDS", "current_players": 450000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "Land, loot, and outlast in the original battle royale experience.", "store_url": "https://store.steampowered.com/app/578080", "rating": 68.0, "trending_score": 85.0},
        "1172470": {"app_id": 1172470, "name": "Apex Legends", "current_players": 320000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "A free-to-play hero shooter where legendary characters battle for glory.", "store_url": "https://store.steampowered.com/app/1172470", "rating": 78.0, "trending_score": 88.0},
        "252490": {"app_id": 252490, "name": "Rust", "current_players": 125000, "price": {"amount": 39.99, "discount_percent": 25}, "description": "The only aim in Rust is to survive. Everything wants you to die.", "store_url": "https://store.steampowered.com/app/252490", "rating": 86.0, "trending_score": 82.0},
        "1245620": {"app_id": 1245620, "name": "Elden Ring", "current_players": 95000, "price": {"amount": 59.99, "discount_percent": 35}, "description": "Rise, Tarnished, and be guided by grace to brandish the power of the Elden Ring.", "store_url": "https://store.steampowered.com/app/1245620", "rating": 94.0, "trending_score": 95.0},
        "892970": {"app_id": 892970, "name": "Valheim", "current_players": 45000, "price": {"amount": 19.99, "discount_percent": 0}, "description": "A brutal exploration and survival game for 1-10 players set in a procedurally-generated purgatory.", "store_url": "https://store.steampowered.com/app/892970", "rating": 95.0, "trending_score": 78.0},
        "1091500": {"app_id": 1091500, "name": "Cyberpunk 2077", "current_players": 72000, "price": {"amount": 59.99, "discount_percent": 50}, "description": "An open-world, action-adventure RPG set in the megalopolis of Night City.", "store_url": "https://store.steampowered.com/app/1091500", "rating": 76.0, "trending_score": 89.0},
        "413150": {"app_id": 413150, "name": "Stardew Valley", "current_players": 38000, "price": {"amount": 14.99, "discount_percent": 0}, "description": "You've inherited your grandfather's old farm plot in Stardew Valley.", "store_url": "https://store.steampowered.com/app/413150", "rating": 97.0, "trending_score": 72.0},
        "1599340": {"app_id": 1599340, "name": "Lost Ark", "current_players": 85000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "Embark on an odyssey for the Lost Ark in a vast, vibrant world.", "store_url": "https://store.steampowered.com/app/1599340", "rating": 71.0, "trending_score": 80.0},
        "271590": {"app_id": 271590, "name": "Grand Theft Auto V", "current_players": 145000, "price": {"amount": 29.99, "discount_percent": 60}, "description": "Grand Theft Auto V for PC offers players the option to explore the award-winning world of Los Santos.", "store_url": "https://store.steampowered.com/app/271590", "rating": 85.0, "trending_score": 75.0},
        "1938090": {"app_id": 1938090, "name": "Call of Duty", "current_players": 110000, "price": {"amount": 69.99, "discount_percent": 0}, "description": "The iconic first-person shooter franchise returns with new content.", "store_url": "https://store.steampowered.com/app/1938090", "rating": 72.0, "trending_score": 86.0}
    }, description="Steam games database with app_id as string key")
    
    epic_games: Dict[str, Any] = Field(default_factory=lambda: {
        "9d2d0eb64d5c44529cece33fe2a46482": {"app_id": 100001, "name": "Fortnite", "current_players": 2500000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "Battle Royale, Creative, and Save the World modes in one game.", "store_url": "https://store.epicgames.com/en-US/p/fortnite", "rating": 82.0, "trending_score": 99.0, "is_free_now": False, "is_upcoming_free": False},
        "fn_rocket_league": {"app_id": 100002, "name": "Rocket League", "current_players": 450000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "Soccer meets driving in this physics-based multiplayer game.", "store_url": "https://store.epicgames.com/en-US/p/rocket-league", "rating": 88.0, "trending_score": 90.0, "is_free_now": False, "is_upcoming_free": False},
        "fn_fall_guys": {"app_id": 100003, "name": "Fall Guys", "current_players": 180000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "Stumble through chaotic obstacle courses with up to 60 players.", "store_url": "https://store.epicgames.com/en-US/p/fall-guys", "rating": 80.0, "trending_score": 85.0, "is_free_now": False, "is_upcoming_free": False},
        "fn_genshin": {"app_id": 100004, "name": "Genshin Impact", "current_players": 320000, "price": {"amount": 0.0, "discount_percent": 0}, "description": "Step into Teyvat, a vast world teeming with life and flowing with elemental energy.", "store_url": "https://store.epicgames.com/en-US/p/genshin-impact", "rating": 84.0, "trending_score": 93.0, "is_free_now": False, "is_upcoming_free": False},
        "fn_alan_wake": {"app_id": 100005, "name": "Alan Wake 2", "current_players": 25000, "price": {"amount": 59.99, "discount_percent": 40}, "description": "A survival horror game that blurs the boundaries between fiction and reality.", "store_url": "https://store.epicgames.com/en-US/p/alan-wake-2", "rating": 91.0, "trending_score": 88.0, "is_free_now": False, "is_upcoming_free": False},
        "fn_death_stranding": {"app_id": 100006, "name": "Death Stranding", "current_players": 8000, "price": {"amount": 39.99, "discount_percent": 0}, "description": "From legendary game creator Hideo Kojima comes a genre-defying experience.", "store_url": "https://store.epicgames.com/en-US/p/death-stranding", "rating": 86.0, "trending_score": 65.0, "is_free_now": True, "is_upcoming_free": False},
        "fn_control": {"app_id": 100007, "name": "Control", "current_players": 5000, "price": {"amount": 29.99, "discount_percent": 0}, "description": "A supernatural third-person action-adventure game.", "store_url": "https://store.epicgames.com/en-US/p/control", "rating": 87.0, "trending_score": 60.0, "is_free_now": True, "is_upcoming_free": False},
        "fn_hades": {"app_id": 100008, "name": "Hades", "current_players": 15000, "price": {"amount": 24.99, "discount_percent": 0}, "description": "Defy the god of the dead as you hack and slash your way out of the Underworld.", "store_url": "https://store.epicgames.com/en-US/p/hades", "rating": 96.0, "trending_score": 75.0, "is_free_now": False, "is_upcoming_free": True},
        "fn_celeste": {"app_id": 100009, "name": "Celeste", "current_players": 3000, "price": {"amount": 19.99, "discount_percent": 0}, "description": "Help Madeline survive her inner demons on her journey to the top of Celeste Mountain.", "store_url": "https://store.epicgames.com/en-US/p/celeste", "rating": 94.0, "trending_score": 55.0, "is_free_now": False, "is_upcoming_free": True},
        "fn_disco_elysium": {"app_id": 100010, "name": "Disco Elysium", "current_players": 4500, "price": {"amount": 39.99, "discount_percent": 50}, "description": "A groundbreaking open world role playing game with an insane amount of choice.", "store_url": "https://store.epicgames.com/en-US/p/disco-elysium", "rating": 92.0, "trending_score": 70.0, "is_free_now": False, "is_upcoming_free": False},
        "fn_sifu": {"app_id": 100011, "name": "Sifu", "current_players": 12000, "price": {"amount": 39.99, "discount_percent": 25}, "description": "A third-person action game featuring intense hand-to-hand combat.", "store_url": "https://store.epicgames.com/en-US/p/sifu", "rating": 85.0, "trending_score": 78.0, "is_free_now": False, "is_upcoming_free": False},
        "fn_hitman3": {"app_id": 100012, "name": "Hitman 3", "current_players": 9000, "price": {"amount": 59.99, "discount_percent": 70}, "description": "Death Awaits. Agent 47 returns in HITMAN 3, the dramatic conclusion to the World of Assassination trilogy.", "store_url": "https://store.epicgames.com/en-US/p/hitman-3", "rating": 88.0, "trending_score": 72.0, "is_free_now": False, "is_upcoming_free": False}
    }, description="Epic Games database with internal key")


Scenario_Schema = [GamePrice, SteamGame, EpicGame, GameTrendingScenario]


# Section 2: Class
class GameTrendingAPI:
    def __init__(self):
        """Initialize GameTrending API with empty state."""
        self.steam_games: Dict[str, Any] = {}
        self.epic_games: Dict[str, Any] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = GameTrendingScenario(**scenario)
        self.steam_games = model.steam_games
        self.epic_games = model.epic_games

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "steam_games": self.steam_games,
            "epic_games": self.epic_games
        }

    def get_steam_trending_games(self, limit: int = 5) -> dict:
        """Fetch currently trending Steam titles ranked by trending score."""
        games_list = list(self.steam_games.values())
        sorted_games = sorted(games_list, key=lambda x: x.get("trending_score", 0), reverse=True)
        limited_games = sorted_games[:limit]
        
        result_games = []
        for game in limited_games:
            result_games.append({
                "app_id": game["app_id"],
                "name": game["name"],
                "current_players": game["current_players"],
                "price": {
                    "amount": game["price"]["amount"],
                    "discount_percent": game["price"]["discount_percent"]
                }
            })
        
        return {"games": result_games}

    def get_steam_most_played(self, limit: int = 5) -> dict:
        """Retrieve real-time top Steam games ordered by current concurrent player count."""
        games_list = list(self.steam_games.values())
        sorted_games = sorted(games_list, key=lambda x: x.get("current_players", 0), reverse=True)
        limited_games = sorted_games[:limit]
        
        result_games = []
        for game in limited_games:
            result_games.append({
                "app_id": game["app_id"],
                "name": game["name"],
                "current_players": game["current_players"]
            })
        
        return {"games": result_games}

    def get_epic_free_games(self, include_upcoming: bool = True) -> dict:
        """List currently free and upcoming free titles on the Epic Games Store."""
        current_games = []
        upcoming_games = []
        
        for game in self.epic_games.values():
            if game.get("is_free_now", False):
                current_games.append({
                    "app_id": game["app_id"],
                    "name": game["name"]
                })
            if include_upcoming and game.get("is_upcoming_free", False):
                upcoming_games.append({
                    "app_id": game["app_id"],
                    "name": game["name"]
                })
        
        result = {"current_games": current_games}
        if include_upcoming:
            result["upcoming_games"] = upcoming_games
        
        return result

    def get_epic_trending_games(self, limit: int = 5) -> dict:
        """Fetch trending titles on Epic Games Store driven by sales and community engagement."""
        games_list = list(self.epic_games.values())
        sorted_games = sorted(games_list, key=lambda x: x.get("trending_score", 0), reverse=True)
        limited_games = sorted_games[:limit]
        
        result_games = []
        for game in limited_games:
            result_games.append({
                "app_id": game["app_id"],
                "name": game["name"],
                "current_players": game["current_players"],
                "price": {
                    "amount": game["price"]["amount"],
                    "discount_percent": game["price"]["discount_percent"]
                }
            })
        
        return {"games": result_games}

    def get_app_id(self, game_name: str, platform: Optional[str] = None) -> dict:
        """Search for a game's application identifier across Steam and Epic by title."""
        matches = []
        search_term = game_name.lower()
        
        if platform is None or platform == "steam":
            for game in self.steam_games.values():
                if search_term in game["name"].lower():
                    matches.append({
                        "app_id": game["app_id"],
                        "name": game["name"],
                        "platform": "steam",
                        "store_url": game.get("store_url", "")
                    })
        
        if platform is None or platform == "epic":
            for game in self.epic_games.values():
                if search_term in game["name"].lower():
                    matches.append({
                        "app_id": game["app_id"],
                        "name": game["name"],
                        "platform": "epic",
                        "store_url": game.get("store_url", "")
                    })
        
        return {"matches": matches}

    def get_game_details(self, app_id: int) -> dict:
        """Retrieve rich metadata for a specific game using its application identifier."""
        for game in self.steam_games.values():
            if game["app_id"] == app_id:
                return {
                    "app_id": game["app_id"],
                    "name": game["name"],
                    "description": game.get("description", ""),
                    "price": {
                        "amount": game["price"]["amount"],
                        "discount_percent": game["price"]["discount_percent"]
                    },
                    "store_url": game.get("store_url", ""),
                    "rating": game.get("rating", 0.0),
                    "platform": "steam"
                }
        
        for game in self.epic_games.values():
            if game["app_id"] == app_id:
                return {
                    "app_id": game["app_id"],
                    "name": game["name"],
                    "description": game.get("description", ""),
                    "price": {
                        "amount": game["price"]["amount"],
                        "discount_percent": game["price"]["discount_percent"]
                    },
                    "store_url": game.get("store_url", ""),
                    "rating": game.get("rating", 0.0),
                    "platform": "epic"
                }
        
        return {}


# Section 3: MCP Tools
mcp = FastMCP(name="GameTrending")
api = GameTrendingAPI()


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the GameTrending API.
    
    Args:
        scenario (dict): Scenario dictionary matching GameTrendingScenario schema.
    
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
    Save current GameTrending state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e


@mcp.tool()
def get_steam_trending_games(limit: int = 5) -> dict:
    """
    Fetch currently trending Steam titles ranked by real-time sales, player activity, and community buzz.
    
    Args:
        limit (int): Maximum number of trending games to return (1-10). Defaults to 5. [Optional]
    
    Returns:
        games (list): List of trending Steam games sorted by current momentum. Each game contains:
            - app_id (int): The unique Steam application identifier for this game.
            - name (str): The official title of the game.
            - current_players (int): Live concurrent player count on Steam.
            - price (dict): Current pricing and discount information with amount and discount_percent.
    """
    try:
        if limit is not None:
            if not isinstance(limit, int):
                raise ValueError("Limit must be an integer")
            if limit < 1 or limit > 10:
                raise ValueError("Limit must be between 1 and 10")
        return api.get_steam_trending_games(limit)
    except Exception as e:
        raise e


@mcp.tool()
def get_steam_most_played(limit: int = 5) -> dict:
    """
    Retrieve real-time top Steam games ordered by current concurrent player count.
    
    Args:
        limit (int): Maximum number of most-played games to return (1-10). Defaults to 5. [Optional]
    
    Returns:
        games (list): List of Steam games ranked by live player population. Each game contains:
            - app_id (int): The unique Steam application identifier for this game.
            - name (str): The official title of the game.
            - current_players (int): Live concurrent player count on Steam.
    """
    try:
        if limit is not None:
            if not isinstance(limit, int):
                raise ValueError("Limit must be an integer")
            if limit < 1 or limit > 10:
                raise ValueError("Limit must be between 1 and 10")
        return api.get_steam_most_played(limit)
    except Exception as e:
        raise e


@mcp.tool()
def get_epic_free_games(include_upcoming: bool = True) -> dict:
    """
    List currently free and upcoming free titles on the Epic Games Store.
    
    Args:
        include_upcoming (bool): When true, also returns games that will become free soon. Defaults to true. [Optional]
    
    Returns:
        current_games (list): Games that are free to claim right now. Each game contains:
            - app_id (int): The unique Epic application identifier for this game.
            - name (str): The official title of the game.
        upcoming_games (list): Games scheduled to be free in the near future (only present when include_upcoming is true). Each game contains:
            - app_id (int): The unique Epic application identifier for this game.
            - name (str): The official title of the game.
    """
    try:
        if include_upcoming is not None and not isinstance(include_upcoming, bool):
            raise ValueError("include_upcoming must be a boolean")
        return api.get_epic_free_games(include_upcoming)
    except Exception as e:
        raise e


@mcp.tool()
def get_epic_trending_games(limit: int = 5) -> dict:
    """
    Fetch trending titles on Epic Games Store driven by sales and community engagement.
    
    Args:
        limit (int): Maximum number of trending games to return (1-10). Defaults to 5. [Optional]
    
    Returns:
        games (list): List of trending Epic games sorted by current momentum. Each game contains:
            - app_id (int): The unique Epic application identifier for this game.
            - name (str): The official title of the game.
            - current_players (int): Live concurrent player count on Epic.
            - price (dict): Current pricing and discount information with amount and discount_percent.
    """
    try:
        if limit is not None:
            if not isinstance(limit, int):
                raise ValueError("Limit must be an integer")
            if limit < 1 or limit > 10:
                raise ValueError("Limit must be between 1 and 10")
        return api.get_epic_trending_games(limit)
    except Exception as e:
        raise e


@mcp.tool()
def get_app_id(game_name: str, platform: Optional[str] = None) -> dict:
    """
    Search for a game's application identifier across Steam and Epic by title.
    
    Args:
        game_name (str): The title of the game to look up.
        platform (str): Optional filter to restrict search to a single store. Must be 'steam' or 'epic'. [Optional]
    
    Returns:
        matches (list): Candidate games whose names match the query. Each match contains:
            - app_id (int): The unique application identifier for this game.
            - name (str): The official title of the game.
            - platform (str): Store platform hosting this title: steam or epic.
            - store_url (str): Direct link to the game's page on the store.
    """
    try:
        if not game_name or not isinstance(game_name, str):
            raise ValueError("game_name must be a non-empty string")
        if platform is not None:
            if not isinstance(platform, str):
                raise ValueError("platform must be a string")
            if platform not in ["steam", "epic"]:
                raise ValueError("platform must be 'steam' or 'epic'")
        return api.get_app_id(game_name, platform)
    except Exception as e:
        raise e


@mcp.tool()
def get_game_details(app_id: int) -> dict:
    """
    Retrieve rich metadata for a specific game using its application identifier.
    
    Args:
        app_id (int): The unique application identifier for this game.
    
    Returns:
        app_id (int): The unique application identifier for this game.
        name (str): The official title of the game.
        description (str): Full textual description or synopsis of the game.
        price (dict): Current pricing and discount information with amount and discount_percent.
        store_url (str): Direct link to the game's page on the store.
        rating (float): Aggregate user rating on the store (scale 0-100).
        platform (str): Store platform hosting this title: steam or epic.
    """
    try:
        if app_id is None:
            raise ValueError("app_id is required")
        if not isinstance(app_id, int):
            raise ValueError("app_id must be an integer")
        result = api.get_game_details(app_id)
        if not result:
            raise ValueError(f"Game with app_id {app_id} not found")
        return result
    except Exception as e:
        raise e


# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()