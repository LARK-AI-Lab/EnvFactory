# Amazon SES Research Notes

## Data Source
- Official Docs: https://docs.aws.amazon.com/ses/
- API Reference: https://docs.aws.amazon.com/ses/latest/APIReference/
- SDK/Tutorials: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/
- Base URL: https://email.{region}.amazonaws.com (AWS Signature V4)

## API Overview
- **Purpose**: Cost-effective email service integrated with AWS ecosystem
- **Category**: communication
- **Target users**: AWS users, cost-conscious high-volume senders

## Authentication
- **Type**: AWS Signature Version 4
- **How to obtain**: AWS IAM credentials (Access Key ID + Secret Access Key)
- **Header format**: AWS SigV4 signed headers
- **IAM Permissions**: Required: ses:SendEmail, ses:SendRawEmail, etc.

## Core Endpoints & Design

### 1. Send Email
- **Method & path**: POST (AWS API)
- **Purpose**: Send formatted email
- **Request params**:
  - Source (string): Verified sender address
  - Destination (object): ToAddresses, CcAddresses, BccAddresses
  - Message (object): Subject, Body (Text, Html)
  - ReplyToAddresses (array): Reply-to addresses
  - ReturnPath (string): Bounce address
- **Response**: MessageId

### 2. Send Raw Email
- **Method & path**: POST
- **Purpose**: Send raw MIME message
- **Request params**:
  - Source (string): Sender override
  - Destinations (array): Recipients
  - RawMessage (object): Base64-encoded MIME data
- **Response**: MessageId

### 3. Send Templated Email
- **Method & path**: POST
- **Purpose**: Send using SES template
- **Request params**:
  - Source (string): Sender address
  - Destination (object): Recipients
  - Template (string): Template name
  - TemplateData (string): JSON string with variables
- **Response**: MessageId

### 4. Get Send Statistics
- **Method & path**: POST
- **Purpose**: Account sending statistics (last 14 days)
- **Response**: SendDataPoints array with metrics

### 5. Verify Email Identity
- **Method & path**: POST
- **Purpose**: Start email verification
- **Request params**: EmailAddress
- **Response**: Verification status

### 6. Get Identity Verification Attributes
- **Method & path**: POST
- **Purpose**: Check verification status
- **Request params**: Identities (array)
- **Response**: VerificationAttributes map

## Data Models
- **Destination**: ToAddresses, CcAddresses, BccAddresses
- **Message**: Subject (Data, Charset), Body (Text, Html)
- **SendDataPoint**: Timestamp, DeliveryAttempts, Bounces, Complaints, Rejects

## Use Cases
- High-volume cost-effective email
- AWS-integrated applications
- Applications already using CloudWatch/Lambda
- Email with strict compliance requirements

## Response Example
```json
{
  "MessageId": "0100018e12345678-12345678-1234-1234-1234-123456789012-000000"
}
```

## Constraints
- Sandbox mode: Can only send to verified addresses
- Production: Request sending limit increase
- SES Identity verification required
- DKIM and SPF setup recommended

## Pricing
- $0.10 per 1,000 emails (outbound)
- $0.12 per 1,000 emails (inbound)
- Attachments: $0.12 per GB
- First 3,000 emails free for first 12 months
