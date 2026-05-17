# ClinicalTrialsGov Research Notes

## Data Source
- Official Docs: https://clinicaltrials.gov/data-api/about-api
- API Reference: https://clinicaltrials.gov/data-api/api
- MCP Server: https://github.com/cyanheads/clinicaltrialsgov-mcp-server
- Base URL: `https://clinicaltrials.gov/api/v2`

## API Overview
- **Purpose**: Search, retrieve, and summarize clinical trial records.
- **Category**: Clinical research
- **Target users**: Medical researchers, patient matching tools, trial discovery workflows.

## Authentication
- **Type**: None
- **How to obtain**: Not applicable.
- **Header/param format**: Not applicable.

## Core Endpoints & Design
- **GET /studies**: Search studies with query terms, filters, pagination, and page size.
- **GET /studies/{nctId}**: Retrieve a study by NCT ID.
- **Structured search**: Build common searches for condition, intervention, status, and location.
- **Results extraction**: Return outcome and adverse event sections for a study.
- **Trend analysis**: Group matching studies by status, phase, condition, or sponsor.

## Data Models
- `Study`: nctId, briefTitle, overallStatus, conditions, interventions, phases
- `ProtocolSection`: identification, status, sponsor, design, eligibility
- `ResultsSection`: participantFlow, outcomeMeasures, adverseEvents

## Use Cases
- Find clinical trials for a disease.
- Retrieve details for known NCT identifiers.
- Summarize trial distribution by phase or recruitment status.

## Response Example
```json
{
  "studies": [{"nctId": "NCT04280588", "briefTitle": "COVID-19 Study", "overallStatus": "COMPLETED"}],
  "nextPageToken": null,
  "totalCount": 1
}
```

