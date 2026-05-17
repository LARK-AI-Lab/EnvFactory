# Etsy API Research Notes

## Data Source
- Official Docs: https://developer.etsy.com/documentation/
- API Reference: https://developer.etsy.com/documentation/essentials/
- OAuth Docs: https://developer.etsy.com/documentation/essentials/authentication/
- Base URL: https://openapi.etsy.com/v3/

## API Overview
- **Purpose**: Access to Etsy's handmade, vintage, and craft supplies marketplace for listing management, order processing, and shop operations
- **Category**: ecommerce
- **Target users**: Etsy sellers, shop managers, inventory management tools

## Authentication
- **Type**: OAuth 2.0
- **How to obtain**: Create app at Etsy Developers portal
- **Authorization URL**: https://www.etsy.com/oauth/connect
- **Token URL**: https://api.etsy.com/v3/public/oauth/token
- **Header format**: `x-api-key: {api_key}` + `Authorization: Bearer {access_token}`

## Core Endpoints & Design

### Listings
- **Method & path**: `GET /v3/application/listings`
- **Purpose**: Search Etsy listings
- **Request params**: keywords, category, min_price, max_price, sort_on, limit, offset
- **Response structure**: count, results array with listing details

### Shop Listings
- **Method & path**: `GET /v3/application/shops/{shop_id}/listings`
- **Purpose**: Get listings for a specific shop
- **Request params**: shop_id (path), state (active/inactive), limit, offset
- **Response structure**: Shop listings array

### Create Listing
- **Method & path**: `POST /v3/application/shops/{shop_id}/listings`
- **Purpose**: Create a new listing (requires OAuth)
- **Request params**: title, description, price, quantity, taxonomy_id, who_made, when_made
- **Response structure**: Created listing object

### Receipts (Orders)
- **Method & path**: `GET /v3/application/shops/{shop_id}/receipts`
- **Purpose**: Get shop orders/receipts
- **Request params**: shop_id (path), min_created, max_created, was_paid, was_shipped
- **Response structure**: Receipts array with transaction details

## Data Models

### Listing
- `listing_id` (integer): Unique listing identifier
- `user_id` (integer): Seller user ID
- `shop_id` (integer): Shop ID
- `title` (string): Listing title
- `description` (string): Item description
- `price` (object): {amount (int), currency (str), divisor (int)}
- `quantity` (integer): Available quantity
- `state` (string): active, inactive, expired, sold_out
- `tags` (array): Listing tags
- `materials` (array): Materials used

### Shop
- `shop_id` (integer): Unique shop identifier
- `shop_name` (string): Shop name
- `user_id` (integer): Shop owner user ID
- `create_date` (integer): Shop creation timestamp
- `title` (string): Shop title
- `announcement` (string): Shop announcement

### Receipt
- `receipt_id` (integer): Unique receipt identifier
- `shop_id` (integer): Shop ID
- `buyer_email` (string): Buyer email address
- `name` (string): Buyer name
- `grandtotal` (object): {amount, currency, divisor}
- `subtotal` (object): {amount, currency, divisor}
- `total_shipping_cost` (object): {amount, currency, divisor}
- `transactions` (array): Line items

## Use Cases
- Multi-channel inventory management
- Automated listing tools
- Order management systems
- Shop analytics dashboards
- Print-on-demand integrations

## Response Example
```json
{
  "count": 42,
  "results": [
    {
      "listing_id": 123456789,
      "user_id": 98765432,
      "shop_id": 11111111,
      "title": "Handmade Ceramic Coffee Mug",
      "description": "Beautiful handmade ceramic mug...",
      "price": {
        "amount": 2500,
        "currency": "USD",
        "divisor": 100
      },
      "quantity": 5,
      "state": "active",
      "tags": ["ceramic", "mug", "handmade", "pottery"],
      "materials": ["clay", "glaze"],
      "images": [
        {
          "listing_image_id": 987654321,
          "url_fullxfull": "https://i.etsystatic.com/..."
        }
      ]
    }
  ]
}
```

## Notes
- Rate limits: 10 requests/second per API key
- Some endpoints require user OAuth (not just application auth)
- Strongly typed API with strict validation
- Taxonomy endpoint available for category mapping
- Images must be uploaded separately after listing creation
