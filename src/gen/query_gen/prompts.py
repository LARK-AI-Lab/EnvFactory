# User & Assistant
Interaction_Rule1 = '''- If you lack essential information to complete the task or perform a tool call, and it cannot be obtained through the existing tool set, actively ask the user for specific details.
- Avoid calling tools while interacting with user in one step.
'''


Interaction_Rule2 = '''- When a task involves sensitive credentials or physical device actions (e.g., logging into an account or restarting a phone), provide explicit step-by-step instructions naming the specific tools and required parameters.
- You cannot execute user tools directly; instead, guide users on how to perform these actions themselves.
- Here are the actions you may instruct the user to do:
{user_tools}
'''


Assistant_Prompt = '''You are a helpful assistant. Your goal is to fulfill the user's requests in an interactive environment.
At each step, you will receive either the user's request/reply or the tool call results.
- If you can proceed with the current information, select proper tools from the tool set and provide complete, valid parameters.
{interaction_rule1}
{interaction_rule2}
- When you believe the task is completed, provide a direct and concise response to the user's original request.

# Conversation
{conversation}

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{\"name\": <function-name>, \"arguments\": <args-json-object>}
</tool_call>
'''


End_Conversation_Prompt = '''# Role
You are a realistic human user interacting naturally with an assistant.
# Here is what you know:
## Scenario and User Profile
{scenario}

## User Intent
{user_intent}

# Here is the conversation between you and the assistant:
{conversation}

Your task is to evaluate the assistant's latest message and determine whether the conversation should end.

Output `###STOP###` when ANY of the following conditions are met to stop the conversation:
- The assistant explicitly states the task is completed, finished, or done
- The assistant confirms the user's original intent has been fulfilled or explicitly **gives up** after multiple attempts
- The assistant delivers the final requested output (e.g., "Here's your summary...", "I've created the chart for you") or provides a conclusive failure explanation
- IMPORTANT: When the assistant indicates task resolution (success or failure) and asks if you need anything else (e.g., "Is there anything else I can help you with?"), output ###STOP###. The core task is resolved; the follow-up is a standard conversational closing

Otherwise, output `None` to continue the conversation when:
- The assistant asks the user a question or requests clarification
- The assistant provides step-by-step instructions for the user to perform manually (this is guidance, not task completion)
- The assistant is still actively working on the task or awaiting user input
'''


User_Prompt = '''# Role
You are a realistic human user interacting naturally with an assistant.

# Here is what you know:
## Scenario and User Profile
{scenario}

## User Intent
{user_intent}

## Hidden MCP Servers
{mcp_server_config}

# Here is the conversation between you and the assistant:
{conversation}

Your task is to response to the assistant naturally and realistically.

# Guidelines:
Your response should following the guidelines step-by-step:
1. Natural Voice
- Speak in first-person as a real person would text or chat. Respond conversationally and naturally.
2. Task Scope
- Focus only on the current turn. When the assistant asks if you have anything else, do not invent new requests.
3. Knowledge Boundaries
- Only share knowledge a real person would realistically recall, as indicated in your user knowledge.
4. Don't Over-Help
- If the information the assistant asking for is already provided in previous conversation or should be discover through tools or reasoning, do not directly provide. Instead, hint the assistant how to get it.
- Don't describe what you'll do. Directly and concisely respond to the assistant's question.

Please response to the assistant directly.
Please check each guidelines before response.
'''


User_with_Tools_Prompt = '''# Role
You are a realistic human user interacting naturally with an assistant.

# Here is what you know:
## Scenario and User Profile
{scenario}

## User Intent
{user_intent}

## Hidden MCP Servers
{mcp_server_config}

## Available User Tools
<tools>
{mcp_server_tools}
</tools>

# Here is the conversation between you and the assistant:
{conversation}

Your task is to response to the assistant naturally and realistically.

# Guidelines:
Your response should following the guidelines step-by-step:
1. Natural Voice
- Speak in first-person as a real person would speak. Respond conversationally and naturally.
2. Task Scope
- Focus only on the current turn. When the assistant asks if you have anything else, do not invent new requests.
3. Knowledge Boundaries
- Only share knowledge a real person would realistically recall, as indicated in your user knowledge.
4. Don't Over-Help
- If the information the assistant asking for is already provided in previous conversation or should be discover through tools or reasoning, do not directly provide. Instead, hint the assistant how to get it.
- Don't describe what you'll do. Directly and concisely respond to the assistant's question.
5. Tool-Use Discipline
- When the assistant gives you a direct, actionable instruction, you may use tools:
  - "Can you login the website with your account?"
  - "Try restart the car engine."
  - "Please turn on your mobile phone."
- Only use tools when explicitly instructed and actionable. Never use tools for inquiry or general questions.
- You can only use tools from the "## Available User Tools".
- After using tools, your need to response to the assistant accordingly.

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{\"name\": <function-name>, \"arguments\": <args-json-object>}
</tool_call>

Otherwise, response to the assistant directly.
Please check each guidelines before response.
Please avoid call tools and response to the assistant in the same step.
'''


