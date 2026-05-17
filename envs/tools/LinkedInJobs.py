from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Job(BaseModel):
    """Represents a job posting."""
    job_id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    employment_type: str = Field(..., description="Employment type")
    posted_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Posted date in ISO 8601 format")
    url: str = Field(..., description="Job posting URL")

class JobDetail(BaseModel):
    """Represents detailed job information."""
    job_id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    company_id: str = Field(..., description="Company identifier")
    description: str = Field(..., description="Full job description")
    location: str = Field(..., description="Job location")
    employment_type: str = Field(..., description="Employment type")
    experience_level: str = Field(..., description="Required experience level")
    industries: List[str] = Field(default=[], description="Associated industries")
    posted_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Posted date in ISO 8601 format")
    application_url: str = Field(..., description="Application URL")
    url: str = Field(..., description="Job posting URL")

class CompanyJob(BaseModel):
    """Represents a company job posting."""
    job_id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    location: str = Field(..., description="Job location")
    posted_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Posted date in ISO 8601 format")

class RecommendedJob(BaseModel):
    """Represents a recommended job posting."""
    job_id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Match score between 0.0 and 1.0")
    reason: str = Field(..., description="Recommendation reason")

class Company(BaseModel):
    """Represents company information."""
    company_id: str = Field(..., description="Unique company identifier")
    name: str = Field(..., description="Company name")
    description: str = Field(..., description="Company description")
    industry: str = Field(..., description="Primary industry")
    company_size: str = Field(..., description="Company size range")
    headquarters: str = Field(..., description="Headquarters location")
    website: str = Field(..., description="Company website URL")
    follower_count: int = Field(..., ge=0, description="Number of followers")

class LinkedInJobsScenario(BaseModel):
    """Main scenario model for LinkedIn jobs."""
    jobs: Dict[str, JobDetail] = Field(default={}, description="All job postings by job_id")
    companies: Dict[str, Company] = Field(default={}, description="All companies by company_id")
    user_profiles: Dict[str, Dict[str, Any]] = Field(default={}, description="User profiles with skills and preferences")

Scenario_Schema = [Job, JobDetail, CompanyJob, RecommendedJob, Company, LinkedInJobsScenario]

# Section 2: Class
class LinkedInJobsAPI:
    def __init__(self):
        """Initialize LinkedIn Jobs API with empty state."""
        self.jobs: Dict[str, JobDetail] = {}
        self.companies: Dict[str, Company] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = LinkedInJobsScenario(**scenario)
        self.jobs = {job_id: JobDetail(**job) if isinstance(job, dict) else job for job_id, job in model.jobs.items()}
        self.companies = {company_id: Company(**company) if isinstance(company, dict) else company for company_id, company in model.companies.items()}
        self.user_profiles = model.user_profiles

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "jobs": {job_id: job.model_dump() for job_id, job in self.jobs.items()},
            "companies": {company_id: company.model_dump() for company_id, company in self.companies.items()},
            "user_profiles": self.user_profiles
        }

    def search_jobs(self, keywords: str, location: Optional[str], job_type: Optional[str]) -> dict:
        """Search for job postings using keywords, location, and job type filters."""
        results = []
        for job in self.jobs.values():
            if keywords.lower() in job.title.lower():
                if location and location.lower() not in job.location.lower():
                    continue
                if job_type and job.employment_type != job_type:
                    continue
                results.append({
                    "job_id": job.job_id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "employment_type": job.employment_type,
                    "posted_date": job.posted_date,
                    "url": job.url
                })
        return {"jobs": results, "total_count": len(results)}

    def get_job_details(self, job_id: str) -> dict:
        """Retrieve comprehensive details about a specific job posting."""
        job = self.jobs[job_id]
        return {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "company_id": job.company_id,
            "description": job.description,
            "location": job.location,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "industries": job.industries,
            "posted_date": job.posted_date,
            "application_url": job.application_url
        }

    def get_company_jobs(self, company_id: str, count: Optional[int]) -> dict:
        """Retrieve all active job postings from a specific company."""
        company = self.companies[company_id]
        company_jobs = []
        for job in self.jobs.values():
            if job.company_id == company_id:
                company_jobs.append({
                    "job_id": job.job_id,
                    "title": job.title,
                    "location": job.location,
                    "posted_date": job.posted_date
                })
        if count:
            company_jobs = company_jobs[:count]
        return {"company_name": company.name, "jobs": company_jobs}

    def get_recommended_jobs(self, user_id: Optional[str]) -> dict:
        """Retrieve personalized job recommendations based on user profile."""
        if not user_id:
            user_id = "default_user"
        profile = self.user_profiles.get(user_id, {})
        user_skills = profile.get("skills", [])
        recommendations = []
        for job in self.jobs.values():
            match_count = sum(1 for skill in user_skills if skill.lower() in job.description.lower())
            if match_count > 0:
                match_score = min(match_count / len(user_skills), 1.0) if user_skills else 0.5
                reason = f"Matches your skills in {', '.join(user_skills[:3])}"
                recommendations.append({
                    "job_id": job.job_id,
                    "title": job.title,
                    "company": job.company,
                    "match_score": match_score,
                    "reason": reason
                })
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return {"jobs": recommendations}

    def get_company_info(self, company_id: str) -> dict:
        """Retrieve detailed information about a company."""
        company = self.companies[company_id]
        return {
            "company_id": company.company_id,
            "name": company.name,
            "description": company.description,
            "industry": company.industry,
            "company_size": company.company_size,
            "headquarters": company.headquarters,
            "website": company.website,
            "follower_count": company.follower_count
        }

