
import requests
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class BookMatch(BaseModel):
    """Represents a book search match."""
    key: str = Field(..., description="Open Library unique key for this book edition.")
    title: str = Field(..., description="The title of the matched book.")
    author_name: List[str] = Field(default=[], description="List of author names.")
    first_publish_year: Optional[int] = Field(default=None, description="Year of first publication.")
    isbn: List[str] = Field(default=[], description="List of ISBNs.")
    cover_i: Optional[int] = Field(default=None, description="Internal cover image identifier.")

class AuthorRef(BaseModel):
    """Represents an author reference."""
    name: str = Field(..., description="Author's display name.")
    key: str = Field(..., description="Open Library author key.")

class AuthorResult(BaseModel):
    """Represents an author search result."""
    key: str = Field(..., description="Open Library unique author key.")
    name: str = Field(..., description="Author's primary name.")
    birth_date: Optional[str] = Field(default=None, description="Birth date.")
    top_work: Optional[str] = Field(default=None, description="Most widely held work.")
    work_count: Optional[int] = Field(default=None, description="Total number of works.")

class OpenLibraryScenario(BaseModel):
    """Main scenario model for OpenLibrary MCP server."""
    base_url: str = Field(default="https://openlibrary.org", description="Open Library base URL.")
    covers_url: str = Field(default="https://covers.openlibrary.org", description="Open Library covers base URL.")

Scenario_Schema = [BookMatch, AuthorRef, AuthorResult, OpenLibraryScenario]

