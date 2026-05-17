# Internet Archive Research Notes

## Data Source
- Official Docs: https://archive.org/services/docs/api/
- API Reference: https://archive.org/services/docs/api/internetarchive/index.html
- Base URL: https://archive.org

## API Overview
- **Purpose**: Access millions of free books, movies, software, music, websites, and more
- **Category**: Digital Archive / Education / Media
- **Target users**: Researchers, educators, historians, developers, content curators

## Authentication
- **Type**: None required for read operations (S3-like API requires keys for writes)
- **Rate limits**: Be respectful; no explicit limits documented
- **Terms**: Content is generally public domain or Creative Commons

## Core Endpoints & Design

### 1. Search Items
- **Method & path**: `GET /advancedsearch.php`
- **Purpose**: Search the Internet Archive collection
- **Request params**:
  - `q` (str): Search query (Lucene syntax supported)
  - `fl[]` (list): Fields to return (e.g., identifier, title, creator)
  - `sort[]` (str): Sort order
  - `rows` (int): Results per page
  - `page` (int): Page number
  - `output` (str): Response format (json, xml)
- **Response structure**:
  - `responseHeader` (obj): Search metadata
  - `response` (obj): Results
    - `numFound` (int): Total matches
    - `start` (int): Starting offset
    - `docs` (list): Item records with requested fields

### 2. Get Item Metadata
- **Method & path**: `GET /metadata/{identifier}`
- **Purpose**: Retrieve detailed metadata for an item
- **Request params**:
  - `identifier` (str): Item identifier
- **Response structure**:
  - `metadata` (obj): Core metadata
    - `identifier` (str): Unique ID
    - `title` (str): Item title
    - `creator` (str): Creator/author
    - `date` (str): Date published/created
    - `description` (str): Description
    - `subject` (list): Subject tags
    - `licenseurl` (str): License URL
  - `files` (list): Associated files
    - `name` (str): Filename
    - `format` (str): File format
    - `size` (int): File size in bytes
    - `mtime` (str): Modified time
  - `reviews` (list): User reviews

### 3. Download File
- **Method & path**: `GET /download/{identifier}/{filename}`
- **Purpose**: Download a specific file from an item
- **Request params**:
  - `identifier` (str): Item identifier
  - `filename` (str): Name of file to download

### 4. Get Collection Info
- **Method & path**: `GET /details/{collection_id}`
- **Purpose**: Get information about a collection
- **Response structure**:
  - Collection metadata
  - List of items in collection

### 5. Wayback Machine
- **Method & path**: `GET /wayback/available`
- **Purpose**: Check if a URL snapshot exists in Wayback Machine
- **Request params**:
  - `url` (str): URL to check
  - `timestamp` (str): [Optional] Specific timestamp
- **Response structure**:
  - `url` (str): Original URL
  - `archived_snapshots` (obj): Available snapshots
    - `closest` (obj): Closest snapshot
      - `status` (str): HTTP status
      - `available` (bool): Whether available
      - `url` (str): Snapshot URL
      - `timestamp` (str): Snapshot timestamp

## Data Models
- **Item**: identifier, title, creator, date, description, subject[], license
- **File**: name, format, size, mtime, url
- **Search Result**: identifier, title, creator, date, description

## Use Cases
- Historical research
- Educational content access
- Media preservation
- Academic citations
- Public domain content discovery
- Website archival research

## Response Example (Metadata)
```json
{
  "metadata": {
    "identifier": "TheGreatGatsby",
    "title": "The Great Gatsby",
    "creator": "F. Scott Fitzgerald",
    "date": "1925",
    "description": "A novel about the American dream...",
    "subject": ["American fiction", "Wealth", "1920s"]
  },
  "files": [
    {
      "name": "greatgatsby.pdf",
      "format": "PDF",
      "size": 2500000
    }
  ]
}
```

## Special Collections
- Wayback Machine (web.archive.org)
- Open Library (openlibrary.org)
- Live Music Archive
- Old Time Radio
- Prelinger Archives
