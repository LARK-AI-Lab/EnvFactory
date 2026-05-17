# Coresignal Jobs Research Notes

## Data Source
- Official Docs: https://coresignal.com/solutions/jobs-data-api/
- API Reference: https://coresignal.com/solutions/jobs-data-api/
- Pricing: https://coresignal.com/pricing/
- Base URL: https://api.coresignal.com/cdapi/v1

## API Overview
- **Purpose**: Provides comprehensive job posting data aggregated from multiple sources including LinkedIn, Indeed, Glassdoor, and Wellfound
- **Category**: recruitment
- **Target users**: HR tech platforms, job boards, labor market analytics firms, recruitment agencies, and data-driven enterprises

## Authentication
- **Type**: API Key
- **How to obtain**: Sign up for Coresignal account and request API access
- **Header/param format**: `Authorization: Bearer {api_key}` or `api-key: {api_key}`

## Core Endpoints & Design

### 1. Base Jobs API
- **Method & path**: `GET /jobs`
- **Purpose**: Retrieves job postings from the base job database
- **Request params**:
  - `job_title` (string, optional): Job title keywords
  - `company_name` (string, optional): Company name filter
  - `location` (string, optional): Location (city, state, country)
  - `country` (string, optional): Country code
  - `city` (string, optional): City name
  - `industry` (string, optional): Industry sector
  - `job_type` (string, optional): 'full_time', 'part_time', 'contract', 'internship'
  - `experience_level` (string, optional): 'entry', 'mid', 'senior', 'executive'
  - `posted_after` (string, optional): Date filter (YYYY-MM-DD)
  - `posted_before` (string, optional): Date filter (YYYY-MM-DD)
  - `limit` (integer, optional): Results per page (max 100)
  - `offset` (integer, optional): Pagination offset
- **Response structure**: List of job postings with title, company, location, description, URL, posting date
- **Pagination**: Offset/limit based (default: limit=10, max=100)

### 2. Multi-source Jobs API
- **Method & path**: `GET /jobs/multi_source`
- **Purpose**: Retrieves job postings aggregated from multiple job platforms
- **Request params**:
  - `source` (string, optional): Filter by source - 'linkedin', 'indeed', 'glassdoor', 'wellfound'
  - `job_title` (string, optional): Job title keywords
  - `company_name` (string, optional): Company name
  - `location` (string, optional): Location filter
  - `limit` (integer, optional): Results per page
  - `offset` (integer, optional): Pagination offset
- **Response structure**: Job postings with source attribution and platform-specific data
- **Pagination**: Offset/limit based

### 3. Get Job by ID
- **Method & path**: `GET /jobs/{id}`
- **Purpose**: Retrieves detailed information for a specific job posting
- **Request params**:
  - `id` (string, required): Job posting ID
- **Response structure**: Complete job details including full description, requirements, benefits, company info
- **Pagination**: N/A - single job lookup

### 4. Companies
- **Method & path**: `GET /companies`
- **Purpose**: Retrieves company information from job data sources
- **Request params**:
  - `company_name` (string, optional): Company name search
  - `industry` (string, optional): Industry filter
  - `location` (string, optional): Location filter
  - `size` (string, optional): Company size range
  - `limit` (integer, optional): Results per page
  - `offset` (integer, optional): Pagination offset
- **Response structure**: Company details including name, industry, size, location, website
- **Pagination**: Offset/limit based

### 5. Search Filter Options
- **Method & path**: `GET /jobs/filters`
- **Purpose**: Retrieves available filter values for job searches
- **Response structure**: Available industries, locations, job types, experience levels
- **Pagination**: N/A

### 6. Job Statistics
- **Method & path**: `GET /jobs/statistics`
- **Purpose**: Provides aggregated statistics about job postings
- **Request params**:
  - `group_by` (string, required): 'industry', 'location', 'company', 'job_title'
  - `date_range` (string, optional): Date range for statistics
- **Response structure**: Aggregated counts and metrics
- **Pagination**: N/A - aggregated data

