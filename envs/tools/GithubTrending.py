from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Repository(BaseModel):
    """Represents a trending GitHub repository."""
    rank: int = Field(..., ge=1, description="The repository's position in the trending list")
    name: str = Field(..., description="The short name of the repository")
    fullname: str = Field(..., description="The full name of the repository in the format \"owner/repo\"")
    url: str = Field(..., description="The URL to the repository on GitHub")
    description: str = Field(default="", description="A brief description of the repository's purpose and functionality")
    language: str = Field(default="", description="The primary programming language used in the repository")
    stars: int = Field(..., ge=0, description="The total number of stars the repository has received")
    forks: int = Field(..., ge=0, description="The total number of times the repository has been forked")
    current_period_stars: int = Field(..., ge=0, description="The number of stars gained during the specified trending period")

class Developer(BaseModel):
    """Represents a trending GitHub developer."""
    rank: int = Field(..., ge=1, description="The developer's position in the trending list")
    username: str = Field(..., description="The GitHub username of the developer")
    name: str = Field(default="", description="The display name of the developer")
    url: str = Field(..., description="The URL to the developer's GitHub profile")
    avatar: str = Field(default="", description="The URL to the developer's avatar image")
    repo: Dict[str, Any] = Field(default={}, description="The featured repository associated with the trending developer")

class GithubTrendingScenario(BaseModel):
    """Main scenario model for GitHub trending data."""
    repositories: Dict[str, List[Repository]] = Field(default={}, description="Cached trending repositories by filter key")
    developers: Dict[str, List[Developer]] = Field(default={}, description="Cached trending developers by filter key")
    languageCodesMap: Dict[str, str] = Field(default={
        "python": "Python", "javascript": "JavaScript", "cpp": "C++", "csharp": "C#", 
        "go": "Go", "rust": "Rust", "java": "Java", "typescript": "TypeScript",
        "ruby": "Ruby", "php": "PHP", "swift": "Swift", "kotlin": "Kotlin",
        "scala": "Scala", "r": "R", "matlab": "MATLAB", "perl": "Perl",
        "objectivec": "Objective-C", "shell": "Shell", "powershell": "PowerShell"
    }, description="Valid programming language codes mapping")
    spokenLanguageCodesMap: Dict[str, str] = Field(default={
        "en": "English", "zh": "Chinese", "ja": "Japanese", "es": "Spanish",
        "fr": "French", "de": "German", "ko": "Korean", "ru": "Russian",
        "pt": "Portuguese", "it": "Italian", "ar": "Arabic", "hi": "Hindi",
        "nl": "Dutch", "tr": "Turkish", "pl": "Polish", "vi": "Vietnamese",
        "th": "Thai", "id": "Indonesian", "ms": "Malay", "uk": "Ukrainian"
    }, description="Valid spoken language codes mapping")
    periodOptionsMap: Dict[str, str] = Field(default={
        "daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"
    }, description="Valid period options mapping")

Scenario_Schema = [Repository, Developer, GithubTrendingScenario]

