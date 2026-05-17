# Server: Hugeicons

def list_icons(limit: int = None, offset: int = None) -> list:
    """
    Get a list of all available Hugeicons icons.
    
    Args:
        limit (int): [Optional] Maximum number of icons to return
        offset (int): [Optional] Pagination offset for results
        
    Returns:
        list: Each icon contains {
            "icon_name": str,
            "category": str,
            "tags": list[str],
            "styles": list[str]
        }
    """
    pass

def search_icons(query: str, tags: list = None, limit: int = None) -> list:
    """
    Search for icons by name or tags.
    
    Args:
        query (str): Search keyword for icon name
        tags (list): [Optional] Filter by tags (e.g., ["social", "media"])
        limit (int): [Optional] Maximum number of results to return
        
    Returns:
        list: Each icon contains {
            "icon_name": str,
            "category": str,
            "tags": list[str],
            "styles": list[str]
        }
    """
    pass


def get_icon_glyph_by_style(icon_name: str, style: str = None) -> dict:
    """
    Get the glyph (unicode character) for a specific icon with a particular style.
    
    Args:
        icon_name (str): Name of the icon (from list_icons or search_icons)
        style (str): Icon style enum("outline", "solid", "duotone"). if not provided, return all styles.
        
    Returns:
        dict: {
            "icon_name": str,
            "style": str,
            "glyph": str
        }
    """
    pass 

