# Glassdoor Research Notes

## Data Source
- Official Docs: https://www.glassdoor.com/developer/index.htm
- API Reference: https://www.glassdoor.com/developer/companies.htm
- Pricing: https://www.glassdoor.com/developer/
- Base URL: https://api.glassdoor.com/api/api.htm

## API Overview
- **Purpose**: Provides company reviews, salary data, job listings, and interview information from Glassdoor's database
- **Category**: recruitment
- **Target users**: Job search platforms, career research tools, HR analytics, and employer branding services

## Authentication
- **Type**: Partner ID + API Key (t.p + t.k parameters)
- **How to obtain**: Apply for Glassdoor Partner API access at https://www.glassdoor.com/developer/
- **Header/param format**: `t.p={partner_id}&t.k={api_key}` as query parameters

## Core Endpoints & Design

### 1. Companies Search
- **Method & path**: `GET /api.htm`
- **Purpose**: Searches for companies and retrieves company information
- **Request params**:
  - `t.p` (string, required): Partner ID
  - `t.k` (string, required): API Key
  - `userip` (string, required): End user's IP address
  - `useragent` (string, required): End user's browser user-agent
  - `format` (string, optional): 'json' or 'xml' (default: json)
  - `v` (string, required): API version (1)
  - `action` (string, required): 'employers' for company search
  - `q` (string, optional): Query string (company name)
  - `l` (string, optional): Location
  - `pn` (integer, optional): Page number
  - `ps` (integer, optional): Page size (max 100)
  - `returnStates` (boolean, optional): Return state data
  - `returnCities` (boolean, optional): Return city data
  - `returnJobTitles` (boolean, optional): Return job title data
  - `returnEmployers` (boolean, optional): Return employer data
- **Response structure**: Company list with name, ID, ratings, reviews count, website, etc.
- **Pagination**: Page-based with `pn` (page number) and `ps` (page size)

### 2. Jobs Search
- **Method & path**: `GET /api.htm`
- **Purpose**: Searches for job listings on Glassdoor
- **Request params**:
  - `t.p` (string, required): Partner ID
  - `t.k` (string, required): API Key
  - `userip` (string, required): End user's IP address
  - `useragent` (string, required): End user's browser user-agent
  - `format` (string, optional): 'json' or 'xml' (default: json)
  - `v` (string, required): API version (1)
  - `action` (string, required): 'jobs' for job search
  - `q` (string, optional): Job title keywords
  - `l` (string, optional): Location
  - `pn` (integer, optional): Page number
  - `ps` (integer, optional): Page size (max 100)
  - `employerId` (integer, optional): Filter by specific employer ID
  - `jobType` (string, optional): 'fulltime', 'parttime', 'contract', 'internship'
  - `fromAge` (integer, optional): Days since posting
  - `minSalary` (number, optional): Minimum salary
  - `maxSalary` (number, optional): Maximum salary
- **Response structure**: Job listings with title, company, location, salary, URL, etc.
- **Pagination**: Page-based with `pn` (page number) and `ps` (page size)

### 3. Company Reviews
- **Method & path**: `GET /api.htm`
- **Purpose**: Retrieves company reviews (may require additional permissions)
- **Request params**:
  - `t.p` (string, required): Partner ID
  - `t.k` (string, required): API Key
  - `action` (string, required): 'reviews'
  - `employerId` (integer, required): Company ID
- **Response structure**: Reviews with ratings, pros, cons, advice to management
- **Pagination**: Page-based pagination

## Data Models
Key entities and their fields:
- `Employer`: id (integer), name (string), website (string), industry (string), numberOfRatings (integer), overallRating (number), cultureAndValuesRating (number), workLifeBalanceRating (number), seniorManagementRating (number), compensationAndBenefitsRating (number), careerOpportunitiesRating (number), squareLogo (string), ceo (object), featuredReview (object)
- `JobListing`: jobTitle (string), employerName (string), employerId (integer), location (string), basePay (object), jobUrl (string), jobSource (string), datePosted (string), description (string), category (string)
- `Review`: id (integer), employerId (integer), employerName (string), ratingOverall (number), ratingCeo (string), ratingCultureAndValues (number), ratingWorkLifeBalance (number), ratingSeniorManagement (number), ratingCompensationAndBenefits (number), ratingCareerOpportunities (number), pros (string), cons (string), adviceToManagement (string), headline (string), reviewDateTime (string), jobTitle (object), location (string), originalLanguageId (integer)
- `CEO`: name (string), title (string), numberOfRatings (integer), pctApprove (number), pctDisapprove (number)
- `Salary`: jobTitle (string), employerName (string), location (string), basePay (object), meanBasePay (number), currencyCode (string)

## Use Cases
- Company research and comparison platforms
- Job search aggregation and filtering
- Salary benchmarking and compensation analysis
- Employer branding and reputation monitoring
- Interview preparation resources
- Career decision support tools
- HR competitive intelligence

## Response Example
```json
{
  "success": true,
  "status": "OK",
  "jsessionid": "ABC123XYZ789",
  "headers": {
    " elapsedTime": "125",
    "timeStamp": "2024-02-15 10:30:45",
    "apiVersion": "1.0"
  },
  "response": {
    "employers": [
      {
        "id": 12345,
        "name": "TechCorp Inc",
        "website": "www.techcorp.com",
        "industry": "Computer Software",
        "numberOfRatings": 2856,
        "squareLogo": "https://media.glassdoor.com/sql/12345/techcorp-squarelogo.png",
        "overallRating": "4.2",
        "ratingDescription": "Very Good",
        "cultureAndValuesRating": "4.3",
        "workLifeBalanceRating": "4.0",
        "seniorManagementRating": "3.9",
        "compensationAndBenefitsRating": "4.1",
        "careerOpportunitiesRating": "4.2",
        "recommendToFriendRating": "85",
        "sectorId": 10015,
        "sectorName": "Information Technology",
        "industryId": 20026,
        "industryName": "Enterprise Software",
        "featuredReview": {
          "id": 9876543,
          "reviewDateTime": "2024-01-20 14:30:00",
          "ratingOverall": 5,
          "ratingCeo": "APPROVES",
          "pros": "Great work-life balance and excellent benefits",
          "cons": "Career advancement can be slow",
          "headline": "Great place to work",
          "jobTitle": {
            "jobTitle": "Software Engineer"
          },
          "location": "San Francisco, CA"
        },
        "ceo": {
          "name": "Jane Smith",
          "title": "CEO",
          "numberOfRatings": 1245,
          "pctApprove": 88,
          "pctDisapprove": 12
        }
      }
    ],
    "currentPageNumber": 1,
    "totalNumberOfPages": 15,
    "totalRecordCount": 147,
    "exactMatch": false
  }
}
```

## Pricing
- Free tier: Limited API access for approved partners
- Partner Program: Free for non-commercial use with attribution requirements
- Commercial License: Custom pricing for high-volume commercial use
- Rate limits: Vary based on partnership agreement
- Requirements:
  - Must display Glassdoor attribution
  - Must link back to Glassdoor
  - Limited to specific use cases
- Note: API access is restricted and requires approval from Glassdoor
