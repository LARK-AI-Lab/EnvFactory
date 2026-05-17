# Box Research Notes

## Data Source
- Official Docs: https://developer.box.com/guides/
- API Reference: https://developer.box.com/reference/
- SDK/Tutorials: https://developer.box.com/sdks/
- Base URL: https://api.box.com/2.0

## API Overview
- **Purpose**: Enterprise cloud content management
- **Category**: storage
- **Target users**: Enterprises, regulated industries, content-centric workflows

## Authentication
- **Type**: OAuth 2.0, JWT (Server Authentication), Developer Token
- **How to obtain**: Box Developer Console
- **Header format**: `Authorization: Bearer {access_token}`
- **Auth types**: 
  - Standard OAuth 2.0 (user apps)
  - JWT with RSA key (service accounts)
  - Client Credentials Grant

## Core Endpoints & Design

### 1. Upload File
- **Method & path**: POST /files/content
- **Purpose**: Upload new file
- **Request**: Multipart form with attributes and file
- **Response**: File object

### 2. Upload New Version
- **Method & path**: POST /files/{file_id}/content
- **Purpose**: Upload new version of existing file
- **Request**: Multipart form with file content
- **Response**: File object with version info

### 3. Download File
- **Method & path**: GET /files/{file_id}/content
- **Purpose**: Download file content
- **Response**: 302 redirect to download URL

### 4. List Folder Items
- **Method & path**: GET /folders/{folder_id}/items
- **Purpose**: List folder contents
- **Query params**: limit, offset, fields, sort
- **Response**: Collection of items with pagination

### 5. Get Item Info
- **Method & path**: GET /files/{file_id} or /folders/{folder_id}
- **Purpose**: Retrieve item metadata
- **Response**: File or Folder object

### 6. Create Shared Link
- **Method & path**: PUT /files/{file_id} or /folders/{folder_id}
- **Purpose**: Create/update shared link
- **Request body**: shared_link object with access, password, unshared_at
- **Response**: Updated item with shared_link

## Data Models
- **File**: id, type, name, size, sha1, created_at, modified_at, parent, shared_link
- **Folder**: id, type, name, size, created_at, modified_at, parent, item_collection
- **ItemCollection**: total_count, entries, offset, limit

## Use Cases
- Enterprise content management
- Secure file collaboration
- Workflow automation
- Compliance and governance
- HIPAA/FedRAMP compliant storage

## Response Example
```json
{
  "type": "file",
  "id": "1234567890",
  "name": "contract.pdf",
  "size": 1234567,
  "sha1": "3f0b45c70bf6e7c9d8b2a5f1c4e3d6b8a9c0d1e2",
  "created_at": "2024-03-05T12:00:00-08:00",
  "modified_at": "2024-03-05T12:30:00-08:00",
  "parent": {
    "type": "folder",
    "id": "0",
    "name": "All Files"
  },
  "shared_link": {
    "url": "https://app.box.com/s/abcd1234",
    "download_url": "https://app.box.com/s/abcd1234/download",
    "access": "open",
    "effective_access": "open"
  }
}
```

## Special Features
- File versioning with restore capability
- Metadata templates for custom attributes
- Retention policies and legal holds
- Box Sign for e-signatures
- Advanced collaboration with tasks and comments
- Preview API for 120+ file types
