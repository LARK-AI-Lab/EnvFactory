# Resideline Research Notes

## Data Source
- Official Docs: https://resideline.com/resideline-api
- API Reference: https://resideline.com/resideline-api
- Pricing: https://resideline.com/pricing
- Base URL: https://resideline.com:2087

## API Overview
- **Purpose**: Provides property data, reports, and analytics for real estate professionals with credit-based pricing
- **Category**: real_estate
- **Target users**: Real estate agents, investors, property managers, appraisers, and mortgage professionals

## Authentication
- **Type**: API Key
- **How to obtain**: Create account at Resideline and generate API key from dashboard
- **Header/param format**: `API-Key: {your_api_key}`

## Core Endpoints & Design

### 1. Property Details
- **Method & path**: `GET /api/v1/property/details`
- **Purpose**: Retrieves basic property information and characteristics
- **Request params**:
  - `address` (string, required): Full property address
  - `city` (string, required): City name
  - `state` (string, required): State code
  - `zip` (string, required): ZIP code
- **Response structure**: Property characteristics, tax info, ownership details
- **Pagination**: N/A - single property lookup
- **Credit cost**: 1 credit

### 2. Property Report
- **Method & path**: `GET /api/v1/property/report`
- **Purpose**: Generates comprehensive property report with detailed analysis
- **Request params**:
  - `address` (string, required): Full property address
  - `city` (string, required): City name
  - `state` (string, required): State code
  - `zip` (string, required): ZIP code
  - `report_type` (string, optional): 'full', 'summary', 'investment'
- **Response structure**: Detailed property analysis, comparable sales, market trends, investment metrics
- **Pagination**: N/A - single report per request
- **Credit cost**: 10 credits

### 3. Rental Data
- **Method & path**: `GET /api/v1/property/rental`
- **Purpose**: Retrieves rental market data and rent estimates for a property
- **Request params**:
  - `address` (string, required): Full property address
  - `city` (string, required): City name
  - `state` (string, required): State code
  - `zip` (string, required): ZIP code
  - `bedrooms` (integer, optional): Number of bedrooms
  - `property_type` (string, optional): Property type filter
- **Response structure**: Rent estimates, comparable rentals, rental market trends
- **Pagination**: N/A - single property rental data
- **Credit cost**: 2 credits

### 4. Search Properties
- **Method & path**: `GET /api/v1/properties/search`
- **Purpose**: Search for properties by various criteria
- **Request params**:
  - `city` (string, optional): City name
  - `state` (string, optional): State code
  - `zip` (string, optional): ZIP code
  - `min_price` (number, optional): Minimum price
  - `max_price` (number, optional): Maximum price
  - `bedrooms` (integer, optional): Number of bedrooms
  - `property_type` (string, optional): Type of property
- **Response structure**: List of matching properties with basic details
- **Pagination**: Offset/limit based (default: limit=20, max=100)
- **Credit cost**: 1 credit per result

### 5. Batch Processing
- **Method & path**: `POST /api/v1/batch/properties`
- **Purpose**: Process multiple properties in a single request
- **Request body**: Array of property addresses
- **Response structure**: Results for each property in the batch
- **Pagination**: N/A - batch processing
- **Credit cost**: Sum of individual endpoint costs

## Data Models
Key entities and their fields:
- `PropertyDetails`: address (object), owner (object), taxes (object), characteristics (object), last_sale (object), mortgage (object)
- `PropertyReport`: property_details (object), comparables (array), market_analysis (object), investment_metrics (object), risk_factors (array)
- `RentalData`: estimated_rent (number), rent_range (object), comparable_rentals (array), rental_yield (number), occupancy_rate (number)
- `PropertySearchResult`: id (string), address (object), price (number), bedrooms (integer), bathrooms (number), square_footage (integer), property_type (string), listing_date (string)
- `CreditBalance`: remaining_credits (integer), plan_type (string), reset_date (string)

## Use Cases
- Property investment analysis and due diligence
- Comparative market analysis for real estate agents
- Rental property valuation and rent setting
- Portfolio analysis for property managers
- Mortgage underwriting support
- Property flipping opportunity identification

## Response Example
```json
{
  "property": {
    "address": {
      "street": "789 Pine Street",
      "city": "Denver",
      "state": "CO",
      "zip": "80202",
      "county": "Denver",
      "latitude": 39.7392,
      "longitude": -104.9903
    },
    "owner": {
      "name": "Jane Doe",
      "owner_occupied": false,
      "mailing_address": {
        "street": "321 Elm Blvd",
        "city": "Boulder",
        "state": "CO",
        "zip": "80301"
      }
    },
    "taxes": {
      "assessed_value": 520000,
      "tax_year": 2023,
      "land_value": 200000,
      "improvement_value": 320000,
      "tax_amount": 2800
    },
    "characteristics": {
      "property_type": "Condominium",
      "year_built": 2008,
      "bedrooms": 2,
      "bathrooms": 2,
      "square_footage": 1250,
      "lot_size": null,
      "stories": 1,
      "garage": "1 car attached",
      "pool": false
    },
    "last_sale": {
      "date": "2019-08-12",
      "price": 415000,
      "recording_date": "2019-08-19"
    },
    "mortgage": {
      "amount": 332000,
      "date": "2019-08-12",
      "lender": "Wells Fargo Bank",
      "type": "Conventional"
    }
  },
  "credits_used": 1,
  "credits_remaining": 99,
  "request_id": "req_abc123xyz"
}
```

## Pricing
- Free tier: 100 requests per day (with credit system)
- Credit system:
  - Property Details: 1 credit
  - Rental Data: 2 credits
  - Property Report: 10 credits
  - Additional credits can be purchased
- Paid plans: Monthly subscriptions with credit allocations
- Rate limits: Based on available credits
