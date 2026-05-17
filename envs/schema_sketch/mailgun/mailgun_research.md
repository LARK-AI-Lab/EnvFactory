# Mailgun Research Notes

## Data Source
- Official Docs: https://documentation.mailgun.com/docs/mailgun/
- API Reference: https://documentation.mailgun.com/docs/mailgun/api-reference/
- SDK/Tutorials: https://documentation.mailgun.com/docs/mailgun/quickstart/
- Base URL: 
  - US: https://api.mailgun.net/v3
  - EU: https://api.eu.mailgun.net/v3

## API Overview
- **Purpose**: Developer-focused email delivery service with granular control
- **Category**: communication
- **Target users**: Developer teams, multi-tenant SaaS applications

## Authentication
- **Type**: HTTP Basic Auth
- **How to obtain**: Sign up at mailgun.com, view API key in dashboard
- **Header format**: `Authorization: Basic {base64(api:YOUR_API_KEY)}`
- Username: "api", Password: API key

## Core Endpoints & Design

### 1. Send Email
- **Method & path**: POST /{domain}/messages
- **Purpose**: Send email via form-encoded or multipart
- **Request params**:
  - from (string): Sender address
  - to (string): Recipient address
  - subject (string): Email subject
  - text (string): Plain text body
  - html (string): HTML body
  - template (string): Template name
  - o:tracking-clicks (bool): Click tracking
  - o:tracking-opens (bool): Open tracking
- **Response**: Message ID and status

### 2. Events API
- **Method & path**: GET /{domain}/events
- **Purpose**: Retrieve email event logs
- **Request params**: event, begin, end, limit, page
- **Pagination**: Cursor-based via paging URLs
- **Events**: accepted, delivered, failed, opened, clicked, complained, unsubscribed, stored

### 3. Email Validation
- **Method & path**: GET /v4/address/validate
- **Purpose**: Validate email address
- **Request params**: address
- **Response**: is_valid, mailbox_verification, parts

### 4. Stats API
- **Method & path**: GET /{domain}/stats/total
- **Purpose**: Domain-level statistics
- **Request params**: event, start, end, resolution

## Data Models
- **Event**: event, id, timestamp, recipient, domain, message
- **Stats**: time, accepted, delivered, failed, opened, clicked
- **Validation**: address, is_valid, mailbox_verification, parts

## Use Cases
- High-volume transactional email
- Complex email routing rules
- Multi-tenant email systems
- Email validation at point of capture

## Response Example
```json
{
  "id": "<20240305120000.1.12345@yourdomain.com>",
  "message": "Queued. Thank you."
}
```
