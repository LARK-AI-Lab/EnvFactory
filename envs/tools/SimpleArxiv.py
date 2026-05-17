from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Paper(BaseModel):
    """Represents an arXiv paper with basic metadata."""
    arxiv_id: str = Field(..., description="The unique arXiv identifier for the paper")
    title: str = Field(..., description="The title of the arXiv paper")
    authors: List[str] = Field(..., description="List of author names for the paper")
    published_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="The date the paper was originally published on arXiv, in YYYY-MM-DD format")
    abstract: Optional[str] = Field(default=None, description="The abstract summarizing the paper's content")
    updated_date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="The date the paper was last updated on arXiv, in YYYY-MM-DD format")
    journal_ref: Optional[str] = Field(default=None, description="Journal reference if the paper has been published in a peer-reviewed venue")
    pdf_url: Optional[str] = Field(default=None, description="Direct URL to download the PDF version of the paper")

class ArxivScenario(BaseModel):
    """Main scenario model for arXiv paper management."""
    papers: Dict[str, Paper] = Field(default={}, description="Dictionary of arXiv papers indexed by arXiv ID")
    categoryMap: Dict[str, str] = Field(default={
        "cs.AI": "Artificial Intelligence",
        "cs.LG": "Machine Learning",
        "cs.CL": "Computation and Language",
        "cs.CV": "Computer Vision and Pattern Recognition",
        "cs.RO": "Robotics",
        "cs.CR": "Cryptography and Security",
        "cs.DB": "Databases",
        "cs.DC": "Distributed, Parallel, and Cluster Computing",
        "cs.DS": "Data Structures and Algorithms",
        "cs.GT": "Computer Science and Game Theory",
        "cs.HC": "Human-Computer Interaction",
        "cs.IR": "Information Retrieval",
        "cs.MA": "Multiagent Systems",
        "cs.MM": "Multimedia",
        "cs.NE": "Neural and Evolutionary Computing",
        "cs.NI": "Networking and Internet Architecture",
        "cs.OS": "Operating Systems",
        "cs.PF": "Performance",
        "cs.PL": "Programming Languages",
        "cs.SC": "Symbolic Computation"
    }, description="Mapping of arXiv category codes to full names")
    subCategoryMap: Dict[str, str] = Field(default={
        "cs.AI.ML": "Machine Learning in AI",
        "cs.LG.NE": "Neural Networks in Machine Learning",
        "cs.CV.OD": "Object Detection in Computer Vision",
        "cs.CL.NLP": "Natural Language Processing",
        "cs.RO.MA": "Mobile Robotics",
        "cs.CR.CY": "Cryptography",
        "cs.DB.DM": "Data Mining in Databases",
        "cs.DC.CC": "Cloud Computing",
        "cs.DS.AG": "Algorithms and Graph Theory",
        "cs.GT.EG": "Economic Games",
        "cs.HC.UI": "User Interfaces",
        "cs.IR.SE": "Search Engines",
        "cs.MA.CO": "Coordination in Multiagent Systems",
        "cs.MM.VD": "Video Processing",
        "cs.NE.GA": "Genetic Algorithms",
        "cs.NI.WN": "Wireless Networks",
        "cs.OS.VM": "Virtual Machines",
        "cs.PF.PM": "Performance Modeling",
        "cs.PL.FP": "Functional Programming",
        "cs.SC.AM": "Algebraic Manipulation"
    }, description="Mapping of arXiv subcategory codes to full names")

Scenario_Schema = [Paper, ArxivScenario]

