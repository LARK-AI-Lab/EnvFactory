from agents import Agent, Runner, RunContextWrapper, set_tracing_disabled

from src.graph.tool_graph import ToolGraph
from src.manager.mcp_client_manager import MCPManager

from src.gen.query_gen.prompts import (
    End_Conversation_Prompt, User_Prompt, User_with_Tools_Prompt,
    Interaction_Rule1, Interaction_Rule2, Assistant_Prompt,
    UserVerifier_Prompt, User_Tools_Classification,
    ScenarioPlanner_System_Prompt,
    ScenarioPlanner_System_Prompt_Split_Turn,
    QueryGenerator_Solvability,
    QueryGenerator_System_Prompt,
    QueryRefiner_System_Prompt,
)

SUCCESS_TOKEN = "###SUCCESS###"
FAIL_TOKEN = "###FAIL###"
STOP_TOKEN = "###STOP###"

def get_mcp_server_scenario(initial_scenario: dict, mcp_servers: list[str] = None) -> str:
    mcp_server_scenario = ""
    for i, (mcp_server, scenario) in enumerate(initial_scenario.items()):
        if mcp_servers is None or mcp_server in mcp_servers:
            mcp_server_scenario += f"## MCP Server {mcp_server}\n"
            mcp_server_scenario += f"{scenario}\n"
    
    return mcp_server_scenario

def get_planner_instruction(context: RunContextWrapper, agent: Agent) -> str:
    config = context.context.config
    if config.enable_split_turns:
        return ScenarioPlanner_System_Prompt_Split_Turn
    else:
        return ScenarioPlanner_System_Prompt

def get_generator_instruction(context: RunContextWrapper, agent: Agent) -> str:
    config = context.context.config
    tool_chain = context.context.tool_chain
    idx = context.context.idx
    mcp_servers=tool_chain[idx].mcp_servers
    
    return QueryGenerator_System_Prompt.format(
        mcp_server_config=get_mcp_server_scenario(tool_chain[idx].initial_scenario, mcp_servers),
        mcp_server_tools=get_mcp_server_tools(mcp_servers),
        scenario=tool_chain.scenario,
        conversation=tool_chain.get_conversation(turn_idx=idx),
        solvability=QueryGenerator_Solvability if not config.enable_user_interaction else ""
    )

def get_refiner_instruction(context: RunContextWrapper, agent: Agent) -> str:
    tool_chain = context.context.tool_chain
    idx = context.context.idx
    mcp_servers=tool_chain[idx].mcp_servers
    
    return QueryRefiner_System_Prompt.format(
        mcp_server_config=get_mcp_server_scenario(tool_chain[idx].initial_scenario, mcp_servers),
        mcp_server_tools=get_mcp_server_tools(mcp_servers),
        scenario=tool_chain.scenario,
        user_intent=tool_chain[idx].user_intent,
        conversation=tool_chain.get_conversation(turn_idx=idx),
    )

def get_user_knowledge(tool_graph: ToolGraph, mcp_servers: list[str]) -> str:
    tools = [
        tool for server in mcp_servers for tool in tool_graph.server_to_tools[server]
    ]

    user_providable = []
    non_user_providable = []
    for tool in tools:
        for param in tool.input_schema['parameters']:
            (user_providable if param.user_provided else non_user_providable).append(param.name)

    text = ""
    if user_providable:
        text += f"The User Providable parameters are: {', '.join(user_providable)}\n"
    if non_user_providable:
        text += f"The Non User Providable parameters are: {', '.join(non_user_providable)}\n"
    
    return text

def get_generated_schemas(schemas: dict) -> str:
    generated_schemas = ""
    for mcp_server, schema in schemas.items():
        generated_schemas += f"## MCP Server: {mcp_server}\n"
        generated_schemas += f"{schema}\n\n"

    if generated_schemas:
        return generated_schemas
    else:
        return "None"

def get_mcp_server_tools(mcp_servers: list[str]) -> str:
    mcp_server_tools = ""
    tools = MCPManager.filter_tools(mcp_servers)
    for tool in tools:
        mcp_server_tools += f"{tool['function']}\n"
    
    return mcp_server_tools

def get_solutions(traces: dict, decisions: dict) -> str:
    solutions = ""
    for idx, trace in traces.items():
        if decisions.get(idx):
            solutions += f"## Solution {idx}:\n"
            for i, step in enumerate(trace):
                solutions += f"- Step {i}[{step['role']}]: {step['content']}\n"
    return solutions

