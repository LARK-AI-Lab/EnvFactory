from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class CharacterBuild(BaseModel):
    """Represents a character build configuration."""
    weapon: str = Field(..., description="Recommended weapon")
    echo_set: str = Field(..., description="Recommended echo set")
    main_stats: List[str] = Field(..., description="Main stat priorities")
    sub_stats: List[str] = Field(..., description="Sub stat priorities")
    talent_priority: List[str] = Field(..., description="Talent upgrade priority")

class CharacterInfo(BaseModel):
    """Represents in-game character information."""
    name: str = Field(..., description="Character name")
    rarity: int = Field(..., ge=4, le=5, description="Character rarity (4 or 5)")
    element: str = Field(..., description="Element type")
    weapon_type: str = Field(..., description="Weapon type")
    build_recommendations: CharacterBuild = Field(..., description="Build recommendations")
    team_compositions: List[List[str]] = Field(..., description="Recommended team compositions")
    gameplay_tips: List[str] = Field(..., description="Gameplay strategies and tips")

class EchoInfo(BaseModel):
    """Represents echo set information."""
    name: str = Field(..., description="Echo set name")
    cost: int = Field(..., ge=1, le=4, description="Echo cost (1-4)")
    attributes: Dict[str, float] = Field(..., description="Echo attributes")
    set_effect: str = Field(..., description="Set effect description")
    recommended_for: List[str] = Field(..., description="Characters this echo is recommended for")

class CharacterProfile(BaseModel):
    """Represents out-of-game character profile information."""
    name: str = Field(..., description="Character name")
    voice_actor: str = Field(..., description="Voice actor name")
    background_story: str = Field(..., description="Character background and lore")
    personality: str = Field(..., description="Character personality description")
    design_notes: str = Field(..., description="Character design notes")
    release_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Character release date")

class WuWaScenario(BaseModel):
    """Main scenario model for Wuthering Waves game data."""
    characterDatabase: Dict[str, CharacterInfo] = Field(default={
        "漂泊者": CharacterInfo(
            name="漂泊者",
            rarity=5,
            element="光谱",
            weapon_type="迅刃",
            build_recommendations=CharacterBuild(
                weapon="千古洑流",
                echo_set="沉日劫明",
                main_stats=["暴击率", "暴击伤害", "攻击力%"],
                sub_stats=["暴击率", "暴击伤害", "攻击力%", "共鸣效率"],
                talent_priority=["共鸣回路", "共鸣技能", "常态攻击", "共鸣解放"]
            ),
            team_compositions=[["漂泊者", "维里奈", "白芷"], ["漂泊者", "散华", "白莲"]],
            gameplay_tips=["利用共鸣回路进行快速连击", "保持高共鸣效率以频繁释放技能"]
        ),
        "维里奈": CharacterInfo(
            name="维里奈",
            rarity=5,
            element="衍射",
            weapon_type="音感仪",
            build_recommendations=CharacterBuild(
                weapon="漪澜浮录",
                echo_set="隐世回音",
                main_stats=["攻击力%", "暴击率", "暴击伤害"],
                sub_stats=["攻击力%", "暴击率", "暴击伤害", "共鸣效率"],
                talent_priority=["共鸣回路", "共鸣技能", "共鸣解放", "常态攻击"]
            ),
            team_compositions=[["维里奈", "漂泊者", "白芷"], ["维里奈", "卡卡罗", "白莲"]],
            gameplay_tips=["优先叠加光合能量", "在适当时机使用重击触发额外伤害"]
        ),
        "白芷": CharacterInfo(
            name="白芷",
            rarity=4,
            element="冷凝",
            weapon_type="音感仪",
            build_recommendations=CharacterBuild(
                weapon="鸣动仪-25",
                echo_set="彻响之壁",
                main_stats=["攻击力%", "暴击率", "暴击伤害"],
                sub_stats=["攻击力%", "暴击率", "暴击伤害", "共鸣效率"],
                talent_priority=["共鸣技能", "共鸣回路", "常态攻击", "共鸣解放"]
            ),
            team_compositions=[["白芷", "漂泊者", "维里奈"], ["白芷", "卡卡罗", "桃祈"]],
            gameplay_tips=["利用延奏技能为队友提供伤害加成", "保持共鸣回路层数"]
        )
    }, description="Character information database")
    
    echoDatabase: Dict[str, EchoInfo] = Field(default={
        "沉日劫明": EchoInfo(
            name="沉日劫明",
            cost=4,
            attributes={"攻击力%": 30.0, "暴击率": 15.0},
            set_effect="2件套: 湮灭伤害+10% 5件套: 使用普攻或重击时湮灭伤害+7.5%，可叠加4层",
            recommended_for=["漂泊者", "丹瑾", "散华"]
        ),
        "隐世回音": EchoInfo(
            name="隐世回音",
            cost=4,
            attributes={"攻击力%": 30.0, "暴击伤害": 20.0},
            set_effect="2件套: 攻击力+10% 5件套: 装备者不为后台角色时攻击力+15%",
            recommended_for=["维里奈", "安可", "吟霖"]
        ),
        "彻响之壁": EchoInfo(
            name="彻响之壁",
            cost=3,
            attributes={"防御力%": 20.0, "生命值%": 20.0},
            set_effect="2件套: 防御力+15% 5件套: 受到攻击时防御力+15%，持续5秒",
            recommended_for=["白芷", "桃祈", "渊武"]
        ),
        "不绝余音": EchoInfo(
            name="不绝余音",
            cost=4,
            attributes={"攻击力%": 30.0, "共鸣效率": 20.0},
            set_effect="2件套: 攻击力+10% 5件套: 在场时自身攻击力每1.5秒+5%，最多叠加6层",
            recommended_for=["卡卡罗", "凌阳", "炽霞"]
        ),
        "啸谷长风": EchoInfo(
            name="啸谷长风",
            cost=4,
            attributes={"气动伤害": 30.0, "暴击率": 15.0},
            set_effect="2件套: 气动伤害+10% 5件套: 使用变奏技能时气动伤害+30%，持续15秒",
            recommended_for=["秧秧", "秋水", "莫特斐"]
        )
    }, description="Echo set information database")
    
    characterProfileDatabase: Dict[str, CharacterProfile] = Field(default={
        "漂泊者": CharacterProfile(
            name="漂泊者",
            voice_actor="???",
            background_story="从世界之外漂流而来的旅人，拥有穿越不同世界的能力。",
            personality="冷静、理性，但内心充满对未知世界的好奇",
            design_notes="主角设计简洁大方，体现其来自世界之外的特殊身份",
            release_date="2024-05-23"
        ),
        "维里奈": CharacterProfile(
            name="维里奈",
            voice_actor="张昱",
            background_story="新联邦植物育种员，拥有与植物沟通的能力，致力于培育新的植物品种。",
            personality="温柔、善良，对植物有着深厚的感情",
            design_notes="设计融合了植物元素，服装和技能都体现自然主题",
            release_date="2024-05-23"
        ),
        "白芷": CharacterProfile(
            name="白芷",
            voice_actor="张琦",
            background_story="华胥研究院的研究员，专注于共鸣能力的研究，拥有出色的医疗共鸣能力。",
            personality="冷静、专业，在研究中追求完美",
            design_notes="白大褂和医疗元素体现其研究员身份",
            release_date="2024-05-23"
        )
    }, description="Character profile database")

