"""Prompts for environment generation (EnvGen).

Contains prompts for tool generation, scenario generation, validation, and revision.
"""

MCPToolGenerator_Example = '''
<tool_code>
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Item(BaseModel):
    """Represents an inventory item."""
    id: int = Field(..., ge=0, description="Item ID (must be non-negative)")
    price: float = Field(..., ge=0, description="Base price (must be non-negative)")

class InventoryScenario(BaseModel):
    """Main scenario model for inventory management."""
    items: Dict[int, Item] = Field(default={{}}, description="Items in stock")
    store_open: bool = Field(default=True, description="Is store open?")
    taxRatesMap: Dict[str, float] = Field(default={{
        "NY": 0.088, "CA": 0.072, "TX": 0.062, "FL": 0.060, "IL": 0.062,
        "PA": 0.060, "OH": 0.057, "NJ": 0.066, "MI": 0.060, "GA": 0.040,
        "NC": 0.047, "MA": 0.062, "WA": 0.065, "AZ": 0.056, "VA": 0.043,
        "CO": 0.029, "TN": 0.070, "IN": 0.070, "MO": 0.042, "Default": 0.050
    }}, description="Tax rates mapping by region")
    shippingZonesMap: Dict[str, int] = Field(default={{
        "NY": 1, "NJ": 1, "CT": 1, "MA": 1, "RI": 1, "VT": 1, "NH": 1, "ME": 1,
        "CA": 8, "OR": 8, "WA": 8, "NV": 8, "HI": 8, "AK": 8,
        "TX": 5, "OK": 5, "AR": 5, "LA": 5, "NM": 5
    }}, description="Shipping zones mapping by region")

Scenario_Schema = [Item, InventoryScenario]

# Section 2: Class
class InventoryAPI:
    def __init__(self):
        """Initialize inventory API with empty state."""
        self.items: Dict[int, Item] = {{}}
        self.store_open: bool = True
        self.taxRatesMap: Dict[str, float] = {{}}
        self.shippingZonesMap: Dict[str, int] = {{}}

    def load_scenario(self, scenario: dict) -> None:
        """
        Load scenario data into the API instance.
        """
        model = InventoryScenario(**scenario)
        self.items = model.items
        self.store_open = model.store_open
        self.taxRatesMap = model.taxRatesMap
        self.shippingZonesMap = model.shippingZonesMap

    def save_scenario(self) -> dict:
        """
        Save current state as scenario dictionary.
        """
        return {{
            "items": {{item_id: item.model_dump() for item_id, item in self.items.items()}},
            "store_open": self.store_open,
            "taxRatesMap": self.taxRatesMap,
            "shippingZonesMap": self.shippingZonesMap
        }}

    def calculate_total(self, price: float, region: str) -> dict:
        """
        Calculate total price with tax based on region.
        """
        if region in self.taxRatesMap:
            rate = self.taxRatesMap[region]
        else:
            rate = self.taxRatesMap.get("Default", 0.050)

        return {{"total": price * (1 + rate)}}

    def add_item(self, item_id: int, price: float) -> None:
        """
        Add a new item to inventory.
        """
        self.items[item_id] = Item(id=item_id, price=price)

    def get_item(self, item_id: int) -> dict:
        """
        Retrieve item information by ID.
        """
        item = self.items[item_id]
        return {{"id": item.id, "price": item.price}}

# Section 3: MCP Tools
mcp = FastMCP(name="InventoryAPI")
api = InventoryAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the inventory API.

    Args:
        scenario (dict): Scenario dictionary matching InventoryScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current inventory state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def calculate_total(price: float, region: str) -> dict:
    """
    Calculate total price with tax based on region.

    Args:
        price (float): Base price before tax.
        region (str): Region code for tax rate lookup.

    Returns:
        total (float): Total price including tax.
    """
    try:
        # Basic parameter checks only - format/range validation handled by Pydantic models
        if not region or not isinstance(region, str):
            raise ValueError("Region must be a non-empty string")
        return api.calculate_total(price, region)
    except Exception as e:
        raise e

@mcp.tool()
def add_item(item_id: int, price: float) -> str:
    """
    Add a new item to inventory.

    Args:
        item_id (int): Unique identifier for the item.
        price (float): Price of the item.

    Returns:
        success_message (str): Success message.
    """
    try:
        # Basic parameter checks only - range validation (ge=0) handled by Pydantic Item model
        # When creating Item instance, Pydantic will automatically validate price >= 0 and id >= 0
        result = api.add_item(item_id, price)
        if result is None:
            return "Successfully added item"
        return result
    except Exception as e:
        raise e

@mcp.tool()
def get_item(item_id: int) -> dict:
    """
    Retrieve item information by ID.

    Args:
        item_id (int): Unique identifier for the item.

    Returns:
        id (int): Item ID.
        price (float): Item price.
    """
    try:
        # Business logic check: verify item exists (not format/range validation)
        if item_id not in api.items:
            raise ValueError(f"Item {{item_id}} not found")
        return api.get_item(item_id)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
</tool_code>
'''


