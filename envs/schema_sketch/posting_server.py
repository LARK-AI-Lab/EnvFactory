# Server: Posting

def login(username: str, password: str) -> dict:
    """
    Authenticate user and establish session for posting operations.
    
    Args:
        username (str): The username for authentication
        password (str): The password for authentication
        
    Returns:
        dict: A dictionary containing success (bool) indicating login success or failure, session_token (str) [Optional] session token if login successful, username (str) [Optional] authenticated username.
    """
    pass

def logout() -> dict:
    """
    Log out the currently authenticated user and invalidate session.
    
    Returns:
        dict: A dictionary containing success (bool) indicating logout success or failure.
    """
    pass

def check_login_status() -> dict:
    """
    Check if a user is currently authenticated and session is valid.
    
    Returns:
        dict: A dictionary containing is_authenticated (bool) indicating current authentication status, username (str) [Optional] current authenticated username if logged in.
    """
    pass

def create_tweet(content: str, hashtags: list = None, mentions: list = None) -> dict:
    """
    Create a new tweet for the authenticated user. Requires authentication.
    
    Args:
        content (str): The text content of the tweet
        hashtags (list): [Optional] List of hashtags for the tweet. Each hashtag should start with # (e.g., ["#python", "#coding"]). If not provided, no hashtags are added.
        mentions (list): [Optional] List of usernames to mention in the tweet. Each mention should start with @ (e.g., ["@alice", "@bob"]). If not provided, no mentions are added.
        
    Returns:
        dict: A dictionary containing tweet_id (int) unique identifier of the created tweet, username (str) author username, content (str), hashtags (list[str]) list of hashtags, mentions (list[str]) list of mentioned usernames, created_at (str) timestamp in ISO 8601 format.
    """
    pass

def get_tweet(tweet_id: int) -> dict:
    """
    Get detailed information about a specific tweet by its ID.
    
    Args:
        tweet_id (int): The unique identifier of the tweet. Can be obtained from create_tweet, get_user_tweets, search_tweets, or list_tweets.
        
    Returns:
        dict: A dictionary containing tweet_id (int), username (str) author username, content (str), hashtags (list[str]), mentions (list[str]), created_at (str), retweet_count (int) number of retweets, comment_count (int) number of comments.
    """
    pass

def list_tweets(username: str = None, limit: int = 5, offset: int = 0) -> list:
    """
    List tweets with optional filtering and pagination. If username is provided, returns tweets from that user. If not provided and user is authenticated, returns tweets from followed users.
    
    Args:
        username (str): [Optional] Username to filter tweets by. If not provided and user is authenticated, returns tweets from followed users. If not authenticated, returns public tweets.
        limit (int): [Optional] Maximum number of tweets to return. Defaults to 5.
        offset (int): [Optional] Number of tweets to skip for pagination. Defaults to 0.
        
    Returns:
        list: A list of tweet summaries, each containing tweet_id (int), username (str), content (str), created_at (str), retweet_count (int), comment_count (int). Tweet IDs can be used with get_tweet for full information.
    """
    pass

def search_tweets(query: str, limit: int = 5) -> list:
    """
    Search for tweets containing a specific keyword in content or hashtags.
    
    Args:
        query (str): The search keyword to match against tweet content or hashtags
        limit (int): [Optional] Maximum number of results to return. Defaults to 5.
        
    Returns:
        list: A list of matching tweets, each containing tweet_id (int), username (str), content (str), hashtags (list[str]), created_at (str), retweet_count (int), comment_count (int). Tweet IDs can be used with get_tweet for full information.
    """
    pass

def update_tweet(tweet_id: int, content: str = None, hashtags: list = None, mentions: list = None) -> dict:
    """
    Update an existing tweet. Only the tweet author can update their own tweets. Requires authentication. All fields are optional for partial updates.
    
    Args:
        tweet_id (int): The unique identifier of the tweet to update. Can be obtained from create_tweet, get_user_tweets, or search_tweets.
        content (str): [Optional] New content for the tweet
        hashtags (list): [Optional] New list of hashtags. Each hashtag should start with #.
        mentions (list): [Optional] New list of mentions. Each mention should start with @.
        
    Returns:
        dict: A dictionary containing tweet_id (int), success (bool) indicating update success, updated_at (str) timestamp of the update, updated_fields (list[str]) list of fields that were updated.
    """
    pass

