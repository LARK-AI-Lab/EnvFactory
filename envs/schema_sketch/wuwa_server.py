# Server: WuWa

def get_character_info(character_name: str) -> str:
    """
    Query character detailed information from KooZone and return in Json format.
    This function returns in-game useful information, such as recommended equipment, builds, and gameplay strategies.
    
    Args:
        character_name (str): Chinese name of the character to query
        
    Returns:
        str: Json object containing character in-game information (e.g., equipment recommendations, build guides), or error message if character not found or data retrieval failed
    """
    pass

def get_echo_info(echo_name: str) -> str:
    """
    Query echo detailed information from KooZone and return in Json format.
    
    Args:
        echo_name (str): Chinese name of the echo set to query
        
    Returns:
        str: Json object containing echo information, or error message if echo not found or data retrieval failed
    """
    pass

def get_character_profile(character_name: str) -> str:
    """
    Query character profile information from KooZone and return in Json format.
    This function returns out-of-game information, such as voice actor, character background story, and other meta information.
    Note: This is different from get_character_info, which returns in-game useful information like equipment recommendations.
    
    Args:
        character_name (str): Chinese name of the character to query
        
    Returns:
        str: Json object containing character out-of-game profile information (e.g., voice actor, background story, character design details), or error message if character not found or data retrieval failed
    """
    pass