# Section 2: Class
class ArxivAPI:
    def __init__(self):
        """Initialize arXiv API with empty state."""
        self.papers: Dict[str, Paper] = {}
        self.categoryMap: Dict[str, str] = {}
        self.subCategoryMap: Dict[str, str] = {}
        
    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = ArxivScenario(**scenario)
        self.papers = model.papers
        self.categoryMap = model.categoryMap
        self.subCategoryMap = model.subCategoryMap

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "papers": {arxiv_id: paper.model_dump() for arxiv_id, paper in self.papers.items()},
            "categoryMap": self.categoryMap,
            "subCategoryMap": self.subCategoryMap
        }

    def search_arxiv(self, query: str, limit: Optional[int] = 10, categories: Optional[List[str]] = None, sub_categories: Optional[List[str]] = None) -> dict:
        """Search for papers on arXiv using query and filters."""
        matching_papers = []
        
        for paper in self.papers.values():
            # Check if query matches title or abstract
            query_lower = query.lower()
            if query_lower in paper.title.lower() or (paper.abstract and query_lower in paper.abstract.lower()):
                matching_papers.append(paper)
        
        # Apply category filters if provided
        if categories:
            matching_papers = [p for p in matching_papers if any(cat in p.arxiv_id for cat in categories)]
        
        # Apply subcategory filters if provided
        if sub_categories:
            matching_papers = [p for p in matching_papers if any(sub in p.arxiv_id for sub in sub_categories)]
        
        # Apply limit
        if limit:
            matching_papers = matching_papers[:limit]
        
        # Group by category
        results_by_category = {}
        for paper in matching_papers:
            # Extract category from arxiv_id (assuming format like cs.AI/2103.08220)
            category = paper.arxiv_id.split('/')[0] if '/' in paper.arxiv_id else 'unknown'
            category_name = self.categoryMap.get(category, category)
            
            if category_name not in results_by_category:
                results_by_category[category_name] = []
            
            results_by_category[category_name].append({
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "published_date": paper.published_date
            })
        
        return {"results_by_category": results_by_category}

    def search_metadata(self, query: str, limit: Optional[int] = 10, categories: Optional[List[str]] = None, sub_categories: Optional[List[str]] = None) -> dict:
        """Search for papers and return lightweight metadata."""
        matching_papers = []
        
        for paper in self.papers.values():
            # Check if query matches title or abstract
            query_lower = query.lower()
            if query_lower in paper.title.lower() or (paper.abstract and query_lower in paper.abstract.lower()):
                matching_papers.append(paper)
        
        # Apply category filters if provided
        if categories:
            matching_papers = [p for p in matching_papers if any(cat in p.arxiv_id for cat in categories)]
        
        # Apply subcategory filters if provided
        if sub_categories:
            matching_papers = [p for p in matching_papers if any(sub in p.arxiv_id for sub in sub_categories)]
        
        # Apply limit
        if limit:
            matching_papers = matching_papers[:limit]
        
        papers = [{
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract or ""
        } for paper in matching_papers]
        
        return {"papers": papers}

    def get_paper_details(self, arxiv_id: str) -> dict:
        """Retrieve detailed information for a specific arXiv paper."""
        paper = self.papers[arxiv_id]
        return {
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "authors": paper.authors,
            "published_date": paper.published_date,
            "updated_date": paper.updated_date or paper.published_date,
            "journal_ref": paper.journal_ref or "",
            "abstract": paper.abstract or "",
            "pdf_url": paper.pdf_url or f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        }

# Section 3: MCP Tools
mcp = FastMCP(name="SimpleArxiv")
api = ArxivAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the arXiv API.
    
    Args:
        scenario (dict): Scenario dictionary matching ArxivScenario schema.
    
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
    """Save current arXiv state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_arxiv(query: str, limit: Optional[int] = 10, categories: Optional[List[str]] = None, sub_categories: Optional[List[str]] = None) -> dict:
    """Search for papers on arXiv using a query string, optionally filtered by categories.
    
    Args:
        query (str): Search query for finding papers on arXiv.
        limit (int) [Optional]: Maximum number of results to return. Defaults to 10.
        categories (List[str]) [Optional]: Filter results by arXiv categories.
        sub_categories (List[str]) [Optional]: Filter results by arXiv subcategories.
    
    Returns:
        results_by_category (dict): Search results grouped by arXiv category name.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_arxiv(query, limit, categories, sub_categories)
    except Exception as e:
        raise e

@mcp.tool()
def search_metadata(query: str, limit: Optional[int] = 10, categories: Optional[List[str]] = None, sub_categories: Optional[List[str]] = None) -> dict:
    """Search for papers on arXiv and return only lightweight metadata.
    
    Args:
        query (str): Search query for finding papers on arXiv.
        limit (int) [Optional]: Maximum number of results to return. Defaults to 10.
        categories (List[str]) [Optional]: Filter results by arXiv categories.
        sub_categories (List[str]) [Optional]: Filter results by arXiv subcategories.
    
    Returns:
        papers (List[dict]): List of papers with minimal metadata information.
    """
    try:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        return api.search_metadata(query, limit, categories, sub_categories)
    except Exception as e:
        raise e

@mcp.tool()
def get_paper_details(arxiv_id: str) -> dict:
    """Retrieve detailed information for a specific arXiv paper by its identifier.
    
    Args:
        arxiv_id (str): The unique arXiv identifier for the paper.
    
    Returns:
        paper_details (dict): Dictionary containing full metadata and PDF link.
    """
    try:
        if not arxiv_id or not isinstance(arxiv_id, str):
            raise ValueError("arXiv ID must be a non-empty string")
        if arxiv_id not in api.papers:
            raise ValueError(f"Paper {arxiv_id} not found")
        return api.get_paper_details(arxiv_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()