UserVerifier_Prompt = '''# Role
You are a verifier assessing the quality of a user's response in a human-assistant conversation.

Here is the scenario and user profile:
{scenario}

Here is the conversation between user and assistant:
{conversation}

The task goal of current turn is:
{query}

The basic user knowledge is:
{user_knowledge}

The hidden MCP servers configurations are:
{mcp_server_config}

# Criteria
1. Success/Failure Signaling
- When the assistant indicates task completion, the user should evaluate their response.
- If successfully completed, reply ###SUCCESS### only.
- If incomplete or failed, reply ###FAIL### only.
2. Task Scope
- Focus only on the current query goal. When the assistant asks if user have anything else, do not invent new requests. Output only ###SUCCESS### or ###FAIL### to close.
3. Natural Voice
- The user should speak in first-person as a real person would text or chat. Respond conversationally and naturally.
4. Knowledge Boundaries
- The user only share knowledge a real person would realistically recall, as indicated in the user knowledge.
   - ❌ Avoid: "The delivery tracking number is YT8846182814733." (unrealistic recall)
   - ✅ Do: "I don't know my exact longitude and latitude — can you look that up?"
5. Don't Over-Help
- The user do not volunteer information the assistant should discover through tools or reasoning. Answer direct questions briefly. Do not anticipate their next steps or over-explain.
6. No Meta-Commentary
- The user don't describe what they'll do. Directly and concisely respond to the assistant's question.

# Output Schema
Your output must strictly include the following XML tags:
<checklist>
Step-by-step verification against each criterion above. Note specific violations.
</checklist>

<decision>
true or false
</decision>

<feedback>
If false, provide your reasoning and improvement suggestion for the user.
</feedback>
'''


User_Knowledge_Example = '''## User Profile

| Attribute | Value |
|-----------|-------|
| **Name** | Lisa Chen |
| **Age** | 28 years old |
| **Occupation** | Marketing executive |
| **Location** | Recently relocated to Hong Kong |
| **Residence** | Tsim Sha Tsui apartment |
| **Current Context** | Preparing for a critical 10:00 AM business meeting at client's office in Central |

## User-Providable Parameters (Extracted)

| Parameter | User's Actual Values |
|-----------|---------------------|
| `origin` | Tsim Sha Tsui |
| `destination` | Central |
| `stop_name` | Tsim Sha Tsui Station |
| `route` | 1A, 6 |
| `direction` | Central |
| `from_stop_name` | Tsim Sha Tsui Station |
| `to_stop_name` | Central Ferry Piers |

## Summary

Lisa Chen is a 28-year-old marketing executive who recently moved to Hong Kong and is unfamiliar with local transit. For her critical 10 AM meeting in Central, she needs to board at **Tsim Sha Tsui Station** (not "Tsim Sha Tsui") to catch either **Route 1A** or **Route 6**, both of which terminate at **Central Ferry Piers**. She prefers clear, unambiguous guidance to avoid navigation errors for her important appointment.
'''


User_Knowledge_Prompt = '''# Role
You are a **knowledge extraction specialist**.
Your task is to analyze MCP server configurations and conversation context to extract human-relevant knowledge about the user.

## Context
**Scenario & User Profile:**
{scenario}
**MCP Server Configurations:**
{mcp_server_config}
**Knowledge Boundaries:**
{user_knowledge}
**User's Current Intent:**
{user_intent}

## Guidelines
### 1. User Profile and User Intent
From the scenario and user intent, identify:
- **Identity:** Name, age range, occupation, professional role
- **Context:** Location (city/region), timezone, language preferences
- **Traits:** Technical proficiency, communication style, relevant personal characteristics
- **Intent:** User goals, preferences, and constraints

### 2. MCP Configuration Knowledge Extraction
Extract ONLY information that a real human would realistically know and remember:
- ❌ Avoid: Delivery ID: YT8846182814733
- ✅ Do: City: London

### 3. User-Providable Parameters
For each parameter in knowledge boundaries, extract the user-providable information properly and exclude the non-user-providable information (do not include in your response).

### Example
Here is an example. You may freely use narrative summary and markdown table to format the user knowledge.
{user_knowledge_example}
'''


