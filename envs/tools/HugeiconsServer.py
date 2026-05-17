from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Icon(BaseModel):
    """Represents an icon in the Hugeicons library."""
    icon_name: str = Field(..., description="The unique name identifier of the icon")
    category: str = Field(..., description="The category classification of the icon")
    tags: List[str] = Field(default=[], description="Descriptive tags associated with the icon")
    styles: List[str] = Field(default=[], description="Available visual styles for the icon")

class IconGlyph(BaseModel):
    """Represents an icon glyph for a specific style."""
    icon_name: str = Field(..., description="The unique name identifier of the icon")
    style: str = Field(..., description="The visual style variant of the icon")
    glyph: str = Field(..., description="The unicode character representing the icon glyph")

class HugeiconsScenario(BaseModel):
    """Main scenario model for Hugeicons icon library."""
    icons: List[Icon] = Field(default=[], description="List of all available icons")
    iconGlyphsMap: Dict[str, Dict[str, str]] = Field(default_factory=lambda: {
        "home": {"outline": "\ue900", "solid": "\ue901", "duotone": "\ue902"},
        "user": {"outline": "\ue903", "solid": "\ue904", "duotone": "\ue905"},
        "search": {"outline": "\ue906", "solid": "\ue907", "duotone": "\ue908"},
        "heart": {"outline": "\ue909", "solid": "\ue90a", "duotone": "\ue90b"},
        "star": {"outline": "\ue90c", "solid": "\ue90d", "duotone": "\ue90e"},
        "settings": {"outline": "\ue90f", "solid": "\ue910", "duotone": "\ue911"},
        "mail": {"outline": "\ue912", "solid": "\ue913", "duotone": "\ue914"},
        "phone": {"outline": "\ue915", "solid": "\ue916", "duotone": "\ue917"},
        "calendar": {"outline": "\ue918", "solid": "\ue919", "duotone": "\ue91a"},
        "camera": {"outline": "\ue91b", "solid": "\ue91c", "duotone": "\ue91d"},
        "arrow-right": {"outline": "\ue91e", "solid": "\ue91f", "duotone": "\ue920"},
        "arrow-left": {"outline": "\ue921", "solid": "\ue922", "duotone": "\ue923"},
        "arrow-up": {"outline": "\ue924", "solid": "\ue925", "duotone": "\ue926"},
        "arrow-down": {"outline": "\ue927", "solid": "\ue928", "duotone": "\ue929"},
        "plus": {"outline": "\ue92a", "solid": "\ue92b", "duotone": "\ue92c"},
        "minus": {"outline": "\ue92d", "solid": "\ue92e", "duotone": "\ue92f"},
        "check": {"outline": "\ue930", "solid": "\ue931", "duotone": "\ue932"},
        "close": {"outline": "\ue933", "solid": "\ue934", "duotone": "\ue935"},
        "menu": {"outline": "\ue936", "solid": "\ue937", "duotone": "\ue938"},
        "download": {"outline": "\ue939", "solid": "\ue93a", "duotone": "\ue93b"}
    }, description="Mapping of icon names to their glyph characters by style")
    
Scenario_Schema = [Icon, IconGlyph, HugeiconsScenario]

# Section 2: Class
class HugeiconsAPI:
    def __init__(self):
        """Initialize Hugeicons API with empty state."""
        self.icons: List[Icon] = []
        self.iconGlyphsMap: Dict[str, Dict[str, str]] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = HugeiconsScenario(**scenario)
        self.icons = model.icons
        self.iconGlyphsMap = model.iconGlyphsMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "icons": [icon.model_dump() for icon in self.icons],
            "iconGlyphsMap": self.iconGlyphsMap
        }

    def list_icons(self, limit: Optional[int] = None, offset: Optional[int] = None) -> dict:
        """Retrieve a paginated list of all available icons."""
        if offset is None:
            offset = 0
        if limit is None:
            limit = len(self.icons)
        
        paginated_icons = self.icons[offset:offset + limit]
        return {"icons": [icon.model_dump() for icon in paginated_icons]}

    def search_icons(self, query: str, tags: Optional[List[str]] = None, limit: Optional[int] = None) -> dict:
        """Search for icons by name keyword or filter by associated tags."""
        filtered_icons = []
        
        for icon in self.icons:
            # Check if query matches icon name
            if query.lower() in icon.icon_name.lower():
                # If tags provided, check if icon has all specified tags
                if tags:
                    if all(tag.lower() in [t.lower() for t in icon.tags] for tag in tags):
                        filtered_icons.append(icon)
                else:
                    filtered_icons.append(icon)
        
        if limit is not None:
            filtered_icons = filtered_icons[:limit]
        
        return {"icons": [icon.model_dump() for icon in filtered_icons]}

    def get_icon_glyph_by_style(self, icon_name: str, style: Optional[str] = None) -> dict:
        """Retrieve the unicode glyph character for a specific icon in a particular visual style."""
        if icon_name not in self.iconGlyphsMap:
            raise ValueError(f"Icon '{icon_name}' not found")
        
        glyph_data = self.iconGlyphsMap[icon_name]
        
        if style is not None:
            if style not in glyph_data:
                raise ValueError(f"Style '{style}' not available for icon '{icon_name}'")
            return {
                "icon_name": icon_name,
                "style": style,
                "glyph": glyph_data[style]
            }
        else:
            # Return first available style if no specific style requested
            first_style = list(glyph_data.keys())[0]
            return {
                "icon_name": icon_name,
                "style": first_style,
                "glyph": glyph_data[first_style]
            }

# Section 3: MCP Tools
mcp = FastMCP(name="HugeiconsServer")
api = HugeiconsAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Hugeicons API.
    
    Args:
        scenario (dict): Scenario dictionary matching HugeiconsScenario schema.
    
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
    Save current Hugeicons state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def list_icons(limit: Optional[int] = None, offset: Optional[int] = None) -> dict:
    """
    Retrieve a paginated list of all available icons in the Hugeicons library.
    
    Args:
        limit (int): [Optional] Maximum number of icons to return.
        offset (int): [Optional] Pagination offset to skip results.
    
    Returns:
        icons (list): List of icon objects with name, category, tags, and styles.
    """
    try:
        return api.list_icons(limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def search_icons(query: str, tags: Optional[List[str]] = None, limit: Optional[int] = None) -> dict:
    """
    Search for icons by name keyword or filter by associated tags.
    
    Args:
        query (str): Search keyword to match against icon names.
        tags (list): [Optional] Filter results by specific tags.
        limit (int): [Optional] Maximum number of icons to return.
    
    Returns:
        icons (list): List of icon objects matching the search criteria.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_icons(query, tags, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_icon_glyph_by_style(icon_name: str, style: Optional[str] = None) -> dict:
    """
    Retrieve the unicode glyph character for a specific icon in a particular visual style.
    
    Args:
        icon_name (str): The unique name identifier of the icon.
        style (str): [Optional] The visual style variant ('outline', 'solid', 'duotone').
    
    Returns:
        icon_name (str): The icon name.
        style (str): The visual style variant.
        glyph (str): The unicode character for the icon glyph.
    """
    try:
        # Basic parameter checks only - format validation handled by Pydantic models
        if not icon_name or not isinstance(icon_name, str):
            raise ValueError("Icon name must be a non-empty string")
        if style is not None and not isinstance(style, str):
            raise ValueError("Style must be a string")
        return api.get_icon_glyph_by_style(icon_name, style)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()