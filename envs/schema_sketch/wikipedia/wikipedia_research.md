# Wikipedia Research Notes

## Data Source
- Official Docs: https://www.mediawiki.org/wiki/API:REST_API
- API Reference: https://www.mediawiki.org/wiki/API:Search
- MCP Server: https://github.com/Rudra-ravi/wikipedia-mcp
- Base URL: `https://{language}.wikipedia.org/api/rest_v1`

## API Overview
- **Purpose**: Search Wikipedia and retrieve article summaries, full text, sections, and related pages.
- **Category**: Knowledge and reference
- **Target users**: Entity lookup, education, QA, fact retrieval, and document enrichment workflows.

## Authentication
- **Type**: None for public endpoints
- **How to obtain**: Not applicable.
- **Header/param format**: Not applicable.

## Core Endpoints & Design
- **Search API**: Search pages by text query.
- **GET /page/summary/{title}**: Retrieve concise article summary.
- **GET /page/mobile-sections/{title}**: Retrieve article sections.
- **GET /page/related/{title}**: Retrieve related pages.
- **Article content retrieval**: Return title, text, URL, summary, and section data.

## Data Models
- `SearchResult`: title, pageid, excerpt, description, thumbnail
- `Article`: title, pageid, summary, text, url, sections
- `Section`: title, level, text
- `RelatedPage`: title, pageid, extract, url

## Use Cases
- Search for an entity or concept.
- Retrieve full article text for reasoning tasks.
- Extract sections and summaries for grounded answers.

## Response Example
```json
{
  "title": "Artificial intelligence",
  "summary": "Artificial intelligence is intelligence demonstrated by machines.",
  "sections": [{"title": "History", "level": 2, "text": "..."}]
}
```

