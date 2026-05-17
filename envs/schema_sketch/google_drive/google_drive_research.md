# Google Drive Research Notes

## Data Source
- Official Docs: https://developers.google.com/drive/api/v3/about-sdk
- API Reference: https://developers.google.com/drive/api/v3/reference
- SDK/Tutorials: https://developers.google.com/drive/api/v3/quickstart/python
- Base URL: https://www.googleapis.com/drive/v3

## API Overview
- **Purpose**: Cloud file storage integrated with Google Workspace
- **Category**: storage
- **Target users**: Google Workspace users, document-centric applications

## Authentication
- **Type**: OAuth 2.0
- **How to obtain**: Google Cloud Console, create credentials
- **Scopes**: 
  - https://www.googleapis.com/auth/drive.file (per-file access)
  - https://www.googleapis.com/auth/drive (full access)
- **Header format**: `Authorization: Bearer {access_token}`

## Core Endpoints & Design

### 1. Upload File
- **Method & path**: POST /upload/drive/v3/files
- **Purpose**: Upload file with metadata
- **Upload types**: media (simple), multipart (metadata+content), resumable (large files)
- **Request**: Multipart with metadata and content
- **Response**: File resource

### 2. Download File
- **Method & path**: GET /drive/v3/files/{fileId}/export (for Google Docs)
- **Alt**: GET /drive/v3/files/{fileId}?alt=media (for binary files)
- **Purpose**: Download file content
- **Response**: File content or export format

### 3. List Files
- **Method & path**: GET /drive/v3/files
- **Purpose**: Search and list files
- **Query params**: q (search query), pageSize, orderBy, fields
- **Response**: Files list with nextPageToken

### 4. Get File
- **Method & path**: GET /drive/v3/files/{fileId}
- **Purpose**: Retrieve file metadata
- **Query params**: fields (specify which fields to return)
- **Response**: File resource

### 5. Create Permission
- **Method & path**: POST /drive/v3/files/{fileId}/permissions
- **Purpose**: Share file with others
- **Request params**: role, type, emailAddress
- **Response**: Permission resource

## Data Models
- **File**: id, name, mimeType, description, size, createdTime, modifiedTime, parents, webViewLink, webContentLink
- **Permission**: id, type, role, emailAddress, domain, allowFileDiscovery
- **FileList**: files[], nextPageToken, incompleteSearch

## Use Cases
- Document management with Google Workspace
- Media storage and streaming
- Collaborative editing integration
- Backup solutions for Google users

## Response Example
```json
{
  "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "name": "My Document",
  "mimeType": "application/vnd.google-apps.document",
  "size": "1024",
  "createdTime": "2024-03-05T12:00:00.000Z",
  "modifiedTime": "2024-03-05T12:30:00.000Z",
  "parents": ["0Bz0bd"],
  "webViewLink": "https://docs.google.com/document/d/.../edit",
  "webContentLink": "https://drive.google.com/uc?export=download&id=..."
}
```

## Special Features
- Native Google Docs/Sheets/Slides support (export to various formats)
- Powerful search query language (q parameter)
- Change notifications via push notifications
- Shared drives for team/enterprise