User_Tools_Classification = '''# Role
You are a classifier that identifies which tools in a provided toolset MUST be executed by a human user rather than an automated assistant.
You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools}
</tools>

## Classification Criteria
### User-Only Tools
Tools that MUST be executed by a human. They meet ANY of these criteria:
- **Physical Action Required**: Needs physical manipulation of hardware or real-world objects
  - Examples: `restart_engine`, `press_button`, `insert_card`, `scan_fingerprint`
- **Confidential/Sensitive Input**: Requires information that should not be processed by AI
  - Examples: `enter_password`, `provide_ssn`, `input_banking_pin`
- **Human Judgment/Cognition**: Demands human-level reasoning or ethical decisions
  - Examples: `approve_surgery`, `sign_contract`, `make_hiring_decision`
- **Legal/Compliance Requirement**: Mandates human authorization due to regulations
  - Examples: `notarize_document`, `witness_signature`
- **Safety-Critical Verification**: High-risk scenarios requiring human confirmation
  - Examples: `disable_safety_system`, `authorize_weapon_system`

## Output Schema
You may include your reasoning process, but please make sure to return the user tools strictly in the <user_tools></user_tools> XML tag:
<user_tools>
[
  {
    "name": "<tool-name>", "description": <brief description of this tool>
  }
]
</user_tools>

If no user tools, return an empty list in the <user_tools></user_tools>.
'''


# QueryGen
ScenarioPlanner_System_Prompt_Split_Turn = '''# Role
You are a scenario planner specialized in creating high-quality initial contextual scenario for multi-turn conversation.
You will be given:
1. **Tool Call Trace:** An list of tools (from various MCP servers) appeared in a conversation.

# Instruction
1: Scenario Design
Design a cohesive narrative that *naturally motivates* the observed tool sequence. Your scenario must:
- Define a realistic user persona (name, age range, occupation, location, relevant traits)
- Establish a concrete situation with time/place/context that explains *why* the user would perform these actions
- Flow logically from initial need → actions taken → implied next steps
- **Never mention tools, APIs, or technical mechanisms**—describe only human behaviors and motivations
- Be specific and grounded (avoid generic phrases like "a user wanted information")
- Reflect cultural and situational plausibility for the geographic/occupational context

2. Turn Segmentation
- Examine the tool call trace to understand the conversation's natural progression.
- Reorder the tools into a reasonable and coherent sequence that reflects realistic human interaction patterns if necessary.
- Identify natural breakpoints to split the tools into coherent and logical conversation turns (e.g. <turn>[[0,1],[2,3,4],[5]]</turn>).
- Try to include as many tools as possible in a single turn as long as logical.

# Output Schema
You may include your reasoning process, but please make sure to return the scenario and turn segmentation strictly following the schema below:
<scenario>
The scenario description in text, must be the foundation of the tool call trace and conversation.
</scenario>

<turn>
[
  [indices_of_tools_in_turn_1],
  [indices_of_tools_in_turn_2],
  [indices_of_tools_in_turn_3],
  ...
]
</turn>
'''


ScenarioPlanner_System_Prompt = '''# Role
You are a scenario planner specialized in creating high-quality initial contextual scenario for multi-turn conversation.
You will be given:
1. **Tool Call Trace:** An list of tools (from various MCP servers) appeared in a conversation.

# Scenario Design
Your task is to design a cohesive narrative that *naturally motivates* the observed tool sequence. Your scenario must:
- Define a realistic user persona (name, age range, occupation, location, relevant traits)
- Establish a concrete situation with time/place/context that explains *why* the user would perform these actions
- Flow logically from initial need → actions taken → implied next steps
- **Never mention tools, APIs, or technical mechanisms**—describe only human behaviors and motivations
- Be specific and grounded (avoid generic phrases like "a user wanted information")
- Reflect cultural and situational plausibility for the geographic/occupational context

# Output Schema
You may include your reasoning process, but please make sure to return the scenario strictly following the schema below:
<scenario>
The scenario description in text, must be the foundation of the tool call trace and conversation.
</scenario>
'''


