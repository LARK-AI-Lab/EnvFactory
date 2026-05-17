# Zoom Research Notes

## Data Source
- Official Docs: https://developers.zoom.us/docs/api/
- API Reference: https://developers.zoom.us/docs/api/rest/reference/
- SDK/Tutorials: https://developers.zoom.us/docs/integrations/
- Base URL: https://api.zoom.us/v2

## API Overview
- **Purpose**: Video conferencing platform for meetings, webinars, and communications
- **Category**: communication
- **Target users**: Remote teams, educators, businesses needing video conferencing

## Authentication
- **Type**: OAuth 2.0 (Account-level or User-level) or Server-to-Server OAuth
- **How to obtain**: 
  - Create app at Zoom Marketplace (https://marketplace.zoom.us/)
  - Choose app type: OAuth, Server-to-Server OAuth, or JWT (deprecated)
- **Header format**: `Authorization: Bearer {access_token}`
- **Scopes**: Granular permissions (e.g., meeting:read, meeting:write, recording:read)

## Core Endpoints & Design

### 1. Create Meeting
- **Method & path**: POST /users/{userId}/meetings
- **Purpose**: Schedule a new meeting
- **Request body**: topic, type, start_time, duration, timezone, password, settings
- **Response**: Meeting object with join_url and start_url

### 2. Get Meeting
- **Method & path**: GET /meetings/{meetingId}
- **Purpose**: Retrieve meeting details
- **Response**: Meeting object with full details

### 3. List Meetings
- **Method & path**: GET /users/{userId}/meetings
- **Purpose**: List all meetings for a user
- **Query params**: type (scheduled|live|upcoming|previous), page_size
- **Response**: Paginated list of meetings

### 4. Update Meeting
- **Method & path**: PATCH /meetings/{meetingId}
- **Purpose**: Modify meeting settings
- **Request body**: Fields to update (topic, start_time, duration, settings)
- **Response**: Updated meeting details

### 5. Delete Meeting
- **Method & path**: DELETE /meetings/{meetingId}
- **Purpose**: Delete a meeting
- **Query params**: occurrence_id (for recurring), cancel_meeting_reminder
- **Response**: 204 No Content on success

### 6. List Recordings
- **Method & path**: GET /users/{userId}/recordings
- **Purpose**: Get cloud recordings
- **Query params**: from, to, page_size
- **Response**: List of recordings with download URLs

### 7. Get Recording
- **Method & path**: GET /meetings/{meetingId}/recordings
- **Purpose**: Get recording for specific meeting
- **Response**: Recording files with play_url and download_url

### 8. Delete Recording
- **Method & path**: DELETE /meetings/{meetingId}/recordings
- **Purpose**: Delete recording files
- **Query params**: action (delete|trash)
- **Response**: 204 No Content on success

## Data Models
- **Meeting**: id, topic, type, start_time, duration, timezone, join_url, start_url, password, settings
- **Recording**: id, meeting_id, topic, start_time, duration, total_size, recording_files[]
- **RecordingFile**: id, file_type, file_size, play_url, download_url, recording_type, status

## Use Cases
- Schedule and manage video meetings
- Automate meeting creation for appointments
- Download and archive meeting recordings
- Integrate with calendar and scheduling systems
- Webinar management and registration

## Response Example (Create Meeting)
```json
{
  "id": 123456789,
  "topic": "Team Weekly Standup",
  "type": 2,
  "start_time": "2024-03-10T14:00:00Z",
  "duration": 60,
  "timezone": "America/New_York",
  "join_url": "https://zoom.us/j/123456789?pwd=abc123",
  "start_url": "https://zoom.us/s/123456789?zak=token123",
  "password": "meet123",
  "settings": {
    "host_video": true,
    "participant_video": true,
    "join_before_host": false,
    "mute_upon_entry": true
  }
}
```

## Special Features
- Recurring meetings with multiple occurrence patterns
- Waiting room and security settings
- Breakout rooms configuration
- Polls and Q&A for webinars
- Registration required meetings
- Cloud recording auto-transcription
- Meeting templates
- Webhooks for meeting events (started, ended, participant joined)

## Rate Limits
- Free/Basic: 1 request/second
- Pro: 2 requests/second
- Business/Enterprise: 4 requests/second

## Pricing
- Free: Up to 40 min group meetings, 100 participants
- Pro: $14.99/mo, up to 30 hours, 100 participants, 5GB cloud recording
- Business: $21.99/mo, up to 300 participants, unlimited cloud recording
- Enterprise: Custom pricing, up to 1000 participants

## Notes
- JWT app type is deprecated (June 2023), migrate to Server-to-Server OAuth
- Server-to-Server OAuth recommended for backend integrations
- User-managed OAuth for apps acting on behalf of users
- Account-level scopes required for admin operations
