# Shopify Research Notes

## Data Source
- Official Docs: https://shopify.dev/docs/api/admin-graphql/latest
- REST API Docs: https://shopify.dev/docs/api/admin-rest/latest
- Base URL: https://{store}.myshopify.com/admin/api/2024-01

## API Overview
- **Purpose**: E-commerce platform API for managing online stores
- **Category**: E-commerce Platform
- **Target users**: Developers building Shopify apps, merchants automating operations

## Authentication
- **Type**: OAuth 2.0 or API Access Token
- **How to obtain**: Shopify Partner Dashboard → Apps → Create App
- **Header format**: `X-Shopify-Access-Token: {access_token}`
- **Rate limits**: GraphQL uses calculated query cost; REST has bucket-based limits

## Core Endpoints & Design

### 1. Get Products (GraphQL)
- **Method**: `POST /graphql.json`
- **Query**: `{ products(first: 10) { edges { node { id title variants(first: 5) { edges { node { id price inventoryQuantity } } } } } } }`
- **Purpose**: Retrieve product catalog with variants

### 2. Create Product (REST)
- **Method & path**: `POST /products.json`
- **Request body**:
  - `product` (obj):
    - `title` (str): Product name
    - `body_html` (str): Description HTML
    - `vendor` (str): Brand/vendor name
    - `product_type` (str): Category
    - `variants` (list): Product variants with price, sku, inventory_quantity
- **Response**: Created product object

### 3. Get Orders
- **Method & path**: `GET /orders.json`
- **Query params**:
  - `status` (str): "open", "closed", "cancelled", "any"
  - `limit` (int): Results per page (max 250)
  - `created_at_min` (str): Filter by creation date
- **Response**: List of order objects

### 4. Create Order
- **Method & path**: `POST /orders.json`
- **Request body**:
  - `order` (obj):
    - `line_items` (list): Products with variant_id, quantity, price
    - `customer` (obj): Customer info
    - `financial_status` (str): "pending", "authorized", "paid"
    - `fulfillment_status` (str): "fulfilled", "partial", "restocked"

### 5. Get Customers
- **Method & path**: `GET /customers.json`
- **Query params**:
  - `limit` (int): Results per page
  - `email` (str): Filter by email
- **Response**: List of customer objects

## Data Models
- **Product**: id, title, body_html, vendor, product_type, variants[], images[]
- **Variant**: id, product_id, title, price, sku, inventory_quantity, weight
- **Order**: id, name, total_price, financial_status, fulfillment_status, line_items[]
- **Customer**: id, email, first_name, last_name, orders_count, total_spent

## Use Cases
- Inventory management systems
- Order fulfillment automation
- Customer relationship management
- Product catalog syncing
- Multi-channel sales management

## Response Example
```json
{
  "product": {
    "id": 632910392,
    "title": "IPod Nano - 8GB",
    "body_html": "<p>It's the small iPod with one big idea...</p>",
    "vendor": "Apple",
    "product_type": "Cult Products",
    "variants": [
      {
        "id": 808950810,
        "product_id": 632910392,
        "title": "Pink",
        "price": "199.00",
        "sku": "IPOD2008PINK",
        "inventory_quantity": 10
      }
    ]
  }
}
```
