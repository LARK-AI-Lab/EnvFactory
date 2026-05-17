# OpenLibrary Research Notes

## Data Source
- Official Docs: https://openlibrary.org/developers/api
- MCP Server: https://www.npmjs.com/package/@geobio/mcp-open-library
- API Reference: https://openlibrary.org/dev/docs/api/search
- Base URL: `https://openlibrary.org`

## API Overview
- **Purpose**: Search books and authors in the Open Library catalog.
- **Category**: Books and literature
- **Target users**: Library catalogs, reading apps, book recommendation tools, research assistants.

## Authentication
- **Type**: None for public read endpoints
- **How to obtain**: Not applicable.
- **Header/param format**: Not applicable.

## Core Endpoints & Design
- **GET /search.json?title=...**: Search books by title.
- **GET /isbn/{isbn}.json**: Retrieve book details by ISBN.
- **GET /search/authors.json?q=...**: Search authors by name.
- **GET /authors/{olid}.json**: Retrieve author information.
- **GET /b/{identifierType}/{identifier}-{size}.jpg**: Generate cover image URLs.

## Data Models
- `Book`: key, title, author_name, first_publish_year, isbn, cover_i
- `Edition`: title, authors, publishers, publish_date, identifiers
- `Author`: key, name, birth_date, death_date, bio, photos
- `Cover`: identifier, identifier_type, size, url

## Use Cases
- Find a book from a title mention.
- Retrieve author profile and publication metadata.
- Attach cover URLs to book search results.

## Response Example
```json
{
  "title": "Dune",
  "matches": [{"key": "/works/OL893415W", "title": "Dune", "author_name": ["Frank Herbert"]}]
}
```

