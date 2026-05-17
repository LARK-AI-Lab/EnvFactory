# Server: SimpleArxiv

def search_arxiv(query: str, limit: int = None, categories: list[str] = None, sub_categories: list[str] = None) -> dict:
    """
    Search for papers on arXiv using a query string, optionally filtered by categories.
    
    Args:
        query (str): Search query for papers (e.g., "large language models", "quantum computing")
        limit (int): [Optional] Maximum number of results to return
        categories (list[str]): [Optional] Filter by arXiv categories (e.g., ["cs.AI", "cs.LG"])
        sub_categories (list[str]): [Optional] Filter by arXiv subcategories (e.g., ["cs.AI.ML", "cs.LG.NE"])
        
    Returns:
        dict: Results grouped by category. Format: {
            "category_name": [
                {
                    "arxiv_id": str,
                    "title": str,
                    "authors": list[str],
                    "published_date": str (YYYY-MM-DD)
                },
                ...
            ],
            ...
        }
    """
    pass

def search_metadata(query: str, limit: int = None, categories: list[str] = None, sub_categories: list[str] = None) -> list:
    """
    Search for papers on arXiv and return only metadata (title, authors, abstract).
    This is a lightweight search that returns minimal information.
    
    Args:
        query (str): Search query for papers (e.g., "large language models", "quantum computing")
        limit (int): [Optional] Maximum number of results to return
        categories (list[str]): [Optional] Filter by arXiv categories (e.g., ["cs.AI", "cs.LG"])
        sub_categories (list[str]): [Optional] Filter by arXiv subcategories (e.g., ["cs.AI.ML", "cs.LG.NE"])
        
    Returns:
        list: Each paper contains {
            "title": str,
            "authors": list[str],
            "abstract": str
        }
    """
    pass

def get_paper_details(arxiv_id: str) -> dict:
    """
    Get detailed information for a specific arXiv paper.
    
    Args:
        arxiv_id (str): arXiv paper identifier (e.g., "2103.08220")
        
    Returns:
        dict: {
            "arxiv_id": str,
            "title": str,
            "authors": list[str],
            "published_date": str (YYYY-MM-DD),
            "updated_date": str (YYYY-MM-DD),
            "journal_ref": str,
            "abstract": str,
            "pdf_url": str
        }
    """
    pass