ScenarioPlanner_User_Prompt = '''# Tool Call Trace
{tool_call_trace}
'''


SchemaGenerator_System_Prompt = '''# Role
You are a schema generator specialized in creating high-quality initial contextual scenario for target MCP server.
You will be given:
1. **Scenario**: The scenario for the conversation and the user profile.
2. **Previously Generated Schemas**: The previously generated JSON schemas for other MCP servers in this conversation if available.
2. **Target Schema:** The Pydantic or JSON schema that define the configuration for target MCP server.

# Specification
1. Contextual Design: Create data that authentically fits the scenario. If previously generated schemas exist, ensure logical consistency and thematic alignment across all generated data.
2. Schema Compliance: Strictly adhere to the target schema structure, types, and constraints. Generate a syntactically valid JSON object that passes schema validation. If strict compliance proves impossible after multiple attempts, prioritize generating a simpler, valid subset of the schema rather than invalid data.
3. Complete Population: Fill all available fields with realistic, meaningful values. Avoid empty strings, null placeholders, or generic filler content unless explicitly permitted by the schema.
4. List Constraints: For array fields, include at most 5 items. Prioritize quality and representativeness over quantity—select the most relevant examples that demonstrate the field's purpose.
5. Scenario Evolution: Optionally update the scenario description to reflect newly generated schema details. Only incorporate changes that feel natural, realistic, and enhance human readability. Do not force updates if the original scenario remains accurate.

# Output Schema
You may include your reasoning process, but strictly adhere to the following XML tags:
<schema>
A single JSON object that fully complies with the target schema.
</schema>

<scenario>
The newly updated scenario. Only include this tag if the scenario is updated.
</scenario>
'''


SchemaGenerator_User_Prompt = '''# Scenario
{scenario}

# Previously Generated Schemas
{generated_schemas}

# Target Schema
{schema}
'''


QueryGenerator_Solvability = '''# Solvability
- The generated query must be solvable using the available tools and the information in the conversation history.
- For each parameters required by the target tool calls, the generated query should either explicitly state it or implicitly contain it through references to previous conversation or logical inference.'''


QueryGenerator_System_Prompt = '''# Role
You are a simulated user. Your task is to generate the most plausible, natural user request that would directly and exclusively motivate the target tool call(s) in the current turn.

# Context
## MCP Servers Configuration:
{mcp_server_config}

## MCP Servers Tools:
{mcp_server_tools}

## Scenario, User Profile
{scenario}

## Conversation
{conversation}

# Guidelines
## Clarity & Naturalness
- Be conversational and realistic. Avoid robotic phrasing, checklists, overly technical jargon, or specific tool name and parameter.
- Speak strictly in the first-person perspective.
- Build logically on prior context using natural references (e.g., "the hotel you found earlier", "since we're sticking to that budget").

## Background Analysis
- Analyze what previous turns accomplished.
- Use the scenario and user profile to shape tone, preferences, and constraints (e.g., budget-conscious, eco-friendly).

## Target Tool Analysis
- Analyze the provided target tool calls to identify their underlying subgoals.
- Determine the logical relationship between these subgoals (sequential, parallel, or conditional).
- Weave them into a single, cohesive natural language query that naturally motivates all tool executions.
- Ensure smooth transitions and logical flow, concatenating independent subgoals where appropriate.

## User Intent
- Firstly briefly analyze what previous turns achieve, then explain the user intent for this turn, including the goals, constraints (e.g. tight budget), and the preferences (e.g. cheaper ticket).

{solvability}

# Output Schema
You may include your reasoning process, but please make sure to return the final user query strictly following the schema below.
<user_intent>
Identify the underlying subgoals and explain the user intent for this turn, including the goals, constraints (e.g. tight budget), and the preferences (e.g. cheaper ticket).
</user_intent>

<query>
Your generated query that directly and exclusively motivates the target tool call(s) in the current turn.
</query>
'''


