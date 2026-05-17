# SendGrid Research Notes

## Data Source
- Official Docs: https://docs.sendgrid.com/api-reference
- API Reference: https://docs.sendgrid.com/api-reference/mail-send/mail-send
- SDK/Tutorials: https://docs.sendgrid.com/for-developers
- Base URL: https://api.sendgrid.com/v3

## API Overview
- **Purpose**: Enterprise-grade email delivery platform for transactional and marketing emails
- **Category**: communication
- **Target users**: Enterprise teams, SaaS companies, developers needing high-volume email delivery

## Authentication
- **Type**: Bearer Token
- **How to obtain**: Create API key in SendGrid dashboard (Settings > API Keys)
- **Header format**: `Authorization: Bearer {api_key}`

## Core Endpoints & Design

### 1. Send Email
- **Method & path**: POST /mail/send
- **Purpose**: Send single or bulk emails
- **Request params**: 
  - personalizations (array): Recipient data with to, cc, bcc, substitutions
  - from (object): Sender email
  - subject (string): Email subject
  - content (array): Content blocks with type and value
  - template_id (string): Dynamic template ID
- **Response**: 202 Accepted with message_id

### 2. Email Stats
- **Method & path**: GET /stats
- **Purpose**: Retrieve delivery statistics
- **Request params**: start_date, end_date, aggregated_by
- **Response**: Array of daily stats with metrics

### 3. Suppression Groups
- **Method & path**: GET /asm/groups
- **Purpose**: Manage unsubscribe groups
- **Response**: List of suppression groups

### 4. Email Validation
- **Method & path**: POST /validations/email
- **Purpose**: Validate email deliverability
- **Response**: Validation result with score and checks

## Data Models
- **Personalization**: to, cc, bcc, subject, headers, substitutions, dynamic_template_data
- **Content**: type (text/plain, text/html), value
- **Attachment**: content, type, filename, disposition, content_id

## Use Cases
- Transactional emails (password resets, order confirmations)
- Marketing campaigns
- Bulk email delivery
- Email deliverability optimization

## Response Example
```json
{
  "personalizations": [
    {
      "to": [{"email": "user@example.com"}],
      "dynamic_template_data": {"name": "John"}
    }
  ],
  "from": {"email": "noreply@yourapp.com"},
  "template_id": "d-xxxxxxxxxx"
}
```
