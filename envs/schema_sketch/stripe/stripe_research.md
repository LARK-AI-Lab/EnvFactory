# Stripe Research Notes

## Data Source
- Official Docs: https://docs.stripe.com/api
- API Reference: https://docs.stripe.com/api-reference
- Base URL: https://api.stripe.com/v1

## API Overview
- **Purpose**: Online payment processing platform for businesses of all sizes
- **Category**: Payment Processing / E-commerce
- **Target users**: Developers building payment systems, e-commerce platforms, SaaS applications

## Authentication
- **Type**: API Key (Bearer Token)
- **How to obtain**: Create account at Stripe Dashboard → Developers → API Keys
- **Header format**: `Authorization: Bearer sk_test_...` (test) or `Bearer sk_live_...` (live)

## Core Endpoints & Design

### 1. Create PaymentIntent
- **Method & path**: `POST /payment_intents`
- **Purpose**: Create a new payment intent to collect payment
- **Request body**:
  - `amount` (int): Amount in smallest currency unit (cents)
  - `currency` (str): 3-letter ISO currency code (e.g., "usd")
  - `customer` (str): [Optional] Customer ID
  - `payment_method` (str): [Optional] Payment method ID
  - `confirm` (bool): [Optional] Confirm immediately
  - `metadata` (obj): [Optional] Key-value pairs for custom data
- **Response**: PaymentIntent object with id, client_secret, status, etc.

### 2. Retrieve PaymentIntent
- **Method & path**: `GET /payment_intents/{id}`
- **Purpose**: Get details of an existing payment intent

### 3. Create Customer
- **Method & path**: `POST /customers`
- **Purpose**: Create a new customer for recurring payments
- **Request body**:
  - `email` (str): Customer email
  - `name` (str): Customer name
  - `phone` (str): [Optional] Phone number
  - `metadata` (obj): [Optional] Custom data

### 4. Create Refund
- **Method & path**: `POST /refunds`
- **Purpose**: Refund a payment
- **Request body**:
  - `payment_intent` (str): PaymentIntent ID to refund
  - `amount` (int): [Optional] Partial refund amount
  - `reason` (str): [Optional] "duplicate", "fraudulent", "requested_by_customer"

### 5. List Charges
- **Method & path**: `GET /charges`
- **Purpose**: List all charges/payments
- **Query params**:
  - `limit` (int): Number of results (1-100)
  - `starting_after` (str): Pagination cursor
  - `customer` (str): Filter by customer ID

## Data Models
- **PaymentIntent**: id, amount, currency, status, client_secret, customer, payment_method
- **Customer**: id, email, name, phone, created, metadata
- **Charge**: id, amount, currency, status, receipt_url, payment_method_details
- **Refund**: id, amount, status, reason, receipt_number

## Use Cases
- E-commerce checkout flows
- Subscription billing
- In-app purchases
- Marketplace payments
- Invoice payments
- Donation collection

## Response Example
```json
{
  "id": "pi_3MtwBwLkdIwHu7ix28a3tqPa",
  "object": "payment_intent",
  "amount": 2000,
  "currency": "usd",
  "status": "requires_payment_method",
  "client_secret": "pi_3MtwBwLkdIwHu7ix28a3tqPa_secret_YrKJUKribcBjcG8HVhfZluoGH"
}
```