# Section 2: Class
class GithubTrendingAPI:
    def __init__(self):
        """Initialize GitHub trending API with empty state."""
        self.repositories: Dict[str, List[Repository]] = {}
        self.developers: Dict[str, List[Developer]] = {}
        self.languageCodesMap: Dict[str, str] = {}
        self.spokenLanguageCodesMap: Dict[str, str] = {}
        self.periodOptionsMap: Dict[str, str] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = GithubTrendingScenario(**scenario)
        self.repositories = model.repositories
        self.developers = model.developers
        self.languageCodesMap = model.languageCodesMap
        self.spokenLanguageCodesMap = model.spokenLanguageCodesMap
        self.periodOptionsMap = model.periodOptionsMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "repositories": {k: [repo.model_dump() for repo in v] for k, v in self.repositories.items()},
            "developers": {k: [dev.model_dump() for dev in v] for k, v in self.developers.items()},
            "languageCodesMap": self.languageCodesMap,
            "spokenLanguageCodesMap": self.spokenLanguageCodesMap,
            "periodOptionsMap": self.periodOptionsMap
        }

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        parts = [prefix]
        for key, value in sorted(kwargs.items()):
            if value is not None:
                parts.append(f"{key}:{value}")
        return "|".join(parts)

    def get_github_trending_repositories(self, language: Optional[str] = None, period: Optional[str] = None, spoken_language: Optional[str] = None, limit: Optional[int] = None) -> dict:
        """Retrieve trending repositories based on filters."""
        cache_key = self._generate_cache_key("repos", language=language, period=period, spoken_language=spoken_language)
        
        if cache_key in self.repositories:
            repos = self.repositories[cache_key]
        else:
            repos = []
            base_stars = 1000
            for i in range(1, 51):
                repo_lang = language if language and language in self.languageCodesMap else ("python" if i % 3 == 0 else "javascript" if i % 3 == 1 else "go")
                repo = Repository(
                    rank=i,
                    name=f"trending-repo-{i}",
                    fullname=f"user{i}/trending-repo-{i}",
                    url=f"https://github.com/user{i}/trending-repo-{i}",
                    description=f"A trending repository number {i} written in {self.languageCodesMap.get(repo_lang, repo_lang)}",
                    language=self.languageCodesMap.get(repo_lang, repo_lang),
                    stars=base_stars + (50 - i) * 10,
                    forks=(base_stars + (50 - i) * 10) // 3,
                    current_period_stars=(50 - i) * 2 + 10
                )
                repos.append(repo)
            self.repositories[cache_key] = repos
        
        if limit:
            repos = repos[:limit]
        
        return {"repositories": [repo.model_dump() for repo in repos]}

    def get_github_trending_developers(self, language: Optional[str] = None, period: Optional[str] = None, limit: Optional[int] = None) -> dict:
        """Retrieve trending developers based on filters."""
        cache_key = self._generate_cache_key("devs", language=language, period=period)
        
        if cache_key in self.developers:
            devs = self.developers[cache_key]
        else:
            devs = []
            for i in range(1, 51):
                dev_lang = language if language and language in self.languageCodesMap else ("python" if i % 3 == 0 else "javascript" if i % 3 == 1 else "go")
                dev = Developer(
                    rank=i,
                    username=f"trendingdev{i}",
                    name=f"Trending Developer {i}",
                    url=f"https://github.com/trendingdev{i}",
                    avatar=f"https://avatars.githubusercontent.com/u/{1000 + i}",
                    repo={
                        "name": f"awesome-{dev_lang}-project",
                        "description": f"An awesome project written in {self.languageCodesMap.get(dev_lang, dev_lang)}",
                        "url": f"https://github.com/trendingdev{i}/awesome-{dev_lang}-project"
                    }
                )
                devs.append(dev)
            self.developers[cache_key] = devs
        
        if limit:
            devs = devs[:limit]
        
        return {"developers": [dev.model_dump() for dev in devs]}

# Section 3: MCP Tools
mcp = FastMCP(name="GithubTrending")
api = GithubTrendingAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the GitHub trending API.
    
    Args:
        scenario (dict): Scenario dictionary matching GithubTrendingScenario schema.
    
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
    """Save current GitHub trending state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_github_trending_repositories(language: Optional[str] = None, period: Optional[str] = None, spoken_language: Optional[str] = None, limit: Optional[int] = None) -> dict:
    """Retrieve trending repositories from GitHub based on specified filters.
    
    Args:
        language (str) [Optional]: Programming language to filter by. Must be lowercase letters only.
        period (str) [Optional]: Time period for trending calculation. Valid values are "daily", "weekly", or "monthly".
        spoken_language (str) [Optional]: Spoken language to filter by. Must be an ISO 639-1 two-letter language code.
        limit (int) [Optional]: Maximum number of repositories to return.
    
    Returns:
        repositories (list): List of trending GitHub repositories matching the filters.
    """
    try:
        # Basic parameter checks
        if language and not isinstance(language, str):
            raise ValueError("Language must be a string")
        if period and period not in api.periodOptionsMap:
            raise ValueError(f"Period must be one of: {list(api.periodOptionsMap.keys())}")
        if spoken_language and spoken_language not in api.spokenLanguageCodesMap:
            raise ValueError(f"Spoken language must be one of: {list(api.spokenLanguageCodesMap.keys())}")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        
        return api.get_github_trending_repositories(language, period, spoken_language, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_github_trending_developers(language: Optional[str] = None, period: Optional[str] = None, limit: Optional[int] = None) -> dict:
    """Retrieve trending developers from GitHub based on specified filters.
    
    Args:
        language (str) [Optional]: Programming language to filter by. Must be lowercase letters only.
        period (str) [Optional]: Time period for trending calculation. Valid values are "daily", "weekly", or "monthly".
        limit (int) [Optional]: Maximum number of developers to return.
    
    Returns:
        developers (list): List of trending GitHub developers matching the filters.
    """
    try:
        # Basic parameter checks
        if language and not isinstance(language, str):
            raise ValueError("Language must be a string")
        if period and period not in api.periodOptionsMap:
            raise ValueError(f"Period must be one of: {list(api.periodOptionsMap.keys())}")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("Limit must be a positive integer")
        
        return api.get_github_trending_developers(language, period, limit)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()