# ATTOM Research Notes

## Data Source
- Official Docs: https://api.developer.attomdata.com/docs
- API Reference: https://api.developer.attomdata.com/docs
- Pricing: https://api.developer.attomdata.com/pricing
- Base URL: https://api.gateway.attomdata.com/propertyapi/v1.0.0

## API Overview
- **Purpose**: Provides comprehensive property and neighborhood data including assessments, sales, deeds, mortgages, and foreclosure information
- **Category**: real_estate
- **Target users**: Real estate professionals, financial institutions, insurance companies, marketers, and government agencies

## Authentication
- **Type**: API Key
- **How to obtain**: Register at ATTOM Developer Portal and subscribe to an API plan
- **Header/param format**: `apikey: {your_api_key}` or `Authorization: {your_api_key}`

## Core Endpoints & Design

### 1. Property Basic Profile
- **Method & path**: `GET /property/basicprofile`
- **Purpose**: Retrieves fundamental property information including address, ownership, and basic characteristics
- **Request params**:
  - `address1` (string, required): Street address
  - `address2` (string, required): City, state, ZIP
  - `attomid` (string, optional): ATTOM property ID
- **Response structure**: Property identifier, address, site information, property characteristics, tax assessment
- **Pagination**: N/A - single property lookup

### 2. Property Detail
- **Method & path**: `GET /property/detail`
- **Purpose**: Provides comprehensive property details including sales history, mortgage, and building information
- **Request params**:
  - `address1` (string, required): Street address
  - `address2` (string, required): City, state, ZIP
  - `attomid` (string, optional): ATTOM property ID
- **Response structure**: Full property profile, sale history, mortgage info, building features, tax details, assessment history
- **Pagination**: N/A - single property detail

### 3. Property AVM
- **Method & path**: `GET /property/avm`
- **Purpose**: Returns automated valuation model estimates for a property
- **Request params**:
  - `address1` (string, required): Street address
  - `address2` (string, required): City, state, ZIP
  - `attomid` (string, optional): ATTOM property ID
- **Response structure**: AVM value, value range, confidence score, valuation date, comparable properties
- **Pagination**: N/A - single property AVM

### 4. Assessment Detail
- **Method & path**: `GET /assessment/detail`
- **Purpose**: Retrieves detailed tax assessment information for a property
- **Request params**:
  - `address1` (string, required): Street address
  - `address2` (string, required): City, state, ZIP
  - `attomid` (string, optional): ATTOM property ID
- **Response structure**: Assessment values, tax amounts, assessment year, land and improvement values, exemptions
- **Pagination**: N/A - single assessment record

### 5. Sales History
- **Method & path**: `GET /saleshistory/salehistory`
- **Purpose**: Retrieves historical sales data for a property
- **Request params**:
  - `address1` (string, required): Street address
  - `address2` (string, required): City, state, ZIP
  - `attomid` (string, optional): ATTOM property ID
- **Response structure**: Array of historical sales with prices, dates, and transaction details
- **Pagination**: N/A - historical records for single property

### 6. Property Search
- **Method & path**: `GET /property/address`
- **Purpose**: Searches for properties within a geographic area
- **Request params**:
  - `postalcode` (string, required): ZIP code
  - `page` (integer, optional): Page number
  - `pagesize` (integer, optional): Results per page
  - `propertytype` (string, optional): Filter by property type
- **Response structure**: List of properties with basic details
- **Pagination**: Page-based pagination (default: pagesize=10, max=100)

## Data Models
Key entities and their fields:
- `PropertyProfile`: identifier (object), address (object), location (object), summary (object), building (object), lot (object), assessment (object)
- `PropertyDetail`: property (object), sale (object), mortgage (object), tax (object), assessment (object), building (object), rooms (object), parking (object)
- `AVMResult`: amount (object), valueRange (object), avmCondition (string), avmDate (string), comparables (array)
- `Assessment`: assessmentYear (integer), assessedValue (number), taxAmount (number), landValue (number), improvementValue (number), exemptions (array)
- `SaleHistory`: saleDate (string), saleAmount (number), recordingDate (string), transactionType (string), buyerName (string), sellerName (string)

## Use Cases
- Property valuation and market analysis
- Mortgage underwriting and risk assessment
- Real estate investment research
- Insurance underwriting and claims
- Marketing and lead generation
- Neighborhood and market trend analysis
- Foreclosure and distressed property identification

## Response Example
```json
{
  "status": {
    "version": "1.0.0",
    "code": 0,
    "msg": "Success",
    "total": 1,
    "page": 1,
    "pagesize": 10
  },
  "property": [
    {
      "identifier": {
        "Id": 12345678,
        "fips": "06037",
        "apn": "1234-567-890",
        "attomId": 123456789
      },
      "address": {
        "country": "US",
        "countrySubd": "CA",
        "line1": "123 Main St",
        "line2": "Los Angeles, CA 90001",
        "locality": "Los Angeles",
        "matchCode": "ExaStr"
      },
      "location": {
        "latitude": "34.0522",
        "longitude": "-118.2437",
        "accuracy": "Rooftop"
      },
      "summary": {
        "propclass": "Residential",
        "proptype": "SFR",
        "yearbuilt": 1985,
        "propsize": 2100,
        "proplandarea": 6500,
        "bedrooms": 3,
        "bathstotal": 2,
        "bathsfull": 2,
        "roomsTotal": 7
      },
      "building": {
        "size": {
          "bldgsize": 2100,
          "grosssize": 2100,
          "livingsize": 1950,
          "groundfloorsize": 2100
        },
        "rooms": {
          "beds": 3,
          "bathsFull": 2,
          "roomsTotal": 7
        },
        "parking": {
          "garagetype": "Attached Garage",
          "prkgSize": 400,
          "prkgSpaces": 2
        }
      },
      "assessment": {
        "assessmentYear": 2023,
        "assessedValue": 650000,
        "assessedLandValue": 250000,
        "assessedImprovementValue": 400000,
        "taxAmount": 7800,
        "taxYear": 2023
      },
      "sale": {
        "saleAmount": 720000,
        "saleDate": "2021-06-15",
        "recordingDate": "2021-06-22",
        "transactionType": "Resale"
      }
    }
  ]
}
```

## Pricing
- Free tier: Limited trial access available
- Basic plan: Entry-level access with rate limits
- Professional plan: Higher volume with expanded data sets
- Enterprise plan: Custom pricing for high-volume commercial use
- Rate limits: Vary by subscription tier
- Data packages: Various bundles available (property, neighborhood, foreclosure, etc.)
