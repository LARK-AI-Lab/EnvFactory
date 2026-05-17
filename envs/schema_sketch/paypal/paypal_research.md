# PayPal Research Notes

## Data Source
- Official Docs: https://developer.paypal.com/api/rest/
- Orders API: https://developer.paypal.com/docs/api/orders/v2/
- Base URL: 
  - Sandbox: https://api-m.sandbox.paypal.com
  - Live: https://api-m.paypal.com

## API Overview
- **Purpose**: Online payment processing with global reach
- **Category**: Payment Processing / E-commerce
- **Target users**: Developers integrating payment solutions, e-commerce sites

## Authentication
- **Type**: OAuth 2.0 Client Credentials
- **How to obtain**: PayPal Developer Dashboard → Apps & Credentials → Create App
- **Flow**: 
  1. Get access token using Client ID + Secret
  2. Use access token in Authorization header for API calls
- **Token endpoint**: `POST /v1/oauth2/token`

## Core Endpoints & Design

### 1. Create Order
- **Method & path**: `POST /v2/checkout/orders`
- **Purpose**: Create a new payment order
- **Request body**:
  - `intent` (str): "CAPTURE" (immediate) or "AUTHORIZE" (delayed)
  - `purchase_units` (list):
    - `reference_id` (str): Unique ID for this purchase unit
    - `description` (str): Order description
    - `amount` (obj):
      - `currency_code` (str): "USD", "EUR", etc.
      - `value` (str): Amount as string (e.g., "100.00")
      - `breakdown` (obj): Itemized breakdown (optional)
    - `shipping` (obj): Shipping address and method
    - `items` (list): Line items with name, quantity, unit_amount
- **Response**: Order object with id, status, links

### 2. Capture Order
- **Method & path**: `POST /v2/checkout/orders/{id}/capture`
- **Purpose**: Capture payment for an order (when intent=CAPTURE)
- **Response**: Captured order details

### 3. Authorize Order
- **Method & path**: `POST /v2/checkout/orders/{id}/authorize`
- **Purpose**: Authorize payment without capturing (when intent=AUTHORIZE)
- **Response**: Authorization details

### 4. Capture Authorized Payment
- **Method & path**: `POST /v2/payments/authorizations/{id}/capture`
- **Purpose**: Capture an authorized payment later
- **Request body**:
  - `amount` (obj): Currency and value to capture
  - `final_capture` (bool): Whether this is the final capture
- **Response**: Capture details

### 5. Show Order Details
- **Method & path**: `GET /v2/checkout/orders/{id}`
- **Purpose**: Retrieve order details
- **Response**: Full order object

## Data Models
- **Order**: id, status, intent, purchase_units[], create_time, update_time
- **PurchaseUnit**: reference_id, amount, payee, description, items[], shipping
- **Amount**: currency_code, value, breakdown
- **Capture**: id, status, amount, seller_receivable_breakdown, create_time

## Payment Methods Supported
- PayPal wallet
- Credit/Debit cards
- Pay Later (US)
- Venmo (US mobile)
- Alternative payment methods (iDEAL, Bancontact, etc.)

## Use Cases
- E-commerce checkout
- Subscription billing
- Pre-orders (authorize now, capture later)
- Marketplaces
- Donations
- Invoice payments

## Response Example
```json
{
  "id": "5O190127TN364715T",
  "status": "COMPLETED",
  "intent": "CAPTURE",
  "purchase_units": [
    {
      "reference_id": "default",
      "amount": {
        "currency_code": "USD",
        "value": "100.00"
      },
      "payments": {
        "captures": [
          {
            "id": "2D6172245X905035T",
            "status": "COMPLETED",
            "amount": {
              "currency_code": "USD",
              "value": "100.00"
            },
            "final_capture": true
          }
        ]
      }
    }
  ],
  "payer": {
    "name": {
      "given_name": "John",
      "surname": "Doe"
    },
    "email_address": "customer@example.com"
  }
}
```
