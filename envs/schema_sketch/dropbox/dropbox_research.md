# Dropbox Research Notes

## Data Source
- Official Docs: https://www.dropbox.com/developers/documentation/http/documentation
- API Reference: https://www.dropbox.com/developers/documentation/http/documentation
- SDK/Tutorials: https://www.dropbox.com/developers/reference/getting-started
- Base URL: https://api.dropboxapi.com/2

## API Overview
- **Purpose**: Cloud file storage and synchronization API
- **Category**: storage
- **Target users**: Developers building file sync, backup, or collaboration apps

## Authentication
- **Type**: OAuth 2.0
- **How to obtain**: Create app at Dropbox App Console, get App Key/Secret
- **Header format**: `Authorization: Bearer {access_token}`
- **Token types**: Short-lived access tokens (4 hours), refresh tokens available

## Core Endpoints & Design

### 1. Upload File
- **Method & path**: POST /files/upload
- **Purpose**: Upload file content to Dropbox
- **Request**: Binary content in body, metadata in Dropbox-API-Arg header
- **Response**: File metadata (name, id, path, size, hash)

### 2. Download File
- **Method & path**: POST /files/download
- **Purpose**: Download file content
- **Request**: File path or ID in Dropbox-API-Arg header
- **Response**: File content in body, metadata in Dropbox-API-Result header

### 3. List Folder
- **Method & path**: POST /files/list_folder
- **Purpose**: List contents of a directory
- **Request params**: path, recursive, limit
- **Response**: Entries array with pagination cursor

### 4. Get Metadata
- **Method & path**: POST /files/get_metadata
- **Purpose**: Retrieve file/folder metadata
- **Request params**: path, include_media_info
- **Response**: File or folder metadata object

### 5. Create Shared Link
- **Method & path**: POST /sharing/create_shared_link_with_settings
- **Purpose**: Create shareable link
- **Request params**: path, settings (visibility, expiration)
- **Response**: Shared link metadata

## Data Models
- **FileMetadata**: name, id, client_modified, server_modified, rev, size, path_lower, content_hash
- **FolderMetadata**: name, id, path_lower, shared_folder_id
- **ListFolderResult**: entries, cursor, has_more

## Use Cases
- File backup and sync applications
- Document management systems
- Collaborative workspace tools
- Content distribution via shared links

## Response Example
```json
{
  "name": "test.txt",
  "id": "id:a4ayc_80_OEAAAAAAAAAXw",
  "client_modified": "2024-03-05T12:00:00Z",
  "server_modified": "2024-03-05T12:00:01Z",
  "rev": "a1c10ce0dd78",
  "size": 12,
  "path_lower": "/homework/math/test.txt",
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

## Special Features
- Content hash verification for integrity
- Chunked upload for large files (session-based)
- Paper API for collaborative documents
- Webhooks for change notifications
