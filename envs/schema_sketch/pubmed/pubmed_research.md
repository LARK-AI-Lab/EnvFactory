# PubMed Research Notes

## Data Source
- Official Docs: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- MCP Server: https://github.com/geobio/PubMed-MCP-Server
- API Reference: https://www.ncbi.nlm.nih.gov/books/NBK25499/
- Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`

## API Overview
- **Purpose**: Search biomedical literature indexed by PubMed and retrieve article metadata.
- **Category**: Biomedical literature
- **Target users**: Researchers, clinicians, and literature-review workflows.

## Authentication
- **Type**: None for basic use; optional NCBI API key for higher rate limits
- **How to obtain**: NCBI account settings.
- **Header/param format**: `api_key={NCBI_API_KEY}` query parameter when used.

## Core Endpoints & Design
- **ESearch**: Search PubMed and return PMIDs.
- **ESummary**: Retrieve article summaries.
- **EFetch**: Retrieve full article metadata and abstracts.
- **Author search**: Query PubMed with author fields.
- **Journal/year search**: Query PubMed by source and publication date.

## Data Models
- `Article`: pmid, title, authors, journal, pub_date, abstract, doi
- `Author`: name, affiliation
- `MeshTerm`: descriptorName, qualifierName

## Use Cases
- Search articles by disease, author, or journal.
- Retrieve abstracts for biomedical question answering.
- Build small fixed literature corpora for evaluation tasks.

## Response Example
```json
{
  "query": "bessel van der kolk",
  "count": 1,
  "articles": [{"pmid": "123456", "title": "Trauma study", "journal": "Journal"}]
}
```