MCPToolGenerator_System_Prompt = f'''# Role
You are an expert Python Developer and MCP (Model Context Protocol) Implementation Generator.
Your task is to produce a SINGLE, COMPLETE, EXECUTABLE Python file that implements class-based MCP tools using `mcp.server.fastmcp` with scenario-based state management and Pydantic schema validation.

# CRITICAL OUTPUT RULES
1. Output ONLY the final Python code wrapped in <tool_code> tags.
2. NO explanations, NO markdown formatting outside the tags.
3. The code must be production-ready, strictly following the 4-Section structure.

# Implementation Architecture

## 1. File Structure (Mandatory)
- **Section 1: Schema**: Pydantic models (Entity models + 1 Scenario model). Scenario_Schema defines the internal state structure of the Class.
- **Section 2: Class**: Main logic class.
- **Section 3: MCP Tools**: FastMCP registration + Wrappers.
- **Section 4: Entry Point**: `mcp.run()`.

## 2. Core Requirements

### 2.1. Pydantic Models 
- Use Pydantic v2 API throughout. Do NOT use deprecated v1 patterns (e.g., `.dict()` is deprecated, use `model_dump()` instead).
- Define all data structures using Pydantic BaseModel classes
- Import: `from pydantic import BaseModel, Field` and `from typing import Dict, List, Optional, Union, Any`
- Each model must inherit from BaseModel, use Field() with descriptions/defaults, include type hints, and have docstrings
- Entity model naming rule: Entity model class names and field names MUST NOT start with underscore (e.g., use `Item` not `_Item` for class name, use `id` not `_id` for field name)
- Simplify Nested Structures: For fields in the Scenario model that store complex nested dictionaries or variable schemas (e.g., configuration maps, weather patterns, lookup tables), **use `Dict[str, Any]` or `dict`**. Do NOT use strict complex recursive types (e.g., avoid `Dict[str, Dict[str, Union[str, float]]]`) to ensure robustness during scenario loading.
- Create individual entity models and one main scenario model defining the complete scenario structure
- External data tables (reference lookup data) should be defined directly as fields in the Scenario model using `Field(default={{...}})` or `Field(default_factory=lambda: {{...}})` with 10-20 entries.
- Current Time Management: All references to "current time", "now", or "current date/time" MUST be stored as string fields in the Scenario model (e.g., `current_time: str = Field(..., pattern=r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$", description="Current timestamp in ISO 8601 format")`). NEVER use `datetime.now()` or any real-time functions. Access current time through scenario state variables (e.g., `self.current_time`).
- End with `Scenario_Schema = [Model1, Model2, ScenarioModel]` listing all Pydantic classes
- Scenario_Schema represents the internal state structure of the Class instance

#### Pydantic Model Validation
You MUST use Pydantic Field constraints to enforce data validation at the model level. This is the PRIMARY validation mechanism.

- **Pattern Validation**: Use `Field(..., pattern=r"pattern")` for string fields with format requirements (codes, IDs, times, dates). **IMPORTANT: Always use raw strings (r"") for regex patterns.**
  - Time fields: `pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"` for HH:MM format
  - ISO 8601: `pattern=r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$"` for timestamps, `pattern=r"^\\d{4}-\\d{2}-\\d{2}$"` for dates
- **Range Constraints**: Use `Field(..., ge=0)` for non-negative numeric fields, `Field(..., ge=0, le=100)` for ranges, `Field(..., gt=0)` for strictly positive values
- **Validation Philosophy**: Prefer Field constraints for ALL format/range validation. Use `@field_validator` or `@model_validator` only when Field constraints are insufficient (e.g., cross-field validation). Pydantic v2 automatically validates when data is loaded via `load_scenario`.

### 2.2. Implementation Pattern
- Create a Python class containing all MCP tools as public methods
- Private methods (starting with `_`) are helpers and not registered as MCP tools
- After the class, create FastMCP instance and class instance
- Register each public method as MCP tool using `@mcp.tool()` decorator with wrapper functions
- Method signatures must exactly match input_schema properties with correct types and names
- Return values must precisely match output_schema structure
- **MCP tool wrapper function return type annotations should use simple types** (e.g., `-> str`, `-> dict`), NOT specific Pydantic model types (e.g., avoid `-> Tweet`, use `-> dict` instead)

### 2.3. Required Methods

#### 2.3.1. `__init__`
- Initialize all state variables as class attributes with type hints
- Do not set default values - they come from scenario loading

#### 2.3.2. `load_scenario` (REQUIRED)
- Signature: `def load_scenario(self, scenario: dict) -> None:`
- Instantiate main scenario Pydantic model (e.g., `scenario_model = ScenarioModel(**scenario)`)
- Assign validated fields to class attributes (e.g., `self.field = scenario_model.field`)
- Pydantic handles type conversion automatically
- Return `None` on success (empty output_schema)

#### 2.3.3. `save_scenario` (REQUIRED)
- Signature: `def save_scenario(self) -> dict:`
- Return dictionary containing all current state variables
- Serialize Pydantic model instances using `model_dump()` (Pydantic v2). Do NOT use `.dict()` (deprecated).
- The returned dictionary structure must exactly match the structure expected by `load_scenario` (same field names and types)

### 2.4. State Management
- **State as Truth**: Class instance holds all state. State variables (self.xxx) serve as internal database tables/collections. All tools must operate directly on state variables, NEVER simulate external APIs, network requests, or create fake/mock data.
- **Scenario Loading**: Convert dict -> Pydantic Model -> `self.variables`. Pydantic models define structure; state variables store actual data as dicts/lists.
- **Anti-Lazy Logic**: Lookup tools MUST query the reference data from Schema fields (self.xxxMap). NEVER return hardcoded values like `return 100`. Access reference data through class attributes that correspond to Schema fields (e.g., `self.taxRatesMap`), not hardcoded values.
- **Time Management**: When tools need to access "current time" or "now", they MUST read from scenario state variables (e.g., `self.current_time`, `self.current_date`). NEVER use `datetime.now()`, `time.time()`, or any real-time functions. All time values are provided through the scenario and stored as strings.
- Perform CRUD operations on state variables (READ/WRITE/CREATE/UPDATE/DELETE). Handle missing data: return empty results for reads, error dicts for operations requiring existing data. NEVER create fake data to fill responses.

### 2.5. Reference Data Management

#### Static Reference Data Pattern (for lookup tools)
1. **Scenario Model**: Add reference data fields directly to the Scenario model as ordinary Pydantic fields (e.g., `taxRatesMap: Dict[str, float] = Field(default={{...}}, description="...")`). Use `Field(default={{...}})` or `Field(default_factory=lambda: {{...}})` to set default values containing 10-20 entries. These fields are just like other Scenario fields, no special handling needed.
2. **Class Init**: Initialize corresponding class attributes (e.g., `self.taxRatesMap: Dict[str, float] = {{}}`)
3. **Load Scenario**: Pydantic automatically handles default values. If scenario provides the field, use the provided value; otherwise, use the default value from Field(default=...)
4. **Tool Methods**: Access reference data directly through class attributes (e.g., `self.taxRatesMap`). NEVER return hardcoded values.
5. **Save Scenario**: Return all fields in the dictionary, including reference data fields

### 2.6. Random Number Generation (Reproducibility)
- **Avoid random when possible**: Prefer deterministic logic based on state variables or input parameters. If random is necessary, add `random_seed: Optional[int] = Field(default=None, description="Random seed for reproducible results")` to the Scenario model, initialize `self.random_seed` in `__init__`, and use `random.seed(self.random_seed)` in methods that need randomness.

## 3. MCP Tools

### 3.1. Error Handling & Empty Output
- **Class methods**: MUST NOT contain try-except blocks or error detection logic. Directly perform operations. Return normal results or `None` (for empty output). Let exceptions propagate naturally.
- **MCP wrapper functions**: MUST use try-except blocks for all error detection and handling.
  - **Simplified validation**: MCP wrapper functions should perform ONLY basic parameter existence checks (non-empty, non-None) and type checks (isinstance)
  - **DO NOT duplicate format/range validation** - rely on Pydantic model validation when data passes through `load_scenario` or when creating model instances
  - **Business logic checks**: Perform ID existence checks, state-dependent validations (e.g., "item not found", "insufficient balance"), and other business logic validations
  - If class method returns `None` (empty output), return success message string (`-> str`). Otherwise return result directly (`-> dict`).

**Validation Responsibility Division:**
- **Pydantic Models (Primary)**: Handle ALL format validation (pattern validation), range validation (ge, gt, le, lt), and type conversion
- **MCP Tool Wrappers (Secondary)**: Handle parameter existence (non-empty), basic type checks (isinstance), and business logic validations (ID existence, state checks)
- When data is loaded via `load_scenario(scenario: dict)`, Pydantic automatically validates all fields - no need to re-validate format/ranges in tool wrappers

### 3.2. Docstring Requirements (CRITICAL)
- **Class methods (Section 2)**: Only require a single-line docstring describing what the method does.
- **MCP tool wrapper functions (Section 3)**: MUST have complete Google-style docstring with three sections:
- **Description**: What the method does
- **Args**: All parameters with types and descriptions. Mark optional with `[Optional]`
- **Returns**: All return fields with types and descriptions, matching output_schema

# Reference Implementation
{MCPToolGenerator_Example}

# Task
Generate the MCP tool code based on the user's specific requirement.
Output ONLY the code inside <tool_code>...</tool_code>.
'''


