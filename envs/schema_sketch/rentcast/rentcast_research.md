# RentCast Research Notes

## Data Source
- Official Docs: https://developers.rentcast.io/reference/introduction
- API Reference: https://developers.rentcast.io/reference
- Pricing: https://developers.rentcast.io/reference/pricing-and-rate-limits
- Base URL: https://api.rentcast.io/v1

## API Overview
- **Purpose**: Provides comprehensive property data, real estate listings, AVM (Automated Valuation Model), and market analytics
- **Category**: real_estate
- **Target users**: Real estate investors, property managers, developers, proptech applications, and market researchers

## Authentication
- **Type**: API Key
- **How to obtain**: Sign up at RentCast Developers portal and generate API key
- **Header/param format**: `X-API-Key: {your_api_key}`

## Core Endpoints & Design

### 1. Properties
- **Method & path**: `GET /properties`
- **Purpose**: Retrieves detailed property information including ownership, tax, and physical characteristics
- **Request params**:
  - `address` (string, optional): Full property address
  - `city` (string, optional): City name
  - `state` (string, optional): State code
  - `zipCode` (string, optional): ZIP code
  - `latitude` (number, optional): Latitude coordinate
  - `longitude` (number, optional): Longitude coordinate
  - `radius` (number, optional): Search radius in miles
- **Response structure**: Property details, ownership info, tax assessment, property characteristics
- **Pagination**: Offset/limit based (default: limit=10, max=100)

### 2. Sale Listings
- **Method & path**: `GET /listings/sale`
- **Purpose**: Retrieves active for-sale property listings
- **Request params**:
  - `city` (string, optional): City name
  - `state` (string, optional): State code
  - `zipCode` (string, optional): ZIP code
  - `minPrice` (number, optional): Minimum listing price
  - `maxPrice` (number, optional): Maximum listing price
  - `bedrooms` (integer, optional): Number of bedrooms
  - `bathrooms` (number, optional): Number of bathrooms
  - `propertyType` (string, optional): 'Single Family', 'Condo', 'Townhouse', etc.
- **Response structure**: Listing details, price, property features, listing agent info, days on market
- **Pagination**: Offset/limit based (default: limit=10, max=100)

### 3. Rental Listings
- **Method & path**: `GET /listings/rental`
- **Purpose**: Retrieves active rental property listings
- **Request params**:
  - `city` (string, optional): City name
  - `state` (string, optional): State code
  - `zipCode` (string, optional): ZIP code
  - `minRent` (number, optional): Minimum monthly rent
  - `maxRent` (number, optional): Maximum monthly rent
  - `bedrooms` (integer, optional): Number of bedrooms
  - `bathrooms` (number, optional): Number of bathrooms
  - `petsAllowed` (boolean, optional): Filter pet-friendly rentals
- **Response structure**: Rental details, monthly rent, deposit info, lease terms, amenities
- **Pagination**: Offset/limit based (default: limit=10, max=100)

### 4. AVM (Automated Valuation Model)
- **Method & path**: `GET /avm`
- **Purpose**: Provides automated property valuations based on comparable sales and market data
- **Request params**:
  - `address` (string, required): Full property address
  - `latitude` (number, optional): Latitude coordinate
  - `longitude` (number, optional): Longitude coordinate
- **Response structure**: Estimated value, value range, confidence score, comparable properties
- **Pagination**: N/A - single property valuation

### 5. Market Data
- **Method & path**: `GET /market-data`
- **Purpose**: Retrieves aggregated market statistics for a geographic area
- **Request params**:
  - `city` (string, optional): City name
  - `state` (string, optional): State code
  - `zipCode` (string, optional): ZIP code
  - `propertyType` (string, optional): Filter by property type
- **Response structure**: Median prices, price per sqft, days on market, inventory levels, market trends
- **Pagination**: N/A - aggregated market data

## Data Models
Key entities and their fields:
- `Property`: id (string), address (object), owner (object), taxes (object), propertyType (string), bedrooms (integer), bathrooms (number), squareFootage (integer), lotSize (integer), yearBuilt (integer), assessedValue (number), marketValue (number)
- `SaleListing`: id (string), address (object), price (number), propertyType (string), bedrooms (integer), bathrooms (number), squareFootage (integer), listingDate (string), daysOnMarket (integer), listingAgent (object)
- `RentalListing`: id (string), address (object), monthlyRent (number), deposit (number), propertyType (string), bedrooms (integer), bathrooms (number), petsAllowed (boolean), availableDate (string), amenities (array)
- `AVMResult`: estimatedValue (number), valueRangeLow (number), valueRangeHigh (number), confidenceScore (number), comparables (array), valuationDate (string)
- `MarketData`: medianPrice (number), averagePrice (number), pricePerSqft (number), daysOnMarket (number), totalListings (integer), newListings (integer), priceReductions (integer)

## Use Cases
- Property valuation and investment analysis
- Rental market research and rent pricing
- Real estate listing aggregation platforms
- Market trend analysis and forecasting
- Property management portfolio optimization
- Buyer/seller market condition assessment

## Response Example
```json
{
  "id": "prop_12345",
  "address": {
    "street": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "zipCode": "78701",
    "county": "Travis",
    "latitude": 30.2672,
    "longitude": -97.7431
  },
  "owner": {
    "name": "John Smith",
    "mailingAddress": {
      "street": "456 Oak Ave",
      "city": "Houston",
      "state": "TX",
      "zipCode": "77001"
    }
  },
  "taxes": {
    "assessedValue": 450000,
    "taxAmount": 9500,
    "taxYear": 2023,
    "landValue": 180000,
    "improvementValue": 270000
  },
  "propertyType": "Single Family",
  "bedrooms": 3,
  "bathrooms": 2.5,
  "squareFootage": 2100,
  "lotSize": 6500,
  "yearBuilt": 2015,
  "stories": 2,
  "garageSpaces": 2,
  "pool": false,
  "lastSaleDate": "2020-06-15",
  "lastSalePrice": 380000,
  "estimatedValue": 485000,
  "features": {
    "heating": "Central",
    "cooling": "Central",
    "fireplace": true,
    "basement": false,
    "construction": "Frame",
    "roofType": "Composition Shingle"
  }
}
```

## Pricing
- Free tier: 50 requests per month
- Starter plan: 500 requests/month - $29/month
- Growth plan: 2,500 requests/month - $99/month
- Professional plan: 10,000 requests/month - $299/month
- Enterprise plan: Custom pricing for high volume
- Rate limits: Vary by plan tier