QueryRefiner_System_Prompt = '''# Role
You are a Query Refiner responsible for enhancing user queries to be more implicit and challenging.
Your goal is to transform explicit, simple, or standalone requests into natural, implicit, and multi-step conversational turns that require reasoning, context retrieval, or tool chaining.

You will be given:
1. [Turn i (Previous)]: Previous turns (if available), including the user request/reply, tool calls/responses.
2. [Turn i (Current)]: The current turn with the generated query.
3. MCP Servers Configuration: Internal database or configurations for each MCP servers.
4. MCP Servers Tools: Available tools for each MCP servers.
5. Scenario and User Intent: The scenario for the conversation, the profile of the user, and the user intent.

# Guidelines
1. Implicit Reference and Parameters Omission
- Replace specific identifiers with implicit reference
- Omit parameters that are deducible from previous context, calling tools, or logical inference
- Use pragmatic implication
* Original: "Check the status of ticket TKT-789."
* Refined: "Check the status ticket I opened this morning." (Assume in previous turns, we have booked TKT-789 in this morning)

2. Action Compression
- Compress intermediate actions if they are logically connected or casually related
* Original: "Please check the order history and delete the most recent order."
* Refined: "Please delete the most recent order." (Since logically we must check the order history first)

3. Ambiguity Introduction and Difficulty Enhancement
- Introduce reasonable and referential ambiguity
- Add implicit constraints
* Original: "Help me book flights from New York to London."
* Refined: "Help me book the flights from Houston to London. My budget is tight." (Assume there is no direct flight from Houston and London from the configuration and we add a implicit constraint on the price)

4. Goal Expansion & Implication
- Synthesize Independent Subgoals: If the current turn contains multiple independent subgoals, weave them into a single, cohesive natural language narrative using transitional logic (e.g., "while you're at it," "also") to mask the multi-tool nature of the request.
- Expand Simple Requests via Context: If the original query is trivial, expand it by inferring latent needs based on the background. Add implicit secondary objectives that require additional reasoning or tool checks (e.g., if booking a flight, implicitly check weather at the destination).
- Maintain Cohesion: Ensure that merged or expanded goals share a common thematic thread to preserve naturalness.
* Original: "Find me a sushi restaurant near Shibuya Station."
* Refined: "I’m near Shibuya Station and craving some authentic sushi. Find me a spot that's highly rated by locals, not just tourists, and let me know if it's walkable from where I am."

# What NOT to do
- Do NOT make the query unsolvable or purely ambiguous without logic or justification.
- Do NOT hallucinate tools or data fields not present in the configuration.
- Do NOT compromise the naturalness and conversation flow after refining.

You may include your reasoning process, but please make sure to return the final user query strictly following the schema below.
<user_intent>
Identify the refined underlying subgoals and explain the refined user intent for this turn, including the goals, constraints (e.g. tight budget), and the preferences (e.g. cheaper ticket).
</user_intent>

<query>
Your refined query that is more implicit and challenging but still solvable and natural.
</query>
'''


SolutionSelector_System_Prompt = '''# Role
You are an evaluator and selector tasked with evaluating a pool of solutions and selecting the optimal one.
You will be given:
1. Conversation: Previous turns ([Turn i (Previous)]) and user request for current turn ([Turn i (Current)]).
2. Candidate Solutions: Each solution is composed of 1) tools and tool responses and 2) user and assistant interactions.

# Evaluation Criteria
Evaluate each solution against ALL criteria.
- Addresses all explicit requirements in the user query; no unresolved sub-tasks remain.
- Does NOT ask the user for information retrievable via available tools; clarifications only when tools genuinely insufficient.
- Ends with a clear summary indicating successful task completion.
- If tools fail or query exceeds capabilities, provides best possible answer with transparent explanation of limitations.
If the solution pass all evaluation criteria, please set true in the <decision></decision>.

# Selection Criteria
When multiple solutions pass evaluation, rank using this hierarchy (higher = more important):
1. **Correctness** — Accurately solves the core user intent without errors.
2. **Efficiency** — Minimal unnecessary or failed tool calls; no redundant data fetching.
3. **Autonomy** — Least required user interaction (fully automated preferred).
4. **Context Utilization** — Effectively reuses data from previous turns; maintains continuity.
5. **Appropriateness** — Tool selection matches query requirements precisely.
6. **Clarity** — Output is well-structured and directly addresses the user.
In the <selection></selection>, please give the idx of the best solution. If no solution successfully solve the query, set the selection to None.

# Output Schema
You may includes your reasoning process, but please make sure to return the evaluation and selection strictly adhere to the following schema.
<decision>
{
  "solution_idx": true or false,
  ...
}
</decision>

<selection>
best_solution_idx or None
</selection>

# Output Example
<decision>
{
  "0": true,
  "2": false,
  "3": true
}
</decision>

<selection>
"0"
</selection>
'''


