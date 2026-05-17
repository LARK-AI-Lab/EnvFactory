# Shippo API Research Notes

## Data Source
- Official Docs: https://docs.goshippo.com/
- API Reference: https://docs.goshippo.com/docs/reference
- Quick Start: https://docs.goshippo.com/docs/guides_general/generate_shipping_label
- Base URL: https://api.goshippo.com/

## API Overview
- **Purpose**: Multi-carrier shipping API for getting rates, creating labels, tracking packages, and validating addresses
- **Category**: logistics
- **Target users**: E-commerce platforms, shipping management systems, warehouse management tools

## Authentication
- **Type**: API Token
- **How to obtain**: Sign up at https://goshippo.com/ (free tier available)
- **Header format**: `Authorization: ShippoToken {api_token}`
- **Test mode**: Use test token for development (no real charges)

## Core Endpoints & Design

### Address Validation
- **Method & path**: `POST /addresses`
- **Purpose**: Validate shipping addresses
- **Request body**: {street1, city, state, zip, country, name, phone, validate: true}
- **Response structure**: Address object with validation_status

### Shipping Rates
- **Method & path**: `POST /shipments`
- **Purpose**: Get real-time rates from multiple carriers
- **Request body**: {address_from, address_to, parcels, async: false}
- **Response structure**: Shipment object with rates array

### Create Label (Transaction)
- **Method & path**: `POST /transactions`
- **Purpose**: Purchase shipping label
- **Request body**: {rate, label_file_type, async}
- **Response structure**: Transaction with label_url and tracking_number

### Instalabel (One-Call Label)
- **Method & path**: `POST /transactions`
- **Purpose**: Create label in one API call (shipment + label)
- **Request body**: {shipment: {address_from, address_to, parcels}, carrier_account, servicelevel_token}
- **Response structure**: Transaction with embedded rate and label

### Tracking
- **Method & path**: `GET /tracks/{carrier}/{tracking_number}`
- **Purpose**: Track shipment status
- **Request params**: carrier, tracking_number (path)
- **Response structure**: Tracking object with history

### Carriers
- **Method & path**: `GET /carrier_accounts`
- **Purpose**: List connected carriers
- **Response structure**: Carrier accounts array

## Data Models

### Address
- `object_id` (string): Address identifier
- `name` (string): Recipient name
- `street1` (string): Address line 1
- `street2` (string): Address line 2
- `city` (string): City
- `state` (string): State/province
- `zip` (string): ZIP/postal code
- `country` (string): Country code
- `phone` (string): Phone number
- `email` (string): Email address
- `is_residential` (boolean): Residential flag
- `validation_status` (string): valid, invalid, or warn

### Parcel
- `length` (float): Length
- `width` (float): Width
- `height` (float): Height
- `weight` (string or float): Weight (e.g., "5lb" or 5)
- `distance_unit` (string): in, cm
- `mass_unit` (string): lb, kg, oz, g

### Rate
- `object_id` (string): Rate identifier
- `amount` (string): Price
- `currency` (string): Currency code
- `provider` (string): Carrier name (USPS, FedEx, UPS, etc.)
- `servicelevel` (object): {name, token, terms}
- `days` (integer): Estimated transit days
- `duration_terms` (string): Service description

### Transaction (Label)
- `object_id` (string): Transaction ID
- `status` (string): SUCCESS, ERROR, or WAITING
- `tracking_number` (string): Carrier tracking number
- `tracking_status` (string): UNKNOWN, DELIVERED, etc.
- `tracking_url_provider` (string): Carrier tracking URL
- `label_url` (string): Label PDF/PNG URL
- `eta` (string): Estimated delivery date
- `rate` (object): Rate details

## Use Cases
- E-commerce checkout shipping calculation
- Multi-carrier shipping label generation
- Address validation at checkout
- Automated tracking updates
- Bulk label printing
- International shipping with customs forms

## Response Example
```json
{
  "object_state": "VALID",
  "status": "SUCCESS",
  "object_created": "2022-12-15T11:57:45.631Z",
  "object_id": "2db03e1bc677420a8c56dc77a60e9386",
  "rate": {
    "object_id": "cf6fea899f1848b494d9568e8266e076",
    "amount": "5.50",
    "currency": "USD",
    "provider": "USPS",
    "servicelevel_name": "Priority Mail",
    "servicelevel_token": "usps_priority"
  },
  "tracking_number": "92701901755477000000000011",
  "tracking_status": "UNKNOWN",
  "tracking_url_provider": "https://tools.usps.com/go/TrackConfirmAction_input?origTrackNum=92701901755477000000000011",
  "label_url": "https://deliver.goshippo.com/2db03e1bc677420a8c56dc77a60e9386.pdf",
  "eta": "2022-12-18T12:00:00.000Z",
  "metadata": "Order ID 12345"
}
```

## Supported Carriers
- USPS (US Postal Service)
- UPS (United Parcel Service)
- FedEx
- DHL Express
- Canada Post
- Australia Post
- +80 more international carriers

## Notes
- Free tier: 200 labels/year
- Discounted rates available (up to 90% off)
- Supports international shipping with customs forms
- Address validation available for US addresses
- Webhook support for tracking updates
- Batch processing available for multiple labels