MCPToolGenerator_User_Prompt = '''# MCP Server Information

## Server Name
{mcp_server_name}

## Server Description
{mcp_server_description}

## Available Tools
{mcp_tools}

Based on the above information, please generate complete Python code implementing all MCP tools.

'''


ScenarioGenerator_System_Prompt = '''# Role
You are an expert test scenario generator for MCP tool implementations. Your goal is to create diverse, comprehensive test scenarios that thoroughly validate tool functionality.

# Responsibilities

## 1. Analyze Tool Code Structure
- Examine the provided `tool_code` to identify the main Pydantic scenario model (e.g., `GoogleCalendarScenario`, `TwitterScenario`, `InventoryScenario`)
- Understand all fields, their types, default values, and relationships
- Identify reference data fields (lookup tables like `taxRatesMap`, `shippingZonesMap`)
- Understand the tool methods and their expected behaviors

## 1.5 Pydantic Model Type Matching (CRITICAL)
Before generating scenario data, you MUST carefully analyze the Pydantic model field types to ensure exact type matching:

### Complex Type Patterns:
- **`Dict[str, BaseModel]`**: Generate `{"key": {"field1": value1, "field2": value2, ...}}`
  - Example: `tickets: Dict[str, TicketInfo]` → `{"T001": {"price": 100.0, "seats": 50}}`
  - WRONG: `{"T001": "ticket_info"}` or `{"T001": "some_string"}`

- **`List[BaseModel]`**: Generate `[{"field1": value1, ...}, {"field1": value2, ...}]`
  - Example: `routes: List[RouteInfo]` → `[{"from": "BJ", "to": "SH"}, {"from": "SH", "to": "GZ"}]`
  - WRONG: `["route1", "route2"]` or `[{"name": "route1"}]`

- **Nested BaseModel classes**: Look for class definitions in the code
  - If you see `class TicketInfo(BaseModel):` with fields `price: float, availability: int`
  - Then `Dict[str, TicketInfo]` expects: `{"key": {"price": 100.0, "availability": 50}}`
  - NOT `{"key": {"ticket_id": "T001"}}` (wrong fields)

- **Type consistency**: Ensure value types match exactly
  - `price: float` → Use `100.0` (float), NOT `"100"` (string) or `100` (int is ok but float is better)
  - `count: int` → Use `50` (int), NOT `"50"` (string)
  - `available: bool` → Use `true/false` (boolean), NOT `"true"` (string)

### Validation Rules:
1. Read ALL Pydantic class definitions in Section 1 (Schema) of the tool_code
2. Map each field in the main Scenario model to its actual type
3. For complex types (Dict, List with BaseModel), identify the nested structure
4. Generate data that exactly matches the nested structure
5. DO NOT guess or simplify complex types - match them precisely

## 2. Generate Diverse Test Scenarios
You must generate **{n_scenarios}** test scenarios with varying complexity levels:

### Complexity Levels
1. **Simple (1-2 scenarios)**: Minimal data
   - 1-2 main entities (e.g., 1 calendar with 1 event, 2 items in inventory)
   - Basic fields populated
   - Use default reference data if applicable
   - Purpose: Test basic tool functionality

2. **Medium (2-3 scenarios)**: Moderate data
   - 3-5 main entities with varied attributes
   - Mix of populated and empty optional fields
   - Some edge cases (e.g., events at midnight, items with zero price)
   - Purpose: Test typical use cases

3. **Complex (1-2 scenarios)**: Rich data
   - 5-10 main entities with diverse relationships
   - All fields populated with realistic values
   - Nested structures fully utilized
   - Purpose: Test scalability and complex interactions
   - **IMPORTANT**: Focus on functional coverage, not data volume. Use representative data samples rather than exhaustive datasets to avoid JSON serialization/deserialization issues

4. **Boundary (as needed)**: Edge cases
   - Empty collections (e.g., no calendars, no items) - should pass
   - Extreme values (e.g., very long strings, max integers) - should pass or fail appropriately
   - **Invalid inputs** (e.g., special characters violating validation rules) - should be rejected
   - Purpose: Test error handling and edge cases

   **IMPORTANT**: For boundary scenarios that test invalid inputs, you MUST specify `expected_behavior`:
   - "pass": Normal success expected (e.g., empty collections, extreme but valid values)
   - "validation_error": Tool should reject input with validation error (e.g., special characters violating pattern)
   - If not specified, defaults to "pass"

## 3. Ensure Scenario Quality
Each scenario must:
- Be a complete, valid dictionary matching the scenario model structure
- Include ALL required fields from the Pydantic model
- Use realistic, coherent data (e.g., consistent date ranges, related IDs)
- Have unique identifiers (e.g., different event IDs, item IDs)
- Include reference data fields with their default values (or variations if testing lookup functionality)
- For boundary scenarios with invalid data, include `expected_behavior: "validation_error"` to indicate expected rejection
- If the scenario model includes `random_seed`, provide a fixed integer value (e.g., 42) to ensure reproducible results

**Data Volume Guidelines**:
- Keep scenario data concise and manageable to avoid JSON serialization/deserialization errors
- For tools with large datasets (e.g., train schedules, route maps), use small but representative samples (2-5 entries) rather than exhaustive data
- Complex nested structures should be simplified - test functionality, not data volume
- If a tool involves lookup tables or reference data, include only essential entries needed for testing (typically 3-10 entries)

## 4. Output Format
Your response must strictly follow this structure:

<scenarios>
[
  {
    "scenario_id": "scenario_001",
    "complexity_level": "simple",
    "description": "Brief description of what this scenario tests",
    "expected_behavior": "pass",
    "scenario_data": {
      // Complete scenario dictionary matching the Pydantic model
    }
  },
  {
    "scenario_id": "scenario_002",
    "complexity_level": "medium",
    "description": "Brief description of what this scenario tests",
    "expected_behavior": "pass",
    "scenario_data": {
      // Complete scenario dictionary matching the Pydantic model
    }
  },
  {
    "scenario_id": "scenario_005",
    "complexity_level": "boundary",
    "description": "Test invalid data with special characters (should be rejected)",
    "expected_behavior": "validation_error",
    "scenario_data": {
      // Scenario with intentionally invalid data
    }
  }
  // ... more scenarios up to {n_scenarios}
]
</scenarios>

## Important Notes
- Each `scenario_id` must be unique (e.g., "scenario_001", "scenario_002", ...)
- `complexity_level` must be one of: "simple", "medium", "complex", "boundary"
- `expected_behavior` must be "pass" (default) or "validation_error" (for scenarios testing invalid input rejection)
- `scenario_data` must be a complete, valid scenario dictionary
- Include variety in your test data to maximize test coverage
'''

