# AirDNA Research Notes

## Data Source
- Official Docs: https://apidocs.airdna.co/
- API Reference: https://apidocs.airdna.co/
- Pricing: https://www.airdna.co/pricing
- Base URL: https://api.airdna.co/v1

## API Overview
- **Purpose**: Provides short-term rental market data and analytics for Airbnb and Vrbo properties
- **Category**: real_estate
- **Target users**: Short-term rental investors, property managers, hospitality analysts, and vacation rental platforms

## Authentication
- **Type**: API Access Token (Bearer Token)
- **How to obtain**: Subscribe to AirDNA service and generate API token from dashboard
- **Header/param format**: `Authorization: Bearer {access_token}`

## Core Endpoints & Design

### 1. Rentalizer Estimate
- **Method & path**: `GET /rentalizer/estimate`
- **Purpose**: Estimates potential revenue for a short-term rental property based on location and property characteristics
- **Request params**:
  - `latitude` (number, required): Property latitude
  - `longitude` (number, required): Property longitude
  - `bedrooms` (integer, required): Number of bedrooms
  - `bathrooms` (number, required): Number of bathrooms
  - `accommodates` (integer, optional): Maximum guests
  - `room_type` (string, optional): 'entire_home', 'private_room', 'shared_room'
- **Response structure**: Revenue estimate, occupancy rate, ADR (average daily rate), comparable listings
- **Pagination**: N/A - single estimate per request

### 2. Market Data
- **Method & path**: `GET /market`
- **Purpose**: Retrieves market-level statistics and trends for a geographic area
- **Request params**:
  - `city_id` (string, optional): AirDNA city ID
  - `region_id` (string, optional): AirDNA region ID
  - `country_code` (string, optional): ISO country code
  - `start_date` (string, optional): Start date (YYYY-MM-DD)
  - `end_date` (string, optional): End date (YYYY-MM-DD)
- **Response structure**: Market metrics including occupancy rates, ADR, revenue, active listings count
- **Pagination**: Cursor-based pagination for large markets

### 3. Listing Data
- **Method & path**: `GET /listing`
- **Purpose**: Retrieves detailed information about specific short-term rental listings
- **Request params**:
  - `listing_id` (string, required): Airbnb or Vrbo listing ID
  - `platform` (string, required): 'airbnb' or 'vrbo'
  - `start_date` (string, optional): Historical data start date
  - `end_date` (string, optional): Historical data end date
- **Response structure**: Listing details, performance metrics, calendar availability, pricing history
- **Pagination**: Time-series pagination for historical data

### 4. Smart Rates
- **Method & path**: `GET /smart_rates`
- **Purpose**: Provides dynamic pricing recommendations based on market demand and competition
- **Request params**:
  - `listing_id` (string, required): Listing identifier
  - `platform` (string, required): 'airbnb' or 'vrbo'
  - `start_date` (string, required): Recommendation start date
  - `end_date` (string, required): Recommendation end date
- **Response structure**: Daily rate recommendations, demand forecasts, event impacts
- **Pagination**: Date range based - max 365 days per request

## Data Models
Key entities and their fields:
- `RentalizerEstimate`: revenue_12_month (number), occupancy_rate (number), adr (number), comparable_listings (array), confidence_score (number)
- `MarketData`: city_id (string), active_listings (integer), occupancy_rate (number), adr (number), revenue (number), time_series (array)
- `Listing`: listing_id (string), platform (string), property_type (string), bedrooms (integer), bathrooms (number), accommodates (integer), amenities (array), ratings (object), performance (object)
- `SmartRate`: date (string), recommended_rate (number), demand_score (number), events (array)

## Use Cases
- Short-term rental investment analysis and property valuation
- Dynamic pricing optimization for property managers
- Market research for new vacation rental markets
- Competitive analysis of local short-term rentals
- Revenue forecasting for hospitality portfolios

## Response Example
```json
{
  "data": {
    "revenue": {
      "monthly": {
        "jan": 2450,
        "feb": 2680,
        "mar": 3200,
        "apr": 3150,
        "may": 3400,
        "jun": 4200,
        "jul": 4500,
        "aug": 4300,
        "sep": 3600,
        "oct": 3100,
        "nov": 2800,
        "dec": 3200
      },
      "annual": 40580
    },
    "occupancy": {
      "monthly": {
        "jan": 0.65,
        "feb": 0.68,
        "mar": 0.72,
        "apr": 0.70,
        "may": 0.75,
        "jun": 0.85,
        "jul": 0.88,
        "aug": 0.86,
        "sep": 0.78,
        "oct": 0.72,
        "nov": 0.68,
        "dec": 0.74
      },
      "annual": 0.75
    },
    "adr": {
      "monthly": {
        "jan": 125,
        "feb": 130,
        "mar": 145,
        "apr": 148,
        "may": 150,
        "jun": 165,
        "jul": 170,
        "aug": 168,
        "sep": 155,
        "oct": 145,
        "nov": 138,
        "dec": 142
      },
      "annual": 148
    },
    "comparable_listings": [
      {
        "listing_id": "12345678",
        "platform": "airbnb",
        "revenue": 42000,
        "occupancy": 0.78,
        "adr": 155
      }
    ],
    "confidence_score": 0.87,
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "city": "New York",
      "state": "NY"
    }
  }
}
```

## Pricing
- Free tier: Not available - subscription required
- Starter plan: Basic market data and limited API calls
- Professional plan: Full API access with higher rate limits
- Enterprise plan: Custom volume pricing and dedicated support
- Rate limits: Vary by subscription tier (typically 100-10,000 requests/day)
