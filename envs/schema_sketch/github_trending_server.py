# Server: GithubTrending

def get_github_trending_repositories(
    language: str = None,
    period: str = "daily",
    spoken_language: str = None,
    limit: int = 5
) -> list:
    """
    Get trending repositories from GitHub.
    
    Args:
        language (str): [Optional] Programming language to filter repositories by. Must be lowercase letters only, no spaces or special characters (e.g., "python", "javascript", "cpp", "csharp", "go", "rust", "java").
        period (str): [Optional] Time period to filter repositories by ("daily", "weekly", "monthly")
        spoken_language (str): [Optional] Spoken language to filter repositories by. Must be ISO 639-1 two-letter language code in lowercase (e.g., "en", "zh", "ja", "es", "fr", "de", "ko").
        limit (int): [Optional] Number of repositories to return, default is 5.

    Returns:
        list: Each repository contains {
            "rank": int,
            "name": str,
            "fullname": str,
            "url": str,
            "description": str,
            "language": str,
            "stars": int,
            "forks": int,
            "current_period_stars": int
        }
    """
    pass

def get_github_trending_developers(
    language: str = None,
    period: str = "daily",
    limit: int = 5
) -> list:
    """
    Get trending developers from GitHub.
    
    Args:
        language (str): [Optional] Programming language to filter by. Must be lowercase letters only, no spaces or special characters (e.g., "python", "javascript", "cpp", "csharp", "go", "rust", "java").
        period (str): [Optional] Time period to filter by ("daily", "weekly", "monthly")
        limit (int): [Optional] Number of developers to return, default is 5.
    Returns:
        list: Each developer contains {
            "rank": int,
            "username": str,
            "name": str,
            "url": str,
            "avatar": str,
            "repo": {
                "name": str,
                "description": str,
                "url": str
            }
        }
    """
    pass

