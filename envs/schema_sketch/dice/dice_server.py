# Data Source: https://www.dice.com/
# Server: Dice
# Category: recruitment

def search_tech_jobs(keywords: str, location: str = None, remote_only: bool = False) -> dict:
    """
    Search for technology jobs on Dice.
    
    Args:
        keywords (str): Job title or skills (e.g., "Python Developer", "AWS")
        location (str): [Optional] City, state, or "Remote"
        remote_only (bool): [Optional] Filter for remote positions only
        
    Returns:
        dict: {
            "jobs": [
                {
                    "job_id": str,
                    "title": str,
                    "company": str,
                    "location": str,
                    "employment_type": str,
                    "skills": list,
                    "posted_date": str,
                    "salary_range": str,
                    "is_remote": bool
                }
            ],
            "total_results": int
        }
    """
    pass

def get_job_details(job_id: str) -> dict:
    """
    Get detailed information about a tech job.
    
    Args:
        job_id (str): Dice job ID
        
    Returns:
        dict: {
            "job_id": str,
            "title": str,
            "company": str,
            "company_size": str,
            "location": str,
            "employment_type": str,
            "description": str,
            "requirements": list,
            "preferred_skills": list,
            "experience_level": str,
            "education": str,
            "salary_min": float,
            "salary_max": float,
            "benefits": list,
            "posted_date": str,
            "apply_url": str
        }
    """
    pass

def search_by_skills(skills: list, location: str = None) -> dict:
    """
    Search jobs by specific tech skills.
    
    Args:
        skills (list): List of technical skills (e.g., ["Python", "React", "AWS"])
        location (str): [Optional] Location filter
        
    Returns:
        dict: {
            "jobs": [
                {
                    "job_id": str,
                    "title": str,
                    "company": str,
                    "matching_skills": list,
                    "match_score": float,
                    "location": str
                }
            ],
            "skill_demand": {
                "most_requested_skills": list,
                "salary_by_skill": dict
            }
        }
    """
    pass

def get_salary_insights(job_title: str, location: str = None, years_experience: int = None) -> dict:
    """
    Get salary insights for tech roles.
    
    Args:
        job_title (str): Job title
        location (str): [Optional] Location
        years_experience (int): [Optional] Years of experience
        
    Returns:
        dict: {
            "job_title": str,
            "location": str,
            "salary_range_low": float,
            "salary_range_mid": float,
            "salary_range_high": float,
            "currency": str,
            "pay_period": str,
            "factors": {
                "by_experience": dict,
                "by_skill": dict,
                "by_company_size": dict
            }
        }
    """
    pass

def get_tech_trends(time_period: str = "30d") -> dict:
    """
    Get trending tech skills and job market insights.
    
    Args:
        time_period (str): [Optional] Time period (7d, 30d, 90d)
        
    Returns:
        dict: {
            "time_period": str,
            "top_job_titles": [
                {
                    "title": str,
                    "openings_count": int,
                    "growth_rate": float
                }
            ],
            "hot_skills": [
                {
                    "skill": str,
                    "demand_count": int,
                    "avg_salary": float
                }
            ],
            "top_locations": [
                {
                    "location": str,
                    "job_count": int
                }
            ]
        }
    """
    pass
