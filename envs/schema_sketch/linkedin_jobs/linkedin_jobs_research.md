# LinkedIn Jobs Research Notes

## Data Source
- Official Docs: https://learn.microsoft.com/en-us/linkedin/talent/
- API Reference: https://learn.microsoft.com/en-us/linkedin/talent/job-postings
- Pricing: https://developer.linkedin.com/pricing
- Base URL: https://api.linkedin.com/v2/

## API Overview
- **Purpose**: Enables job posting management, job search, and talent acquisition integration with LinkedIn's professional network
- **Category**: recruitment
- **Target users**: HR platforms, ATS (Applicant Tracking Systems), job boards, and enterprise recruiters

## Authentication
- **Type**: OAuth 2.0
- **How to obtain**: Create a LinkedIn Developer application, request Talent Solutions API access, and complete OAuth flow
- **Header/param format**: `Authorization: Bearer {access_token}`

## Core Endpoints & Design

### 1. Jobs API
- **Method & path**: `GET /jobs`
- **Purpose**: Retrieves job postings and job details
- **Request params**:
  - `jobPosting` (string, required): Job posting ID
  - `fields` (string, optional): Comma-separated list of fields to return
  - `projection` (string, optional): Field projection parameters
- **Response structure**: Job title, description, location, company, application URL, posting dates, employment type
- **Pagination**: Cursor-based pagination with `start` and `count` parameters

### 2. Job Search
- **Method & path**: `GET /jobSearch`
- **Purpose**: Searches for job postings with various filters
- **Request params**:
  - `keywords` (string, optional): Search keywords
  - `location` (string, optional): Location string
  - `geoId` (string, optional): LinkedIn geo ID
  - `company` (string, optional): Company ID or name
  - `jobType` (string, optional): 'F' (Full-time), 'C' (Contract), 'P' (Part-time), 'T' (Temporary)
  - `experienceLevel` (string, optional): Entry, Associate, Mid-Senior, Director, Executive
  - `start` (integer, optional): Pagination offset
  - `count` (integer, optional): Results per page (max 50)
- **Response structure**: List of job postings with basic details
- **Pagination**: Offset-based with `start` and `count` parameters

### 3. Recommended Jobs
- **Method & path**: `GET /recommendedJobs`
- **Purpose**: Retrieves personalized job recommendations for a user
- **Request params**:
  - `q` (string, required): Query type, typically 'criteria'
  - `jobTitle` (string, optional): Target job title
  - `location` (string, optional): Target location
  - `start` (integer, optional): Pagination offset
  - `count` (integer, optional): Results per page
- **Response structure**: List of recommended job postings
- **Pagination**: Offset-based with `start` and `count` parameters

### 4. Create Job Posting
- **Method & path**: `POST /jobs`
- **Purpose**: Creates a new job posting on LinkedIn
- **Request body**:
  - `author` (string, required): Company URN posting the job
  - `lifecycleState` (string, required): 'PUBLISHED' or 'DRAFT'
  - `content` (object, required): Job content including title, description, location
  - `visibility` (string, optional): 'PUBLIC' or 'CONNECTIONS'
- **Response structure**: Created job posting ID and details
- **Pagination**: N/A

### 5. Job Applications
- **Method & path**: `GET /jobApplications`
- **Purpose**: Retrieves job applications for a posted job
- **Request params**:
  - `job` (string, required): Job posting URN
  - `fields` (string, optional): Fields to include
  - `start` (integer, optional): Pagination offset
  - `count` (integer, optional): Results per page
- **Response structure**: List of applicants with profile summaries
- **Pagination**: Offset-based with `start` and `count` parameters

## Data Models
Key entities and their fields:
- `JobPosting`: id (string), title (string), description (object), location (object), company (object), employmentStatus (string), experienceLevel (string), industries (array), skills (array), applicationUrl (string), postingDate (string), closingDate (string)
- `JobLocation`: country (string), city (string), state (string), postalCode (string), description (string)
- `CompanyInfo`: id (string), name (string), logo (string), description (string)
- `JobApplication`: applicant (object), appliedAt (string), resume (object), coverLetter (object), answers (array)
- `JobSearchResult`: jobPosting (object), matchedSkills (array), relevanceScore (number)

## Use Cases
- Job board aggregation and syndication
- ATS integration for job posting and application tracking
- Internal talent marketplace platforms
- Job recommendation engines
- Recruiting analytics and reporting
- Candidate sourcing automation

## Response Example
```json
{
  "paging": {
    "start": 0,
    "count": 10,
    "total": 156
  },
  "elements": [
    {
      "id": "urn:li:jobPosting:123456789",
      "title": "Senior Software Engineer",
      "description": {
        "text": "We are looking for a Senior Software Engineer to join our team..."
      },
      "location": {
        "country": "US",
        "city": "San Francisco",
        "state": "CA",
        "postalCode": "94105"
      },
      "company": {
        "id": "urn:li:organization:1234",
        "name": "Tech Corp",
        "logo": "https://media.licdn.com/dms/image/..."
      },
      "employmentStatus": "FULL_TIME",
      "experienceLevel": "MID_SENIOR_LEVEL",
      "industries": [
        "urn:li:industry:4"
      ],
      "skills": [
        "Python",
        "Java",
        "AWS",
        "Kubernetes"
      ],
      "applicationUrl": "https://careers.techcorp.com/jobs/123",
      "postingDate": "2024-01-15",
      "closingDate": "2024-02-15",
      "listedAt": 1705315200000,
      "views": 1250,
      "applies": 45,
      "remoteAllowed": true,
      "workplaceTypes": [
        "Remote",
        "Hybrid"
      ]
    }
  ]
}
```

## Pricing
- Free tier: Basic API access with limited endpoints (profile, share)
- Recruiter System Connect: Requires LinkedIn Recruiter contract
- Talent Solutions API: Enterprise pricing based on volume and features
- Rate limits: Vary by API tier and partnership agreement
- Note: Job posting API typically requires LinkedIn Talent Solutions partnership