def delete_tweet(tweet_id: int) -> dict:
    """
    Delete a tweet. Only the tweet author can delete their own tweets. Requires authentication.
    
    Args:
        tweet_id (int): The unique identifier of the tweet to delete. Can be obtained from create_tweet, get_user_tweets, or search_tweets.
        
    Returns:
        dict: A dictionary containing tweet_id (int), success (bool) indicating deletion success, message (str) confirmation message.
    """
    pass

def retweet(tweet_id: int) -> dict:
    """
    Retweet a tweet for the authenticated user. Requires authentication.
    
    Args:
        tweet_id (int): The unique identifier of the tweet to retweet. Can be obtained from get_tweet, get_user_tweets, search_tweets, or list_tweets.
        
    Returns:
        dict: A dictionary containing success (bool) indicating retweet success or failure, message (str) status message (e.g., "Successfully retweeted" or "Already retweeted"), retweeted_at (str) [Optional] timestamp if successfully retweeted.
    """
    pass

def add_comment(tweet_id: int, comment_content: str) -> dict:
    """
    Add a comment to a tweet for the authenticated user. Requires authentication.
    
    Args:
        tweet_id (int): The unique identifier of the tweet to comment on. Can be obtained from get_tweet, get_user_tweets, search_tweets, or list_tweets.
        comment_content (str): The text content of the comment
        
    Returns:
        dict: A dictionary containing comment_id (int) unique identifier of the comment, tweet_id (int), username (str) comment author username, comment_content (str), created_at (str) timestamp in ISO 8601 format.
    """
    pass

def get_tweet_comments(tweet_id: int, limit: int = None, offset: int = None) -> list:
    """
    Retrieve all comments for a specific tweet.
    
    Args:
        tweet_id (int): The unique identifier of the tweet. Can be obtained from get_tweet, get_user_tweets, search_tweets, or list_tweets.
        limit (int): [Optional] Maximum number of comments to return. Defaults to 50.
        offset (int): [Optional] Number of comments to skip for pagination. Defaults to 0.
        
    Returns:
        list: A list of comments, each containing comment_id (int), tweet_id (int), username (str) comment author, comment_content (str), created_at (str).
    """
    pass

def follow_user(username: str) -> dict:
    """
    Follow a user for the authenticated user. Requires authentication.
    
    Args:
        username (str): Username of the user to follow
        
    Returns:
        dict: A dictionary containing success (bool) indicating follow success or failure, message (str) status message (e.g., "Successfully followed" or "Already following"), followed_at (str) [Optional] timestamp if successfully followed.
    """
    pass

def unfollow_user(username: str) -> dict:
    """
    Unfollow a user for the authenticated user. Requires authentication.
    
    Args:
        username (str): Username of the user to unfollow
        
    Returns:
        dict: A dictionary containing success (bool) indicating unfollow success or failure, message (str) status message (e.g., "Successfully unfollowed" or "Not following").
    """
    pass

def list_following(username: str = None, limit: int = None, offset: int = None) -> list:
    """
    List all users that a specific user or the authenticated user is following. Requires authentication if username is not provided.
    
    Args:
        username (str): [Optional] Username to get following list for. If not provided, returns following list for the current authenticated user.
        limit (int): [Optional] Maximum number of users to return. Defaults to 50.
        offset (int): [Optional] Number of users to skip for pagination. Defaults to 0.
        
    Returns:
        list: A list of usernames that the specified user is following, each entry contains username (str), followed_at (str) [Optional] timestamp when the user was followed.
    """
    pass

def list_followers(username: str = None, limit: int = None, offset: int = None) -> list:
    """
    List all users that follow a specific user or the authenticated user. Requires authentication if username is not provided.
    
    Args:
        username (str): [Optional] Username to get followers list for. If not provided, returns followers list for the current authenticated user.
        limit (int): [Optional] Maximum number of users to return. Defaults to 50.
        offset (int): [Optional] Number of users to skip for pagination. Defaults to 0.
        
    Returns:
        list: A list of usernames that follow the specified user, each entry contains username (str), followed_at (str) [Optional] timestamp when the user started following.
    """
    pass

def get_user_stats(username: str = None) -> dict:
    """
    Get statistics for a specific user or the authenticated user. Requires authentication if username is not provided.
    
    Args:
        username (str): [Optional] Username to get statistics for. If not provided, returns statistics for the current authenticated user.
        
    Returns:
        dict: A dictionary containing username (str), tweet_count (int) number of tweets posted by the user, following_count (int) number of users the user is following, followers_count (int) number of users following this user, retweet_count (int) number of retweets made by the user.
    """
    pass