# Section 2: Class
class OpenLibraryAPI:
    def __init__(self):
        """Initialize OpenLibrary API with empty state."""
        self.base_url: str = ""
        self.covers_url: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = OpenLibraryScenario(**scenario)
        self.base_url = model.base_url
        self.covers_url = model.covers_url

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "base_url": self.base_url,
            "covers_url": self.covers_url,
        }

    def get_book_by_title(self, title: str) -> dict:
        """Search Open Library for books matching the given title."""
        resp = requests.get(f"{self.base_url}/search.json", params={"title": title}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        matches = []
        for doc in data.get("docs", []):
            matches.append({
                "key": doc.get("key", ""),
                "title": doc.get("title", ""),
                "author_name": doc.get("author_name", []),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", []),
                "cover_i": doc.get("cover_i"),
            })
        return {"title": title, "matches": matches}

    def get_book_by_id(self, identifier: str, identifier_type: str = "isbn") -> dict:
        """Retrieve detailed metadata for a specific book by identifier."""
        id_map = {"isbn": "ISBN", "lccn": "LCCN", "oclc": "OCLC", "olid": "OLID"}
        key = id_map.get(identifier_type.lower(), "ISBN")
        resp = requests.get(f"{self.base_url}/api/books.json", params={"bibkeys": f"{key}:{identifier}", "format": "json", "jscmd": "data"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        book = data.get(f"{key}:{identifier}", {})
        authors = [{"name": a.get("name", ""), "key": a.get("url", "").replace("https://openlibrary.org", "")} for a in book.get("authors", [])]
        return {
            "title": book.get("title", ""),
            "authors": authors,
            "publishers": [p.get("name", "") for p in book.get("publishers", [])],
            "publish_date": book.get("publish_date", ""),
            "covers": book.get("covers", []),
            "identifiers": book.get("identifiers", {}),
            "key": book.get("key", ""),
        }

    def get_authors_by_name(self, name: str, limit: int = 10) -> dict:
        """Search Open Library for authors matching the given name."""
        resp = requests.get(f"{self.base_url}/search/authors.json", params={"q": name, "limit": limit}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        authors = []
        for doc in data.get("docs", []):
            authors.append({
                "key": doc.get("key", ""),
                "name": doc.get("name", ""),
                "birth_date": doc.get("birth_date"),
                "top_work": doc.get("top_work"),
                "work_count": doc.get("work_count"),
            })
        return {"authors": authors, "count": len(authors)}

    def get_author_info(self, author_key: str) -> dict:
        """Fetch biographical and bibliographical data for a specific author."""
        key = author_key if author_key.startswith("/authors/") else f"/authors/{author_key}"
        resp = requests.get(f"{self.base_url}{key}.json", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        bio = data.get("bio", "")
        if isinstance(bio, dict):
            bio = bio.get("value", "")
        return {
            "key": data.get("key", ""),
            "name": data.get("name", ""),
            "bio": bio,
            "birth_date": data.get("birth_date"),
            "death_date": data.get("death_date"),
            "photos": data.get("photos", []),
            "wikipedia": data.get("wikipedia"),
        }

    def get_book_cover(self, identifier: str, identifier_type: str = "isbn", size: str = "M") -> dict:
        """Generate a direct URL to a book's cover image."""
        id_type = identifier_type.upper()
        url = f"{self.covers_url}/b/{id_type}/{identifier}-{size}.jpg"
        return {
            "url": url,
            "identifier": identifier,
            "identifier_type": identifier_type,
            "size": size,
        }

# Section 3: MCP Tools
mcp = FastMCP(name="OpenLibrary")
api = OpenLibraryAPI()
api.load_scenario({})

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the OpenLibrary API.

    Args:
        scenario (dict): Scenario dictionary matching OpenLibraryScenario schema.

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
    Save current state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def get_book_by_title(title: str) -> dict:
    """
    Search the Open Library catalog for books matching the provided title.

    Args:
        title (str): The book title to search for in the Open Library catalog.

    Returns:
        title (str): The original search title used for the query.
        matches (list): List of catalog entries that match the search title, each containing key, title, author_name, first_publish_year, isbn, and cover_i.
    """
    try:
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        return api.get_book_by_title(title)
    except Exception as e:
        raise e

@mcp.tool()
def get_book_by_id(identifier: str, identifier_type: str = "isbn") -> dict:
    """
    Retrieve detailed metadata for a specific book using an ISBN, LCCN, OCLC, or Open Library ID.

    Args:
        identifier (str): The book identifier value (ISBN, LCCN, OCLC, or OLID).
        identifier_type (str): [Optional] Type of identifier: 'isbn', 'lccn', 'oclc', or 'olid'. Defaults to 'isbn'.

    Returns:
        title (str): The full title of the book.
        authors (list): List of authors with name and key fields.
        publishers (list): Names of publishers.
        publish_date (str): Publication date as a human-readable string.
        covers (list): List of internal cover image identifiers.
        identifiers (dict): Dictionary mapping identifier types to their values.
        key (str): Open Library unique key for this book edition.
    """
    try:
        if not identifier or not isinstance(identifier, str):
            raise ValueError("identifier must be a non-empty string")
        if identifier_type not in ("isbn", "lccn", "oclc", "olid"):
            raise ValueError("identifier_type must be one of: isbn, lccn, oclc, olid")
        return api.get_book_by_id(identifier, identifier_type)
    except Exception as e:
        raise e

@mcp.tool()
def get_authors_by_name(name: str, limit: int = 10) -> dict:
    """
    Search Open Library for authors whose names contain the provided query string.

    Args:
        name (str): Author name or partial name to search for.
        limit (int): [Optional] Maximum number of author records to return. Defaults to 10.

    Returns:
        authors (list): List of authors matching the search query, each with key, name, birth_date, top_work, and work_count.
        count (int): Total number of authors returned in this response.
    """
    try:
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")
        return api.get_authors_by_name(name, limit)
    except Exception as e:
        raise e

@mcp.tool()
def get_author_info(author_key: str) -> dict:
    """
    Fetch comprehensive biographical and bibliographical data for a specific author.

    Args:
        author_key (str): Open Library author key (e.g., 'OL23919A' or '/authors/OL23919A').

    Returns:
        key (str): Open Library unique author key.
        name (str): Author's full name.
        bio (str): Biographical summary for the author.
        birth_date (str): Birth date in human-readable format.
        death_date (str): Death date in human-readable format, if applicable.
        photos (list): List of internal photo identifiers for author images.
        wikipedia (str): URL to the author's Wikipedia page, if available.
    """
    try:
        if not author_key or not isinstance(author_key, str):
            raise ValueError("author_key must be a non-empty string")
        return api.get_author_info(author_key)
    except Exception as e:
        raise e

@mcp.tool()
def get_book_cover(identifier: str, identifier_type: str = "isbn", size: str = "M") -> dict:
    """
    Generate a direct URL to a book's cover image hosted by Open Library.

    Args:
        identifier (str): ISBN, OCLC, LCCN, OLID, or cover ID whose cover image is requested.
        identifier_type (str): [Optional] Type of identifier: 'isbn', 'oclc', 'lccn', 'olid', or 'id'. Defaults to 'isbn'.
        size (str): [Optional] Requested cover size: 'S', 'M', or 'L'. Defaults to 'M'.

    Returns:
        url (str): Direct URL to the cover image on Open Library's servers.
        identifier (str): The identifier value used to locate the cover.
        identifier_type (str): The identifier type that was used in the request.
        size (str): Size parameter used to generate the cover image URL.
    """
    try:
        if not identifier or not isinstance(identifier, str):
            raise ValueError("identifier must be a non-empty string")
        if identifier_type not in ("isbn", "oclc", "lccn", "olid", "id"):
            raise ValueError("identifier_type must be one of: isbn, oclc, lccn, olid, id")
        if size not in ("S", "M", "L"):
            raise ValueError("size must be one of: S, M, L")
        return api.get_book_cover(identifier, identifier_type, size)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
