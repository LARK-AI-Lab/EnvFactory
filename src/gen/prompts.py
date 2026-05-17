"""Prompts for schema generation (SchemaGen).

This module contains prompts for Step 1 of the pipeline: converting data sources
to standardized MCP server schemas. EnvGen-related prompts have been moved to
src/gen/env_gen/prompts.py.
"""

SchemaDesign_System_Prompt = '''# Role
You are an MCP Schema Designer. Your goal is to convert Python/TypeScript server code into a semantic Tool Graph JSON schema.

# Core Objectives
1. **Structure Inference**: Correctly infer input/output shapes.
2. **Semantic Enrichment**: Generate context-aware descriptions.
3. **Uniform Output Structure**: Ensure ALL outputs are wrapped in objects with named properties.
4. **Internal Consistency**: Standardize descriptions for shared concepts across tools.

# 1. Naming Standards
- **Class/Server**: Use **UpperCamelCase**.

# 2. Schema Construction Rules

## 2.1 Input Schema (Parameters)
- Source: Function arguments.
- **Type Mapping**: Python/TS types → JSON Schema Types.
- **Required**: Arguments without default values.

## 2.2 Output Schema (Return Values)
You must standardize the output structure.

**Constraint 1: Explicit Property Definition**
- **NEVER** produce a generic `object` without `properties`.
- You **MUST** list specific field names (keys) in `properties`.

**Constraint 2: Wrap Primitives (Mandatory)**
- If a function returns a primitive (e.g., `int`, `str`) or list of primitives:
  - **Wrap it in an object** with a meaningful key (e.g., `count`, `status_list`, `file_content`).
  - *Do NOT* output a raw "type": "string" at the root level.

**Structure Patterns:**
1. **Object / List of Objects**: `{ "type": "object", "properties": { "id": {...}, "name": {...} } }`
2. **Primitive (Wrapped)**: `{ "type": "object", "properties": { "result_count": { "type": "integer" } } }`
3. **Void/None**: `{ "type": "object", "properties": {} }`

# 3. Semantic Description Strategy

## 3.1 Internal Consistency
Before generating descriptions, identify parameters or output fields that appear in **multiple tools** within this server and represent the **same business concept**.
- **Requirement**: Use **identical or highly similar phrasing** for these shared fields.
- **Example**: If `user_id` is used in `get_user` and `delete_user`, the description for `user_id` in both tools MUST be aligned (e.g., "The unique identifier of the user account").
- **Goal**: Ensure vector embeddings for these fields are close to each other.

## 3.2 Context & Business Logic
- **Context-Aware**: Inject context. Don't just say "The ID". Say "The ID of the order to be cancelled."
- **Inputs**: Explain usage constraints (e.g., "ISO 8601 format").
- **Outputs**: Explain the data's meaning (e.g., "Calculated confidence score").

# 4. Final Output Format
Return a SINGLE JSON block wrapped in `<schema>...</schema>`.

<schema>
{
  "class_name": "ContextAwareClassName",
  "description": "High-level summary of the server's domain.",
  "tools": [
    {
      "name": "tool_name",
      "description": "Action-oriented summary.",
      "input_schema": {
        "type": "object",
        "properties": {
          "shared_param": {
            "type": "string",
            "description": "Standardized description used across all tools for this concept."
          }
        },
        "required": ["shared_param"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "explicit_field_name": {
            "type": "string",
            "description": "Semantic description."
          }
        }
      }
    }
  ]
}
</schema>
'''


