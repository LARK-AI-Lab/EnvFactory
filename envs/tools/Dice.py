
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class JobPosting(BaseModel):
    """Represents a job posting on Dice."""
    job_id: str = Field(..., description="Unique identifier for the job posting")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    employment_type: str = Field(..., description="Employment type")
    skills: List[str] = Field(default=[], description="Required skills")
    posted_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Posted date in YYYY-MM-DD format")
    salary_range: str = Field(default="", description="Salary range string")
    is_remote: bool = Field(default=False, description="Remote work flag")
    description: str = Field(default="", description="Job description")
    requirements: List[str] = Field(default=[], description="Job requirements")
    preferred_skills: List[str] = Field(default=[], description="Preferred skills")
    experience_level: str = Field(default="", description="Experience level")
    education: str = Field(default="", description="Education requirement")
    salary_min: float = Field(default=0, ge=0, description="Minimum salary")
    salary_max: float = Field(default=0, ge=0, description="Maximum salary")
    benefits: List[str] = Field(default=[], description="Benefits")
    apply_url: str = Field(default="", description="Application URL")
    company_size: str = Field(default="", description="Company size")

class DiceScenario(BaseModel):
    """Main scenario model for Dice recruitment platform."""
    jobs: Dict[str, JobPosting] = Field(default={}, description="All job postings indexed by job_id")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [JobPosting, DiceScenario]

