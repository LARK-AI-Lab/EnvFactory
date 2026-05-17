# Postmark Research Notes

## Data Source
- Official Docs: https://postmarkapp.com/developer
- API Reference: https://postmarkapp.com/developer/api/overview
- SDK/Tutorials: https://postmarkapp.com/developer/integration
- Base URL: https://api.postmarkapp.com

## API Overview
- **Purpose**: Fast, reliable transactional email service
- **Category**: communication
- **Target users**: SaaS companies, e-commerce platforms needing critical email delivery

## Authentication
- **Type**: Server Token (custom header)
- **How to obtain**: Create server in Postmark dashboard, copy Server API Token
- **Header format**: `X-Postmark-Server-Token: {server_token}`
- Note: Account API token for management operations, Server token for sending

## Core Endpoints & Design

### 1. Send Email
- **Method & path**: POST /email
- **Purpose**: Send single transactional email
- **Request params**:
  - From (string): Sender address
  - To (string): Recipient address
  - Subject (string): Email subject
  - TextBody (string): Plain text content
  - HtmlBody (string): HTML content
  - Tag (string): Message tag for tracking
  - TrackOpens (bool): Enable open tracking
  - TrackLinks (string): Link tracking mode
- **Response**: To, SubmittedAt, MessageID, ErrorCode, Message

### 2. Send Email Batch
- **Method & path**: POST /email/batch
- **Purpose**: Send up to 500 emails in one request
- **Request body**: Array of email objects
- **Response**: Array of results

### 3. Bounces API
- **Method & path**: GET /bounces
- **Purpose**: Retrieve bounced emails
- **Request params**: count, offset, inactive, emailFilter
- **Response**: Total count and bounce details

### 4. Stats API
- **Method & path**: GET /stats/outbound
- **Purpose**: Outbound email statistics
- **Request params**: tag, fromdate, todate
- **Response**: Sent, bounces, opens, clicks metrics

### 5. Message Opens
- **Method & path**: GET /messages/outbound/opens/{message_id}
- **Purpose**: Get open tracking data for specific email
- **Response**: Open events with client, OS, geo data

## Data Models
- **Email**: From, To, Cc, Bcc, Subject, Tag, HtmlBody, TextBody
- **Bounce**: ID, Type, Name, Description, Email, BouncedAt
- **Open**: Client, OS, Platform, Geo, ReadSeconds, ReceivedAt

## Use Cases
- Password reset emails
- Two-factor authentication codes
- Order confirmations
- Time-critical notifications

## Response Example
```json
{
  "To": "user@example.com",
  "SubmittedAt": "2024-03-05T12:00:00.0000000Z",
  "MessageID": "b7bc2f4a-e38e-4336-af7d-e6c392c2f817",
  "ErrorCode": 0,
  "Message": "OK"
}
```

## Special Features
- Message Streams: Separate transactional and broadcast email infrastructure
- Ultra-fast delivery (<2 seconds for critical emails)
- Separate reputation protection for different email types
