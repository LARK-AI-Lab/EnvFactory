from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
import uuid

# Section 1: Schema
class User(BaseModel):
    """Represents a user account."""
    username: str = Field(..., description="Unique username")
    password: str = Field(..., description="User password")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Account creation timestamp")

class Tweet(BaseModel):
    """Represents a tweet."""
    tweet_id: int = Field(..., ge=0, description="Unique tweet ID")
    username: str = Field(..., description="Author username")
    content: str = Field(..., description="Tweet content")
    hashtags: List[str] = Field(default=[], description="List of hashtags")
    mentions: List[str] = Field(default=[], description="List of mentions")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Last update timestamp")
    retweet_count: int = Field(default=0, ge=0, description="Number of retweets")
    comment_count: int = Field(default=0, ge=0, description="Number of comments")

class Comment(BaseModel):
    """Represents a comment on a tweet."""
    comment_id: int = Field(..., ge=0, description="Unique comment ID")
    tweet_id: int = Field(..., ge=0, description="Tweet ID being commented on")
    username: str = Field(..., description="Comment author username")
    comment_content: str = Field(..., description="Comment content")
    created_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Creation timestamp")

class FollowRelationship(BaseModel):
    """Represents a follow relationship between users."""
    follower: str = Field(..., description="Username of follower")
    following: str = Field(..., description="Username of user being followed")
    followed_at: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="When follow was established")