# Section 3: MCP Tools
mcp = FastMCP(name="LinkedInJobs")
api = LinkedInJobsAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the LinkedIn Jobs API.

    Args:
        scenario (dict): Scenario dictionary matching LinkedInJobsScenario schema.

    Returns:
        success_message (str): Success message.
    """
    if not isinstance(scenario, dict):
        raise ValueError("Scenario must be a dictionary")
    api.load_scenario(scenario)
    return "Successfully loaded scenario"

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current LinkedIn Jobs state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    return api.save_scenario()

@mcp.tool()
def search_jobs(keywords: str, location: str = None, job_type: str = None) -> dict:
    """
    Search for job postings on LinkedIn using keywords, location, and employment type filters.

    Args:
        keywords (str): Job title or keywords to search for.
        location (str): [Optional] Geographic location to filter job results.
        job_type (str): [Optional] Employment type filter (FULL_TIME, PART_TIME, CONTRACT, TEMPORARY, INTERNSHIP, VOLUNTEER).

    Returns:
        jobs (array): List of job postings matching the search criteria.
        total_count (int): Total number of job postings found.
    """
    if not keywords or not isinstance(keywords, str):
        raise ValueError("Keywords must be a non-empty string")
    return api.search_jobs(keywords, location, job_type)

@mcp.tool()
def get_job_details(job_id: str) -> dict:
    """
    Retrieve comprehensive details about a specific LinkedIn job posting.

    Args:
        job_id (str): The unique identifier for the LinkedIn job posting.

    Returns:
        job_id (str): The unique identifier for the LinkedIn job posting.
        title (str): The job title or position name.
        company (str): The name of the hiring company.
        company_id (str): The unique identifier for the company on LinkedIn.
        description (str): The full job description.
        location (str): The geographic location of the job.
        employment_type (str): The type of employment.
        experience_level (str): The required experience level.
        industries (array): List of industries associated with the job posting.
        posted_date (str): The date when the job was posted.
        application_url (str): The URL where candidates can apply.
    """
    if not job_id or not isinstance(job_id, str):
        raise ValueError("Job ID must be a non-empty string")
    if job_id not in api.jobs:
        raise ValueError(f"Job {job_id} not found")
    return api.get_job_details(job_id)

@mcp.tool()
def get_company_jobs(company_id: str, count: int = None) -> dict:
    """
    Retrieve all active job postings from a specific company on LinkedIn.

    Args:
        company_id (str): The unique identifier for the company on LinkedIn.
        count (int): [Optional] The maximum number of job postings to return.

    Returns:
        company_name (str): The name of the company.
        jobs (array): List of active job postings from the company.
    """
    if not company_id or not isinstance(company_id, str):
        raise ValueError("Company ID must be a non-empty string")
    if company_id not in api.companies:
        raise ValueError(f"Company {company_id} not found")
    return api.get_company_jobs(company_id, count)

@mcp.tool()
def get_recommended_jobs(user_id: str = None) -> dict:
    """
    Retrieve personalized job recommendations based on user profile, skills, and preferences.

    Args:
        user_id (str): [Optional] The unique identifier for the LinkedIn user.

    Returns:
        jobs (array): List of recommended job postings tailored to the user's profile.
    """
    return api.get_recommended_jobs(user_id)

@mcp.tool()
def get_company_info(company_id: str) -> dict:
    """
    Retrieve detailed information about a company from LinkedIn.

    Args:
        company_id (str): The unique identifier for the company on LinkedIn.

    Returns:
        company_id (str): The unique identifier for the company on LinkedIn.
        name (str): The official name of the company.
        description (str): A detailed description of the company.
        industry (str): The primary industry sector.
        company_size (str): The size range of the company.
        headquarters (str): The location of the company's headquarters.
        website (str): The company's official website URL.
        follower_count (int): The number of LinkedIn users following the company.
    """
    if not company_id or not isinstance(company_id, str):
        raise ValueError("Company ID must be a non-empty string")
    if company_id not in api.companies:
        raise ValueError(f"Company {company_id} not found")
    return api.get_company_info(company_id)

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()

