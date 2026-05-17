
import requests
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class SearchResult(BaseModel):
    """A single Wikipedia search result."""
    title: str = Field(..., description="Display title of the Wikipedia page")
    pageid: int = Field(..., description="Unique numeric identifier of the page")
    excerpt: str = Field(default="", description="Short text snippet highlighting matched context")
    description: str = Field(default="", description="Concise subtitle or description")
    thumbnail: Optional[Dict[str, Any]] = Field(default=None, description="Thumbnail image metadata")

class ArticleSection(BaseModel):
    """A section within a Wikipedia article."""
    title: str = Field(..., description="Heading text of the section")
    level: int = Field(..., ge=1, description="Nesting depth of the section")
    text: str = Field(default="", description="Content of the section")

class RelatedPage(BaseModel):
    """A related Wikipedia page."""
    title: str = Field(..., description="Display title of the related page")
    pageid: int = Field(..., description="Unique numeric identifier")
    extract: str = Field(default="", description="Brief summary extract")
    url: str = Field(default="", description="Canonical web URL")

class WikipediaScenario(BaseModel):
    """Main scenario model for Wikipedia server state."""
    default_language: str = Field(default="en", description="Default Wikipedia language code")
    default_search_limit: int = Field(default=5, ge=1, le=50, description="Default search result limit")
    default_related_limit: int = Field(default=10, ge=1, le=50, description="Default related pages limit")

Scenario_Schema = [SearchResult, ArticleSection, RelatedPage, WikipediaScenario]

