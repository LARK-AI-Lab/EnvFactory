# eBay API Research Notes

## Data Source
- Official Docs: https://developer.ebay.com/api-docs/
- API Reference: https://developer.ebay.com/api-docs/static/gs_ebay-rest-getting-started-landing.html
- SDK/Tutorials: https://developer.ebay.com/tools
- Base URL: https://api.ebay.com/

## API Overview
- **Purpose**: Programmatic access to eBay's global marketplace for buying, selling, searching, and managing e-commerce operations
- **Category**: ecommerce
- **Target users**: eBay sellers, buyers, affiliate marketers, e-commerce developers

## Authentication
- **Type**: OAuth 2.0
- **How to obtain**: Register at eBay Developers Program (https://developer.ebay.com/)
- **Header format**: `Authorization: Bearer {access_token}`
- **Additional headers**: `X-EBAY-C-MARKETPLACE-ID: EBAY_US` (for marketplace specification)

## Core Endpoints & Design

### Buy APIs (for buyers)
- **Method & path**: `GET /buy/browse/v1/item_summary/search`
- **Purpose**: Search for items on eBay
- **Request params**: q (keywords), category_ids, limit, offset, sort
- **Response structure**: itemSummaries array with title, price, condition, seller info

### Sell APIs (for sellers)
- **Method & path**: `POST /sell/inventory/v1/inventory_item`
- **Purpose**: Create inventory items/listings
- **Request params**: SKU, locale, product details, availability, condition
- **Response structure**: 201 Created with item details

### Finding APIs
- **Method & path**: `GET /buy/browse/v1/item/{item_id}`
- **Purpose**: Get detailed item information
- **Request params**: item_id (path parameter)
- **Response structure**: Full item details including description, images, shipping

## Data Models

### Item
- `itemId` (string): Unique eBay item identifier
- `title` (string): Item title
- `price` (object): {value (float), currency (string)}
- `condition` (string): Item condition (NEW, USED, etc.)
- `seller` (object): {username, feedbackScore, feedbackPercentage}
- `image` (object): {imageUrl}
- `itemWebUrl` (string): Direct link to item

### Order
- `orderId` (string): Unique order identifier
- `orderFulfillmentStatus` (string): PENDING, IN_PROGRESS, FULFILLED
- `buyer` (object): Buyer details
- `lineItems` (array): Items in order
- `pricingSummary` (object): Total cost breakdown

## Use Cases
- Price comparison applications
- Inventory management systems
- Affiliate marketing tools
- Multi-channel selling platforms
- Automated listing tools
- Order management systems

## Response Example
```json
{
  "itemSummaries": [
    {
      "itemId": "v1|123456789|0",
      "title": "Apple iPhone 14 Pro 256GB Deep Purple",
      "price": {
        "value": "899.99",
        "currency": "USD"
      },
      "condition": "NEW",
      "seller": {
        "username": "techstore99",
        "feedbackScore": 15420,
        "feedbackPercentage": "99.2"
      },
      "image": {
        "imageUrl": "https://i.ebayimg.com/00/s/..."
      },
      "itemWebUrl": "https://www.ebay.com/itm/..."
    }
  ],
  "total": 156
}
```

## Notes
- Rate limits apply based on API tier
- Sandbox environment available for testing
- Multiple marketplaces supported (US, UK, DE, etc.)
- Some APIs require partner approval