## Data Models
Key entities and their fields:
- `JobPosting`: id (string), title (string), company (object), location (object), description (string), requirements (array), responsibilities (array), benefits (array), job_type (string), experience_level (string), salary_range (object), posting_date (string), application_url (string), source (string), source_url (string), industry (array), skills (array), remote_allowed (boolean)
- `Company`: id (string), name (string), website (string), industry (array), size (string), headquarters (object), description (string), logo (string), linkedin_url (string)
- `Location`: city (string), state (string), country (string), postal_code (string), address (string), remote (boolean)
- `SalaryRange`: min_amount (number), max_amount (number), currency (string), period (string), disclosed (boolean)
- `JobStatistics`: category (string), count (integer), trend (number), avg_salary (number), top_skills (array)
- `JobSource`: name (string), url (string), last_updated (string), total_jobs (integer), coverage (array)

## Data Sources
- **LinkedIn**: Professional job postings with company insights
- **Indeed**: Wide range of job listings across industries
- **Glassdoor**: Jobs with company reviews and salary data
- **Wellfound (AngelList)**: Startup and tech-focused job postings

## Use Cases
- Job board aggregation and syndication
- Labor market trend analysis
- Competitive intelligence for recruitment
- Salary benchmarking across platforms
- Job recommendation engines
- Talent pool analysis
- Market research and reporting
- AI/ML training data for recruitment models

## Response Example
```json
{
  "data": [
    {
      "id": "job_abc123xyz",
      "title": "Senior Data Engineer",
      "company": {
        "id": "comp_def456uvw",
        "name": "DataTech Solutions",
        "website": "https://www.datatech.com",
        "industry": ["Software Development", "Data Analytics"],
        "size": "500-1000 employees",
        "headquarters": {
          "city": "San Francisco",
          "state": "CA",
          "country": "US"
        },
        "linkedin_url": "https://www.linkedin.com/company/datatech-solutions"
      },
      "location": {
        "city": "San Francisco",
        "state": "CA",
        "country": "US",
        "postal_code": "94105",
        "remote": true,
        "remote_type": "hybrid"
      },
      "description": "We are looking for a Senior Data Engineer to join our growing team...",
      "requirements": [
        "5+ years of experience with data engineering",
        "Strong Python and SQL skills",
        "Experience with AWS data services (Redshift, Glue, EMR)",
        "Knowledge of data warehousing and ETL processes"
      ],
      "responsibilities": [
        "Design and build scalable data pipelines",
        "Optimize data architecture for analytics",
        "Collaborate with data science teams",
        "Ensure data quality and governance"
      ],
      "benefits": [
        "Competitive salary",
        "Health, dental, and vision insurance",
        "401(k) matching",
        "Flexible PTO",
        "Remote work options"
      ],
      "job_type": "full_time",
      "experience_level": "senior",
      "salary_range": {
        "disclosed": true,
        "min_amount": 150000,
        "max_amount": 200000,
        "currency": "USD",
        "period": "yearly"
      },
      "posting_date": "2024-02-10",
      "application_url": "https://careers.datatech.com/jobs/senior-data-engineer",
      "source": "linkedin",
      "source_url": "https://www.linkedin.com/jobs/view/senior-data-engineer-12345",
      "industry": ["Software Development", "Data Analytics"],
      "skills": ["Python", "SQL", "AWS", "ETL", "Data Warehousing", "Apache Spark"],
      "remote_allowed": true
    }
  ],
  "meta": {
    "total": 15234,
    "limit": 10,
    "offset": 0,
    "sources": {
      "linkedin": 8234,
      "indeed": 4512,
      "glassdoor": 1876,
      "wellfound": 612
    }
  }
}
```

## Pricing
- Free tier: Limited trial access available
- Starter plan: Basic API access with limited requests
- Professional plan: Higher volume with full data access
- Enterprise plan: Custom pricing with dedicated support and custom data exports
- Rate limits: Vary by subscription tier
- Data freshness: Real-time to 24-hour updates depending on plan