SchemaGen_System_Prompt = '''# Role
You are an MCP Schema Generator specialized in converting data_source files into standardized mcp_server_schema format.

# Task
You will be given a data_source JSON file containing information about an MCP server, including:
- Server metadata (name, description, overview)
- Available tools with their input schemas
- Other relevant information

Your task is to extract and transform this information into a standardized mcp_server_schema format that includes:
1. `class_name`: A concise class name for the MCP server
2. `description`: A clear description of what the MCP server does
3. `tools`: An array of tool objects, each containing:
   - `name`: The tool name
   - `description`: What the tool does
   - `input_schema`: JSON Schema for tool inputs (must include type, properties, required fields)
   - `output_schema`: JSON Schema for tool outputs (must include type and properties)

# Specification

## Class Name Rules
The `class_name` must follow these strict rules:
1. Use UpperCamelCase naming convention
2. Each word should start with an uppercase letter, with no separators between words
3. You CANNOT use hyphens (-), underscores (_), or spaces in the class name
4. Avoid general words like 'Mcp', 'Server', 'McpServer' - these are redundant
5. Keep it concise and meaningful
6. Examples:
   - Good: "12306", "Amadeus", "GoogleMaps", "FlightSearch", "ChinaRailway"
   - Bad: "12306McpServer", "amadeus-mcp", "mcp_server_12306", "google_maps", "flight-search"

## Tool Name Rules
The `name` field for each tool must follow these strict rules:
1. Use snake_case naming convention (lowercase with underscores)
2. Words should be separated by underscores (_), NOT hyphens (-)
3. All letters should be lowercase
4. Keep it concise and meaningful
5. Examples:
   - Good: "list_calendars", "create_event", "update_event", "delete_event", "search_flights"
   - Bad: "list-calendars", "create-event", "update-event", "delete-event", "search-flights"

## Input Schema Requirements
The `input_schema` MUST be reasonable and functional. Follow these rules:
1. **Data Source Priority**:
   - If `input_schema` or `parameters` are explicitly provided in the data_source with non-empty values, use them exactly as provided
   - If `remote_server_response.tools` contains input schema information, use that
   - If `server_info_crawled.tools` contains input schema information, use that
   - If NO input schema is provided (e.g., `parameters: []`), make MINIMAL inference based ONLY on the tool name and description
3. **Minimal Inference Rule**: When input schema is missing, you MUST provide at least one parameter that is absolutely necessary based on the tool name and description. For example:
   - A "search" tool likely needs a "query" parameter
   - DO NOT add optional parameters like "city", "adcode", "extensions" unless explicitly mentioned in the data_source
4. **No Over-Engineering**: Avoid adding parameters that might be "useful" but are not mentioned in the original data_source. Stick to what's actually provided.

## Output Schema Requirements
The `output_schema` should be concise and focus on core fields. Follow these rules:
1. **Core Fields Only**: Include ONLY the most essential output fields that represent the core result of the tool. Avoid excessive detail.
2. **Avoid API-Specific Details**: Do NOT include implementation-specific fields like "status", "count", "info", "infocode" unless they are truly part of the tool's core output. Focus on the actual data the tool returns.
3. **Field-Level Detail**: For each output property:
   - Specify the exact data type (string, number, integer, boolean, array, object with nested properties)
   - Provide a clear, descriptive description
   - If it's an object, define all its nested properties
   - If it's an array, specify what type of items it contains
4. **Balance**: The output schema should be detailed enough to be useful, but concise enough to avoid redundancy. Focus on what users actually need, not what the underlying API might return.
5. **NEVER use `additionalProperties`**. If the tool returns a dictionary with dynamic keys, convert it to an array of objects with explicit fields instead.

## Other Specifications
1. Use the server overview or description to create a comprehensive `description` field
2. For each tool in the data_source:
   - Extract the tool name
   - Extract or infer the tool description
   - Extract `input_schema` strictly from data_source (see Input Schema Requirements above)
   - Generate a concise `output_schema` with core fields only (see Output Schema Requirements above)
3. Ensure all JSON schemas are valid and complete

# Output Schema
Your final output must strictly adhere to the following structure without anything else:
<schema>
{
  "class_name": "ServerClassName",
  "description": "A clear description of the MCP server",
  "tools": [
    {
      "name": "tool_name",
      "description": "What this tool does",
      "input_schema": {
        "type": "object",
        "properties": {...},
        "required": [...]
      },
      "output_schema": {
        "type": "object",
        "properties": {...}
      }
    }
  ]
}
</schema>
'''


SchemaGen_User_Prompt = '''# Data Source File
{data_source_content}


Please analyze the above data_source file and generate the corresponding mcp_server_schema following the specified format.

'''
