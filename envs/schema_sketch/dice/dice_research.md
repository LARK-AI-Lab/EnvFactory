# Dice Research Notes

## Data Source
- Official Docs: https://www.dice.com/
- API Reference: https://www.dice.com/
- Pricing: https://www.dice.com/
- Base URL: https://api.dice.com/

## API Overview
- **Purpose**: Provides job search and posting capabilities focused on technology and engineering careers
- **Category**: recruitment
- **Target users**: Tech recruiters, IT professionals, engineering teams, and technology-focused job platforms

## Authentication
- **Type**: API Key
- **How to obtain**: Contact Dice for API partnership and access credentials
- **Header/param format**: `Authorization: Bearer {api_key}` or `X-API-Key: {api_key}`

## Core Endpoints & Design

### 1. Job Search
- **Method & path**: `GET /jobs/search`
- **Purpose**: Searches for technology and engineering job postings
- **Request params**:
  - `q` (string, optional): Search keywords (skills, title)
  - `title` (string, optional): Job title filter
  - `skills` (string, optional): Comma-separated skills
  - `location` (string, optional): City, state, or ZIP
  - `radius` (integer, optional): Search radius in miles
  - `remote` (boolean, optional): Remote jobs only
  - `employmentType` (string, optional): 'FULL_TIME', 'CONTRACT', 'PART_TIME', 'INTERNSHIP'
  - `experienceLevel` (string, optional): 'ENTRY', 'MID', 'SENIOR', 'LEAD'
  - `company` (string, optional): Company name
  - `postedDate` (string, optional): '1', '3', '7', '14', '30' days
  - `sort` (string, optional): 'relevance', 'date', 'salary'
  - `page` (integer, optional): Page number
  - `pageSize` (integer, optional): Results per page (max 100)
- **Response structure**: Job listings with title, company, location, skills, salary, posting date
- **Pagination**: Page-based with `page` and `pageSize` parameters

### 2. Get Job Details
- **Method & path**: `GET /jobs/{jobId}`
- **Purpose**: Retrieves detailed information for a specific job posting
- **Request params**:
  - `jobId` (string, required): Unique job identifier
- **Response structure**: Complete job details including description, requirements, company info, benefits
- **Pagination**: N/A - single job lookup

### 3. Skills Taxonomy
- **Method & path**: `GET /skills`
- **Purpose**: Retrieves available skills for filtering and categorization
- **Request params**:
  - `category` (string, optional): Skill category (e.g., 'Programming', 'Cloud', 'Data')
  - `search` (string, optional): Search skill names
- **Response structure**: List of skills with categories and popularity
- **Pagination**: N/A or offset-based

### 4. Companies
- **Method & path**: `GET /companies`
- **Purpose**: Retrieves technology companies posting jobs on Dice
- **Request params**:
  - `search` (string, optional): Company name search
  - `industry` (string, optional): Industry filter
  - `size` (string, optional): Company size
  - `page` (integer, optional): Page number
  - `pageSize` (integer, optional): Results per page
- **Response structure**: Company profiles with job counts, ratings, location
- **Pagination**: Page-based

### 5. Salary Estimates
- **Method & path**: `GET /salary/estimate`
- **Purpose**: Provides salary estimates for tech roles based on market data
- **Request params**:
  - `jobTitle` (string, required): Job title
  - `location` (string, optional): Location
  - `skills` (string, optional): Relevant skills
  - `experienceYears` (integer, optional): Years of experience
- **Response structure**: Salary range, median, market trends
- **Pagination**: N/A

### 6. Job Categories
- **Method & path**: `GET /categories`
- **Purpose**: Retrieves job category taxonomy for Dice
- **Response structure**: Categories and subcategories (Software Development, Data Science, DevOps, etc.)
- **Pagination**: N/A