class PostingScenario(BaseModel):
    """Main scenario model for social media posting system."""
    users: Dict[str, User] = Field(default={}, description="Registered users")
    tweets: Dict[int, Tweet] = Field(default={}, description="All tweets")
    comments: Dict[int, Comment] = Field(default={}, description="All comments")
    follow_relationships: List[FollowRelationship] = Field(default=[], description="Follow relationships")
    current_session: Optional[Dict[str, str]] = Field(default=None, description="Current active session")
    next_tweet_id: int = Field(default=1, ge=0, description="Next available tweet ID")
    next_comment_id: int = Field(default=1, ge=0, description="Next available comment ID")
    user_stats: Dict[str, Dict[str, int]] = Field(default={}, description="User statistics")
    current_time: str = Field(default="2024-01-01T00:00:00", pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [User, Tweet, Comment, FollowRelationship, PostingScenario]

# Section 2: Class
class PostingAPI:
    def __init__(self):
        """Initialize posting API with empty state."""
        self.users: Dict[str, User] = {}
        self.tweets: Dict[int, Tweet] = {}
        self.comments: Dict[int, Comment] = {}
        self.follow_relationships: List[FollowRelationship] = []
        self.current_session: Optional[Dict[str, str]] = None
        self.next_tweet_id: int = 1
        self.next_comment_id: int = 1
        self.user_stats: Dict[str, Dict[str, int]] = {}
        self.current_time: str = "2024-01-01T00:00:00"
        
    def _ensure_user_stats(self, username: str) -> None:
        """Ensure user has stats initialized with all required fields."""
        if username not in self.user_stats:
            self.user_stats[username] = {
                "tweets": 0,
                "following_count": 0,
                "followers_count": 0,
                "retweets": 0
            }
        else:
            # Ensure all required fields exist, even if loaded from scenario
            default_stats = {
                "tweets": 0,
                "following_count": 0,
                "followers_count": 0,
                "retweets": 0
            }
            # Merge with existing stats, preserving existing values but adding missing fields
            for key, default_value in default_stats.items():
                if key not in self.user_stats[username]:
                    self.user_stats[username][key] = default_value
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = PostingScenario(**scenario)
        self.users = model.users
        self.tweets = model.tweets
        self.comments = model.comments
        self.follow_relationships = model.follow_relationships
        self.current_session = model.current_session
        self.next_tweet_id = model.next_tweet_id
        self.next_comment_id = model.next_comment_id
        self.user_stats = model.user_stats
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "users": {username: user.model_dump() for username, user in self.users.items()},
            "tweets": {tweet_id: tweet.model_dump() for tweet_id, tweet in self.tweets.items()},
            "comments": {comment_id: comment.model_dump() for comment_id, comment in self.comments.items()},
            "follow_relationships": [rel.model_dump() for rel in self.follow_relationships],
            "current_session": self.current_session,
            "next_tweet_id": self.next_tweet_id,
            "next_comment_id": self.next_comment_id,
            "user_stats": self.user_stats,
            "current_time": self.current_time
        }

    def login(self, username: str, password: str) -> dict:
        """Authenticate user with credentials."""
        if username not in self.users:
            return {"success": False}
        
        user = self.users[username]
        if user.password != password:
            return {"success": False}
        
        session_token = str(uuid.uuid4())
        self.current_session = {
            "username": username,
            "session_token": session_token
        }
        
        return {
            "success": True,
            "session_token": session_token,
            "username": username
        }

    def logout(self) -> dict:
        """Terminate current user session."""
        if self.current_session is None:
            return {"success": False}
        
        self.current_session = None
        return {"success": True}

    def check_login_status(self) -> dict:
        """Verify current authentication status."""
        if self.current_session is None:
            return {"is_authenticated": False}
        
        return {
            "is_authenticated": True,
            "username": self.current_session["username"]
        }

    def create_tweet(self, content: str, hashtags: Optional[List[str]] = None, mentions: Optional[List[str]] = None) -> dict:
        """Create a new tweet for authenticated user."""
        if self.current_session is None:
            raise ValueError("User not authenticated")
        
        username = self.current_session["username"]
        now = self.current_time
        
        # Validate hashtags and mentions format - allow with or without prefixes
        processed_hashtags = []
        if hashtags:
            for tag in hashtags:
                if not tag.startswith('#'):
                    processed_hashtags.append('#' + tag)
                else:
                    processed_hashtags.append(tag)
        
        processed_mentions = []
        if mentions:
            for mention in mentions:
                if not mention.startswith('@'):
                    processed_mentions.append('@' + mention)
                else:
                    processed_mentions.append(mention)
        
        tweet = Tweet(
            tweet_id=self.next_tweet_id,
            username=username,
            content=content,
            hashtags=processed_hashtags,
            mentions=processed_mentions,
            created_at=now
        )
        
        self.tweets[self.next_tweet_id] = tweet
        self.next_tweet_id += 1
        
        # Update user stats
        self._ensure_user_stats(username)
        self.user_stats[username]["tweets"] += 1
        
        return {
            "tweet_id": tweet.tweet_id,
            "username": tweet.username,
            "content": tweet.content,
            "hashtags": tweet.hashtags,
            "mentions": tweet.mentions,
            "created_at": tweet.created_at
        }

    def get_tweet(self, tweet_id: int) -> dict:
        """Retrieve detailed tweet information."""
        if tweet_id not in self.tweets:
            raise ValueError(f"Tweet {tweet_id} not found")
        
        tweet = self.tweets[tweet_id]
        return {
            "tweet_id": tweet.tweet_id,
            "username": tweet.username,
            "content": tweet.content,
            "hashtags": tweet.hashtags,
            "mentions": tweet.mentions,
            "created_at": tweet.created_at,
            "retweet_count": tweet.retweet_count,
            "comment_count": tweet.comment_count
        }

    def list_tweets(self, username: Optional[str] = None, limit: int = 5, offset: int = 0) -> dict:
        """List tweets with optional filtering."""
        tweets_list = []
        
        # Determine which tweets to show
        if username:
            # Show tweets by specific user
            user_tweets = [t for t in self.tweets.values() if t.username == username]
            tweets_to_show = user_tweets
        elif self.current_session:
            # Show tweets from followed users
            current_username = self.current_session["username"]
            followed_users = [rel.following for rel in self.follow_relationships if rel.follower == current_username]
            followed_tweets = [t for t in self.tweets.values() if t.username in followed_users or t.username == current_username]
            tweets_to_show = followed_tweets
        else:
            # Show all tweets for non-authenticated users
            tweets_to_show = list(self.tweets.values())
        
        # Sort by creation time (newest first)
        tweets_to_show.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        paginated_tweets = tweets_to_show[offset:offset + limit]
        
        for tweet in paginated_tweets:
            tweets_list.append({
                "tweet_id": tweet.tweet_id,
                "username": tweet.username,
                "content": tweet.content,
                "created_at": tweet.created_at,
                "retweet_count": tweet.retweet_count,
                "comment_count": tweet.comment_count
            })
        
        return {"tweets": tweets_list}

    def search_tweets(self, query: str, limit: int = 5) -> dict:
        """Search tweets by keyword in content or hashtags."""
        matching_tweets = []
        
        for tweet in self.tweets.values():
            # Search in content (case-insensitive)
            content_match = query.lower() in tweet.content.lower()
            
            # Search in hashtags
            hashtag_match = any(query.lower() in tag.lower() for tag in tweet.hashtags)
            
            if content_match or hashtag_match:
                matching_tweets.append(tweet)
        
        # Sort by creation time (newest first)
        matching_tweets.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        limited_tweets = matching_tweets[:limit]
        
        results = []
        for tweet in limited_tweets:
            results.append({
                "tweet_id": tweet.tweet_id,
                "username": tweet.username,
                "content": tweet.content,
                "hashtags": tweet.hashtags,
                "created_at": tweet.created_at,
                "retweet_count": tweet.retweet_count,
                "comment_count": tweet.comment_count
            })
        
        return {"tweets": results}

    def update_tweet(self, tweet_id: int, content: Optional[str] = None, hashtags: Optional[List[str]] = None, mentions: Optional[List[str]] = None) -> dict:
        """Update existing tweet content."""
        if self.current_session is None:
            raise ValueError("User not authenticated")
        
        if tweet_id not in self.tweets:
            raise ValueError(f"Tweet {tweet_id} not found")
        
        tweet = self.tweets[tweet_id]
        if tweet.username != self.current_session["username"]:
            raise ValueError("Can only update your own tweets")
        
        updated_fields = []
        now = self.current_time
        
        if content is not None:
            tweet.content = content
            updated_fields.append("content")
        
        if hashtags is not None:
            # Process hashtags - allow with or without prefixes
            processed_hashtags = []
            for tag in hashtags:
                if not tag.startswith('#'):
                    processed_hashtags.append('#' + tag)
                else:
                    processed_hashtags.append(tag)
            tweet.hashtags = processed_hashtags
            updated_fields.append("hashtags")
        
        if mentions is not None:
            # Process mentions - allow with or without prefixes
            processed_mentions = []
            for mention in mentions:
                if not mention.startswith('@'):
                    processed_mentions.append('@' + mention)
                else:
                    processed_mentions.append(mention)
            tweet.mentions = processed_mentions
            updated_fields.append("mentions")
        
        if updated_fields:
            tweet.updated_at = now
        
        return {
            "tweet_id": tweet_id,
            "success": True,
            "updated_at": tweet.updated_at,
            "updated_fields": updated_fields
        }

    def delete_tweet(self, tweet_id: int) -> dict:
        """Delete a tweet."""
        if self.current_session is None:
            raise ValueError("User not authenticated")
        
        if tweet_id not in self.tweets:
            raise ValueError(f"Tweet {tweet_id} not found")
        
        tweet = self.tweets[tweet_id]
        if tweet.username != self.current_session["username"]:
            raise ValueError("Can only delete your own tweets")
        
        # Delete the tweet
        del self.tweets[tweet_id]
        
        # Update user stats
        username = tweet.username
        self._ensure_user_stats(username)
        if "tweets" in self.user_stats[username] and self.user_stats[username]["tweets"] > 0:
            self.user_stats[username]["tweets"] -= 1
        
        return {
            "tweet_id": tweet_id,
            "success": True,
            "message": f"Tweet {tweet_id} successfully deleted"
        }

    def retweet(self, tweet_id: int) -> dict:
        """Retweet an existing tweet."""
        if self.current_session is None:
            raise ValueError("User not authenticated")
        
        if tweet_id not in self.tweets:
            raise ValueError(f"Tweet {tweet_id} not found")
        
        current_username = self.current_session["username"]
        tweet = self.tweets[tweet_id]
        
        # Check if already retweeted (simple check - in real system would need retweet tracking)
        # For this implementation, we'll allow multiple retweets from same user
        
        tweet.retweet_count += 1
        
        # Update user stats
        self._ensure_user_stats(current_username)
        self.user_stats[current_username]["retweets"] += 1
        
        now = self.current_time
        
        return {
            "success": True,
            "message": "Successfully retweeted",
            "retweeted_at": now
        }

    def add_comment(self, tweet_id: int, comment_content: str) -> dict:
        """Add a comment to a tweet."""
        if self.current_session is None:
            raise ValueError("User not authenticated")
        
        if tweet_id not in self.tweets:
            raise ValueError(f"Tweet {tweet_id} not found")
        
        username = self.current_session["username"]
        now = self.current_time
        
        comment = Comment(
            comment_id=self.next_comment_id,
            tweet_id=tweet_id,
            username=username,
            comment_content=comment_content,
            created_at=now
        )
        
        self.comments[self.next_comment_id] = comment
        self.next_comment_id += 1
        
        # Update tweet comment count
        self.tweets[tweet_id].comment_count += 1
        
        return {
            "comment_id": comment.comment_id,
            "tweet_id": tweet_id,
            "username": username,
            "comment_content": comment_content,
            "created_at": now
        }

    def get_tweet_comments(self, tweet_id: int, limit: int = 50, offset: int = 0) -> dict:
        """Get comments for a specific tweet."""
        if tweet_id not in self.tweets:
            raise ValueError(f"Tweet {tweet_id} not found")
        
        # Get all comments for this tweet
        tweet_comments = [c for c in self.comments.values() if c.tweet_id == tweet_id]
        
        # Sort by creation time (newest first)
        tweet_comments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        paginated_comments = tweet_comments[offset:offset + limit]
        
        comments_list = []
        for comment in paginated_comments:
            comments_list.append({
                "comment_id": comment.comment_id,
                "tweet_id": comment.tweet_id,
                "username": comment.username,
                "comment_content": comment.comment_content,
                "created_at": comment.created_at
            })
        
        return {"comments": comments_list}

    def follow_user(self, username: str) -> dict:
        """Follow another user."""
        if self.current_session is None:
            raise ValueError("User not authenticated")
        
        if username not in self.users:
            raise ValueError(f"User {username} not found")
        
        current_username = self.current_session["username"]
        
        # Check if already following
        for rel in self.follow_relationships:
            if rel.follower == current_username and rel.following == username:
                return {
                    "success": False,
                    "message": "Already following"
                }
        
        # Can't follow yourself
        if current_username == username:
            raise ValueError("Cannot follow yourself")
        
        now = self.current_time
        
        follow_rel = FollowRelationship(
            follower=current_username,
            following=username,
            followed_at=now
        )
        
        self.follow_relationships.append(follow_rel)
        
        # Update user stats
        self._ensure_user_stats(current_username)
        self._ensure_user_stats(username)
        
        self.user_stats[current_username]["following_count"] += 1
        self.user_stats[username]["followers_count"] += 1
        
        return {
            "success": True,
            "message": "Successfully followed",
            "followed_at": now
        }

    def unfollow_user(self, username: str) -> dict:
        """Unfollow a user."""
        if self.current_session is None:
            raise ValueError("User not authenticated")
        
        current_username = self.current_session["username"]
        
        # Find and remove the follow relationship
        relationship_found = False
        for i, rel in enumerate(self.follow_relationships):
            if rel.follower == current_username and rel.following == username:
                del self.follow_relationships[i]
                relationship_found = True
                break
        
        if not relationship_found:
            return {
                "success": False,
                "message": "Not following"
            }
        
        # Update user stats
        self._ensure_user_stats(current_username)
        self._ensure_user_stats(username)
        
        if self.user_stats[current_username]["following_count"] > 0:
            self.user_stats[current_username]["following_count"] -= 1
        if self.user_stats[username]["followers_count"] > 0:
            self.user_stats[username]["followers_count"] -= 1
        
        return {
            "success": True,
            "message": "Successfully unfollowed"
        }

    def list_following(self, username: Optional[str] = None, limit: int = 50, offset: int = 0) -> dict:
        """List users that a specific user is following."""
        if username is None:
            if self.current_session is None:
                raise ValueError("Must provide username or be authenticated")
            target_username = self.current_session["username"]
        else:
            if username not in self.users:
                raise ValueError(f"User {username} not found")
            target_username = username
        
        # Get all users this person is following
        following = [rel for rel in self.follow_relationships if rel.follower == target_username]
        
        # Apply pagination
        paginated_following = following[offset:offset + limit]
        
        following_list = []
        for rel in paginated_following:
            following_list.append({
                "username": rel.following,
                "followed_at": rel.followed_at
            })
        
        return {"following": following_list}

    def list_followers(self, username: Optional[str] = None, limit: int = 50, offset: int = 0) -> dict:
        """List users that follow a specific user."""
        if username is None:
            if self.current_session is None:
                raise ValueError("Must provide username or be authenticated")
            target_username = self.current_session["username"]
        else:
            if username not in self.users:
                raise ValueError(f"User {username} not found")
            target_username = username
        
        # Get all users following this person
        followers = [rel for rel in self.follow_relationships if rel.following == target_username]
        
        # Apply pagination
        paginated_followers = followers[offset:offset + limit]
        
        followers_list = []
        for rel in paginated_followers:
            followers_list.append({
                "username": rel.follower,
                "followed_at": rel.followed_at
            })
        
        return {"followers": followers_list}

    def get_user_stats(self, username: Optional[str] = None) -> dict:
        """Get statistics for a user."""
        if username is None:
            if self.current_session is None:
                raise ValueError("Must provide username or be authenticated")
            target_username = self.current_session["username"]
        else:
            if username not in self.users:
                raise ValueError(f"User {username} not found")
            target_username = username
        
        # Get or create stats
        self._ensure_user_stats(target_username)
        
        stats = self.user_stats[target_username]
        
        return {
            "username": target_username,
            "tweet_count": stats.get("tweets", 0),
            "following_count": stats.get("following_count", 0),
            "followers_count": stats.get("followers_count", 0),
            "retweet_count": stats.get("retweets", 0)
        }

