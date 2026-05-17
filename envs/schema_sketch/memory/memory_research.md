# Memory Research Notes

## Data Source
- Official Docs: https://github.com/modelcontextprotocol/servers/tree/main/src/memory
- API Reference: https://github.com/modelcontextprotocol/servers/tree/main/src/memory#api
- SDK/Tutorials: https://modelcontextprotocol.io
- Base URL: Local JSONL or JSON storage file

## API Overview
- **Purpose**: Store persistent facts as a local knowledge graph.
- **Category**: Knowledge graph
- **Target users**: Agents that need durable memory about users, organizations, events, and preferences.

## Authentication
- **Type**: None
- **How to obtain**: Not applicable.
- **Header/param format**: Not applicable.

## Core Endpoints & Design
- **create_entities**: Create graph nodes with observations.
- **create_relations**: Add directed typed edges between entities.
- **add_observations**: Add new fact strings to existing entities.
- **search_nodes**: Search names, types, and observations.
- **open_nodes**: Open named entities and relations between them.

## Data Models
- `Entity`: name, entityType, observations
- `Relation`: from, to, relationType
- `ObservationUpdate`: entityName, contents

## Use Cases
- Store user preferences and profile facts.
- Model relationships among people, projects, and events.
- Search a compact graph in a deterministic local scenario.

## Response Example
```json
{
  "entities": [{"name": "Alice", "entityType": "person", "observations": ["Likes morning meetings"]}],
  "relations": [{"from": "Alice", "to": "MCPFactory", "relationType": "works_on"}]
}
```

