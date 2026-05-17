# MongoDB Research Notes

## Data Source
- Official Docs: https://www.mongodb.com/docs/mongodb-mcp-server/current/
- MCP Server: https://github.com/mongodb-js/mongodb-mcp-server
- API Reference: https://www.mongodb.com/docs/manual/reference/command/
- Base URL: MongoDB connection URI

## API Overview
- **Purpose**: Inspect and query MongoDB databases and collections.
- **Category**: Database
- **Target users**: Developers and analysts working with document databases.

## Authentication
- **Type**: MongoDB connection string
- **How to obtain**: Create a MongoDB deployment or local server and generate a URI.
- **Header/param format**: Connection URI such as `mongodb+srv://...`

## Core Endpoints & Design
- **listDatabases**: List database names and metadata.
- **listCollections**: List collections in a database.
- **find**: Query documents using a MongoDB filter, projection, sort, limit, and skip.
- **aggregate**: Run aggregation pipeline stages.
- **insertOne**: Insert one document into a collection.

## Data Models
- `Database`: name, sizeOnDisk, empty
- `Collection`: name, type, options
- `Document`: `_id` and arbitrary JSON fields
- `AggregationPipeline`: ordered list of stages

## Use Cases
- Explore imported sample databases.
- Answer analytical questions over document collections.
- Simulate CRUD and aggregation without a live MongoDB instance.

## Response Example
```json
{
  "database": "video_game_store",
  "collection": "Purchase History",
  "documents": [{"_id": "txn_001", "Customer Segment": "First-time"}],
  "count": 1
}
```