# Section 3: MCP Tools
mcp = FastMCP(name="PostingAPI")
api = PostingAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the posting API."""
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current posting state as scenario dictionary."""
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def login(username: str, password: str) -> dict:
    """Authenticate a user with credentials."""
    try:
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        return api.login(username, password)
    except Exception as e:
        raise e

@mcp.tool()
def logout() -> dict:
    """Terminate the current user session."""
    try:
        return api.logout()
    except Exception as e:
        raise e

@mcp.tool()
def check_login_status() -> dict:
    """Verify whether a user session is currently active."""
    try:
        return api.check_login_status()
    except Exception as e:
        raise e

@mcp.tool()
def create_tweet(content: str, hashtags: Optional[List[str]] = None, mentions: Optional[List[str]] = None) -> dict:
    """Publish a new tweet with optional hashtags and mentions."""
    try:
        if not content or not isinstance(content, str):
            raise ValueError("Content must be a non-empty string")
        return api.create_tweet(content, hashtags, mentions)
    except Exception as e:
        raise e

@mcp.tool()
def get_tweet(tweet_id: int) -> dict:
    """Retrieve detailed information about a specific tweet."""
    try:
        if not isinstance(tweet_id, int) or tweet_id < 0:
            raise ValueError("Tweet ID must be a non-negative integer")
        return api.get_tweet(tweet_id)
    except Exception as e:
        raise e

