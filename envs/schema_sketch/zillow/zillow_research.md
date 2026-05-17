# Zillow Research Notes

## Data Source
- Official Docs: https://www.zillow.com/howto/api/APIOverview.htm
- API Reference: https://www.zillow.com/howto/api/APIOverview.htm
- Pricing: https://www.zillow.com/howto/api/APIOverview.htm
- Base URL: http://www.zillow.com/webservice/

## API Overview
- **Purpose**: Provides real estate property data, home valuations (Zestimates), and market trends
- **Category**: real_estate
- **Target users**: Real estate developers, researchers, property investors, and applications requiring property data

## Authentication
- **Type**: ZWSID (API Key)
- **How to obtain**: Sign up at Zillow Developer Network and request API access
- **Header/param format**: Passed as query parameter `zws-id={your_zwsid}`

## Core Endpoints & Design

### 1. GetDeepSearchResults
- **Method & path**: `GET /GetDeepSearchResults.htm`
- **Purpose**: Retrieves comprehensive property details including Zestimate, tax assessment, lot size, etc.
- **Request params**: 
  - `zws-id` (string, required): Your Zillow API key
  - `address` (string, required): Property street address
  - `citystatezip` (string, required): City, state, or ZIP code
  - `rentzestimate` (boolean, optional): Include rent Zestimate
- **Response structure**: Property details, Zestimate (estimated market value), rent Zestimate, local real estate data
- **Pagination**: N/A - single property lookup

### 2. GetZestimate
- **Method & path**: `GET /GetZestimate.htm`
- **Purpose**: Retrieves Zillow's estimated market value (Zestimate) for a property
- **Request params**:
  - `zws-id` (string, required): Your Zillow API key
  - `zpid` (string, required): Zillow property ID
  - `rentzestimate` (boolean, optional): Include rent Zestimate
- **Response structure**: Zestimate amount, value range, last updated date, value change
- **Pagination**: N/A - single property lookup

### 3. GetComps
- **Method & path**: `GET /GetComps.htm`
- **Purpose**: Retrieves comparable recent sales for a property
- **Request params**:
  - `zws-id` (string, required): Your Zillow API key
  - `zpid` (string, required): Zillow property ID
  - `count` (integer, required): Number of comparable properties (max 25)
  - `rentzestimate` (boolean, optional): Include rent Zestimate
- **Response structure**: List of comparable properties with Zestimates and sales data
- **Pagination**: N/A - limited to count parameter

### 4. GetChart
- **Method & path**: `GET /GetChart.htm`
- **Purpose**: Generates chart images showing property value history or market trends
- **Request params**:
  - `zws-id` (string, required): Your Zillow API key
  - `zpid` (string, required): Zillow property ID
  - `unit-type` (string, required): 'dollar' or 'percent'
  - `width` (integer, optional): Chart width in pixels (default: 300)
  - `height` (integer, optional): Chart height in pixels (default: 150)
- **Response structure**: URL to generated chart image
- **Pagination**: N/A - single chart per request

## Data Models
Key entities and their fields:
- `Property`: zpid (string), address (object), zestimate (object), rentzestimate (object), taxAssessment (number), yearBuilt (integer), lotSizeSqFt (integer), finishedSqFt (integer)
- `Zestimate`: amount (number), last-updated (string), valueChange (number), valuationRange (object)
- `Address`: street (string), zipcode (string), city (string), state (string), latitude (number), longitude (number)
- `Comparable`: property fields plus lastSoldPrice (number), lastSoldDate (string)

## Use Cases
- Real estate valuation and comparison tools
- Property investment analysis applications
- Market trend visualization dashboards
- Mortgage and financing calculators
- Property listing enrichment services

## Response Example
```json
{
  "request": {
    "address": "2114 Bigelow Ave",
    "citystatezip": "Seattle, WA"
  },
  "message": {
    "text": "Request successfully processed",
    "code": "0"
  },
  "response": {
    "results": {
      "result": {
        "zpid": "48749425",
        "links": {
          "homedetails": "https://www.zillow.com/homedetails/...",
          "graphsanddata": "http://www.zillow.com/app?chartType=...",
          "mapthishome": "http://www.zillow.com/homes/..."
        },
        "address": {
          "street": "2114 Bigelow Ave N",
          "zipcode": "98109",
          "city": "Seattle",
          "state": "WA",
          "latitude": "47.63793",
          "longitude": "-122.347936"
        },
        "zestimate": {
          "amount": {
            "currency": "USD",
            "__value__": "1606150"
          },
          "last-updated": "12/20/2023",
          "valueChange": {
            "duration": "30",
            "currency": "USD",
            "__value__": "-13609"
          },
          "valuationRange": {
            "low": {
              "currency": "USD",
              "__value__": "1365227"
            },
            "high": {
              "currency": "USD",
              "__value__": "1847072"
            }
          }
        },
        "localRealEstate": {
          "region": {
            "name": "Westlake",
            "id": "344118",
            "type": "neighborhood"
          }
        }
      }
    }
  }
}
```

## Pricing
- Free tier: Available for individual, non-commercial use with rate limits
- Rate limits: 1000 requests per day (varies by API endpoint)
- Commercial use: Contact Zillow for partnership and licensing
- Note: API access is being deprecated in favor of Zillow Data Exporter and other data solutions
