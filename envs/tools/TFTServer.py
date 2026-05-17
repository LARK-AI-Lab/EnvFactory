from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class ItemBuild(BaseModel):
    """Represents an item build recommendation for a champion."""
    item_name: str = Field(..., description="The name of the recommended TFT item")
    priority: int = Field(..., ge=1, description="Priority ranking (lower is higher priority)")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage when equipped")

class ChampionBuild(BaseModel):
    """Represents champion item build data."""
    champion_name: str = Field(..., description="The TFT champion name")
    items: List[ItemBuild] = Field(default=[], description="List of recommended items")

class PlayStyle(BaseModel):
    """Represents a TFT play style."""
    style: str = Field(..., description="The play style name")
    description: str = Field(..., description="Detailed explanation of the play style")
    recommendations: List[str] = Field(default=[], description="Strategic recommendations and tips")

class Augment(BaseModel):
    """Represents a TFT augment."""
    name: str = Field(..., description="The augment name")
    tier: str = Field(..., description="Tier classification (Silver, Gold, Prismatic)")
    description: str = Field(..., description="In-game description of the augment's effect")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage when selected")

class ChampionItemSynergy(BaseModel):
    """Represents champion synergy with a specific item."""
    champion_name: str = Field(..., description="The TFT champion name")
    synergy_score: float = Field(..., ge=0, le=10, description="Synergy score indicating how well item fits")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage when champion uses item")

class ItemCombination(BaseModel):
    """Represents an item combination recipe."""
    item1: str = Field(..., description="First base component item")
    item2: str = Field(..., description="Second base component item")
    result: str = Field(..., description="Completed item created from combining components")
    description: str = Field(..., description="Description of resulting item's effect")

class MetaDeck(BaseModel):
    """Represents a meta deck composition."""
    name: str = Field(..., description="Community name or identifier for deck")
    champions: List[str] = Field(default=[], description="List of TFT champion names in deck")
    traits: List[str] = Field(default=[], description="List of trait synergies activated")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage achieved")
    play_rate: float = Field(..., ge=0, le=100, description="Percentage of games deck is played")

def _get_default_champion_builds() -> Dict[str, ChampionBuild]:
    """Generate default champion builds data."""
    return {
        "Jinx": ChampionBuild(
            champion_name="Jinx",
            items=[
                ItemBuild(item_name="Infinity Edge", priority=1, win_rate=67.5),
                ItemBuild(item_name="Last Whisper", priority=2, win_rate=65.2),
                ItemBuild(item_name="Giant Slayer", priority=3, win_rate=63.8)
            ]
        ),
        "Yasuo": ChampionBuild(
            champion_name="Yasuo",
            items=[
                ItemBuild(item_name="Bloodthirster", priority=1, win_rate=69.1),
                ItemBuild(item_name="Titan's Resolve", priority=2, win_rate=66.7),
                ItemBuild(item_name="Quicksilver", priority=3, win_rate=64.3)
            ]
        ),
        "Ahri": ChampionBuild(
            champion_name="Ahri",
            items=[
                ItemBuild(item_name="Jeweled Gauntlet", priority=1, win_rate=68.9),
                ItemBuild(item_name="Blue Buff", priority=2, win_rate=67.4),
                ItemBuild(item_name="Rabadon's Deathcap", priority=3, win_rate=65.1)
            ]
        ),
        "Garen": ChampionBuild(
            champion_name="Garen",
            items=[
                ItemBuild(item_name="Sunfire Cape", priority=1, win_rate=64.2),
                ItemBuild(item_name="Bramble Vest", priority=2, win_rate=62.8),
                ItemBuild(item_name="Dragon's Claw", priority=3, win_rate=61.5)
            ]
        ),
        "Jhin": ChampionBuild(
            champion_name="Jhin",
            items=[
                ItemBuild(item_name="Infinity Edge", priority=1, win_rate=71.3),
                ItemBuild(item_name="Last Whisper", priority=2, win_rate=69.7),
                ItemBuild(item_name="Giant Slayer", priority=3, win_rate=68.2)
            ]
        )
    }