Scenario_Schema = [CharacterBuild, CharacterInfo, EchoInfo, CharacterProfile, WuWaScenario]

# Section 2: Class
class WuWaAPI:
    def __init__(self):
        """Initialize WuWa API with empty state."""
        self.characterDatabase: Dict[str, CharacterInfo] = {}
        self.echoDatabase: Dict[str, EchoInfo] = {}
        self.characterProfileDatabase: Dict[str, CharacterProfile] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = WuWaScenario(**scenario)
        self.characterDatabase = model.characterDatabase
        self.echoDatabase = model.echoDatabase
        self.characterProfileDatabase = model.characterProfileDatabase

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "characterDatabase": {name: char.model_dump() for name, char in self.characterDatabase.items()},
            "echoDatabase": {name: echo.model_dump() for name, echo in self.echoDatabase.items()},
            "characterProfileDatabase": {name: profile.model_dump() for name, profile in self.characterProfileDatabase.items()}
        }

    def get_character_info(self, character_name: str) -> dict:
        """Query in-game character information."""
        if character_name in self.characterDatabase:
            return {"character_info": self.characterDatabase[character_name].model_dump_json()}
        else:
            return {"character_info": '{"error": "Character not found"}'}

    def get_echo_info(self, echo_name: str) -> dict:
        """Query echo set information."""
        if echo_name in self.echoDatabase:
            return {"echo_info": self.echoDatabase[echo_name].model_dump_json()}
        else:
            return {"echo_info": '{"error": "Echo not found"}'}

    def get_character_profile(self, character_name: str) -> dict:
        """Query out-of-game character profile information."""
        if character_name in self.characterProfileDatabase:
            return {"character_profile": self.characterProfileDatabase[character_name].model_dump_json()}
        else:
            return {"character_profile": '{"error": "Character profile not found"}'}

# Section 3: MCP Tools
mcp = FastMCP(name="WuWa")
api = WuWaAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the WuWa API.
    
    Args:
        scenario (dict): Scenario dictionary matching WuWaScenario schema.
    
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
    """Save current WuWa state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_character_info(character_name: str) -> dict:
    """Query in-game character information from KooZone.
    
    Args:
        character_name (str): The Chinese name of the character to query for in-game information.
    
    Returns:
        character_info (str): JSON-formatted string containing in-game character information.
    """
    try:
        if not character_name or not isinstance(character_name, str):
            raise ValueError("Character name must be a non-empty string")
        return api.get_character_info(character_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_echo_info(echo_name: str) -> dict:
    """Query echo set information from KooZone.
    
    Args:
        echo_name (str): The Chinese name of the echo set to query.
    
    Returns:
        echo_info (str): JSON-formatted string containing echo set information.
    """
    try:
        if not echo_name or not isinstance(echo_name, str):
            raise ValueError("Echo name must be a non-empty string")
        return api.get_echo_info(echo_name)
    except Exception as e:
        raise e

@mcp.tool()
def get_character_profile(character_name: str) -> dict:
    """Query out-of-game character profile information from KooZone.
    
    Args:
        character_name (str): The Chinese name of the character to query for profile information.
    
    Returns:
        character_profile (str): JSON-formatted string containing out-of-game character profile information.
    """
    try:
        if not character_name or not isinstance(character_name, str):
            raise ValueError("Character name must be a non-empty string")
        return api.get_character_profile(character_name)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()