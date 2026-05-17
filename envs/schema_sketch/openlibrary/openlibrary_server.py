# Data Source: https://openlibrary.org/developers/api
# Server: OpenLibrary
# Category: Books & Literature


def get_book_by_title(title: str) -> dict:
    """
    Search Open Library for books matching a title and return the best catalog matches.

    Args:
        title (str): Book title to search for

    Returns:
        dict: {
            "title": str,
            "matches": list[{
                "key": str,
                "title": str,
                "author_name": list[str],
                "first_publish_year": int,
                "isbn": list[str],
                "cover_i": int
            }]
        }
    """
    pass


def get_book_by_id(identifier: str, identifier_type: str = "isbn") -> dict:
    """
    Retrieve detailed book information using an ISBN, LCCN, OCLC, or Open Library ID.

    Args:
        identifier (str): Book identifier value
        identifier_type (str): [Optional] Identifier type such as "isbn", "lccn", "oclc", or "olid"

    Returns:
        dict: {
            "title": str,
            "authors": list[{"name": str, "key": str}],
            "publishers": list[str],
            "publish_date": str,
            "covers": list[int],
            "identifiers": dict,
            "key": str
        }
    """
    pass


def get_authors_by_name(name: str, limit: int = 10) -> dict:
    """
    Search Open Library authors by name.

    Args:
        name (str): Author name query
        limit (int): [Optional] Maximum number of authors to return

    Returns:
        dict: {
            "authors": list[{
                "key": str,
                "name": str,
                "birth_date": str,
                "top_work": str,
                "work_count": int
            }],
            "count": int
        }
    """
    pass


def get_author_info(author_key: str) -> dict:
    """
    Retrieve detailed information about an Open Library author.

    Args:
        author_key (str): Open Library author key such as "OL23919A" or "/authors/OL23919A"

    Returns:
        dict: {
            "key": str,
            "name": str,
            "bio": str,
            "birth_date": str,
            "death_date": str,
            "photos": list[int],
            "wikipedia": str
        }
    """
    pass


def get_book_cover(identifier: str, identifier_type: str = "isbn",
                   size: str = "M") -> dict:
    """
    Get a cover image URL for a book.

    Args:
        identifier (str): ISBN, OCLC, LCCN, OLID, or cover ID
        identifier_type (str): [Optional] Identifier type such as "isbn", "oclc", "lccn", "olid", or "id"
        size (str): [Optional] Cover size, one of "S", "M", or "L"

    Returns:
        dict: {
            "url": str,
            "identifier": str,
            "identifier_type": str,
            "size": str
        }
    """
    pass
