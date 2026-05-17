

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema

class Article(BaseModel):
    """Represents a PubMed article."""
    pmid: str = Field(..., description="Unique PubMed identifier")
    title: str = Field(default="", description="Article title")
    authors: List[str] = Field(default=[], description="List of author names")
    journal: str = Field(default="", description="Journal name or abbreviation")
    pub_date: str = Field(default="", description="Publication date")
    abstract: str = Field(default="", description="Abstract text")
    publication_types: List[str] = Field(default=[], description="MeSH publication types")
    mesh_terms: List[str] = Field(default=[], description="MeSH terms")
    doi: str = Field(default="", description="Digital Object Identifier")

class PubMedScenario(BaseModel):
    """Main scenario model for PubMed server state."""
    articles: Dict[str, Any] = Field(default_factory=dict, description="Stored articles keyed by PMID")
    search_results: Dict[str, Any] = Field(default_factory=dict, description="Cached search results keyed by query")
    author_results: Dict[str, Any] = Field(default_factory=dict, description="Cached author search results")
    journal_results: Dict[str, Any] = Field(default_factory=dict, description="Cached journal search results")
    current_time: str = Field(default="2026-04-17T01:46:12", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Article, PubMedScenario]


# Section 2: Class

class PubMedAPI:
    def __init__(self):
        self.articles: Dict[str, Any] = {}
        self.search_results: Dict[str, Any] = {}
        self.author_results: Dict[str, Any] = {}
        self.journal_results: Dict[str, Any] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance, fully replacing all state."""
        # Validate via Pydantic but read raw values directly from input dict
        # to avoid any silent field transformation or filtering by Pydantic
        PubMedScenario(**scenario)  # validate only
        self.articles = dict(scenario.get("articles") or {})
        self.search_results = dict(scenario.get("search_results") or {})
        self.author_results = dict(scenario.get("author_results") or {})
        self.journal_results = dict(scenario.get("journal_results") or {})
        self.current_time = scenario.get("current_time", "2026-04-17T01:46:12")

    def save_scenario(self) -> dict:
        return {
            "articles": self.articles,
            "search_results": self.search_results,
            "author_results": self.author_results,
            "journal_results": self.journal_results,
            "current_time": self.current_time,
        }

    def search_pubmed_key_words(self, key_words: str, max_results: int = 10, sort: Optional[str] = None) -> dict:
        key = f"{key_words}|{max_results}|{sort}"
        if key in self.search_results:
            return self.search_results[key]

        kw_lower = key_words.lower()
        matches = []
        for pmid, art in self.articles.items():
            title = art.get("title", "").lower()
            abstract = art.get("abstract", "").lower()
            mesh = " ".join(art.get("mesh_terms", [])).lower()
            if kw_lower in title or kw_lower in abstract or kw_lower in mesh:
                matches.append(art)

        if sort == "pub_date":
            matches.sort(key=lambda a: a.get("pub_date", ""), reverse=True)
        elif sort == "journal":
            matches.sort(key=lambda a: a.get("journal", ""))

        matches = matches[:max_results]
        result = {"query": key_words, "count": len(matches), "articles": matches}
        self.search_results[key] = result
        return result

    def get_pubmed_article(self, pmid: str) -> dict:
        return self.articles[pmid]

    def fetch_pubmed_articles(self, pmids: List[str]) -> dict:
        found = []
        missing = []
        for pmid in pmids:
            if pmid in self.articles:
                found.append(self.articles[pmid])
            else:
                missing.append(pmid)
        return {"articles": found, "missing_pmids": missing}

    def search_pubmed_by_author(self, author: str, max_results: int = 10) -> dict:
        key = f"{author}|{max_results}"
        if key in self.author_results:
            return self.author_results[key]

        author_lower = author.lower()
        matches = []
        for pmid, art in self.articles.items():
            for a in art.get("authors", []):
                if author_lower in a.lower():
                    matches.append(art)
                    break

        matches = matches[:max_results]
        result = {"author": author, "articles": matches, "count": len(matches)}
        self.author_results[key] = result
        return result

    def search_pubmed_by_journal(self, journal: str, year: Optional[int] = None, max_results: int = 10) -> dict:
        key = f"{journal}|{year}|{max_results}"
        if key in self.journal_results:
            return self.journal_results[key]

        journal_lower = journal.lower()
        matches = []
        for pmid, art in self.articles.items():
            if journal_lower in art.get("journal", "").lower():
                if year is None or art.get("pub_date", "").startswith(str(year)):
                    matches.append(art)

        matches = matches[:max_results]
        result = {"journal": journal, "year": year, "articles": matches, "count": len(matches)}
        self.journal_results[key] = result
        return result


# Section 3: MCP Tools

mcp = FastMCP(name="PubMedServer")
api = PubMedAPI()


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the PubMed API.

    Args:
        scenario (dict): Scenario dictionary matching PubMedScenario schema.

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
    Save current PubMed state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e


@mcp.tool()
def search_pubmed_key_words(key_words: str, max_results: int = 10, sort: Optional[str] = None) -> dict:
    """
    Search PubMed articles by free-text keywords and optionally sort the results.

    Args:
        key_words (str): Keyword query string used to search PubMed article titles, abstracts, and MeSH terms.
        max_results (int): Maximum number of articles to return (default 10). [Optional]
        sort (str): Sort mode: "relevance", "pub_date", or "journal". [Optional]

    Returns:
        query (str): The original keyword query string submitted to PubMed.
        count (int): Total number of matching articles found.
        articles (list): List of matching articles with basic bibliographic metadata.
    """
    try:
        if not key_words or not isinstance(key_words, str):
            raise ValueError("key_words must be a non-empty string")
        if sort is not None and sort not in ("relevance", "pub_date", "journal"):
            raise ValueError("sort must be one of: relevance, pub_date, journal")
        return api.search_pubmed_key_words(key_words, max_results, sort)
    except Exception as e:
        raise e


@mcp.tool()
def get_pubmed_article(pmid: str) -> dict:
    """
    Retrieve detailed metadata, abstract, and identifiers for a single PubMed article by its PMID.

    Args:
        pmid (str): The unique PubMed identifier (PMID) of the article to retrieve.

    Returns:
        pmid (str): The unique PubMed identifier.
        title (str): Title of the article.
        authors (list): List of author names.
        journal (str): Journal name or abbreviation.
        publication_types (list): MeSH publication types.
        mesh_terms (list): MeSH terms indexing the article.
        abstract (str): Abstract text.
        doi (str): Digital Object Identifier.
    """
    try:
        if not pmid or not isinstance(pmid, str):
            raise ValueError("pmid must be a non-empty string")
        if pmid not in api.articles:
            raise ValueError(f"Article with PMID {pmid} not found")
        return api.get_pubmed_article(pmid)
    except Exception as e:
        raise e


@mcp.tool()
def fetch_pubmed_articles(pmids: List[str]) -> dict:
    """
    Batch retrieve multiple PubMed articles by their PMIDs in a single call.

    Args:
        pmids (list): List of PubMed identifiers (PMIDs) to retrieve.

    Returns:
        articles (list): List of successfully retrieved article objects.
        missing_pmids (list): List of PMIDs that could not be found.
    """
    try:
        if not pmids or not isinstance(pmids, list):
            raise ValueError("pmids must be a non-empty list")
        return api.fetch_pubmed_articles(pmids)
    except Exception as e:
        raise e


@mcp.tool()
def search_pubmed_by_author(author: str, max_results: int = 10) -> dict:
    """
    Search PubMed for articles authored by a specific researcher.

    Args:
        author (str): Author name query (last name, first initial, or full name).
        max_results (int): Maximum number of articles to return (default 10). [Optional]

    Returns:
        author (str): The author name query string used for the search.
        articles (list): List of articles attributed to the specified author.
        count (int): Total number of articles found for the author.
    """
    try:
        if not author or not isinstance(author, str):
            raise ValueError("author must be a non-empty string")
        return api.search_pubmed_by_author(author, max_results)
    except Exception as e:
        raise e


@mcp.tool()
def search_pubmed_by_journal(journal: str, year: Optional[int] = None, max_results: int = 10) -> dict:
    """
    Search PubMed for articles published in a specific journal, optionally filtered by year.

    Args:
        journal (str): Journal title or standard abbreviation to search.
        year (int): Optional publication year filter (e.g., 2023). [Optional]
        max_results (int): Maximum number of articles to return (default 10). [Optional]

    Returns:
        journal (str): The journal title or abbreviation used for the search.
        year (int): The publication year filter applied, if any.
        articles (list): List of articles published in the specified journal.
        count (int): Total number of articles found.
    """
    try:
        if not journal or not isinstance(journal, str):
            raise ValueError("journal must be a non-empty string")
        return api.search_pubmed_by_journal(journal, year, max_results)
    except Exception as e:
        raise e


# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()


