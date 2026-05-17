# PDFRest Research Notes

## Data Source
- Official Docs: https://pdfrest.com/
- API Reference: https://pdfrest.com/documentation/
- SDK/Tutorials: https://github.com/pdfrest
- Base URL: https://api.pdfrest.com/

## API Overview
- **Purpose**: Comprehensive PDF REST API built on Adobe PDF Library technology
- **Category**: document
- **Target users**: Developers needing PDF processing without infrastructure setup

## Authentication
- **Type**: API Key
- **How to obtain**: Sign up at pdfrest.com, API key provided in dashboard
- **Header format**: `Api-Key: {api_key}`

## Core Endpoints & Design

### 1. Compress PDF
- **Method & path**: `POST /compress-pdf`
- **Purpose**: Reduce PDF file size with configurable compression level
- **Request params**:
  - `file` (file): PDF file to compress
  - `compression_level` (string): "low", "medium", "high", "lossless"
- **Response structure**: Output file ID and download URL

### 2. Convert to PDF
- **Method & path**: `POST /{filetype}-to-pdf` (e.g., `/word-to-pdf`)
- **Purpose**: Convert Word, Excel, PowerPoint, images to PDF
- **Request params**:
  - `file` (file): Input file
  - `output` (string): Output filename
- **Response structure**: PDF download URL

### 3. Split PDF
- **Method & path**: `POST /split-pdf`
- **Purpose**: Extract specific pages or split into multiple files
- **Request params**:
  - `file` (file): Input PDF
  - `page_ranges` (string): Comma-separated ranges (e.g., "1-3,4-6")
- **Response structure**: Array of output file URLs

### 4. Watermark PDF
- **Method & path**: `POST /watermarked-pdf`
- **Purpose**: Add text or image watermarks
- **Request params**:
  - `file` (file): Input PDF
  - `watermark_text` (string) OR `watermark_file` (file)
  - `pages` (string): Page range
  - `opacity` (float): 0.0 to 1.0
- **Response structure**: Watermarked PDF URL

### 5. PDF to Images
- **Method & path**: `POST /pdf-to-images`
- **Purpose**: Convert PDF pages to PNG/JPEG/TIFF
- **Request params**:
  - `file` (file): Input PDF
  - `format` (string): "png", "jpeg", "tiff"
  - `dpi` (integer): Resolution
  - `pages` (string): Page range
- **Response structure**: Array of image URLs

## Data Models

**OutputFile**:
- `outputId` (string): Unique output identifier
- `downloadUrl` (string): Temporary download URL
- `fileSize` (integer): Size in bytes

**ProcessingResult**:
- `processId` (string): Job identifier
- `outputFiles` (array): List of OutputFile objects
- `status` (string): "pending", "processing", "complete", "error"

## Use Cases
- Reducing PDF file sizes for email/web upload
- Converting office documents to PDF format
- Extracting specific pages from large documents
- Adding watermarks for document branding/security
- Creating image previews of PDF pages

## Response Example
```json
{
  "processId": "proc_abc123",
  "outputFiles": [
    {
      "outputId": "out_xyz789",
      "downloadUrl": "https://api.pdfrest.com/download/out_xyz789",
      "fileSize": 1024567
    }
  ],
  "status": "complete"
}
```

## Chainable Operations
PDFRest supports chaining operations - output of one can be input to another:
1. Compress PDF
2. Then watermark the compressed PDF
3. Then convert to images

## Pricing
- Free tier: Available for testing
- Paid plans: Credit-based, starting around $0.02 per operation