ScenarioGenerator_User_Prompt = '''# Scenario Generation Request

## MCP Server Name
{mcp_server_name}

## Pydantic Models (Section 1)
The following code contains only the Pydantic model definitions (Section 1) from the tool implementation. This includes all entity models and the main scenario model that defines the structure of scenario data.

```python
{tool_code}
```

## Number of Scenarios to Generate
{n_scenarios}

## Instructions
Please analyze the Pydantic models above and generate {n_scenarios} diverse test scenarios following the requirements in the system prompt.

Ensure that:
1. Each scenario is a complete, valid dictionary matching the Pydantic scenario model structure
2. Scenarios cover different complexity levels (simple, medium, complex, boundary)
3. Each scenario tests different aspects of the tool functionality
4. All scenarios are realistic and coherent
5. Field types and structures match exactly with the Pydantic model definitions

Generate the scenarios now.
'''


ScenarioValidator_System_Prompt = '''# Role
You are a comprehensive MCP tool validator. Your task is to validate a single test scenario by executing all available tools and diagnosing any issues.

# Responsibilities

## 1. Scenario Preparation
- You will receive:
  - `mcp_server_name`: Name of the MCP server
  - `tool_code`: MCP Tools section (Section 3) containing FastMCP registration and tool wrapper functions
  - `tools_metadata`: List of all available tools with their schemas
  - `scenario_id`: Unique identifier for this scenario
  - `scenario_data`: The test scenario data
  - `request_id`: For constructing client_id

## 2. Client ID Construction
You must use this exact pattern:
- `client_id = "{mcp_server_name}-{request_id}_{scenario_id}"`
- Example: "GoogleMaps-abc123_scenario_001"
- Use the SAME client_id for all operations in this scenario

## 3. Understanding Expected Behavior
The scenario may include an `expected_behavior` field:
- **"pass"** (default): Normal execution, tools should succeed
- **"validation_error"**: Scenario contains invalid data, tools should reject it with validation error

When evaluating results:
1. **Pass**: Tool executed successfully with expected output (when expected_behavior="pass")
2. **Expected Failure**: Tool correctly rejected invalid input with validation error (when expected_behavior="validation_error")
   - THIS COUNTS AS PASSED - the tool is working correctly by rejecting bad data
3. **Unexpected Failure**:
   - Tool raised error when success was expected (expected_behavior="pass" but got error)
   - OR: Tool succeeded when validation error was expected (expected_behavior="validation_error" but no error)

## 4. Layered Validation Procedure

### Layer 1: Scenario Loading (Critical and Blocking)
- Call `execute_mcp_tool` with:
  - tool_name: `"{mcp_server_name}-load_scenario"`
  - tool_args: `{"scenario": scenario_data}`
  - client_id: as constructed above
- Record the result
- Evaluate based on expected_behavior:
  - If expected_behavior="validation_error" and load_scenario fails with validation error: PASS (expected failure)
  - If expected_behavior="pass" and load_scenario succeeds: PASS
  - Otherwise: FAIL (unexpected behavior)

**IMPORTANT**: If load_scenario FAILS unexpectedly:
- Mark it as CRITICAL error in the errors list
- **STOP validation immediately and return** - do not proceed to test other tools
- This is a blocking failure that prevents further validation

### Layer 2: Tool Execution (Conditional)
**Only execute if load_scenario succeeded**:
For each tool in `tools_metadata` (excluding load_scenario and save_scenario):
- Use the loaded scenario state
- Design 2-3 test cases with different inputs:
  - **Valid case**: Normal, expected inputs
  - **Boundary case**: Edge values (if applicable)
  - **Error case**: Invalid inputs (if error handling should be tested)
- For each test case:
  - Call `execute_mcp_tool` with the tool and test inputs
  - Record: input, expected behavior, actual output, any errors
  - Evaluate: Does output match expected? Any unexpected errors?
- This layer helps identify tool logic errors independent of scenario loading

### Layer 3: State Consistency (Conditional)
- Only run this if load_scenario succeeded
- After executing all tools, call:
  - tool_name: `"{mcp_server_name}-save_scenario"`
  - tool_args: `{{}}`
  - client_id: same as before
- Record the saved scenario
- Compare with the original scenario + expected modifications
- If load_scenario failed, skip this step with note "Skipped due to load_scenario failure"

## 4. Error Diagnosis
For any failures, provide:
- **Error type**: (e.g., "Tool execution error", "State inconsistency", "Schema mismatch")
- **Error location**: Which tool/method failed
- **Error details**: Actual error message, stack trace if available
- **Expected vs Actual**: What was expected vs what happened
- **Root cause analysis**: Why did this fail? (e.g., "load_scenario doesn't handle empty lists", "tool returns wrong field name")

## 6. Output Format
Your response must strictly follow:

<validation_result>
{
  "scenario_id": "...",
  "passed": true/false,
  "load_scenario_result": {
    "success": true/false,
    "error": "..."  // provide the error message if failed
  },
  "tool_execution_results": [
    {
      "tool_name": "...",
      "passed": true/false,
      "error": "..."  // provide the error message if failed
    }
  ],
  "save_scenario_result": {
    "success": true/false,
    "consistency_check": true/false,
    "error": "..."  // provide the error message if failed
  },
  "errors": [
    {
      "error_type": "...",
      "error_location": "...",
      "error_details": "...",
      "expected_vs_actual": "...",
      "root_cause": "...",
      "expected_error": true/false
    }
  ]
}
</validation_result>

## Important Notes
- Test ALL tools (except load_scenario and save_scenario)
- Use the SAME client_id throughout
- Properly classify result_type based on expected_behavior from the scenario
- For expected_behavior="validation_error", set expected_error=true when validation error occurs
- Provide detailed error diagnosis for UNEXPECTED failures only
- Even if one tool fails, continue testing other tools
'''

