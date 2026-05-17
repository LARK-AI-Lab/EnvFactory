# Resend Research Notes

## Data Source
- Official Docs: https://resend.com/docs
- API Reference: https://resend.com/docs/api-reference/introduction
- SDK/Tutorials: https://resend.com/docs/send-with-python
- Base URL: https://api.resend.com

## API Overview
- **Purpose**: Modern email API with excellent developer experience
- **Category**: communication
- **Target users**: JavaScript/React developers, modern web applications

## Authentication
- **Type**: Bearer Token
- **How to obtain**: Create API key in Resend dashboard
- **Header format**: `Authorization: Bearer {api_key}`

## Core Endpoints & Design

### 1. Send Email
- **Method & path**: POST /emails
- **Purpose**: Send single email
- **Request params**:
  - from (string): Sender address
  - to (string/array): Recipient(s)
  - subject (string): Email subject
  - html (string): HTML content
  - text (string): Plain text content
  - reply_to (string/array): Reply-to addresses
  - cc (array): CC recipients
  - bcc (array): BCC recipients
- **Response**: Email ID

### 2. Send Batch
- **Method & path**: POST /emails/batch
- **Purpose**: Send multiple emails
- **Request body**: Array of email objects
- **Response**: Array of sent email data

### 3. Get Email
- **Method & path**: GET /emails/{email_id}
- **Purpose**: Retrieve email details
- **Response**: Full email object with status

### 4. List Emails
- **Method & path**: GET /emails
- **Purpose**: List sent emails
- **Request params**: domain_id, limit
- **Response**: List of email objects

### 5. Update Email
- **Method & path**: PATCH /emails/{email_id}
- **Purpose**: Update scheduled email
- **Request params**: scheduled_at
- **Response**: Updated email data

## Data Models
- **Email**: id, object, to, from, created_at, subject, html, text, bcc, cc, reply_to, last_event
- **BatchResult**: id, to, from, created_at

## Use Cases
- React/Next.js applications
- Modern web apps prioritizing DX
- Scheduled email campaigns
- Email with modern templating

## Response Example
```json
{
  "id": "49a3999c-6560-4616-9774-8453234f4a73"
}
```

## Special Features
- React Email integration for modern templating
- Simple, clean API design
- Good TypeScript support
