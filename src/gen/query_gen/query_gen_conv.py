# Query generation framework for conversational environment.
# The conversation will stop if the user stops the conversation.
import json
import traceback

from agents import Agent, Runner, set_tracing_disabled

from src.graph.tool_graph import ToolGraph
from src.manager.mcp_client_manager import MCPManager

from src.gen.query_gen import QueryGenContext, QueryGenState, QueryGenConfig
from src.gen.query_gen.query_gen_non_conv import QueryGenNonConv
from src.gen.query_gen.utils import (
    STOP_TOKEN,
    get_conversation_end,
    get_user_instruction,
    get_user_verification,
)

set_tracing_disabled(True)


class QueryGenConv(QueryGenNonConv):
    def __init__(self, tool_graph: ToolGraph, config: QueryGenConfig = QueryGenConfig()):
        super().__init__(tool_graph=tool_graph, config=config)

    def load_agents(self):
        super().load_agents()
        self.end_conversation = Agent(
            name="EndConversation",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_conversation_end,
        )
        self.user = Agent(
            name="User",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_user_instruction,
        )
        self.user_verifier = Agent(
            name="UserVerifier",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_user_verification,
        )

    async def interact(self, context: QueryGenContext, message: str) -> dict:
        request_id = f"{context.conversation_id}{context.idx}{context.k}"
        end_agent = f"{self.end_conversation.name}_{context.k}"
        end_session = self.context_manager.get_session(end_agent, request_id)
        user_agent = f"{self.user.name}_{context.k}"
        user_session = self.context_manager.get_session(user_agent, request_id)
        user_verifier_agent = f"{self.user_verifier.name}_{context.k}"
        user_verifier_session = self.context_manager.get_session(user_verifier_agent, request_id)

        # Stop
        prompt = self.context_manager.get_prompt(end_agent, request_id) or message
        user_response = await Runner.run(
            self.end_conversation,
            input=prompt,
            session=end_session,
            context=context,
        )
        user_response_json = await self.log(
            conversation_id=context.conversation_id,
            idx=context.idx,
            agent=self.end_conversation,
            output=user_response,
            context=context,
        )
        if STOP_TOKEN in user_response_json["non_think"]:
            return user_response_json["non_think"]

        final_user_response = ""
        for i in range(self.config.max_interaction_iterations):
            try:
                # Interact
                prompt = self.context_manager.get_prompt(user_agent, request_id) or message
                user_response = await Runner.run(
                    self.user, 
                    input=prompt, 
                    session=user_session, 
                    context=context
                )
                user_response_json = await self.log(
                    conversation_id=context.conversation_id, 
                    idx=context.idx, 
                    agent=self.user, 
                    output=user_response,
                    context=context
                )

                # Tool Call
                if "tool_call" in user_response_json:
                    tools = user_response_json['tool_call']
                    if not isinstance(tools, list):
                        tools = [tools]

                    tool_responses_text = "Based on the following observations, you may adjust your tool-use accordingly or response to the assistant as a user concisely in first-person.\n"
                    for tool in tools:
                        if tool["name"] not in self.user_tools:
                            tool_response = f"Error: {tool["name"]} is not a valid user tool. You can not use it."
                        else:
                            tool_response = self.execute(tool, request_id)[0]
                            final_user_response += f"I do:\n<tool_call>\n{tool}\n</tool_call>\n"
                            final_user_response += f"I observe:\n<tool_response>\n{tool_response}\n</tool_response>\n"

                        tool_responses_text += f"<tool_response>\n{tool_response}\n</tool_response>\n"
                    self.context_manager.add_prompt(user_agent, request_id, tool_responses_text)
                    continue
                else:
                    final_user_response += user_response_json["non_think"]

                # Verify
                if self.config.enable_user_verification:
                    output = await Runner.run(
                        self.user_verifier, 
                        input=user_response_json.get("response", ""), 
                        session=user_verifier_session, 
                        context=context
                    )
                    output_json = await self.log(
                        conversation_id=context.conversation_id, 
                        idx=context.idx, 
                        agent=self.user_verifier, 
                        output=output,
                        context=context
                    )
                    if output_json.get("decision"):
                        break

                    feedback = output_json.get("feedback") or output_json.get("non_think", "")
                    self.context_manager.add_prompt(user_agent, request_id, feedback)
                else:
                    break

            except Exception as e:
                traceback.print_exc()
                err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
                self.context_manager.add_prompt(user_agent, request_id, err_msg)

        return final_user_response

    async def solve(self, context: QueryGenContext) -> None:
        agent = self.query_solver
        agent_name = f"{agent.name}_{context.k}"
        request_id_k = f"{context.conversation_id}{context.idx}{context.k}"
        session = self.context_manager.get_session(agent_name, request_id_k)
        initial_scenario = context.tool_chain[context.idx].initial_scenario

        # Record trace
        context.tool_chain[context.idx].pass_k_trace[context.k] = [
            {"role": "user", "content": context.tool_chain[context.idx].query}
        ]

        # Load scenario
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id_k}"
            MCPManager.load_scenario(scenario=scenario, client_id=client_id)

        # Solve query
        for _ in range(self.config.max_solve_iterations):
            try:
                prompt = self.context_manager.get_prompt(agent_name, request_id_k)
                if prompt is None:
                    prompt = context.tool_chain[context.idx].query

                output = await Runner.run(agent, input=prompt, session=session, context=context)
                output_json = await self.log(
                    conversation_id=context.conversation_id, 
                    idx=context.idx, 
                    agent=agent, 
                    output=output,
                    context=context,
                )

                if "tool_call" in output_json: # call tools
                    tools = output_json['tool_call']
                    if not isinstance(tools, list):
                        tools = [tools]

                    tool_responses = []
                    tool_responses_text = ""
                    for tool in tools:
                        if tool["name"] in self.user_tools:
                            tool_response = f"Error: Tool {tool["name"]} is not found."
                        else:
                            tool_response = self.execute(tool, request_id_k)[0]

                        tool_responses.append(tool_response)
                        tool_responses_text += f"<tool_response>\n{tool_response}\n</tool_response>\n"

                    context.tool_chain[context.idx].pass_k_trace[context.k].append({
                        "role": "tool_call", 
                        "content": tools,
                        "think": output_json.get("think"),
                    })
                    context.tool_chain[context.idx].pass_k_trace[context.k].append({
                        "role": "tool_response", 
                        "content": tool_responses,
                    })
                    self.context_manager.add_prompt(agent_name, request_id_k, tool_responses_text)

                else: # interact with the user
                    user_response = await self.interact(context=context, message=output_json.get("non_think"))
                    context.tool_chain[context.idx].pass_k_trace[context.k].append({
                        "role": "assistant", 
                        "content": output_json.get("non_think"),
                        "think": output_json.get("think"),
                    })

                    if STOP_TOKEN in user_response: # stop conversation
                        context.tool_chain[context.idx].pass_k_decision[context.k] = True
                        break

                    context.tool_chain[context.idx].pass_k_trace[context.k].append({
                        "role": "user", 
                        "content": user_response,
                    })
                    self.context_manager.add_prompt(agent_name, request_id_k, user_response)

            except Exception as e:
                traceback.print_exc()
                err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
                self.context_manager.add_prompt(agent_name, request_id_k, err_msg)
        
        # Save scenario
        final_scenario = {}
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id_k}"
            tool_response = MCPManager.call_tool(
                client_id=client_id,
                tool_name="save_scenario",
                tool_args={},
            )
            final_scenario[mcp_server] = json.loads(tool_response)
        context.tool_chain[context.idx].pass_k_scenario[context.k] = final_scenario

        # Close sessions and clients
        self.context_manager.close_session(request_id_k)
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id_k}"
            MCPManager.close_client(client_id=client_id)
