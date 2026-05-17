# OneDrive Research Notes

## Data Source
- Official Docs: https://docs.microsoft.com/en-us/onedrive/developer/rest-api/
- API Reference: https://docs.microsoft.com/en-us/onedrive/developer/rest-api/api/
- SDK/Tutorials: https://docs.microsoft.com/en-us/graph/onedrive-concept-overview
- Base URL: https://graph.microsoft.com/v1.0

## API Overview
- **Purpose**: Cloud file storage integrated with Microsoft 365
- **Category**: storage
- **Target users**: Microsoft 365 users, enterprise applications

## Authentication
- **Type**: OAuth 2.0 (Microsoft identity platform)
- **How to obtain**: Azure AD app registration
- **Scopes**: Files.Read, Files.ReadWrite, Files.Read.All, Files.ReadWrite.All
- **Header format**: `Authorization: Bearer {access_token}`
- **Unified endpoint**: Microsoft Graph API

## Core Endpoints & Design

### 1. Upload Small File
- **Method & path**: PUT /me/drive/items/{parent-id}:/{filename}:/content
- **Purpose**: Upload file < 4MB
- **Request**: Binary content in body
- **Response**: DriveItem resource

### 2. Upload Large File
- **Method & path**: POST /me/drive/items/{parent-id}:/{filename}:/createUploadSession
- **Purpose**: Resumable upload for large files
- **Flow**: Create session → Upload chunks → Complete
- **Response**: Upload session URL

### 3. Download File
- **Method & path**: GET /me/drive/items/{item-id}/content
- **Purpose**: Download file content
- **Response**: 302 redirect to download URL or content directly

### 4. List Children
- **Method & path**: GET /me/drive/items/{item-id}/children
- **Purpose**: List folder contents
- **Query params**: $top, $select, $expand
- **Response**: Collection of DriveItems

### 5. Get Item
- **Method & path**: GET /me/drive/items/{item-id}
- **Purpose**: Retrieve item metadata
- **Response**: DriveItem with @downloadUrl

### 6. Create Share Link
- **Method & path**: POST /me/drive/items/{item-id}/createLink
- **Purpose**: Create sharing link
- **Request body**: type (view/edit/embed), scope (anonymous/organization)
- **Response**: Permission with link

## Data Models
- **DriveItem**: id, name, size, webUrl, downloadUrl, file/folder facet, parentReference
- **Drive**: id, driveType (personal/business), owner, quota
- **Permission**: id, roles, link, grantedTo

## Use Cases
- Enterprise document management
- Microsoft 365 integrated apps
- SharePoint file access
- Teams file collaboration

## Response Example
```json
{
  "id": "0123456789abc!123",
  "name": "document.docx",
  "size": 12345,
  "webUrl": "https://1drv.ms/x/s!...",
  "downloadUrl": "https://...",
  "createdDateTime": "2024-03-05T12:00:00Z",
  "lastModifiedDateTime": "2024-03-05T12:30:00Z",
  "file": {
    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "hashes": {
      "sha1Hash": "..."
    }
  },
  "parentReference": {
    "driveId": "0123456789abc",
    "id": "0123456789abc!456"
  }
}
```

## Special Features
- Delta sync for incremental changes
- Webhooks for real-time notifications
- Excel workbook API for spreadsheet operations
- SharePoint integration
- Personal vault access
