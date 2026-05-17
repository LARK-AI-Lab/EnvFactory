# Convertio Research Notes

## Data Source
- Official Docs: https://developers.convertio.co/
- API Reference: https://developers.convertio.co/api/docs/
- CLI Docs: https://developers.convertio.co/cli/
- Base URL: https://api.convertio.co/convert

## API Overview
- **Purpose**: Universal file conversion API supporting 300+ formats
- **Category**: document
- **Target users**: Developers needing multi-format file conversion

## Authentication
- **Type**: API Key
- **How to obtain**: Sign up at convertio.co, get API key from dashboard
- **Header/Body format**: `apikey` parameter in request body

## Core Endpoints & Design

### 1. Convert File (POST)
- **Method & path**: `POST /convert`
- **Purpose**: Submit a file for conversion
- **Request params**:
  - `apikey` (string): Your API key
  - `input` (string): "upload", "url", or "base64"
  - `file` (string): File content (if upload/base64) or URL
  - `filename` (string): Original filename
  - `outputformat` (string): Target format
  - `options` (object): [Optional] Format-specific options
- **Response structure**:
  ```json
  {
    "status": "ok",
    "data": {
      "id": "abc123",
      "minutes": "0.12"
    }
  }
  ```

### 2. Check Status (GET)
- **Method & path**: `GET /convert/{id}/status`
- **Purpose**: Poll for conversion completion
- **Response structure**:
  ```json
  {
    "status": "ok",
    "data": {
      "id": "abc123",
      "step": "finish",
      "minutes": "0.12",
      "output": {
        "url": "https://...",
        "size": 12345
      }
    }
  }
  ```

### 3. Cancel Conversion (DELETE)
- **Method & path**: `DELETE /convert/{id}`
- **Purpose**: Cancel an ongoing conversion

## Data Models

**ConversionRequest**:
- `apikey` (string): Authentication
- `input` (string): Input method
- `file` (string): File data or URL
- `outputformat` (string): Target format

**ConversionStatus**:
- `id` (string): Conversion ID
- `status` (string): "ok", "wait", "error"
- `step` (string): "load", "convert", "finish"
- `minutes` (float): API minutes used
- `output` (object): Result file info

## Supported Formats (300+)

**Documents**: PDF, DOCX, DOC, TXT, RTF, ODT, EPUB, MOBI, etc.
**Images**: JPG, PNG, GIF, BMP, TIFF, WEBP, SVG, etc.
**Audio**: MP3, WAV, AAC, FLAC, OGG, WMA, etc.
**Video**: MP4, AVI, MKV, MOV, WMV, FLV, WebM, etc.
**Archives**: ZIP, RAR, 7Z, TAR, GZ, etc.
**CAD**: DWG, DXF, etc.
**Presentations**: PPTX, PPT, ODP, etc.
**Spreadsheets**: XLSX, XLS, CSV, ODS, etc.

## Input Methods
1. **Upload**: Send file content in request
2. **URL**: Provide public URL to file
3. **Base64**: Send base64-encoded file content

## Use Cases
- Converting legacy document formats
- Creating PDFs from various office formats
- Converting media files for web optimization
- Batch processing multiple files
- Archive extraction and creation

## Response Example
```json
{
  "status": "ok",
  "data": {
    "id": "conv_123456",
    "step": "finish",
    "step_percent": 100,
    "minutes": "0.25",
    "output": {
      "url": "https://api.convertio.co/d/abc123/output.pdf",
      "size": 1024000
    }
  }
}
```

## Pricing
- Free tier: 25 conversion minutes/day (no credit card)
- Paid plans: Based on conversion minutes
  - Light: $9.99/mo - 500 minutes
  - Basic: $19.99/mo - 2000 minutes
  - Unlimited: $49.99/mo - Unlimited

## API Wrapper Libraries
- PHP: Available on GitHub
- Node.js/Python: Community SDKs (marked as "coming soon" in docs)