def _get_default_play_styles() -> Dict[str, PlayStyle]:
    """Generate default play styles data."""
    return {
        "aggro": PlayStyle(
            style="aggro",
            description="Aggressive early game strategy focused on winning streaks and maintaining board strength",
            recommendations=[
                "Roll early to upgrade 1 and 2 cost units",
                "Prioritize strong early game items like Sunfire Cape",
                "Maintain win streak by leveling aggressively",
                "Spend gold to keep board strength high"
            ]
        ),
        "economy": PlayStyle(
            style="economy",
            description="Gold-focused strategy building economy through loss streaks or interest optimization",
            recommendations=[
                "Build 50 gold quickly for maximum interest",
                "Accept loss streaks early for better carousel priority",
                "Only spend gold when it provides significant power spike",
                "Transition to strong board at level 7-8"
            ]
        ),
        "reroll": PlayStyle(
            style="reroll",
            description="Strategy focused on 3-starring low cost units by rolling at low levels",
            recommendations=[
                "Stay at level 4-5 to maximize 1-2 cost unit odds",
                "Slow roll above 50 gold to maintain economy",
                "Focus on 3-4 key units to 3-star",
                "Build items that scale well with unit upgrades"
            ]
        ),
        "fast8": PlayStyle(
            style="fast8",
            description="Rush to level 8 quickly to find 4 and 5 cost units",
            recommendations=[
                "Build economy early while maintaining health",
                "Level to 6 at 3-2, 7 at 4-1, 8 at 4-5",
                "Roll at level 8 for 4-5 cost carries",
                "Use strong mid-game units to preserve health"
            ]
        )
    }

def _get_default_augments() -> List[Augment]:
    """Generate default augments data."""
    return [
        Augment(name="Cybernetic Implants", tier="Silver", description="Your units with items gain 200 HP and 20% attack damage", win_rate=58.5),
        Augment(name="Titanic Strength", tier="Silver", description="Your units gain 15% of their maximum HP as attack damage", win_rate=59.2),
        Augment(name="Binary Airdrop", tier="Gold", description="Your champions equipped with exactly 2 items gain a random completed item", win_rate=63.7),
        Augment(name="Wise Spending", tier="Gold", description="Gain 2 experience points when you refresh the shop", win_rate=62.1),
        Augment(name="High End Shopping", tier="Prismatic", description="Champions in your shop appear as higher tier", win_rate=71.4),
        Augment(name="Level Up!", tier="Prismatic", description="When you buy experience points, gain an additional 3 points", win_rate=69.8),
        Augment(name="Windfall", tier="Silver", description="Gain 20 gold immediately", win_rate=57.3),
        Augment(name="Thrill of the Hunt", tier="Silver", description="Your units heal 400 HP on kill", win_rate=60.1),
        Augment(name="Portable Forge", tier="Gold", description="Gain an Ornn item component and 7 gold", win_rate=64.5),
        Augment(name="Sunfire Board", tier="Gold", description="At start of combat, enemies take true damage for 10 seconds", win_rate=61.9)
    ]

def _get_default_item_synergies() -> Dict[str, List[ChampionItemSynergy]]:
    """Generate default item champion synergies data."""
    return {
        "Infinity Edge": [
            ChampionItemSynergy(champion_name="Jhin", synergy_score=9.5, win_rate=71.3),
            ChampionItemSynergy(champion_name="Jinx", synergy_score=8.8, win_rate=67.5),
            ChampionItemSynergy(champion_name="Caitlyn", synergy_score=8.2, win_rate=65.1),
            ChampionItemSynergy(champion_name="Tristana", synergy_score=7.9, win_rate=63.7),
            ChampionItemSynergy(champion_name="Zeri", synergy_score=7.5, win_rate=62.3)
        ],
        "Blue Buff": [
            ChampionItemSynergy(champion_name="Ahri", synergy_score=9.8, win_rate=68.9),
            ChampionItemSynergy(champion_name="Lux", synergy_score=9.1, win_rate=66.4),
            ChampionItemSynergy(champion_name="Ziggs", synergy_score=8.5, win_rate=64.8),
            ChampionItemSynergy(champion_name="Malzahar", synergy_score=8.0, win_rate=63.2),
            ChampionItemSynergy(champion_name="Twisted Fate", synergy_score=7.7, win_rate=61.9)
        ],
        "Bloodthirster": [
            ChampionItemSynergy(champion_name="Yasuo", synergy_score=9.3, win_rate=69.1),
            ChampionItemSynergy(champion_name="Fiora", synergy_score=8.7, win_rate=66.8),
            ChampionItemSynergy(champion_name="Irelia", synergy_score=8.4, win_rate=65.5),
            ChampionItemSynergy(champion_name="Tryndamere", synergy_score=8.1, win_rate=64.2),
            ChampionItemSynergy(champion_name="Riven", synergy_score=7.8, win_rate=62.9)
        ]
    }