# Section 2: Class
class DiceAPI:
    def __init__(self):
        """Initialize Dice API with empty state."""
        self.jobs: Dict[str, JobPosting] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = DiceScenario(**scenario)
        self.jobs = model.jobs
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "jobs": {job_id: job.model_dump() for job_id, job in self.jobs.items()},
            "current_time": self.current_time
        }

    def search_tech_jobs(self, keywords: str, location: Optional[str], remote_only: bool) -> dict:
        """Search for technology job postings."""
        results = []
        for job in self.jobs.values():
            if keywords.lower() not in job.title.lower() and not any(keywords.lower() in skill.lower() for skill in job.skills):
                continue
            if location and location.lower() not in job.location.lower():
                continue
            if remote_only and not job.is_remote:
                continue
            results.append({
                "job_id": job.job_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "employment_type": job.employment_type,
                "skills": job.skills,
                "posted_date": job.posted_date,
                "salary_range": job.salary_range,
                "is_remote": job.is_remote
            })
        return {"jobs": results, "total_results": len(results)}

    def get_job_details(self, job_id: str) -> dict:
        """Retrieve comprehensive details for a specific job posting."""
        job = self.jobs[job_id]
        return {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "company_size": job.company_size,
            "location": job.location,
            "employment_type": job.employment_type,
            "description": job.description,
            "requirements": job.requirements,
            "preferred_skills": job.preferred_skills,
            "experience_level": job.experience_level,
            "education": job.education,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "benefits": job.benefits,
            "posted_date": job.posted_date,
            "apply_url": job.apply_url
        }

    def search_by_skills(self, skills: List[str], location: Optional[str]) -> dict:
        """Find job opportunities matching specific technical skill sets."""
        results = []
        skill_counts = {skill: 0 for skill in skills}
        skill_salaries = {skill: [] for skill in skills}
        
        for job in self.jobs.values():
            if location and location.lower() not in job.location.lower():
                continue
            matching = [s for s in skills if any(s.lower() in js.lower() for js in job.skills)]
            if not matching:
                continue
            match_score = len(matching) / len(skills)
            results.append({
                "job_id": job.job_id,
                "title": job.title,
                "company": job.company,
                "matching_skills": matching,
                "match_score": match_score,
                "location": job.location
            })
            for skill in matching:
                skill_counts[skill] += 1
                if job.salary_min > 0 and job.salary_max > 0:
                    skill_salaries[skill].append((job.salary_min + job.salary_max) / 2)
        
        most_requested = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        salary_by_skill = {skill: sum(salaries) / len(salaries) if salaries else 0 for skill, salaries in skill_salaries.items()}
        
        return {
            "jobs": results,
            "skill_demand": {
                "most_requested_skills": [s[0] for s in most_requested if s[1] > 0],
                "salary_by_skill": salary_by_skill
            }
        }

    def get_salary_insights(self, job_title: str, location: Optional[str], years_experience: Optional[int]) -> dict:
        """Obtain salary range estimates and compensation factor analysis."""
        salaries = []
        exp_salaries = {}
        skill_salaries = {}
        size_salaries = {}
        
        for job in self.jobs.values():
            if job_title.lower() not in job.title.lower():
                continue
            if location and location.lower() not in job.location.lower():
                continue
            if job.salary_min > 0 and job.salary_max > 0:
                avg = (job.salary_min + job.salary_max) / 2
                salaries.append(avg)
                if job.experience_level:
                    exp_salaries.setdefault(job.experience_level, []).append(avg)
                for skill in job.skills:
                    skill_salaries.setdefault(skill, []).append(avg)
                if job.company_size:
                    size_salaries.setdefault(job.company_size, []).append(avg)
        
        salaries.sort()
        n = len(salaries)
        low = salaries[n // 4] if n > 0 else 0
        mid = salaries[n // 2] if n > 0 else 0
        high = salaries[3 * n // 4] if n > 0 else 0
        
        return {
            "job_title": job_title,
            "location": location or "All",
            "salary_range_low": low,
            "salary_range_mid": mid,
            "salary_range_high": high,
            "currency": "USD",
            "pay_period": "yearly",
            "factors": {
                "by_experience": {k: sum(v) / len(v) for k, v in exp_salaries.items()},
                "by_skill": {k: sum(v) / len(v) for k, v in skill_salaries.items()},
                "by_company_size": {k: sum(v) / len(v) for k, v in size_salaries.items()}
            }
        }

    def get_tech_trends(self, time_period: str) -> dict:
        """Analyze current technology job market trends."""
        title_counts = {}
        skill_counts = {}
        skill_salaries = {}
        location_counts = {}
        
        for job in self.jobs.values():
            title_counts[job.title] = title_counts.get(job.title, 0) + 1
            location_counts[job.location] = location_counts.get(job.location, 0) + 1
            for skill in job.skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
                if job.salary_min > 0 and job.salary_max > 0:
                    skill_salaries.setdefault(skill, []).append((job.salary_min + job.salary_max) / 2)
        
        top_titles = sorted(title_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_locs = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "time_period": time_period,
            "top_job_titles": [{"title": t, "openings_count": c, "growth_rate": 0.0} for t, c in top_titles],
            "hot_skills": [{"skill": s, "demand_count": c, "avg_salary": sum(skill_salaries.get(s, [0])) / len(skill_salaries.get(s, [1]))} for s, c in top_skills],
            "top_locations": [{"location": l, "job_count": c} for l, c in top_locs]
        }

# Section 3: MCP Tools
mcp = FastMCP(name="Dice")
api = DiceAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Dice API.

    Args:
        scenario (dict): Scenario dictionary matching DiceScenario schema.

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
    Save current Dice state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_tech_jobs(keywords: str, location: str = None, remote_only: bool = False) -> dict:
    """
    Search for technology job postings on Dice using keywords, location filters, and remote work preferences.

    Args:
        keywords (str): Job title, role, or technical skills to search for.
        location (str): [Optional] Geographic location to filter results.
        remote_only (bool): [Optional] Filter to show only remote positions.

    Returns:
        jobs (list): List of job postings matching the search criteria.
        total_results (int): Total number of matching job postings.
    """
    try:
        if not keywords or not isinstance(keywords, str):
            raise ValueError("Keywords must be a non-empty string")
        return api.search_tech_jobs(keywords, location, remote_only)
    except Exception as e:
        raise e

@mcp.tool()
def get_job_details(job_id: str) -> dict:
    """
    Retrieve comprehensive details for a specific tech job posting using its unique identifier.

    Args:
        job_id (str): The unique identifier assigned to a job posting on Dice.

    Returns:
        job_id (str): The unique identifier.
        title (str): Job title.
        company (str): Company name.
        company_size (str): Company size category.
        location (str): Job location.
        employment_type (str): Employment classification.
        description (str): Job description.
        requirements (list): Job requirements.
        preferred_skills (list): Preferred skills.
        experience_level (str): Required experience level.
        education (str): Education requirements.
        salary_min (float): Minimum salary.
        salary_max (float): Maximum salary.
        benefits (list): Benefits offered.
        posted_date (str): Posted date.
        apply_url (str): Application URL.
    """
    try:
        if not job_id or not isinstance(job_id, str):
            raise ValueError("Job ID must be a non-empty string")
        if job_id not in api.jobs:
            raise ValueError(f"Job {job_id} not found")
        return api.get_job_details(job_id)
    except Exception as e:
        raise e

@mcp.tool()
def search_by_skills(skills: list, location: str = None) -> dict:
    """
    Find job opportunities matching specific technical skill sets with relevance scoring and demand analytics.

    Args:
        skills (list): Technical skills or technologies to search for.
        location (str): [Optional] Geographic location to filter results.

    Returns:
        jobs (list): List of job postings matching the specified skills.
        skill_demand (dict): Analytics regarding skill demand in the market.
    """
    try:
        if not skills or not isinstance(skills, list):
            raise ValueError("Skills must be a non-empty list")
        return api.search_by_skills(skills, location)
    except Exception as e:
        raise e

@mcp.tool()
def get_salary_insights(job_title: str, location: str = None, years_experience: int = None) -> dict:
    """
    Obtain salary range estimates and compensation factor analysis for tech roles based on market data.

    Args:
        job_title (str): The official job title or position name.
        location (str): [Optional] Geographic location to filter results.
        years_experience (int): [Optional] Years of professional experience.

    Returns:
        job_title (str): Job title.
        location (str): Location.
        salary_range_low (float): 25th percentile salary.
        salary_range_mid (float): Median salary.
        salary_range_high (float): 75th percentile salary.
        currency (str): Currency code.
        pay_period (str): Pay period.
        factors (dict): Salary variations by different factors.
    """
    try:
        if not job_title or not isinstance(job_title, str):
            raise ValueError("Job title must be a non-empty string")
        return api.get_salary_insights(job_title, location, years_experience)
    except Exception as e:
        raise e

@mcp.tool()
def get_tech_trends(time_period: str = "30d") -> dict:
    """
    Analyze current technology job market trends including in-demand skills, job title popularity, and geographic distribution.

    Args:
        time_period (str): [Optional] Time window for trend analysis (default: '30d').

    Returns:
        time_period (str): Time window used for analysis.
        top_job_titles (list): Job titles in highest demand.
        hot_skills (list): Technical skills experiencing high demand.
        top_locations (list): Geographic regions with highest job concentration.
    """
    try:
        return api.get_tech_trends(time_period)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
