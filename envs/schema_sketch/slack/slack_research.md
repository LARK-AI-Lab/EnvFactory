# Slack Research Notes

## Data Source
- Official Docs: https://api.slack.com/methods
- MCP Server: https://github.com/korotovsky/slack-mcp-server
- API Reference: https://api.slack.com/web
- Base URL: `https://slack.com/api`

## API Overview
- **Purpose**: Search and retrieve Slack conversations, channels, users, and messages.
- **Category**: Team communication
- **Target users**: Teams analyzing workspace conversations or automating message workflows.

## Authentication
- **Type**: OAuth token or browser session token depending on MCP mode
- **How to obtain**: Slack app OAuth or session-token setup from the MCP server docs.
- **Header/param format**: `Authorization: Bearer {token}`

## Core Endpoints & Design
- **conversations.list**: List channels, DMs, and group DMs.
- **conversations.history**: Retrieve messages from a conversation.
- **conversations.replies**: Retrieve thread replies.
- **search.messages**: Search Slack messages by query and filters.
- **chat.postMessage**: Add a message to a conversation or thread.

## Data Models
- `Channel`: id, name, type flags, member count, topic
- `User`: id, name, real_name, display_name, email
- `Message`: ts, user, text, channel, thread_ts, reactions
- `Reaction`: name, users, count

## Use Cases
- Search imported workspace data.
- Retrieve channel history for reasoning tasks.
- Simulate thread replies and posting messages as state updates.

## Response Example
```json
{
  "messages": [
    {"user": "U123", "text": "Movie night?", "ts": "1733200000.000100"}
  ],
  "next_cursor": ""
}
```

