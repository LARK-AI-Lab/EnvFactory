---
name: mcp-sketch-discovery
description: Discover and draft new MCP server sketches through systematic web search. Generate lightweight function definitions with complete docstrings. Output 5 sketches per run directly to envs/schema_sketch/.
---

# MCP Sketch Discovery 

## Overview
Systematically discover high-quality API opportunities and generate lightweight MCP server sketches.

**Key Principles:**
- Non-AI focus: Target utility APIs only—exclude AI/LLM services (chat, embeddings, image gen, etc.)
- Semi-automated: Proposes search directions, user confirms/adjusts
- State-based: All external dependencies simulated via state variables (no real HTTP calls in sketch)
- Lightweight: Function signatures + docstrings only (pass body)
- Batch output: 5 sketches per run

## Pipeline (6 Steps)

### Step 1: Inventory & Proposal
Scan `envs/schema_sketch/` to categorize existing servers, then propose 3 search directions.

**Proposal format:**
```
Existing coverage: [category counts]

Proposed directions:
A. [keyword1] - rationale
B. [keyword2] - rationale  
C. [keyword3] - rationale

Reply: Choose A/B/C or suggest modification
```

### Step 2: Discovery Search
Execute web search based on confirmed direction. Search queries include:
- "best [category] APIs 2025"
- "[category] API documentation"
- "free [category] API for developers"

Only allow these sources:
- official domain
- GitHub organization
- developer portal

Collect 10-15 raw candidates.

### Step 3: Deduplication & Selection
Filter candidates against existing servers:
- Exclude AI-related APIs (LLM, chat, embeddings, image gen, etc.)
- Skip if similar server exists
- Prioritize: Unique functionality > Developer popularity > Documentation quality

Select top 5 candidates with brief rationale.

### Step 4: Deep Research
For each of the 5 candidates, research:
- Official documentation URL
- Authentication method (if any)
- Core endpoints/functionality
- Typical use cases

### Step 5: Sketch Generation
Generate 5 sketch files at `envs/schema_sketch/{server_name}/{server_name}_server.py`.

**Sketch format:**
```python
# Data Source: {official_doc_url}
# Server: {ServerName}
# Category: {category}


def core_tool(param1: str, param2: int = None) -> dict:
    """
    {Description of what this tool does}.
    
    Args:
        param1 (str): Description of param1
        param2 (int): [Optional] Description of param2
        
    Returns:
        dict: {
            "field1": type,
            "field2": type
        }
    """
    pass
```

**Requirements:**
- Use `pass` for function body (no implementation)
- Complete docstrings with Args and Returns
- Include type hints
- Mark optional parameters with `[Optional]` in docstring

**Research file format (`{server_name}_research.md`):**
```markdown
# {ServerName} Research Notes

## Data Source
- Official Docs: {url}
- API Reference: {url}
- SDK/Tutorials: {url}
- Base URL: {api_base_url}

## API Overview
- **Purpose**: One-sentence description of what the API does
- **Category**: e.g., productivity, data, infrastructure
- **Target users**: Who typically uses this API

## Authentication
- **Type**: API Key / OAuth2 / Bearer Token / None
- **How to obtain**: Signup flow, dashboard, etc.
- **Header/param format**: e.g., `Authorization: Bearer {key}`

## Core Endpoints & Design
For each endpoint:
- **Method & path**: e.g., `GET /v1/resources`
- **Purpose**: What it does
- **Request params**: Query/body params with types and constraints
- **Response structure**: Main fields and types
- **Pagination**: Cursor/offset/limit if applicable

## Data Models
Key entities and their fields:
- `EntityName`: field1 (type), field2 (type), ...

## Use Cases
- Typical integration scenarios
- Example applications

## Response Example
Include sample JSON payload for a representative endpoint, e.g.:
    { "field": "value", "items": [...] }

```

### Step 6: Summary Report
Output summary table:

```
| # | Server | Category | Key Tools | Data Source |
|---|--------|----------|-----------|-------------|
| 1 | XxxServer | xxx | tool_a, tool_b | url |
| ... | ... | ... | ... | ... |

Next round suggestions: [keyword1, keyword2, keyword3]
```

## Usage Flow

```
User: "Start sketch discovery"
Agent: [Step 1] Inventory + 3 proposals
User: "Go with A" / "Change to [custom keywords]"
Agent: [Step 2-6] Execute and generate 5 sketches
Agent: Output summary
```

Repeat for more batches.

## Output Location
```
envs/schema_sketch/
├── {server_name_1}/
│   └── {server_name_1}_server.py
├── {server_name_2}/
│   └── {server_name_2}_server.py
└── ...
```

## Selection Criteria

| Factor | Weight | Description |
|--------|--------|-------------|
| Uniqueness | 35% | Not overlapping with existing servers |
| Practicality | 35% | Solves real developer/user problems |
| Doc Quality | 20% | Has official docs with clear examples |
| Simplicity | 10% | Core functionality can be expressed in 3-5 tools |

## Constraints
- No AI-related servers: Exclude LLM APIs, chat completions, embeddings, image generation, or any AI/ML model inference services. Focus on utility APIs (data, productivity, infrastructure, etc.)
- No external HTTP calls in sketch (state-based simulation)
- 3-5 core tools per server (avoid over-design)
- Real API documentation URL required
- Clear, descriptive parameter names