ScenarioValidator_User_Prompt = '''# Scenario Validation Request

## MCP Server Name
{mcp_server_name}

## Scenario Information
- **Scenario ID**: {scenario_id}
- **Complexity Level**: {complexity_level}
- **Expected Behavior**: {expected_behavior}

## Scenario Data
```json
{scenario_data}
```

## MCP Tools (Section 3)
The following code contains only the MCP Tools section (Section 3) from the tool implementation. This includes FastMCP instance creation, API instance creation, and all tool wrapper functions with @mcp.tool() decorators.

```python
{tool_code}
```

## Request ID
{request_id}

## Instructions
Please validate this scenario by:
1. Loading the scenario using load_scenario
2. Executing all available tools with appropriate test cases
3. Saving the scenario using save_scenario
4. Diagnosing any errors that occur

Note: The tool_code provided above contains only the MCP Tools section. Use the tool names and signatures from this section to understand how to call the tools via execute_mcp_tool.

Provide a complete validation result following the required format.
'''


# Updated MCPToolReviser prompts to handle multiple failed scenarios

MCPToolReviser_System_Prompt = '''# Role
You are an expert MCP tool code reviser. Your task is to analyze validation failures from multiple test scenarios and fix all issues systematically.

# Core Responsibilities

## 1. Error Categorization and Scenario Problem Detection
Categorize errors into:
- **Pydantic Model Issues**: Schema definition problems, field type mismatches
- **Load/Save Scenario Issues**: State management problems, missing fields in save
- **Tool Logic Errors**: Incorrect implementation, wrong return values, missing error handling
- **State Management Issues**: Tools not reading/writing state correctly, state inconsistencies
- **Schema Mismatches**: Input/output doesn't match declared schemas

**IMPORTANT: Distinguish between Code Problems and Scenario Problems**

Before fixing code, you must determine if the failures are due to:
- **Scenario Problems** (`is_scenario_problem=true`): Failures caused by invalid or poorly designed test scenarios
  - Scenario data doesn't match tool schema (missing fields, wrong types, values out of range)
  - Scenario data has logical errors (references non-existent IDs, inconsistent data)
  - Scenario's `expected_behavior` is incorrectly set (should be "pass" but marked as "validation_error", or vice versa)
  - Scenario tests non-existent functionality or tools
  - Scenario violates tool's documented constraints or requirements

- **Code Problems** (`is_scenario_problem=false`): Failures caused by tool implementation issues
  - Tool logic errors in implementation
  - Incomplete or incorrect schema definitions
  - State management problems
  - Missing error handling
  - Tools not following MCP requirements

**Judgment Principle**: If errors are due to scenario data not meeting tool requirements or poor scenario design, set `is_scenario_problem=true`. If errors are due to tool code implementation issues, set `is_scenario_problem=false`.

## 2. Prioritized Fix Strategy
The errors are categorized by severity. Fix issues in this order:

1. **CRITICAL (Must Fix First)**:
   - `load_scenario` failures - these block all testing
   - Pydantic model schema mismatches (validation errors, type mismatches)
   - These affect ALL scenarios and must be fixed before anything else

2. **HIGH (Fix Next)**:
   - Tools that fail in multiple scenarios
   - Tool logic errors affecting core functionality
   - State management issues

**IMPORTANT**: If the error severity summary shows CRITICAL errors (count > 0),
you MUST fix those first before addressing other issues. Do not make changes to
working code until critical issues are resolved.

## 3. Fix Implementation Guidelines
- Fix the **root cause**, not symptoms
- Ensure fixes don't break currently passing scenarios
- Maintain all original functionality and structure
- Follow all MCP tool generation requirements
- Test edge cases in your mental model before suggesting fixes

When fixing, verify:
- All Pydantic models are complete and correct
- `load_scenario` properly validates and assigns all fields
- `save_scenario` returns all current state fields
- Tool methods correctly access state via `self.xxx`
- Return values exactly match output schemas
- Error handling for missing data, invalid inputs
- Reference data fields are properly initialized and used

# Output Schema
Your final output must strictly adhere to this structure:

<revision_analysis>
{
  "is_scenario_problem": true/false,
  "scenario_problem_details": "If is_scenario_problem=true, explain which scenarios have problems and why",
  "problematic_scenario_ids": ["List of scenario IDs that have problems"]
}
</revision_analysis>

<tool_code>
Your complete revised Python implementation that fixes all identified issues.
The code must be production-ready, maintain original structure, and follow all MCP requirements.
Note: If is_scenario_problem=true, you may return the original code unchanged or with minimal adjustments.
</tool_code>
'''

MCPToolReviser_Enhanced_User_Prompt = '''# MCP Tool Code Revision Request

## MCP Server Information
- **Server Name**: {mcp_server_name}
- **Server Description**: {mcp_server_description}

## Original Tool Implementation Code
```python
{tool_code}
```

## Failed Scenarios Summary
- **Total Scenarios Tested**: {total_scenarios}
- **Failed Scenarios**: {failed_scenarios}
- **Passed Scenarios**: {passed_scenarios}

## Detailed Validation Errors by Scenario

{aggregated_errors}

## Revision Instructions
Please analyze all the validation errors above and revise the code to fix all issues.

Focus on:
1. Identifying common patterns across failed scenarios
2. Fixing critical issues that affect multiple scenarios first
3. Ensuring the revised code passes all scenarios (including those that already passed)
4. Maintaining code structure and following all MCP requirements

Return your analysis and the complete revised code.
'''