def _get_default_item_combinations() -> List[ItemCombination]:
    """Generate default item combinations data."""
    return [
        ItemCombination(item1="B.F. Sword", item2="B.F. Sword", result="Infinity Edge", description="Grants 75% critical strike chance and 10% critical strike damage"),
        ItemCombination(item1="Tear of the Goddess", item2="Tear of the Goddess", result="Blue Buff", description="After casting, set mana to 20. Gain 30 mana on takedown"),
        ItemCombination(item1="B.F. Sword", item2="Negatron Cloak", result="Bloodthirster", description="Grant 40% omnivamp. Once per combat at 40% HP, gain 25% max HP shield"),
        ItemCombination(item1="Chain Vest", item2="Giant's Belt", result="Sunfire Cape", description="Grant 150 bonus HP. Every 2 seconds, deal true damage to nearby enemies"),
        ItemCombination(item1="Recurve Bow", item2="Chain Vest", result="Titan's Resolve", description="Grant 2% attack damage and 2% armor and magic resist, stacking up to 25 times"),
        ItemCombination(item1="Needlessly Large Rod", item2="Sparring Gloves", result="Jeweled Gauntlet", description="Abilities can critically strike and gain 30% critical strike damage"),
        ItemCombination(item1="B.F. Sword", item2="Recurve Bow", result="Giant Slayer", description="Deal 20% bonus damage. If target has more than 1600 HP, deal 60% bonus instead"),
        ItemCombination(item1="Chain Vest", item2="Chain Vest", result="Bramble Vest", description="Neglect 50% bonus damage from all critical strikes. When struck, deal magic damage"),
        ItemCombination(item1="Negatron Cloak", item2="Negatron Cloak", result="Dragon's Claw", description="Grant 30 bonus magic resist. Reduce incoming magic damage by 30%"),
        ItemCombination(item1="Needlessly Large Rod", item2="Needlessly Large Rod", result="Rabadon's Deathcap", description="Grant 75 bonus ability power")
    ]

def _get_default_meta_decks() -> List[MetaDeck]:
    """Generate default meta decks data."""
    return [
        MetaDeck(
            name="Syphoners",
            champions=["Nasus", "Renekton", "Rakan", "Xayah", "Zeri", "Sivir", "Aatrox", "Kayle"],
            traits=["Syphoner", "Shimmerscale", "Ragewing", "Swiftshot", "Guardian"],
            win_rate=24.3,
            play_rate=18.7
        ),
        MetaDeck(
            name="Mage Guild",
            champions=["Heimerdinger", "Ryvra", "Tulsi", "Lux", "Ziggs", "Sona", "Bard", "Lulu"],
            traits=["Mage", "Guild", "Evoker", "Caretaker", "Mystic"],
            win_rate=22.1,
            play_rate=16.2
        ),
        MetaDeck(
            name="Dragonmancer",
            champions=["Lee Sin", "Karma", "Volibear", "Yasuo", "Sett", "Shen", "Swain", "Shi Oh Yu"],
            traits=["Dragonmancer", "Legendary", "Mystic", "Guardian", "Bruiser"],
            win_rate=19.8,
            play_rate=14.5
        ),
        MetaDeck(
            name="Assassins",
            champions=["Pyke", "Qiyana", "Diana", "Talom", "Akali", "Katarina", "Kha'Zix", "Zed"],
            traits=["Assassin", "Whispers", "Scalescorn", "Thief", "Mystic"],
            win_rate=18.2,
            play_rate=12.3
        ),
        MetaDeck(
            name="Cavaliers",
            champions=["Sejuani", "Lillia", "Nunu", "Hecarim", "Rell", "Yone", "Braum", "Daeja"],
            traits=["Cavalier", "Mirage", "Guardian", "Cannon", "Revel"],
            win_rate=16.7,
            play_rate=10.8
        )
    ]

