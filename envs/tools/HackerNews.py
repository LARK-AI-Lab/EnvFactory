from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Story(BaseModel):
    """Represents a Hacker News story."""
    story_id: int = Field(..., ge=0, description="The unique identifier of the Hacker News story")
    title: str = Field(..., description="The title of the story")
    url: Optional[str] = Field(None, description="The URL link to the story's external content")
    author: str = Field(..., description="The username of the user who submitted the story")
    points: int = Field(..., ge=0, description="The score of the story based on upvotes")
    created_at: str = Field(..., description="The timestamp when the story was submitted")

class Comment(BaseModel):
    """Represents a Hacker News comment."""
    comment_id: int = Field(..., ge=0, description="The unique identifier of the comment")
    author: str = Field(..., description="The username of the user who wrote the comment")
    text: str = Field(..., description="The text content of the comment")
    created_at: str = Field(..., description="The timestamp when the comment was posted")

class User(BaseModel):
    """Represents a Hacker News user."""
    user_id: str = Field(..., description="The username (user ID) of the Hacker News user")
    karma: int = Field(..., ge=0, description="The user's karma points")
    created: str = Field(..., description="The timestamp when the user account was created")
    about: Optional[str] = Field(None, description="The user's self-written bio or about section")

class Submission(BaseModel):
    """Represents a user submission (story or comment)."""
    story_id: int = Field(..., ge=0, description="The unique identifier of the submission")
    submission_type: str = Field(..., pattern=r"^(story|comment)$", description="The type of submission")
    title: Optional[str] = Field(None, description="The title of the submission (applicable for stories)")
    url: Optional[str] = Field(None, description="The URL link to the submission's external content")
    points: int = Field(..., ge=0, description="The score of the submission based on upvotes")
    created_at: str = Field(..., description="The timestamp when the submission was posted")

class HackerNewsScenario(BaseModel):
    """Main scenario model for Hacker News data."""
    stories: Dict[int, Story] = Field(default={}, description="Stories stored by ID")
    comments: Dict[int, Comment] = Field(default={}, description="Comments stored by ID")
    users: Dict[str, User] = Field(default={}, description="Users stored by username")
    submissions: Dict[str, List[Submission]] = Field(default={}, description="User submissions by username")
    searchResults: Dict[str, List[Story]] = Field(default={}, description="Search results by query")
    categorizedStories: Dict[str, List[Story]] = Field(default={}, description="Stories by category type")

Scenario_Schema = [Story, Comment, User, Submission, HackerNewsScenario]

# Section 2: Class
class HackerNewsAPI:
    def __init__(self):
        """Initialize Hacker News API with empty state."""
        self.stories: Dict[int, Story] = {}
        self.comments: Dict[int, Comment] = {}
        self.users: Dict[str, User] = {}
        self.submissions: Dict[str, List[Submission]] = {}
        self.searchResults: Dict[str, List[Story]] = {}
        self.categorizedStories: Dict[str, List[Story]] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = HackerNewsScenario(**scenario)
        self.stories = model.stories
        self.comments = model.comments
        self.users = model.users
        self.submissions = model.submissions
        self.searchResults = model.searchResults
        self.categorizedStories = model.categorizedStories

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "stories": {story_id: story.model_dump() for story_id, story in self.stories.items()},
            "comments": {comment_id: comment.model_dump() for comment_id, comment in self.comments.items()},
            "users": {user_id: user.model_dump() for user_id, user in self.users.items()},
            "submissions": {user_id: [sub.model_dump() for sub in subs] for user_id, subs in self.submissions.items()},
            "searchResults": {query: [story.model_dump() for story in stories] for query, stories in self.searchResults.items()},
            "categorizedStories": {category: [story.model_dump() for story in stories] for category, stories in self.categorizedStories.items()}
        }

    def search(self, query: str, content_type: Optional[str] = None, page: Optional[int] = None, hits_per_page: Optional[int] = None) -> dict:
        """Search for stories and comments."""
        if query in self.searchResults:
            return {"hits": self.searchResults[query]}
        return {"hits": []}

    def getStories(self, story_type: str, limit: Optional[int] = None) -> dict:
        """Get multiple stories by category type."""
        if story_type in self.categorizedStories:
            stories = self.categorizedStories[story_type]
            if limit and limit > 0:
                stories = stories[:limit]
            return {"stories": stories}
        return {"stories": []}

    def getStoryWithComments(self, story_id: int, max_depth: Optional[int] = None, max_comments: Optional[int] = None) -> dict:
        """Get a story along with its comment thread."""
        if story_id in self.stories:
            story = self.stories[story_id]
            comments = []
            if max_comments and max_comments > 0:
                # Filter comments for this story (simplified - in real implementation would filter by story_id)
                all_comments = list(self.comments.values())
                comments = all_comments[:max_comments]
            else:
                comments = list(self.comments.values())
            
            return {
                "story_id": story.story_id,
                "title": story.title,
                "url": story.url,
                "author": story.author,
                "points": story.points,
                "created_at": story.created_at,
                "comments": comments
            }
        return {}

    def getUser(self, user_id: str) -> dict:
        """Get a user's profile information."""
        if user_id in self.users:
            user = self.users[user_id]
            return {
                "user_id": user.user_id,
                "karma": user.karma,
                "created": user.created,
                "about": user.about
            }
        return {}

    def getUserSubmissions(self, user_id: str) -> dict:
        """Get a user's submissions including both stories and comments."""
        if user_id in self.submissions:
            return {"submissions": self.submissions[user_id]}
        return {"submissions": []}

