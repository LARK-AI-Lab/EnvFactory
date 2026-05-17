from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Movie(BaseModel):
    """Represents a movie with basic information."""
    movie_id: int = Field(..., ge=0, description="The unique identifier of the movie from TMDb")
    title: str = Field(..., description="The official title of the movie")
    overview: str = Field(default="", description="A brief synopsis or description of the movie's plot")
    release_date: str = Field(default="", pattern=r"^\d{4}-\d{2}-\d{2}$", description="The theatrical release date of the movie in YYYY-MM-DD format")

class MovieDetails(BaseModel):
    """Represents detailed movie information."""
    movie_id: int = Field(..., ge=0, description="The unique identifier of the movie from TMDb")
    title: str = Field(..., description="The official title of the movie")
    overview: str = Field(default="", description="A brief synopsis or description of the movie's plot")
    release_date: str = Field(default="", pattern=r"^\d{4}-\d{2}-\d{2}$", description="The theatrical release date of the movie in YYYY-MM-DD format")
    duration: int = Field(default=0, ge=0, description="The runtime of the movie in minutes")
    genres: List[str] = Field(default=[], description="List of genre categories the movie belongs to")
    vote_average: float = Field(default=0.0, ge=0, le=10, description="The average user rating score for the movie on TMDb")
    views: int = Field(default=0, ge=0, description="The total number of views or popularity count for the movie")
    actors: List[str] = Field(default=[], description="List of main actors appearing in the movie")

class MovieRecommenderScenario(BaseModel):
    """Main scenario model for movie recommender service."""
    movies: Dict[int, MovieDetails] = Field(default={}, description="Movies database")
    popular_movies: List[int] = Field(default=[], description="List of popular movie IDs")
    api_key: str = Field(default="demo_key", description="TMDb API key")
    
Scenario_Schema = [Movie, MovieDetails, MovieRecommenderScenario]

# Section 2: Class
class MovieRecommenderAPI:
    def __init__(self):
        """Initialize movie recommender API with empty state."""
        self.movies: Dict[int, MovieDetails] = {}
        self.popular_movies: List[int] = []
        self.api_key: str = ""
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = MovieRecommenderScenario(**scenario)
        self.movies = model.movies
        self.popular_movies = model.popular_movies
        self.api_key = model.api_key

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "movies": {movie_id: movie.model_dump() for movie_id, movie in self.movies.items()},
            "popular_movies": self.popular_movies,
            "api_key": self.api_key
        }

    def get_movies(self, keyword: str, limit: Optional[int] = 5) -> dict:
        """Search for movies matching keyword."""
        if limit is None:
            limit = 5
        matches = []
        for movie in self.movies.values():
            if keyword.lower() in movie.title.lower() or keyword.lower() in movie.overview.lower():
                matches.append({
                    "movie_id": movie.movie_id,
                    "title": movie.title,
                    "overview": movie.overview,
                    "release_date": movie.release_date
                })
                if len(matches) >= limit:
                    break
        return {"movies": matches}

    def get_movie_details(self, movie_id: int) -> dict:
        """Retrieve detailed information for a specific movie."""
        movie = self.movies[movie_id]
        return {
            "movie_id": movie.movie_id,
            "title": movie.title,
            "overview": movie.overview,
            "release_date": movie.release_date,
            "duration": movie.duration,
            "genres": movie.genres,
            "vote_average": movie.vote_average,
            "views": movie.views,
            "actors": movie.actors
        }

    def get_popular_movies(self, filter: Optional[str] = None, date: Optional[str] = None, limit: Optional[int] = 5) -> dict:
        """Retrieve popular movies with optional filtering."""
        if limit is None:
            limit = 5
        popular_list = []
        for movie_id in self.popular_movies:
            if movie_id in self.movies:
                movie = self.movies[movie_id]
                if date and movie.release_date < date:
                    continue
                popular_list.append(movie)
        
        if filter == "vote_average":
            popular_list.sort(key=lambda x: x.vote_average, reverse=True)
        elif filter == "views":
            popular_list.sort(key=lambda x: x.views, reverse=True)
        
        result_movies = []
        for movie in popular_list[:limit]:
            result_movies.append({
                "movie_id": movie.movie_id,
                "title": movie.title,
                "overview": movie.overview,
                "release_date": movie.release_date,
                "vote_average": movie.vote_average,
                "views": movie.views,
                "actors": movie.actors
            })
        return {"movies": result_movies}

# Section 3: MCP Tools
mcp = FastMCP(name="MovieRecommender")
api = MovieRecommenderAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the movie recommender API.
    
    Args:
        scenario (dict): Scenario dictionary matching MovieRecommenderScenario schema.
    
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
    Save current movie recommender state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_movies(keyword: str, limit: Optional[int] = 5) -> dict:
    """
    Search for movie suggestions from TMDb based on a keyword matching movie titles or descriptions.
    
    Args:
        keyword (str): Search keyword to match against movie titles or descriptions.
        limit (int): [Optional] Maximum number of movie results to return.
    
    Returns:
        movies (list): List of movies matching the search keyword.
    """
    try:
        if not keyword or not isinstance(keyword, str):
            raise ValueError("Keyword must be a non-empty string")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.get_movies(keyword, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_movie_details(movie_id: int) -> dict:
    """
    Retrieve detailed information for a specific movie including cast, genres, and ratings.
    
    Args:
        movie_id (int): The unique identifier of the movie from TMDb.
    
    Returns:
        movie_id (int): The unique identifier of the movie from TMDb.
        title (str): The official title of the movie.
        overview (str): A brief synopsis or description of the movie's plot.
        release_date (str): The theatrical release date of the movie in YYYY-MM-DD format.
        duration (int): The runtime of the movie in minutes.
        genres (list): List of genre categories the movie belongs to.
        vote_average (float): The average user rating score for the movie on TMDb.
        views (int): The total number of views or popularity count for the movie.
        actors (list): List of main actors appearing in the movie.
    """
    try:
        if not isinstance(movie_id, int) or movie_id < 0:
            raise ValueError("Movie ID must be a non-negative integer")
        if movie_id not in api.movies:
            raise ValueError(f"Movie {movie_id} not found")
        return api.get_movie_details(movie_id)
    except Exception as e:
        raise e

@mcp.tool()
def get_popular_movies(filter: Optional[str] = None, date: Optional[str] = None, limit: Optional[int] = 5) -> dict:
    """
    Retrieve a list of currently popular movies from TMDb, with optional filtering by rating, views, or release date.
    
    Args:
        filter (str): [Optional] Sorting criteria for popularity ranking. Accepts 'vote_average' for rating-based or 'views' for view count-based sorting.
        date (str): [Optional] Filter movies released on or after this date in YYYY-MM-DD format.
        limit (int): [Optional] Maximum number of movie results to return. Defaults to 5 if not specified.
    
    Returns:
        movies (list): List of popular movies matching the specified filter criteria.
    """
    try:
        if filter is not None and filter not in ["vote_average", "views"]:
            raise ValueError("Filter must be either 'vote_average' or 'views'")
        if date is not None and (not isinstance(date, str) or len(date) != 10):
            raise ValueError("Date must be in YYYY-MM-DD format")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        return api.get_popular_movies(filter, date, limit)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()