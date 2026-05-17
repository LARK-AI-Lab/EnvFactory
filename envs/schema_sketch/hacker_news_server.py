# Server: HackerNews

def search(query: str, content_type: str = None, page: int = None, hits_per_page: int = None) -> dict:
    """
    Search for stories and comments on Hacker News using Algolia's search API.
    Use this function when you need to search by keywords or specific terms.
    
    Args:
        query (str): Search query (keywords to search for)
        content_type (str): [Optional] Filter by content type ('story' or 'comment')
        page (int): [Optional] Page number for pagination
        hits_per_page (int): [Optional] Results per page (max 100)
        
    Returns:
        dict: {
            "hits": list[dict] - Each hit contains {
                "story_id": int,
                "title": str,
                "url": str,
                "author": str,
                "points": int,
                "created_at": str
            }
        }
    """
    pass

def getStories(story_type: str, limit: int = None) -> list:
    """
    Get multiple stories by category type without searching.
    Use this function to fetch pre-categorized story lists (top, new, best, etc.).
    This is different from search() which requires a search query.
    
    Args:
        story_type (str): Category of stories to fetch ('top', 'new', 'best', 'ask', 'show', 'job')
        limit (int): [Optional] Number of stories to fetch (max 100)
        
    Returns:
        list: Each story contains {
            "story_id": int,
            "title": str,
            "url": str,
            "author": str,
            "points": int,
            "created_at": str
        }
    """
    pass

def getStoryWithComments(story_id: int, max_depth: int = None, max_comments: int = None) -> dict:
    """
    Get a story along with its comment thread.
    Can return comments as a flat list or as a hierarchical tree structure.
    
    Args:
        story_id (int): Story ID
        max_depth (int): [Optional] Maximum depth of comment tree (only applies when return_tree=True)
        max_comments (int): [Optional] Maximum number of comments to return
        
    Returns:
        dict: {
            "story_id": int,
            "title": str,
            "url": str,
            "author": str,
            "points": int,
            "created_at": str,
            "comments": list[dict] - Each comment contains {
                "comment_id": int,
                "author": str,
                "text": str,
                "created_at": str
            }
        }
    """
    pass

def getUser(user_id: str) -> dict:
    """
    Get a user's profile information.
    
    Args:
        user_id (str): Username 
        
    Returns:
        dict: {
            "user_id": str,
            "karma": int,  # User's karma points (reputation score based on upvotes)
            "created": str,
            "about": str
        }
    """
    pass

def getUserSubmissions(user_id: str) -> list:
    """
    Get a user's submissions (stories and comments).
    
    Args:
        user_id (str): Username (user ID)
        
    Returns:
        list: Each submission contains {
            "story_id": int,  # or comment_id for comments
            "submission_type": str,  # 'story' or 'comment'
            "title": str,
            "url": str,
            "points": int,
            "created_at": str
        }
    """
    pass