# Section 3: MCP Tools
mcp = FastMCP(name="HackerNews")
api = HackerNewsAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the Hacker News API.
    
    Args:
        scenario (dict): Scenario dictionary matching HackerNewsScenario schema.
    
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
    """Save current Hacker News state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search(query: str, content_type: Optional[str] = None, page: Optional[int] = None, hits_per_page: Optional[int] = None) -> dict:
    """Search for stories and comments on Hacker News using Algolia's search API.
    
    Args:
        query (str): The search query containing keywords to search for in Hacker News stories and comments.
        content_type (str) [Optional]: Filter results by content type. Valid values are 'story' or 'comment'.
        page (int) [Optional]: Page number for pagination when retrieving search results.
        hits_per_page (int) [Optional]: Number of results to return per page (maximum 100).
    
    Returns:
        hits (list): List of search results matching the query.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search(query, content_type, page, hits_per_page)
    except Exception as e:
        raise e

@mcp.tool()
def getStories(story_type: str, limit: Optional[int] = None) -> dict:
    """Get multiple stories by category type without searching.
    
    Args:
        story_type (str): The category of stories to fetch. Valid values are 'top', 'new', 'best', 'ask', 'show', or 'job'.
        limit (int) [Optional]: Number of stories to fetch (maximum 100).
    
    Returns:
        stories (list): List of stories in the requested category.
    """
    try:
        if not story_type or not isinstance(story_type, str):
            raise ValueError("Story type must be a non-empty string")
        if story_type not in ['top', 'new', 'best', 'ask', 'show', 'job']:
            raise ValueError("Invalid story type. Must be one of: top, new, best, ask, show, job")
        return api.getStories(story_type, limit)
    except Exception as e:
        raise e

@mcp.tool()
def getStoryWithComments(story_id: int, max_depth: Optional[int] = None, max_comments: Optional[int] = None) -> dict:
    """Get a story along with its comment thread.
    
    Args:
        story_id (int): The unique identifier of the Hacker News story.
        max_depth (int) [Optional]: Maximum depth of the comment tree to retrieve for nested replies.
        max_comments (int) [Optional]: Maximum number of comments to return.
    
    Returns:
        story_id (int): The unique identifier of the Hacker News story.
        title (str): The title of the story.
        url (str): The URL link to the story's external content.
        author (str): The username of the user who submitted the story.
        points (int): The score of the story based on upvotes.
        created_at (str): The timestamp when the story was submitted.
        comments (list): List of comments associated with the story.
    """
    try:
        if story_id not in api.stories:
            raise ValueError(f"Story {story_id} not found")
        return api.getStoryWithComments(story_id, max_depth, max_comments)
    except Exception as e:
        raise e

@mcp.tool()
def getUser(user_id: str) -> dict:
    """Get a user's profile information including karma, account creation date, and bio.
    
    Args:
        user_id (str): The username (user ID) of the Hacker News user.
    
    Returns:
        user_id (str): The username (user ID) of the Hacker News user.
        karma (int): The user's karma points, a reputation score based on upvotes received on submissions and comments.
        created (str): The timestamp when the user account was created.
        about (str): The user's self-written bio or about section.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        if user_id not in api.users:
            raise ValueError(f"User {user_id} not found")
        return api.getUser(user_id)
    except Exception as e:
        raise e

@mcp.tool()
def getUserSubmissions(user_id: str) -> dict:
    """Get a user's submissions including both stories and comments they have posted.
    
    Args:
        user_id (str): The username (user ID) of the Hacker News user.
    
    Returns:
        submissions (list): List of submissions (stories and comments) by the user.
    """
    try:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        if user_id not in api.submissions:
            raise ValueError(f"User {user_id} has no submissions")
        return api.getUserSubmissions(user_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()