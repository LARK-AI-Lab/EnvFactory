# Docparser Research Notes

## Data Source
- Official Docs: https://docparser.com/
- API Reference: https://docparser.com/api-docs/
- Base URL: https://api.docparser.com/v1/

## API Overview
- **Purpose**: Extract structured data from PDFs and scanned documents using OCR and rule-based parsing
- **Category**: document
- **Target users**: Finance teams, accountants, businesses processing invoices, POs, forms

## Authentication
- **Type**: API Key
- **How to obtain**: Sign up at docparser.com, generate API key in settings
- **Header format**: `Authorization: Basic {base64(api_key:)}` (key as username, empty password)

## Core Endpoints & Design

### 1. Upload Document (POST)
- **Method & path**: `POST /document/upload/{parser_id}`
- **Purpose**: Submit a document for parsing
- **Request params**:
  - `file` (file): Document to upload
  - `remote_id` (string): [Optional] Custom tracking ID
  - `file_name` (string): [Optional] Override filename
- **Response structure**:
  ```json
  {
    "id": "doc_123",
    "file_name": "invoice.pdf",
    "file_size": 102400,
    "page_count": 1,
    "uploaded_at": "2025-01-15T10:30:00Z"
  }
  ```

### 2. Fetch Parsed Data (GET)
- **Method & path**: `GET /document/{document_id}`
- **Purpose**: Retrieve extracted data from a document
- **Response structure**: Parsed fields based on parser configuration

### 3. List Documents (GET)
- **Method & path**: `GET /documents/{parser_id}`
- **Purpose**: Get list of parsed documents
- **Query params**:
  - `limit` (int): Number of results
  - `offset` (int): Pagination offset
  - `date_from`, `date_to`: Date range filters

## Parser Types / Rules

Docparser uses predefined rule templates for different document types:

**Invoice Parser**:
- Invoice number, date, due date
- Vendor/buyer information
- Line items (description, quantity, unit price, total)
- Tax, discounts, total amounts

**Bank Statement Parser**:
- Account information
- Statement period
- Individual transactions (date, description, amount, balance)
- Opening/closing balances

**Purchase Order Parser**:
- PO number and date
- Vendor/buyer details
- Line items
- Totals and delivery info

**Generic Document Parser**:
- Zonal OCR (select areas)
- Table extraction
- Barcode/QR code reading
- Checkbox detection

## Data Models

**Document**:
- `id` (string): Unique document ID
- `file_name` (string): Original filename
- `file_size` (int): Size in bytes
- `page_count` (int): Number of pages
- `uploaded_at` (datetime): Upload timestamp
- `parsed_data` (object): Extracted fields

**ParsedField**:
- `name` (string): Field identifier
- `value` (string): Extracted value
- `confidence` (float): OCR confidence

## Use Cases
- Automated invoice processing for AP/AR
- Expense report automation
- Bank reconciliation
- Purchase order digitization
- Contract data extraction
- HR document processing

## Integration Options
- REST API
- Email forwarding (send docs to unique parser email)
- Cloud storage (Dropbox, Box, Google Drive, OneDrive)
- Zapier, Make.com, Workato, MS Power Automate
- Webhooks for real-time notifications

## Response Example - Parsed Invoice
```json
{
  "id": "doc_abc123",
  "file_name": "invoice_001.pdf",
  "parsed_data": {
    "invoice_number": "INV-2025-001",
    "invoice_date": "2025-01-10",
    "due_date": "2025-02-10",
    "vendor_name": "Acme Corp",
    "total_amount": "$1,250.00",
    "currency": "USD",
    "line_items": [
      {
        "description": "Consulting Services",
        "quantity": "10",
        "unit_price": "$100.00",
        "amount": "$1,000.00"
      },
      {
        "description": "Software License",
        "quantity": "1",
        "unit_price": "$250.00",
        "amount": "$250.00"
      }
    ]
  }
}
```

## Pricing
- Free trial: Available
- Starter: $39/mo - 500 pages/month
- Professional: $74/mo - 2000 pages/month
- Business: $149/mo - 5000 pages/month
- Enterprise: Custom pricing

## DocparserAI
New AI-powered extraction engine that:
- Simplifies rule creation
- Handles variable document layouts
- Improves accuracy on complex documents
- Reduces setup time
