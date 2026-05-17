# AdobePDFServices Research Notes

## Data Source
- Official Docs: https://developer.adobe.com/document-services/apis/pdf-services/
- API Reference: https://developer.adobe.com/document-services/docs/apis/pdf-services/
- SDK/Tutorials: https://developer.adobe.com/document-services/docs/overview/
- Base URL: https://pdf-services.adobe.io/

## API Overview
- **Purpose**: Comprehensive PDF processing API for creating, converting, editing, and protecting PDF documents
- **Category**: document
- **Target users**: Developers, enterprises, SaaS applications needing PDF automation

## Authentication
- **Type**: OAuth 2.0 (Client Credentials)
- **How to obtain**: Sign up at Adobe Developer Console, create a new project, add PDF Services API
- **Header format**: `Authorization: Bearer {access_token}` + `x-api-key: {client_id}`

## Core Endpoints & Design

### 1. Create PDF from HTML
- **Method & path**: `POST /operation/createpdf`
- **Purpose**: Convert HTML content to PDF
- **Request params**:
  - `assetID` (string): Input HTML asset ID
  - `pageLayout` (object): pageWidth, pageHeight, margin
  - `jsonDataForMerge` (object): [Optional] Data for template merging
- **Response structure**: Operation location URL for polling
- **Async**: Yes, returns job ID to poll for result

### 2. Export PDF
- **Method & path**: `POST /operation/exportpdf`
- **Purpose**: Convert PDF to Word, Excel, PowerPoint, or images
- **Request params**:
  - `assetID` (string): Input PDF asset ID
  - `targetFormat` (string): DOCX, XLSX, PPTX, JPEG, PNG
- **Response structure**: Download URL for exported file

### 3. OCR PDF
- **Method & path**: `POST /operation/ocr`
- **Purpose**: Make scanned PDFs searchable or extract text
- **Request params**:
  - `assetID` (string): Input PDF asset ID
  - `ocrLang` (string): Language code (e.g., "en-US")
  - `type` (string): "searchable_image" or "editable_pdf"
- **Response structure**: Processed PDF URL + confidence scores

### 4. Combine PDFs
- **Method & path**: `POST /operation/combinepdf`
- **Purpose**: Merge multiple PDFs into one
- **Request params**:
  - `assetIDs` (array): List of PDF asset IDs in order
  - `pageRanges` (array): [Optional] Specific pages from each PDF

### 5. Protect PDF
- **Method & path**: `POST /operation/protectpdf`
- **Purpose**: Add password and permission restrictions
- **Request params**:
  - `assetID` (string): Input PDF asset ID
  - `passwordProtection` (object): userPassword, ownerPassword
  - `encryptionAlgorithm` (string): "AES_128" or "AES_256"
  - `permissions` (object): printing, copying, editing, commenting

## Data Models

**Asset**: Represents a file in Adobe's storage
- `assetID` (string): Unique identifier
- `downloadUri` (string): Temporary download URL
- `mediaType` (string): MIME type

**OperationResult**:
- `status` (string): "in_progress", "done", "failed"
- `error` (object): Error code and message if failed
- `asset` (Asset): Output file info

## Use Cases
- Invoice/report generation from HTML templates
- Converting legacy documents to editable formats
- Making scanned documents searchable for archiving
- Combining multiple documents for batch processing
- Securing confidential PDFs with encryption

## Response Example
```json
{
  "status": "done",
  "asset": {
    "assetID": "urn:aaid:sc:VA6C2:...",
    "downloadUri": "https://dcplatformstorageservice-prod-us-east-1.s3.amazonaws.com/...",
    "mediaType": "application/pdf"
  }
}
```

## Pricing
- Free tier: 500 Document Transactions/month
- Paid plans: Volume-based pricing starting at $0.05/transaction