@mcp.tool()
def list_tweets(username: Optional[str] = None, limit: int = 5, offset: int = 0) -> dict:
    """Retrieve a paginated list of tweets."""
    try:
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        return api.list_tweets(username, limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def search_tweets(query: str, limit: int = 5) -> dict:
    """Search for tweets containing a specific keyword."""
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        return api.search_tweets(query, limit)
    except Exception as e:
        raise e

@mcp.tool()
def update_tweet(tweet_id: int, content: Optional[str] = None, hashtags: Optional[List[str]] = None, mentions: Optional[List[str]] = None) -> dict:
    """Modify an existing tweet's content, hashtags, or mentions."""
    try:
        if not isinstance(tweet_id, int) or tweet_id < 0:
            raise ValueError("Tweet ID must be a non-negative integer")
        return api.update_tweet(tweet_id, content, hashtags, mentions)
    except Exception as e:
        raise e

@mcp.tool()
def delete_tweet(tweet_id: int) -> dict:
    """Permanently remove a tweet from the system."""
    try:
        if not isinstance(tweet_id, int) or tweet_id < 0:
            raise ValueError("Tweet ID must be a non-negative integer")
        return api.delete_tweet(tweet_id)
    except Exception as e:
        raise e

@mcp.tool()
def retweet(tweet_id: int) -> dict:
    """Share an existing tweet by retweeting it."""
    try:
        if not isinstance(tweet_id, int) or tweet_id < 0:
            raise ValueError("Tweet ID must be a non-negative integer")
        return api.retweet(tweet_id)
    except Exception as e:
        raise e

@mcp.tool()
def add_comment(tweet_id: int, comment_content: str) -> dict:
    """Post a comment on an existing tweet."""
    try:
        if not isinstance(tweet_id, int) or tweet_id < 0:
            raise ValueError("Tweet ID must be a non-negative integer")
        if not comment_content or not isinstance(comment_content, str):
            raise ValueError("Comment content must be a non-empty string")
        return api.add_comment(tweet_id, comment_content)
    except Exception as e:
        raise e

@mcp.tool()
def get_tweet_comments(tweet_id: int, limit: int = 50, offset: int = 0) -> dict:
    """Retrieve all comments posted on a specific tweet."""
    try:
        if not isinstance(tweet_id, int) or tweet_id < 0:
            raise ValueError("Tweet ID must be a non-negative integer")
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        return api.get_tweet_comments(tweet_id, limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def follow_user(username: str) -> dict:
    """Establish a following relationship with another user."""
    try:
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        return api.follow_user(username)
    except Exception as e:
        raise e

@mcp.tool()
def unfollow_user(username: str) -> dict:
    """Remove an existing following relationship."""
    try:
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        return api.unfollow_user(username)
    except Exception as e:
        raise e

@mcp.tool()
def list_following(username: Optional[str] = None, limit: int = 50, offset: int = 0) -> dict:
    """Retrieve a paginated list of users that a specific user is following."""
    try:
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        return api.list_following(username, limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def list_followers(username: Optional[str] = None, limit: int = 50, offset: int = 0) -> dict:
    """Retrieve a paginated list of users that follow a specific user."""
    try:
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        return api.list_followers(username, limit, offset)
    except Exception as e:
        raise e

@mcp.tool()
def get_user_stats(username: Optional[str] = None) -> dict:
    """Retrieve comprehensive statistics for a user."""
    try:
        return api.get_user_stats(username)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()