# Airtable Research Notes

## Data Source
- Official Docs: https://airtable.com/developers/web/api/introduction
- MCP Server: https://github.com/felores/airtable-mcp
- API Reference: https://airtable.com/developers/web/api/list-bases
- Base URL: `https://api.airtable.com/v0`

## API Overview
- **Purpose**: Manage Airtable bases, tables, fields, and records.
- **Category**: Productivity database
- **Target users**: Teams building lightweight databases, workflows, and internal tools.

## Authentication
- **Type**: Personal access token
- **How to obtain**: Create a token from Airtable Builder Hub.
- **Header/param format**: `Authorization: Bearer {AIRTABLE_API_KEY}`

## Core Endpoints & Design
- **GET /meta/bases**: List accessible bases.
- **GET /meta/bases/{baseId}/tables**: List tables and field schemas in a base.
- **GET /{baseId}/{tableIdOrName}**: List records with view, formula, pagination, and max record filters.
- **POST /{baseId}/{tableIdOrName}**: Create a record with field values.
- **PATCH /{baseId}/{tableIdOrName}/{recordId}**: Update fields on an existing record.

## Data Models
- `Base`: id, name, permissionLevel
- `Table`: id, name, description, fields, views
- `Field`: id, name, type, options
- `Record`: id, createdTime, fields

## Use Cases
- Inspect bases and tables.
- Query task, CRM, inventory, or planning records.
- Create and update records in a stateful simulated workspace.

## Response Example
```json
{
  "records": [
    {
      "id": "rec123",
      "createdTime": "2025-01-01T00:00:00.000Z",
      "fields": {"Name": "Launch plan", "Status": "In progress"}
    }
  ],
  "offset": null
}
```