def get_user_tool_classification(context: RunContextWrapper, agent: Agent) -> str:
    tool_chain = context.context.tool_chain
    idx = context.context.idx

    prompt = User_Tools_Classification
    prompt = prompt.replace("{tools}", get_mcp_server_tools(tool_chain[idx].mcp_servers))

    return prompt

def get_conversation_end(context: RunContextWrapper, agent: Agent) -> str:
    tool_chain = context.context.tool_chain
    idx = context.context.idx

    return End_Conversation_Prompt.format(
        scenario=tool_chain.scenario,
        user_intent=tool_chain[idx].user_intent,
        conversation=tool_chain.get_conversation(turn_idx=idx),
    )

def get_user_instruction(context: RunContextWrapper, agent: Agent) -> str:
    config = context.context.config
    tool_chain = context.context.tool_chain
    tool_graph = context.context.tool_graph
    idx = context.context.idx

    if config.enable_user_tool_use:
        # Prepare user tools
        mcp_server_tools = ""
        all_tools = MCPManager.filter_tools(tool_chain[idx].mcp_servers)
        for tool in all_tools:
            if tool["function"]["name"] in context.context.user_tools:
                mcp_server_tools += f"{tool['function']}\n"
        
        # Format prompts
        prompt = User_with_Tools_Prompt
        prompt = prompt.replace("{scenario}", tool_chain.scenario)
        prompt = prompt.replace("{user_intent}", tool_chain[idx].user_intent)
        prompt = prompt.replace("{conversation}", tool_chain.get_conversation(turn_idx=idx))
        prompt = prompt.replace("{mcp_server_config}", get_mcp_server_scenario(tool_chain[idx].initial_scenario, tool_chain[idx].mcp_servers))
        prompt = prompt.replace("{mcp_server_tools}", mcp_server_tools)
        return prompt
    else:
        prompt = User_Prompt
        prompt = prompt.replace("{scenario}", tool_chain.scenario)
        prompt = prompt.replace("{user_intent}", tool_chain[idx].user_intent)
        prompt = prompt.replace("{conversation}", tool_chain.get_conversation(turn_idx=idx))
        prompt = prompt.replace("{user_knowledge}", get_user_knowledge(tool_graph, tool_chain.mcp_servers))
        prompt = prompt.replace("{mcp_server_config}", get_mcp_server_scenario(tool_chain[idx].initial_scenario, tool_chain[idx].mcp_servers))
        return prompt

def get_user_verification(context: RunContextWrapper, agent: Agent) -> str:
    tool_chain = context.context.tool_chain
    tool_graph = context.context.tool_graph
    idx = context.context.idx

    return UserVerifier_Prompt.format(
        scenario=tool_chain.scenario,
        mcp_server_config=get_mcp_server_scenario(tool_chain[idx].initial_scenario, tool_chain[idx].mcp_servers),
        user_knowledge=get_user_knowledge(tool_graph, tool_chain.mcp_servers),
        conversation=tool_chain.get_conversation(turn_idx=idx),
    )

def get_assistant_instruction(context: RunContextWrapper, agent: Agent) -> str:
    tool_chain = context.context.tool_chain
    idx = context.context.idx
    config = context.context.config

    # Prepare assistant tools
    mcp_server_tools = ""
    user_tools = ""
    all_tools = MCPManager.filter_tools(tool_chain[idx].mcp_servers)
    for tool in all_tools:
        tool_name = tool["function"]["name"]
        if tool_name in context.context.user_tools:
            tool_desc = context.context.user_tools[tool_name]["description"]
            user_tools += f"{tool_name}: {tool_desc}\n"
        else:
            mcp_server_tools += f"{tool['function']}\n"

    interaction_rule1 = Interaction_Rule1 if config.enable_user_interaction else ""
    interaction_rule2 = Interaction_Rule2 if config.enable_user_tool_use else ""
    interaction_rule2 = interaction_rule2.replace("{user_tools}", user_tools)

    prompt = Assistant_Prompt
    prompt = prompt.replace("{interaction_rule1}", interaction_rule1)
    prompt = prompt.replace("{interaction_rule2}", interaction_rule2)
    prompt = prompt.replace("{conversation}", tool_chain.get_conversation(turn_idx=idx))
    prompt =prompt.replace("{tools}", mcp_server_tools)

    return prompt