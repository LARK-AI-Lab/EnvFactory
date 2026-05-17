# OCRSpace Research Notes

## Data Source
- Official Docs: https://ocr.space/ocrapi
- API Reference: https://ocr.space/ocrapi
- Base URL: https://api.ocr.space/parse/image

## API Overview
- **Purpose**: Free OCR API for extracting text from images and PDFs
- **Category**: document
- **Target users**: Developers, small businesses, hobbyists needing affordable OCR

## Authentication
- **Type**: API Key
- **How to obtain**: Free registration at ocr.space
- **Header format**: `apikey: {api_key}` (sent in header)
- **Free tier**: 25,000 requests/month, 1MB file limit, 3 PDF page limit

## Core Endpoints & Design

### 1. Parse Image/PDF (POST)
- **Method & path**: `POST /parse/image`
- **Purpose**: Main OCR endpoint for images and PDFs
- **Request params**:
  - `url` or `file` or `base64Image`: Input source
  - `language` (string): 3-letter code (eng, chs, jpn, etc.)
  - `isOverlayRequired` (bool): Return word positions
  - `detectOrientation` (bool): Auto-rotate
  - `scale` (bool): Internal upscaling for low-res
  - `isTable` (bool): Preserve line structure for tables
  - `OCREngine` (int): 1, 2, or 3
  - `isCreateSearchablePdf` (bool): Generate searchable PDF
  - `isSearchablePdfHideTextLayer` (bool): Hide text layer
- **Response structure**: JSON with parsed results, confidence, overlay data

### 2. Parse via GET (Simple)
- **Method & path**: `GET /parse/ImageUrl`
- **Purpose**: Quick OCR via URL-only request
- **Limitations**: Only supports URL input, no file upload
- **Request params**: All in URL query string

## OCR Engines

**Engine 1** (Default):
- Fastest processing
- Supports many languages including CJK
- Multi-page TIFF support
- Good for general text

**Engine 2**:
- Language auto-detection (`language=auto`)
- Better for special characters (§$@€)
- Better for rotated text
- Good for single character OCR

**Engine 3**:
- Best text recognition quality
- 200+ languages supported
- Handwriting recognition
- Table/layout recognition (returns markdown)
- Checkbox recognition (☐☑)
- Slower processing for large images

## Data Models

**ParsedResult**:
- `FileParseExitCode` (int): 1=success, -10=parse error, -20=timeout
- `ParsedText` (string): Extracted text
- `TextOverlay` (object): Word positions and bounding boxes
- `ErrorMessage` (string): Error details if failed

**TextOverlay**:
- `Lines` (array): Lines of text
- `Words` (array): Word objects with text, position (Left, Top, Height, Width)
- `HasOverlay` (bool): Whether overlay data is available

## Response Example
```json
{
  "ParsedResults": [
    {
      "TextOverlay": {
        "Lines": [...],
        "HasOverlay": true
      },
      "FileParseExitCode": 1,
      "ParsedText": "Extracted text content...",
      "ErrorMessage": null
    }
  ],
  "OCRExitCode": 1,
  "IsErroredOnProcessing": false,
  "SearchablePDFURL": null,
  "ProcessingTimeInMilliseconds": "1234"
}
```

## Supported Languages (25+)
- English (eng), Chinese Simplified (chs), Chinese Traditional (cht)
- Japanese (jpn), Korean (kor)
- German (ger), French (fre), Spanish (spa)
- Arabic (ara), Russian (rus), and more...
- Engine 3 supports 200+ languages with auto-detection

## Use Cases
- Digitizing scanned documents
- Extracting text from receipts for expense tracking
- Converting PDFs to searchable format
- Table extraction from financial reports
- CAPTCHA solving (for legitimate accessibility)

## Pricing Tiers
| Plan | Price | Requests | File Size | PDF Pages |
|------|-------|----------|-----------|-----------|
| Free | Free | 25,000/mo | 1MB | 3 |
| PRO | $30/mo | 300,000/mo | 5MB | 3 |
| PRO PDF | $60/mo | 300,000/mo | 100MB+ | 999+ |
| Enterprise | $999+/mo | Custom | 100MB+ | 999+ |
