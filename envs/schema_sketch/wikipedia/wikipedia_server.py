# Data Source: https://www.mediawiki.org/wiki/API:REST_API
# Server: Wikipedia
# Category: Knowledge & Reference


def search_wikipedia(query: str, limit: int = 5,
                     language: str = "en") -> dict:
    """
    Search Wikipedia pages matching a query.

    Args:
        query (str): Search query string
        limit (int): [Optional] Maximum number of pages to return
        language (str): [Optional] Wikipedia language code

    Returns:
        dict: {
            "query": str,
            "results": list[{
                "title": str,
                "pageid": int,
                "excerpt": str,
                "description": str,
                "thumbnail": dict
            }]
        }
    """
    pass


def get_article(title: str, language: str = "en") -> dict:
    """
    Retrieve full Wikipedia article content and metadata.

    Args:
        title (str): Wikipedia page title
        language (str): [Optional] Wikipedia language code

    Returns:
        dict: {
            "title": str,
            "pageid": int,
            "summary": str,
            "text": str,
            "url": str,
            "sections": list[dict]
        }
    """
    pass


def get_summary(title: str, language: str = "en") -> dict:
    """
    Retrieve a concise summary for a Wikipedia article.

    Args:
        title (str): Wikipedia page title
        language (str): [Optional] Wikipedia language code

    Returns:
        dict: {
            "title": str,
            "extract": str,
            "description": str,
            "thumbnail": dict,
            "lang": str,
            "timestamp": str
        }
    """
    pass


def get_page_sections(title: str, language: str = "en") -> dict:
    """
    Retrieve section headings and section text for a Wikipedia article.

    Args:
        title (str): Wikipedia page title
        language (str): [Optional] Wikipedia language code

    Returns:
        dict: {
            "title": str,
            "sections": list[{
                "title": str,
                "level": int,
                "text": str
            }]
        }
    """
    pass


def get_related_pages(title: str, limit: int = 10,
                      language: str = "en") -> dict:
    """
    Retrieve pages related to a Wikipedia article.

    Args:
        title (str): Wikipedia page title
        limit (int): [Optional] Maximum number of related pages to return
        language (str): [Optional] Wikipedia language code

    Returns:
        dict: {
            "title": str,
            "related": list[{
                "title": str,
                "pageid": int,
                "extract": str,
                "url": str
            }]
        }
    """
    pass
