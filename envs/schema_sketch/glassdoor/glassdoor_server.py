# Data Source: https://www.glassdoor.com/developer/index.htm
# Server: Glassdoor
# Category: recruitment

def search_companies(query: str, location: str = None) -> dict:
    """
    Search for companies on Glassdoor.
    
    Args:
        query (str): Company name or keyword
        location (str): [Optional] Location filter
        
    Returns:
        dict: {
            "companies": [
                {
                    "company_id": int,
                    "name": str,
                    "website": str,
                    "industry": str,
                    "size": str,
                    "headquarters": str,
                    "overall_rating": float,
                    "number_of_ratings": int
                }
            ],
            "total_count": int
        }
    """
    pass

def get_company_details(company_id: int) -> dict:
    """
    Get detailed company information including ratings.
    
    Args:
        company_id (int): Glassdoor company ID
        
    Returns:
        dict: {
            "company_id": int,
            "name": str,
            "website": str,
            "industry": str,
            "size": str,
            "description": str,
            "headquarters": str,
            "founded": int,
            "overall_rating": float,
            "culture_rating": float,
            "work_life_balance_rating": float,
            "senior_leadership_rating": float,
            "compensation_rating": float,
            "career_opportunities_rating": float
        }
    """
    pass

def get_company_reviews(company_id: int, page: int = 1) -> dict:
    """
    Get employee reviews for a company.
    
    Args:
        company_id (int): Glassdoor company ID
        page (int): [Optional] Page number (default 1)
        
    Returns:
        dict: {
            "company_name": str,
            "reviews": [
                {
                    "review_id": str,
                    "job_title": str,
                    "location": str,
                    "overall_rating": float,
                    "pros": str,
                    "cons": str,
                    "advice_to_management": str,
                    "recommend_to_friend": bool,
                    "approve_of_ceo": bool,
                    "review_date": str,
                    "helpful_count": int
                }
            ],
            "total_reviews": int
        }
    """
    pass

def get_salary_data(company_id: int, job_title: str = None) -> dict:
    """
    Get salary data for a company or job title.
    
    Args:
        company_id (int): Glassdoor company ID
        job_title (str): [Optional] Filter by specific job title
        
    Returns:
        dict: {
            "company_name": str,
            "salaries": [
                {
                    "job_title": str,
                    "base_pay": float,
                    "additional_pay": float,
                    "total_pay": float,
                    "pay_period": str,
                    "currency": str,
                    "reported_count": int
                }
            ]
        }
    """
    pass

def search_jobs(query: str, location: str = None, job_type: str = None) -> dict:
    """
    Search for jobs on Glassdoor.
    
    Args:
        query (str): Job search query
        location (str): [Optional] Location
        job_type (str): [Optional] Job type (fulltime, parttime, etc.)
        
    Returns:
        dict: {
            "jobs": [
                {
                    "job_id": str,
                    "title": str,
                    "company": str,
                    "location": str,
                    "snippet": str,
                    "salary_estimate": str,
                    "rating": float,
                    "posted_date": str
                }
            ],
            "total_count": int
        }
    """
    pass