class TFTScenario(BaseModel):
    """Main scenario model for TFT game data."""
    championBuildsMap: Dict[str, ChampionBuild] = Field(
        default_factory=_get_default_champion_builds,
        description="Champion item builds mapping"
    )
    playStylesMap: Dict[str, PlayStyle] = Field(
        default_factory=_get_default_play_styles,
        description="Play style recommendations mapping"
    )
    augmentsList: List[Augment] = Field(
        default_factory=_get_default_augments,
        description="List of available augments"
    )
    itemChampionSynergiesMap: Dict[str, List[ChampionItemSynergy]] = Field(
        default_factory=_get_default_item_synergies,
        description="Item champion synergies mapping"
    )
    itemCombinationsList: List[ItemCombination] = Field(
        default_factory=_get_default_item_combinations,
        description="List of item combination recipes"
    )
    metaDecksList: List[MetaDeck] = Field(
        default_factory=_get_default_meta_decks,
        description="List of current meta decks"
    )

Scenario_Schema = [ItemBuild, ChampionBuild, PlayStyle, Augment, ChampionItemSynergy, ItemCombination, MetaDeck, TFTScenario]

# Section 2: Class
class TFTServer:
    def __init__(self):
        """Initialize TFT server with empty state."""
        self.championBuildsMap: Dict[str, ChampionBuild] = {}
        self.playStylesMap: Dict[str, PlayStyle] = {}
        self.augmentsList: List[Augment] = []
        self.itemChampionSynergiesMap: Dict[str, List[ChampionItemSynergy]] = {}
        self.itemCombinationsList: List[ItemCombination] = []
        self.metaDecksList: List[MetaDeck] = []

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the server instance."""
        model = TFTScenario(**scenario)
        self.championBuildsMap = model.championBuildsMap
        self.playStylesMap = model.playStylesMap
        self.augmentsList = model.augmentsList
        self.itemChampionSynergiesMap = model.itemChampionSynergiesMap
        self.itemCombinationsList = model.itemCombinationsList
        self.metaDecksList = model.metaDecksList

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "championBuildsMap": {k: v.model_dump() for k, v in self.championBuildsMap.items()},
            "playStylesMap": {k: v.model_dump() for k, v in self.playStylesMap.items()},
            "augmentsList": [a.model_dump() for a in self.augmentsList],
            "itemChampionSynergiesMap": {k: [s.model_dump() for s in v] for k, v in self.itemChampionSynergiesMap.items()},
            "itemCombinationsList": [c.model_dump() for c in self.itemCombinationsList],
            "metaDecksList": [d.model_dump() for d in self.metaDecksList]
        }

    def tft_get_champion_item_build(self, champion_name: str) -> dict:
        """Get recommended item builds for a specific champion."""
        if champion_name not in self.championBuildsMap:
            return {"champion_name": champion_name, "items": []}
        
        build = self.championBuildsMap[champion_name]
        return {
            "champion_name": build.champion_name,
            "items": [item.model_dump() for item in build.items]
        }

    def tft_get_play_style(self, style: Optional[str] = None) -> dict:
        """Get play style recommendations and strategies."""
        if style and style in self.playStylesMap:
            play_style = self.playStylesMap[style]
            return play_style.model_dump()
        
        # Return default aggro style if no specific style requested
        default_style = self.playStylesMap.get("aggro", PlayStyle(style="aggro", description="Default aggressive style", recommendations=[]))
        return default_style.model_dump()

    def tft_list_augments(self, limit: Optional[int] = None) -> dict:
        """List TFT augments with performance statistics."""
        augments = self.augmentsList
        if limit:
            augments = augments[:limit]
        
        return {"augments": [augment.model_dump() for augment in augments]}

    def tft_list_champions_for_item(self, item_name: str) -> dict:
        """Get champion recommendations for a specific item."""
        if item_name not in self.itemChampionSynergiesMap:
            return {"champions": []}
        
        synergies = self.itemChampionSynergiesMap[item_name]
        return {"champions": [synergy.model_dump() for synergy in synergies]}

    def tft_list_item_combinations(self, limit: Optional[int] = None) -> dict:
        """List item combination recipes."""
        combinations = self.itemCombinationsList
        if limit:
            combinations = combinations[:limit]
        
        return {"combinations": [combo.model_dump() for combo in combinations]}

    def tft_list_meta_decks(self, tier: Optional[str] = None, limit: Optional[int] = None) -> dict:
        """List current meta deck compositions."""
        decks = self.metaDecksList
        
        if tier:
            # Filter by tier if provided (simple string matching)
            filtered_decks = []
            for deck in decks:
                if tier.upper() in deck.name.upper():
                    filtered_decks.append(deck)
            decks = filtered_decks
        
        if limit:
            decks = decks[:limit]
        
        return {"decks": [deck.model_dump() for deck in decks]}

# Section 3: MCP Tools
mcp = FastMCP(name="TFTServer")
server = TFTServer()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the TFT server.
    
    Args:
        scenario (dict): Scenario dictionary matching TFTScenario schema.
    
    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        server.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current TFT state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return server.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def tft_get_champion_item_build(champion_name: str) -> dict:
    """Get recommended item builds for a specific TFT champion.
    
    Args:
        champion_name (str): The name of the TFT champion.
    
    Returns:
        champion_name (str): Champion name.
        items (list): List of recommended items with priority and win rate.
    """
    try:
        if not champion_name or not isinstance(champion_name, str):
            raise ValueError("Champion name must be a non-empty string")
        return server.tft_get_champion_item_build(champion_name)
    except Exception as e:
        raise e

@mcp.tool()
def tft_get_play_style(style: Optional[str] = None) -> dict:
    """Get play style recommendations and strategies.
    
    Args:
        style (str) [Optional]: The play style name (e.g., 'aggro', 'economy', 'reroll').
    
    Returns:
        style (str): Play style name.
        description (str): Detailed explanation of the play style.
        recommendations (list): Strategic recommendations and tips.
    """
    try:
        if style and not isinstance(style, str):
            raise ValueError("Style must be a string if provided")
        return server.tft_get_play_style(style)
    except Exception as e:
        raise e

@mcp.tool()
def tft_list_augments(limit: Optional[int] = None) -> dict:
    """List TFT augments with their tier and performance statistics.
    
    Args:
        limit (int) [Optional]: Maximum number of augments to return.
    
    Returns:
        augments (list): List of augments with name, tier, description, and win rate.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        return server.tft_list_augments(limit)
    except Exception as e:
        raise e

