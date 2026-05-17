Get_User_Provided_Prompt = '''You are an expert AI Agent Architect specializing in Intent Recognition and Slot Filling.

Your Task:
Analyze a list of API parameters (Entities) and determine if each parameter is "User-Provided" within a specific interaction scenario.

The Scenario:
A user sends a natural language message (User Query) to an AI Agent to accomplish a task (e.g., "Book a flight to New York" or "Find python code for sorting"). The Agent needs to call a function/tool to fulfill this request.

Your Goal:
For each entity provided below, answer this binary question:
"Can the value for this parameter be **explicitly and directly** extracted from the words the user typed in their first turn, WITHOUT requiring system lookups, calculations, or context?"

**IMPORTANT: When in doubt, default to `false`. Only mark as `true` if you can confidently point to specific words the user would type.**

{tool_context}

Entities (Index: Name (Type): Description):
{text}

---
### Decision Logic (The "Source of Truth" Test)

Evaluate each entity based on where its data comes from:

**TRUE: Source is the User's Text (Explicit and Direct)**
Return `true` ONLY if the parameter represents information the user *explicitly states* in their natural language input.
* **The "Pointing" Rule:** Can you point to a specific word or phrase in a hypothetical user sentence (e.g., "Search for *apples*") that maps DIRECTLY to this parameter? If yes, it is `true`.
* **Keywords:** Search queries, city names, dates, specific filters, email contents, prompts, user-entered text.
* **Examples:**
    * `q` / `query`: User says "How to cook pasta?" -> True (user explicitly says the query).
    * `destination`: User says "Fly to Paris" -> True (user explicitly says "Paris").
    * `start_date`: User says "Next Monday" -> True (user explicitly mentions the date).
    * `message`: User says "Send this message: Hello" -> True (user explicitly provides message content).
    * `path`: User says "Open the file at path /Users/john/Desktop/example.txt" -> True (user explicitly provides the file path).

**FALSE: Source is System, Context, or Tool (Implicit/Derived/Calculated)**
Return `false` if the parameter requires ANY of the following:
* **Inferable/Secondary Information:** If a parameter implies location or time (like `zipcode`, `timezone`, `country_code`) but is usually derived from a primary input (like `city_name` or `address`), mark it as `false`. Users typically provide the "What" (City), not the "Metadata" (Zipcode).
* **System/Context Lookup:** `user_id`, `session_id`, `api_key`, `current_timestamp`, `auth_token`. (The user *has* an ID, but they don't *type* it in the chat box).
* **Derived/Calculated Data:** `latitude`, `longitude`, `distance`, `price_total`. (User says "Paris", not "48.8566, 2.3522". System calculates these).
* **Tool Outputs:** `search_results`, `page_content`, `image_url`, `file_path`. (This is what the tool *returns*, not what the user *inputs*).
* **Internal Flags/Config:** `is_debug`, `max_retries`, `timeout`, `format`.
* **Database Lookups:** `product_id` (UUID), `order_id` (even if user mentions product name, system must look up the ID).
* **Computed/Inferred Values:** Any value that requires processing, transformation, or inference beyond direct text extraction.

**Examples of FALSE:**
    * `user_id`: User never types their own ID -> False.
    * `latitude` / `longitude`: User says "London", system converts to coordinates -> False.
    * `product_id` / 'item_id' (UUID): User says "Buy the red shoe", system looks up ID -> False.
    * `search_results`: This is tool output, not user input -> False.
    * `current_timestamp`: System generates this, user doesn't type it -> False.
    * `page_number`: User says "next page" but system calculates the number -> False.

---
### Output Format
Return ONLY the raw JSON object mapping indices to booleans. No markdown, no comments.
Example: {{"0": true, "1": false, "2": true}}

Your JSON Output:
'''

Build_Tool_Dependency_Prompt = '''# Role
You are an expert tool relationship analyst specializing in dependency inference.
Your task is to **augment** the current tool dependency graph by adding *only missing, justified directed edges* — **do not remove or modify any existing edges**.

You are given:
1. **Tool Descriptions**: A list of tools, each with name, functional description, and parameters.
2. **Current Adjacency Map**: A dict `tool_name → [list of successor tool names]`, representing *existing* dependencies (Tool A → Tool B means Tool B may depend on or follow Tool A).

# Guidelines
For every *candidate* ordered pair (Tool A → Tool B) **not already present**, assess:
- **Semantic Complementarity**: Do the tools solve parts of a shared task or pipeline? (e.g., preprocessing → analysis)
- **Data Flow Feasibility**: Can outputs (explicit, implicit, or inferred context) from Tool A reasonably inform or enable Tool B's execution?
- **Workflow Plausibility**: Would a rational user *naturally* run Tool B after Tool A in a realistic scenario?
- **Parameter/Context Alignment**: Are parameters, domains, or expected inputs/outputs conceptually aligned—even if naming differs?

# Constraints
- No self-loops (Tool A → Tool A is forbidden).
- Only add edges where Tool A and Tool B are distinct and exist in the tool list.

# Output Schema
Your output must strictly adhere to the following schema without anything else:
<analysis>
[Concise explanation: Summarize key missing relationships you identified and why they're valid. Mention tools involved and justification (semantic/data/workflow). Do *not* critique existing edges.]
</analysis>

<adjacency_map>
{{
    "Tool_A": ["Tool_X", "Tool_Y"], // Only newly added successors (not already in input map). Omit tools with no new edges.
    "Tool_B": ["Tool_Z"],           // Include entry only if at least one new edge is added
}}
</adjacency_map>

# Tool Descriptions
{tool_desc}

# Current Adjacency Map (DO NOT MODIFY EXISTING ENTRIES)
{adjacency_map}
'''

Build_Tool_Chain_Prompt = '''# Role
You are a conversation turn segmentation specialist.
Your task is to analyze sequences of tool calls from multi-turn conversations and identify natural breakpoints between conversation turns.
You will be given a **Tool Call Trace**, which is an ordered list of tools (from various MCP servers) executed in a conversation.

# Segmentation Guidelines
1. Contextual Coherence: Group tools that logically belong together in the same conversational exchange
2. Intent Completion: End a turn when a user's request appears to be completed or when there's a clear shift in focus
3. Natural Dialogue Flow: Consider how a typical conversation would progress with pauses for user input
4. Tool Dependency: Keep tools that are closely dependent on each other in the same turn

# Output Format
<reason>
Your analysis of the tool call trace and reasoning for split turns.
Explain why you placed breakpoints where you did, considering user intent, task completion, and conversation flow.
</reason>

<turn>
[
  [indices_of_tools_in_turn_1],
  [indices_of_tools_in_turn_2],
  [indices_of_tools_in_turn_3],
  ...
]
</turn>

# Output Example
<turn>
[
  [0, 1],
  [2, 3, 4],
  [5]
]
</turn>

# Tool Call Trace
{tool_call_trace}
'''