## Data Models
Key entities and their fields:
- `TechJob`: id (string), title (string), company (object), location (object), description (string), requirements (array), skills (array), employmentType (string), experienceLevel (string), salaryRange (object), remoteOptions (object), postedDate (string), applicationUrl (string), companyInfo (object), jobType (string), clearanceRequired (boolean), visaSponsorship (boolean)
- `TechCompany`: id (string), name (string), website (string), industry (string), size (string), headquarters (object), description (string), techStack (array), benefits (array), jobCount (integer), rating (number)
- `Skill`: id (string), name (string), category (string), aliases (array), popularity (number), relatedSkills (array)
- `SalaryEstimate`: jobTitle (string), location (object), experienceRange (string), minSalary (number), maxSalary (number), medianSalary (number), currency (string), period (string), confidence (number), marketTrend (string)
- `JobCategory`: id (string), name (string), parentId (string), jobCount (integer), popularSkills (array)

## Technology Focus Areas
- Software Development & Engineering
- Data Science & Analytics
- Cloud Computing & DevOps
- Cybersecurity
- AI/ML & Deep Learning
- Mobile Development
- Web Development
- Database Administration
- Network Engineering
- IT Project Management

## Use Cases
- Tech-focused job board aggregation
- Skills-based job matching for developers
- Technology recruitment platforms
- IT staffing and consulting tools
- Tech salary benchmarking
- Developer career planning resources
- Engineering team hiring solutions
- Tech stack analysis for companies

## Response Example
```json
{
  "jobs": [
    {
      "id": "dice-job-123456",
      "title": "Senior Full Stack Developer",
      "company": {
        "id": "comp-tech789",
        "name": "InnovateTech Corp",
        "website": "https://www.innovatetech.com",
        "industry": "Software Development",
        "size": "200-500 employees",
        "headquarters": {
          "city": "Austin",
          "state": "TX",
          "country": "US"
        },
        "rating": 4.2,
        "logo": "https://assets.dice.com/companies/innovatetech-logo.png"
      },
      "location": {
        "city": "Austin",
        "state": "TX",
        "country": "US",
        "postalCode": "78701",
        "address": "123 Tech Blvd"
      },
      "description": "Join our dynamic engineering team building next-generation SaaS products...",
      "requirements": [
        "7+ years of software development experience",
        "Strong proficiency in React, Node.js, and TypeScript",
        "Experience with cloud platforms (AWS or Azure)",
        "Knowledge of microservices architecture",
        "Bachelor's degree in Computer Science or related field"
      ],
      "skills": [
        "React",
        "Node.js",
        "TypeScript",
        "AWS",
        "MongoDB",
        "GraphQL",
        "Docker",
        "Kubernetes",
        "CI/CD",
        "Agile"
      ],
      "employmentType": "FULL_TIME",
      "experienceLevel": "SENIOR",
      "salaryRange": {
        "disclosed": true,
        "min": 140000,
        "max": 180000,
        "currency": "USD",
        "period": "YEARLY"
      },
      "remoteOptions": {
        "available": true,
        "type": "HYBRID",
        "daysInOffice": 2
      },
      "postedDate": "2024-02-12",
      "applicationUrl": "https://careers.innovatetech.com/jobs/senior-full-stack-developer",
      "jobType": "PERMANENT",
      "clearanceRequired": false,
      "visaSponsorship": true,
      "benefits": [
        "Competitive salary",
        "Stock options",
        "Health insurance",
        "401(k) matching",
        "Flexible PTO",
        "Home office stipend",
        "Learning budget"
      ],
      "techStack": [
        "React",
        "Node.js",
        "AWS",
        "MongoDB",
        "Redis"
      ],
      "views": 1250,
      "applications": 45
    }
  ],
  "meta": {
    "totalResults": 3456,
    "page": 1,
    "pageSize": 25,
    "totalPages": 139,
    "sort": "relevance",
    "query": "Senior Full Stack Developer",
    "location": "Austin, TX",
    "filtersApplied": {
      "remote": false,
      "employmentType": ["FULL_TIME"],
      "experienceLevel": ["SENIOR"]
    }
  }
}
```

## Pricing
- Free tier: Limited access for job seekers
- Job Poster: Pricing per job posting or subscription for employers
- API Access: Custom pricing based on volume and use case
- Partnership: Custom agreements for platforms and aggregators
- Rate limits: Vary by access tier
- Note: Primary API access typically requires partnership agreement with Dice
