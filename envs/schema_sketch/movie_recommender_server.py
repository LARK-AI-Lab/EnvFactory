# Server: MovieRecommender

def get_movies(keyword: str, limit: int = None) -> list:
    """
    Get movie suggestions from TMDb API based on keyword.
    
    Args:
        keyword (str): Search keyword for movie title or description
        limit (int): [Optional] Maximum number of results to return
        
    Returns:
        list: Each movie contains {
            "movie_id": int,
            "title": str,
            "overview": str,
            "release_date": str (YYYY-MM-DD),
        }
    """
    pass

def get_movie_details(movie_id: int) -> dict:
    """
    Get detailed information for a specific movie.
    
    Args:
        movie_id (int): Unique identifier of the movie from TMDb
        
    Returns:
        dict: {
            "movie_id": int,
            "title": str,
            "overview": str,
            "release_date": str (YYYY-MM-DD),
            "duration": int,
            "genres": list[str],
            "vote_average": float,
            'views': int,
            "actors": list[str],
        }
    """
    pass

def get_popular_movies(filter: str = "vote_average", date: str = None, limit: int = 5) -> list:
    """
    Get currently popular movies from TMDb, optionally filtered by date.
    
    Args:
        filter (str): [Optional] Filter by "vote_average" or "views".
        date (str): [Optional] Date to filter movies by (YYYY-MM-DD)
        limit (int): [Optional] Maximum number of results to return, default is 5.
        
    Returns:
        list: Each movie contains {
            "movie_id": int,
            "title": str,
            "overview": str,
            "release_date": str (YYYY-MM-DD),
            "vote_average": float,
            'views': int,
            "actors": list[str],
        }
    """
    pass

