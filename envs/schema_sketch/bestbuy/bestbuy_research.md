# Best Buy API Research Notes

## Data Source
- Official Docs: https://bestbuyapis.github.io/api-documentation/
- Getting Started: https://bestbuyapis.github.io/api-documentation/#getting-started
- Products API: https://bestbuyapis.github.io/api-documentation/#products-api
- Base URL: https://api.bestbuy.com/v1/

## API Overview
- **Purpose**: Access to Best Buy's product catalog, store information, categories, and recommendations
- **Category**: ecommerce
- **Target users**: Developers building price comparison tools, product research apps, store locators

## Authentication
- **Type**: API Key
- **How to obtain**: Register at https://developer.bestbuy.com/ (free)
- **Parameter format**: `apiKey={your_api_key}` (query parameter)
- **Rate limits**: 5 calls/second, 50,000 calls/day (standard tier)

## Core Endpoints & Design

### Products API
- **Method & path**: `GET /v1/products(search={keywords})`
- **Purpose**: Search products in catalog
- **Request params**: search, categoryPath.id, salePrice>, salePrice<, inStoreAvailability, onlineAvailability
- **Response structure**: metadata + products array
- **Pagination**: page, pageSize (max 100), cursorMark for large result sets

### Product Details
- **Method & path**: `GET /v1/products/{sku}.json`
- **Purpose**: Get specific product details
- **Request params**: sku (path), show (field selection)
- **Response structure**: Single product object with all attributes

### Reviews API
- **Method & path**: `GET /v1/reviews(sku={sku})`
- **Purpose**: Get product reviews
- **Request params**: sku, limit, show
- **Response structure**: Reviews array with ratings and text

### Stores API
- **Method & path**: `GET /v1/stores(city={city})` or `GET /v1/stores(area({lat},{lng},{radius}))`
- **Purpose**: Find store locations
- **Request params**: city, region (state), postalCode, lat/lng for location search
- **Response structure**: Stores array with address and hours

### Categories API
- **Method & path**: `GET /v1/categories`
- **Purpose**: Get category hierarchy
- **Request params**: id, name
- **Response structure**: Categories tree structure

## Data Models

### Product
- `sku` (integer): 7-digit Best Buy SKU
- `name` (string): Product name
- `description` (string): Short description
- `longDescription` (string): Full description
- `salePrice` (float): Current price
- `regularPrice` (float): Original price
- `onSale` (boolean): Sale status
- `customerReviewAverage` (float): Average rating
- `customerReviewCount` (integer): Number of reviews
- `images` (object): {thumbnailImage, mediumImage, largeImage}
- `manufacturer` (string): Brand name
- `modelNumber` (string): Model number

### Store
- `storeId` (integer): Store identifier
- `storeType` (string): Store type (Big Box, Mobile, etc.)
- `name` (string): Store name
- `address` (string): Street address
- `city` (string): City
- `region` (string): State
- `postalCode` (string): ZIP code
- `phone` (string): Phone number
- `hours` (string): Store hours
- `services` (array): Available services

### Review
- `id` (integer): Review ID
- `rating` (integer): 1-5 star rating
- `reviewer` (object): {displayName}
- `submissionTime` (string): Date posted
- `title` (string): Review title
- `reviewText` (string): Review content
- `helpfulness` (integer): Helpful votes

## Use Cases
- Price comparison websites
- Product research applications
- Deal alert systems
- Store locator apps
- Product recommendation engines

## Response Example
```json
{
  "from": 1,
  "to": 10,
  "total": 156,
  "currentPage": 1,
  "totalPages": 16,
  "queryTime": "0.052",
  "totalTime": "0.125",
  "partial": false,
  "canonicalUrl": "/v1/products(search=iphone&categoryPath.id=abcat)...",
  "products": [
    {
      "sku": 6418599,
      "name": "Apple - iPhone 14 Pro 256GB - Deep Purple",
      "description": "iPhone 14 Pro. Capture incredible detail...",
      "salePrice": 1099.99,
      "regularPrice": 1099.99,
      "onSale": false,
      "customerReviewAverage": 4.8,
      "customerReviewCount": 2847,
      "thumbnailImage": "https://pisces.bbystatic.com/...",
      "url": "https://api.bestbuy.com/click/...",
      "manufacturer": "Apple",
      "modelNumber": "MQ1F3LL/A",
      "inStoreAvailability": true,
      "onlineAvailability": true
    }
  ]
}
```

## Notes
- Query parameters for search use special syntax: `attribute=value`
- Complex queries use parentheses: `(manufacturer=Apple&salePrice<1000)`
- OR queries use pipe: `wifiReady=true|wifiBuiltIn=true`
- Date searches support relative dates like `today`
- Links expire after 7 days (no caching allowed per ToS)