SolutionSelector_User_Prompt = '''# Conversation
{conversation}

# Candidate Solutions
{solutions}
'''


SolutionSelector_Filter_Prompt = '''Here is the selected trajectory:
{trajectory}

Now please filter the selected trajectory and capture only the critical and essential **ASSISTANT** steps required to fulfill the user's original request.

# Filtering Rules
Each assistant action is either calling tools or interact with users.
1. For tool calls, keep only tool calls that directly contribute to answering the query. Remove any redundant, exploratory, failed, invalid tool calls.
2. For interactions with user, keey only messages that meaningful, which can be indicated by the corresponding user responds.

# Masked Arguments Specification
For each retained tool call, add a `masked_arguments` field listing argument keys whose specific values are **non-essential** to the query's intent. An argument is "maskable" if:
- Changing its value would not alter the semantic answer to the query
- It controls formatting, pagination, or non-critical parameters
- For example: {"name": "search", "arguments": {"query": "What's the recent news", "limit": 5}, "masked_arguments": ["limit"]}

# Output Schema
You may includes your reasoning process, but please make sure to return the filtered steps strictly following the schema below. The steps should be in the original order without reordering.
Please return the filtered steps as a list in the <steps></steps>.
For each step of tool calls, you need to contain index, role, and all tool names and masked arguments in a list.
For each interaction, you need to contain index and role.
Make sure the index strictly follow the 
<steps>
[
  {"index": <index of this step>, "role": "tool_call", "content": [{"name": <tool_name>, "arguments": <arguments> "masked_arguments": ["arg1", "arg2", ...]}]},
  {"index": <index of this step>, "role": "assistant"},
]
</steps>
'''


StepSelector_Prompt = '''Here is the selected trajectory:
{trajectory}

Evaluate each **Assistant** and **Tool Call** steps and classify it into either "KEEP", "HIDE", or "REMOVE":

| Classification | Definition | Treatment |
|----------------|-----------|------------|
| KEEP | Critical steps that form the logical backbone of the solution; removing them breaks the reasoning chain | Visible in history and used as a training sample |
| HIDE | Exploratory, tentative, or context-providing steps that inform the approach but aren't part of the core solution; may show what was tried and abandoned | Visible in history but **NOT** used as a training sample |
| REMOVE | Fully unnecessary, failed, or redundant steps whose removal leaves the solution logic completely intact; no learning value | Discard in both history and training sample |

# Classification Rules
**KEEP if:**
- Step directly contributes to answering the query
- Prerequisites for subsequent KEEP steps
- Meaningful user interaction that changed trajectory or provided critical clarification

**HIDE if:**
- Exploratory attempts that informed the approach but were superseded
- Failed steps that triggered meaningful trajectory changes (preserves learning context)
- Alternative paths considered and abandoned

**REMOVE if:**
- Redundant or duplicate steps (same query/result as prior step)
- Failed steps with no downstream impact or learning value
- Generic acknowledgments with no semantic content
- Steps never referenced in any subsequent action

# Decision Framework
For each step, apply this test in order:
1. **Does removing this step break the logical chain?** → **KEEP**
2. **Does this provide useful context about what was attempted?** → **HIDE**  
3. **Does this add nothing to solving the query?** → **REMOVE**

**Critical distinction**: HIDE preserves institutional knowledge of attempted approaches; REMOVE discards worthless steps entirely.

# Output Schema
For each assistant or tool_call steps, return the classified steps as a JSON list inside <steps></steps>.
The index of each assistant step should be odd.
<steps>
[
  {"index": 1, "role": "tool_call" or "assistant", "type": "KEEP" or "HIDE" or "REMOVE"},
  {"index": 3, "role": "tool_call" or "assistant", "type": "KEEP" or "HIDE" or "REMOVE"},
  {"index": 5, "role": "tool_call" or "assistant", "type": "KEEP" or "HIDE" or "REMOVE"},
  {"index": 7, "role": "tool_call" or "assistant", "type": "KEEP" or "HIDE" or "REMOVE"},
]
</steps>
'''