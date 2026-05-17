# WooCommerce Research Notes

## Data Source
- Official Docs: https://woocommerce.github.io/woocommerce-rest-api-docs/
- API Reference: https://woocommerce.com/document/woocommerce-rest-api/
- Base URL: https://{store}/wp-json/wc/v3

## API Overview
- **Purpose**: REST API for WooCommerce stores running on WordPress
- **Category**: E-commerce Platform
- **Target users**: Developers integrating with WooCommerce stores, automation tools

## Authentication
- **Type**: Basic Auth (Consumer Key + Consumer Secret) or OAuth 1.0a
- **How to obtain**: WooCommerce → Settings → Advanced → REST API → Add Key
- **Header format**: Basic Auth with Consumer Key as username, Consumer Secret as password
- **Or**: Query params `consumer_key` and `consumer_secret`

## Core Endpoints & Design

### 1. List Products
- **Method & path**: `GET /products`
- **Query params**:
  - `per_page` (int): Items per page (max 100)
  - `page` (int): Page number
  - `category` (str): Filter by category slug
  - `search` (str): Search keyword
  - `orderby` (str): Sort field
  - `order` (str): "asc" or "desc"
- **Response**: Array of product objects

### 2. Create Product
- **Method & path**: `POST /products`
- **Request body**:
  - `name` (str): Product name
  - `type` (str): "simple", "grouped", "external", "variable"
  - `regular_price` (str): Regular price
  - `sale_price` (str): Sale price
  - `description` (str): Full description
  - `short_description` (str): Short description
  - `categories` (list): Category objects with id
  - `images` (list): Image objects with src
  - `manage_stock` (bool): Enable stock management
  - `stock_quantity` (int): Stock quantity
- **Response**: Created product object

### 3. List Orders
- **Method & path**: `GET /orders`
- **Query params**:
  - `per_page`, `page`: Pagination
  - `status` (str): "pending", "processing", "on-hold", "completed", "cancelled", "refunded"
  - `customer` (int): Filter by customer ID
  - `after`, `before`: Date range filters
- **Response**: Array of order objects

### 4. Create Order
- **Method & path**: `POST /orders`
- **Request body**:
  - `payment_method` (str): Payment method ID
  - `payment_method_title` (str): Payment method name
  - `set_paid` (bool): Mark as paid
  - `billing` (obj): Billing address
  - `shipping` (obj): Shipping address
  - `line_items` (list): Products with product_id, quantity
  - `shipping_lines` (list): Shipping method with method_id, total
- **Response**: Created order object

### 5. Get Customers
- **Method & path**: `GET /customers`
- **Query params**:
  - `per_page`, `page`: Pagination
  - `search` (str): Search by name or email
  - `role` (str): Filter by role (customer, subscriber, etc.)
- **Response**: Array of customer objects

## Data Models
- **Product**: id, name, slug, type, status, price, regular_price, sale_price, stock_quantity, categories[], images[]
- **Order**: id, number, status, currency, total, customer_id, billing, shipping, line_items[], date_created
- **Customer**: id, email, first_name, last_name, billing, shipping, orders_count, total_spent
- **Coupon**: id, code, discount_type, amount, expiry_date, usage_count

## Use Cases
- Store management automation
- Inventory syncing across channels
- Order fulfillment integration
- Customer data management
- Multi-store aggregation

## Response Example
```json
{
  "id": 799,
  "name": "Premium Quality",
  "slug": "premium-quality-19",
  "type": "simple",
  "status": "publish",
  "featured": false,
  "catalog_visibility": "visible",
  "description": "<p>This is a premium quality product.</p>",
  "short_description": "Premium product.",
  "sku": "",
  "price": "21.99",
  "regular_price": "21.99",
  "sale_price": "",
  "manage_stock": true,
  "stock_quantity": 5,
  "categories": [
    {
      "id": 9,
      "name": "Clothing",
      "slug": "clothing"
    }
  ],
  "images": [
    {
      "id": 792,
      "src": "https://example.com/wp-content/uploads/2017/01/premium-quality-front.jpg",
      "name": "Premium Quality - Front",
      "alt": ""
    }
  ]
}
```