@mcp.tool()
def tft_list_champions_for_item(item_name: str) -> dict:
    """Get champion recommendations for a specific TFT item.
    
    Args:
        item_name (str): The name of the TFT item.
    
    Returns:
        champions (list): List of champions recommended for the item with synergy scores.
    """
    try:
        if not item_name or not isinstance(item_name, str):
            raise ValueError("Item name must be a non-empty string")
        return server.tft_list_champions_for_item(item_name)
    except Exception as e:
        raise e

@mcp.tool()
def tft_list_item_combinations(limit: Optional[int] = None) -> dict:
    """List TFT item combination recipes.
    
    Args:
        limit (int) [Optional]: Maximum number of combinations to return.
    
    Returns:
        combinations (list): List of item combinations showing components and results.
    """
    try:
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        return server.tft_list_item_combinations(limit)
    except Exception as e:
        raise e

@mcp.tool()
def tft_list_meta_decks(tier: Optional[str] = None, limit: Optional[int] = None) -> dict:
    """List current meta deck compositions with performance statistics.
    
    Args:
        tier (str) [Optional]: Filter decks by tier classification (e.g., 'S', 'A', 'B').
        limit (int) [Optional]: Maximum number of decks to return.
    
    Returns:
        decks (list): List of meta decks with champions, traits, and performance data.
    """
    try:
        if tier is not None and not isinstance(tier, str):
            raise ValueError("Tier must be a string if provided")
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise ValueError("Limit must be a non-negative integer")
        return server.tft_list_meta_decks(tier, limit)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()