# Section 2: Class
class WikipediaAPI:
    def __init__(self):
        """Initialize Wikipedia API with default state."""
        self.default_language: str = "en"
        self.default_search_limit: int = 5
        self.default_related_limit: int = 10

    def _base_url(self, language: str) -> str:
        """Return the MediaWiki REST API base URL for a given language."""
        return f"https://{language}.wikipedia.org/w/rest.php/v1"

    def _legacy_url(self, language: str) -> str:
        """Return the legacy MediaWiki API URL for a given language."""
        return f"https://{language}.wikipedia.org/w/api.php"

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = WikipediaScenario(**scenario)
        self.default_language = model.default_language
        self.default_search_limit = model.default_search_limit
        self.default_related_limit = model.default_related_limit

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "default_language": self.default_language,
            "default_search_limit": self.default_search_limit,
            "default_related_limit": self.default_related_limit,
        }

    def search_wikipedia(self, query: str, limit: int, language: str) -> dict:
        """Search Wikipedia and return ranked results with excerpts."""
        url = f"{self._base_url(language)}/search/page"
        resp = requests.get(url, params={"q": query, "limit": limit}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for page in data.get("pages", []):
            thumb = page.get("thumbnail")
            results.append({
                "title": page.get("title", ""),
                "pageid": page.get("id", 0),
                "excerpt": page.get("excerpt", ""),
                "description": page.get("description", ""),
                "thumbnail": {"url": thumb["url"], "width": thumb.get("width"), "height": thumb.get("height")} if thumb else None,
            })
        return {"query": query, "results": results}

    def get_article(self, title: str, language: str) -> dict:
        """Retrieve full article content and section breakdown."""
        # Get summary for metadata
        summary_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
        summary_resp = requests.get(summary_url, timeout=10)
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        # Get full wikitext sections via parse API
        parse_resp = requests.get(self._legacy_url(language), params={
            "action": "parse", "page": title, "prop": "sections|wikitext", "format": "json"
        }, timeout=10)
        parse_resp.raise_for_status()
        parse_data = parse_resp.json().get("parse", {})

        sections = []
        for s in parse_data.get("sections", []):
            sections.append({
                "title": s.get("line", ""),
                "level": int(s.get("level", 1)),
                "text": s.get("anchor", ""),
            })

        return {
            "title": summary_data.get("title", title),
            "pageid": summary_data.get("pageid", 0),
            "summary": summary_data.get("extract", ""),
            "text": parse_data.get("wikitext", {}).get("*", ""),
            "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "sections": sections,
        }

    def get_summary(self, title: str, language: str) -> dict:
        """Retrieve concise summary and metadata for a Wikipedia article."""
        url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        thumb = data.get("thumbnail")
        return {
            "title": data.get("title", title),
            "extract": data.get("extract", ""),
            "description": data.get("description", ""),
            "thumbnail": {"url": thumb["url"], "width": thumb.get("width"), "height": thumb.get("height")} if thumb else None,
            "lang": data.get("lang", language),
            "timestamp": data.get("timestamp", ""),
        }

    def get_page_sections(self, title: str, language: str) -> dict:
        """Retrieve hierarchical section headings and text for a Wikipedia article."""
        resp = requests.get(self._legacy_url(language), params={
            "action": "parse", "page": title, "prop": "sections", "format": "json"
        }, timeout=10)
        resp.raise_for_status()
        parse_data = resp.json().get("parse", {})
        sections = [
            {"title": s.get("line", ""), "level": int(s.get("level", 1)), "text": s.get("anchor", "")}
            for s in parse_data.get("sections", [])
        ]
        return {"title": parse_data.get("title", title), "sections": sections}

    def get_related_pages(self, title: str, limit: int, language: str) -> dict:
        """Retrieve thematically related Wikipedia pages."""
        url = f"https://{language}.wikipedia.org/api/rest_v1/page/related/{requests.utils.quote(title)}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        related = []
        for page in data.get("pages", [])[:limit]:
            related.append({
                "title": page.get("title", ""),
                "pageid": page.get("pageid", 0),
                "extract": page.get("extract", ""),
                "url": page.get("content_urls", {}).get("desktop", {}).get("page", ""),
            })
        return {"title": title, "related": related}


# Section 3: MCP Tools
mcp = FastMCP(name="WikipediaServer")
api = WikipediaAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Wikipedia API.

    Args:
        scenario (dict): Scenario dictionary matching WikipediaScenario schema.

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
    Save current Wikipedia API state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_wikipedia(query: str, limit: int = None, language: str = None) -> dict:
    """
    Search Wikipedia for pages matching a query.

    Args:
        query (str): The search string used to find matching Wikipedia pages.
        limit (int): [Optional] Maximum number of search results to return (default 5).
        language (str): [Optional] Wikipedia language code (e.g., 'en' for English).

    Returns:
        query (str): The original search query string echoed back.
        results (list): List of matching Wikipedia page summaries, each with title, pageid, excerpt, description, and thumbnail.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("query must be a non-empty string")
        resolved_limit = limit if limit is not None else api.default_search_limit
        resolved_lang = language if language else api.default_language
        return api.search_wikipedia(query, resolved_limit, resolved_lang)
    except Exception as e:
        raise e

@mcp.tool()
def get_article(title: str, language: str = None) -> dict:
    """
    Retrieve the full Wikipedia article content and section breakdown.

    Args:
        title (str): The exact Wikipedia page title whose full article is requested.
        language (str): [Optional] Wikipedia language code (e.g., 'en' for English).

    Returns:
        title (str): Display title of the retrieved Wikipedia page.
        pageid (int): Unique numeric identifier of the page.
        summary (str): Brief lead paragraph summarizing the article.
        text (str): Complete article text including all sections.
        url (str): Canonical web URL of the Wikipedia page.
        sections (list): Hierarchical list of article sections with title, level, and text.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        resolved_lang = language if language else api.default_language
        return api.get_article(title, resolved_lang)
    except Exception as e:
        raise e

@mcp.tool()
def get_summary(title: str, language: str = None) -> dict:
    """
    Retrieve a concise summary and metadata for a Wikipedia article.

    Args:
        title (str): The exact Wikipedia page title whose summary is requested.
        language (str): [Optional] Wikipedia language code (e.g., 'en' for English).

    Returns:
        title (str): Display title of the Wikipedia page.
        extract (str): Concise plain-text summary of the article topic.
        description (str): Short subtitle or description of the page topic.
        thumbnail (dict): Thumbnail image metadata (url, width, height) if available.
        lang (str): Language code of the returned summary.
        timestamp (str): ISO 8601 timestamp of when the summary was last updated.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        resolved_lang = language if language else api.default_language
        return api.get_summary(title, resolved_lang)
    except Exception as e:
        raise e

@mcp.tool()
def get_page_sections(title: str, language: str = None) -> dict:
    """
    Retrieve hierarchical section headings and text fragments of a Wikipedia article.

    Args:
        title (str): The exact Wikipedia page title whose section outline is requested.
        language (str): [Optional] Wikipedia language code (e.g., 'en' for English).

    Returns:
        title (str): Display title of the Wikipedia page.
        sections (list): Ordered list of sections with title, level, and text content.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        resolved_lang = language if language else api.default_language
        return api.get_page_sections(title, resolved_lang)
    except Exception as e:
        raise e

@mcp.tool()
def get_related_pages(title: str, limit: int = None, language: str = None) -> dict:
    """
    Retrieve a list of Wikipedia pages thematically related to a given article.

    Args:
        title (str): The exact Wikipedia page title whose related pages are requested.
        limit (int): [Optional] Maximum number of related pages to return (default 10).
        language (str): [Optional] Wikipedia language code (e.g., 'en' for English).

    Returns:
        title (str): Display title of the source Wikipedia page.
        related (list): List of related pages, each with title, pageid, extract, and url.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        resolved_limit = limit if limit is not None else api.default_related_limit
        resolved_lang = language if language else api.default_language
        return api.get_related_pages(title, resolved_limit, resolved_lang)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
