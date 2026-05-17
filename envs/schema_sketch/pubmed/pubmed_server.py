# Data Source: https://www.ncbi.nlm.nih.gov/books/NBK25501/
# Server: PubMed
# Category: Biomedical Literature


def search_pubmed_key_words(key_words: str, max_results: int = 10,
                            sort: str = None) -> dict:
    """
    Search PubMed articles by keywords.

    Args:
        key_words (str): Keyword query for PubMed search
        max_results (int): [Optional] Maximum number of articles to return
        sort (str): [Optional] Sort mode such as "relevance", "pub_date", or "journal"

    Returns:
        dict: {
            "query": str,
            "count": int,
            "articles": list[{
                "pmid": str,
                "title": str,
                "authors": list[str],
                "journal": str,
                "pub_date": str,
                "abstract": str
            }]
        }
    """
    pass


def get_pubmed_article(pmid: str) -> dict:
    """
    Retrieve detailed metadata and abstract text for a PubMed article.

    Args:
        pmid (str): PubMed identifier

    Returns:
        dict: {
            "pmid": str,
            "title": str,
            "authors": list[str],
            "journal": str,
            "publication_types": list[str],
            "mesh_terms": list[str],
            "abstract": str,
            "doi": str
        }
    """
    pass


def fetch_pubmed_articles(pmids: list) -> dict:
    """
    Retrieve multiple PubMed articles by PMID.

    Args:
        pmids (list): PubMed identifiers to retrieve

    Returns:
        dict: {
            "articles": list[dict],
            "missing_pmids": list[str]
        }
    """
    pass


def search_pubmed_by_author(author: str, max_results: int = 10) -> dict:
    """
    Search PubMed articles by author name.

    Args:
        author (str): Author name query
        max_results (int): [Optional] Maximum number of articles to return

    Returns:
        dict: {
            "author": str,
            "articles": list[dict],
            "count": int
        }
    """
    pass


def search_pubmed_by_journal(journal: str, year: int = None,
                             max_results: int = 10) -> dict:
    """
    Search PubMed articles by journal and optional publication year.

    Args:
        journal (str): Journal title or abbreviation
        year (int): [Optional] Publication year to filter by
        max_results (int): [Optional] Maximum number of articles to return

    Returns:
        dict: {
            "journal": str,
            "year": int,
            "articles": list[dict],
            "count": int
        }
    """
    pass

