# Amazon Product Advertising API Research Notes

## Data Source
- Official Docs: https://webservices.amazon.com/paapi5/documentation/
- API Reference: https://webservices.amazon.com/paapi5/documentation/api-reference.html
- Base URL: https://webservices.amazon.com/paapi5

## API Overview
- **Purpose**: Access Amazon product data for affiliate marketing and product comparison
- **Category**: Product Data / Affiliate Marketing
- **Target users**: Affiliate marketers, price comparison sites, product review platforms

## Authentication
- **Type**: AWS Signature V4 + Associate Tag
- **Credentials needed**:
  - `AWS_ACCESS_KEY_ID`: From Amazon Associates
  - `AWS_SECRET_ACCESS_KEY`: From Amazon Associates  
  - `AWS_ASSOCIATE_TAG`: Your affiliate tracking ID
- **Rate limits**: 
  - Initial: 1 TPS, 8640 TPD
  - Scales with shipped revenue ($5 = +1 TPD, $4320 = +1 TPS up to 10)

## Core Endpoints & Design

### 1. Search Items
- **Method & path**: `POST /paapi5/searchitems`
- **Purpose**: Search for products by keywords
- **Request body**:
  - `Keywords` (str): Search terms
  - `SearchIndex` (str): Category (e.g., "All", "Electronics", "Books")
  - `ItemPage` (int): Page number (1-10)
  - `Resources` (list): Data to return (Images, Prices, Reviews, etc.)
  - `PartnerTag` (str): Associate tag
  - `PartnerType` (str): "Associates"
  - `Marketplace` (str): e.g., "www.amazon.com"
- **Response**: List of search results with ASIN, title, price, image, etc.

### 2. Get Items
- **Method & path**: `POST /paapi5/getitems`
- **Purpose**: Get details for specific products by ASIN
- **Request body**:
  - `ItemIds` (list): List of ASINs (max 10)
  - `Resources` (list): Data to return
  - `PartnerTag`, `PartnerType`, `Marketplace`
- **Response**: Detailed product information

### 3. Get Variations
- **Method & path**: `POST /paapi5/getvariations`
- **Purpose**: Get product variations (size, color, etc.)
- **Request body**:
  - `ASIN` (str): Parent product ASIN
  - `Resources` (list): Data to return
  - `PartnerTag`, `PartnerType`, `Marketplace`

### 4. Get Browse Nodes
- **Method & path**: `POST /paapi5/getbrowsenodes`
- **Purpose**: Get category hierarchy information
- **Request body**:
  - `BrowseNodeIds` (list): Category IDs
  - `Resources` (list)
  - `PartnerTag`, `PartnerType`, `Marketplace`

## Data Models
- **Item**: ASIN, title, image, price, rating, reviews, features, offers
- **Price**: amount, currency, display_amount
- **BrowseNode**: id, name, is_root, children[]

## Supported Marketplaces
- US, UK, DE, FR, JP, CA, CN, IT, ES, IN, MX, BR, AU, AE, TR, SG, NL, SA, SE, BE, PL

## Use Cases
- Product comparison websites
- Price tracking apps
- Affiliate marketing
- Product research tools
- Review aggregation platforms

## Response Example
```json
{
  "ItemsResult": {
    "Items": [
      {
        "ASIN": "B08N5WRWNW",
        "DetailPageURL": "https://www.amazon.com/dp/B08N5WRWNW",
        "ItemInfo": {
          "Title": {
            "DisplayValue": "Apple iPhone 12"
          }
        },
        "Offers": {
          "Listings": [
            {
              "Price": {
                "Amount": 699.00,
                "Currency": "USD"
              }
            }
          ]
        },
        "Images": {
          "Primary": {
            "Medium": {
              "URL": "https://m.media-amazon.com/images/..."
            }
          }
        }
      }
    ]
  }
}
```
