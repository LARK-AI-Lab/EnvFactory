# Query generation framework for non-conversational environment.
# The conversation will stop if the assistant stops calling tools.
import asyncio
import os
import json
from uuid import uuid4
import traceback
import random
random.seed(42)

from agents import Agent, Runner, set_tracing_disabled

from src.gen import Gen
from src.graph.tool_chain import ToolQueryChain, ToolQueryNode
from src.graph.tool_graph import ToolGraph
from src.manager.mcp_client_manager import MCPManager
from src.utils.utils import read_scenario_schema

from src.gen.query_gen import QueryGenContext, QueryGenState, QueryGenConfig
from src.gen.query_gen.prompts import (
    ScenarioPlanner_User_Prompt,
    SchemaGenerator_System_Prompt, SchemaGenerator_User_Prompt,
    SolutionSelector_System_Prompt, SolutionSelector_User_Prompt,
    SolutionSelector_Filter_Prompt, StepSelector_Prompt,
)
from src.gen.query_gen.utils import (
    get_planner_instruction,
    get_generator_instruction,
    get_refiner_instruction,
    get_assistant_instruction,
    get_generated_schemas,
    get_solutions,
    get_user_tool_classification,
)

set_tracing_disabled(True)


class QueryGenNonConv(Gen):
    def __init__(self, tool_graph: ToolGraph, config: QueryGenConfig = QueryGenConfig()):
        super().__init__(config=config)
        self.tool_graph = tool_graph
        self.user_tools = {}

    def load_agents(self):
        self.scenario_planner = Agent(
            name="ScenarioPlanner",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_planner_instruction,
        )
        self.schema_generator = Agent(
            name="SchemaGenerator",
            model=self.model,
            model_settings=self.model_settings,
            instructions=SchemaGenerator_System_Prompt,
        )
        self.query_generator = Agent(
            name="QueryGenerator",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_generator_instruction,
        )
        self.query_refiner = Agent(
            name="QueryRefiner",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_refiner_instruction,
        )
        self.query_solver = Agent(
            name="QuerySolver",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_assistant_instruction,
        )
        self.solution_selector = Agent(
            name="SolutionSelector",
            model=self.model,
            model_settings=self.model_settings,
            instructions=SolutionSelector_System_Prompt,
        )
        self.user_tool_classifier = Agent(
            name="UserToolClassifier",
            model=self.model,
            model_settings=self.model_settings,
            instructions=get_user_tool_classification,
        )

    def split_turns(self, init_tool_chain: list, max_turn: int = 5) -> list:
        if not init_tool_chain:
            return []
        
        turns = []
        current_turn_indices = []
        
        for i, tool in enumerate(init_tool_chain):
            current_turn_indices.append(i)
            
            should_split = len(current_turn_indices) >= max_turn or \
                        (len(current_turn_indices) > 0 and random.random() < len(current_turn_indices) / max_turn)
            
            if should_split:
                turns.append(ToolQueryNode(raw_tool_call=[init_tool_chain[j] for j in current_turn_indices]))
                current_turn_indices.clear()

        if current_turn_indices:
            turns.append(ToolQueryNode(raw_tool_call=[init_tool_chain[j] for j in current_turn_indices]))
        
        return turns

    async def classify_tools(self, context: QueryGenContext):
        if not self.config.enable_user_tool_use:
            return QueryGenState.Terminated

        agent = self.user_tool_classifier
        request_id = f"{context.conversation_id}{context.idx}"
        session = self.context_manager.get_session(agent=agent.name, session_id=request_id)
        prompt = "Please classify the provided tools and return the user-only tools inside the <user_tools></user_tools> XML tag."

        for _ in range(self.config.max_retry):
            try:
                output = await Runner.run(agent, input=prompt, session=session, context=context)
                output_json = await self.log(
                    conversation_id=context.conversation_id,
                    idx=context.idx,
                    agent=agent,
                    output=output,
                )

                user_tools = {}
                assert "user_tools" in output_json, "Your output must include the <user_tools></user_tools> XML tag."
                for user_tool_dict in output_json["user_tools"]:
                    user_tool_name = user_tool_dict["name"]
                    user_tool_description = user_tool_dict["description"]
                    user_tool = MCPManager.tools[user_tool_name]

                    user_tools.update({
                        user_tool_name: {
                            "tool": user_tool,
                            "description": user_tool_description
                        }
                    })

                self.user_tools = user_tools.copy()
                if len(self.user_tools) == 0:
                    self.config.enable_user_tool_use = False # disable user tool-use

                context.tool_chain.user_tools = output_json["user_tools"]
                return QueryGenState.Terminated
                
            except Exception as e:
                traceback.print_exc()
                err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
                prompt = err_msg

    async def prepare(self, context: QueryGenContext) -> QueryGenState:
        '''This state splits turns, generates scenario, and classifies tools.'''
        agent = self.scenario_planner
        request_id = f"{context.conversation_id}{context.idx}"
        session = self.context_manager.get_session(agent=agent.name, session_id=request_id)
        prompt = self.context_manager.get_prompt(agent=agent.name, request_id=request_id)
        if prompt is None:
            prompt = ScenarioPlanner_User_Prompt.format(
                tool_call_trace=context.tool_chain.trace,
            )
        try:
            output = await Runner.run(agent, input=prompt, session=session, context=context)
            output_json = await self.log(
                conversation_id=context.conversation_id,
                idx=context.idx,
                agent=agent,
                output=output,
            )
            assert 'scenario' in output_json, "Your output must include the XML tag <scenario></scenario>."
            context.tool_chain.scenario = output_json['scenario']

            if 'turn' in output_json: # Split by llm
                for turn in output_json['turn']:
                    context.tool_chain.tool_chain.append(ToolQueryNode(
                        raw_tool_call=[context.tool_chain.init_tool_chain[i] for i in turn]
                    ))
            else: # Split by probability
                context.tool_chain.tool_chain = self.split_turns(context.tool_chain.init_tool_chain)

            return await self.classify_tools(context)

        except Exception as e:
            traceback.print_exc()
            err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
            self.context_manager.add_prompt(agent.name, request_id, err_msg)
            return QueryGenState.Preparing

    async def schema_generate(self, context: QueryGenContext) -> dict:
        '''Generate initial scenario for the first turn one at a time.'''
        agent = self.schema_generator
        mcp_servers = context.tool_chain.mcp_servers
        result = {}

        # Generate initial scenario one at a time due to context length limit
        for idx, mcp_server in enumerate(mcp_servers):
            request_id = f"{context.conversation_id}{idx}"
            session = self.context_manager.get_session(agent=agent.name, session_id=request_id)

            for retry in range(self.config.max_retry):
                try:
                    # Get prompt
                    prompt = self.context_manager.get_prompt(agent=agent.name, request_id=request_id)
                    if prompt is None:
                        prompt = SchemaGenerator_User_Prompt.format(
                            scenario=context.tool_chain.scenario,
                            generated_schemas=get_generated_schemas(result),
                            schema=read_scenario_schema(mcp_server, mode="Pydantic"),
                        )

                    # Generate initial scenario
                    output = await Runner.run(agent, input=prompt, session=session)
                    output_json = await self.log(
                        conversation_id=context.conversation_id, 
                        idx=0, 
                        agent=agent, 
                        output=output
                    )
                    assert 'schema' in output_json, "Your output must include the XML tag <schema></schema>."
                    if 'scenario' in output_json:
                        context.tool_chain.scenario = output_json['scenario']

                    # Validate initial scenario
                    client_id = f"{mcp_server}-{request_id}"
                    tool_response = MCPManager.load_scenario(
                        scenario=output_json['schema'], 
                        client_id=client_id, 
                        check=True
                    )
                    MCPManager.close_client(client_id)
                    if "Successfully" not in tool_response:
                        raise ValueError(
                            f"Cannot load scenario properly for MCP server {mcp_server}.\n{tool_response}"
                        )
                    result.update({mcp_server: output_json['schema']})
                    break
                except Exception as e:
                    traceback.print_exc()
                    err_msg = f"Error attempt: {repr(e)}. Please retry and correct the schema in <schema></schema>.\n"
                    self.context_manager.add_prompt(agent.name, request_id, err_msg)

        return result

    async def start(self, context: QueryGenContext) -> QueryGenState:
        if context.idx == 0:
            initial_scenario = await self.schema_generate(context)
        else:
            initial_scenario = context.tool_chain[context.idx - 1].final_scenario

        mcp_servers = context.tool_chain.mcp_servers
        if initial_scenario and all(server in initial_scenario for server in mcp_servers):
            context.tool_chain.update_node(context.idx, initial_scenario=initial_scenario)
            return QueryGenState.Generating
        else:
            return QueryGenState.Terminated

    async def generate(self, context: QueryGenContext) -> QueryGenState:
        '''This state generates query based on the sampled tool chain.'''
        agent = self.query_generator
        request_id = f"{context.conversation_id}{context.idx}"
        session = self.context_manager.get_session(agent=agent.name, session_id=request_id)
        prompt = self.context_manager.get_prompt(agent=agent.name, request_id=request_id)
        if prompt is None:
            prompt = "Please generate the most plausible, natural user request that would directly motivate the following target tool calls:\n"
            for j, tool in enumerate(context.tool_chain[context.idx].raw_tool_call):
                prompt += f"- Target Tool Name {j+1}: {tool.name}\n"
        try:
            output = await Runner.run(agent, input=prompt, session=session, context=context)
            output_json = await self.log(
                conversation_id=context.conversation_id, 
                idx=context.idx, 
                agent=agent, 
                output=output
            )
            assert 'query' in output_json, "Your output must include the XML tag <query></query>."
            assert 'user_intent' in output_json, "Your output must include the XML tag <user_intent></user_intent>."
            query = output_json['query']
            user_intent = output_json['user_intent']
            context.tool_chain[context.idx].steps = [{'role': 'user', 'content': query}]
            context.tool_chain.update_node(context.idx, query=query, user_intent=user_intent)
            if self.config.enable_query_refinement:
                return QueryGenState.Refining
            else:
                return QueryGenState.Solving
        except Exception as e:
            traceback.print_exc()
            err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
            self.context_manager.add_prompt(agent.name, request_id, err_msg)
            return QueryGenState.Generating

    async def refine(self, context: QueryGenContext) -> QueryGenState:
        agent = self.query_refiner
        request_id = f"{context.conversation_id}{context.idx}"
        session = self.context_manager.get_session(agent=agent.name, session_id=request_id)
        prompt = self.context_manager.get_prompt(agent=agent.name, request_id=request_id)
        if prompt is None:
            prompt = "Here is the current user query, please refine the query according to the guidelines step by step:\n"
            prompt += context.tool_chain[context.idx].query
        try:
            output = await Runner.run(agent, input=prompt, session=session, context=context)
            output_json = await self.log(
                conversation_id=context.conversation_id, 
                idx=context.idx, 
                agent=agent, 
                output=output
            )
            assert 'query' in output_json, "Your output must include the XML tag <query></query>."
            assert 'user_intent' in output_json, "Your output must include the XML tag <user_intent></user_intent>."
            query = output_json['query']
            user_intent = output_json['user_intent']
            context.tool_chain[context.idx].steps = [{'role': 'user', 'content': query}]
            context.tool_chain.update_node(context.idx, query=query, user_intent=user_intent)
            return QueryGenState.Solving
        except Exception as e:
            traceback.print_exc()
            err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
            self.context_manager.add_prompt(agent.name, request_id, err_msg)
            return QueryGenState.Refining

    async def solve(self, context: QueryGenContext) -> None:
        agent = self.query_solver
        agent_name = f"{agent.name}_{context.k}"
        request_id = f"{context.conversation_id}{context.idx}{context.k}"
        session = self.context_manager.get_session(agent_name, request_id)
        initial_scenario = context.tool_chain[context.idx].initial_scenario

        # Record trace
        context.tool_chain[context.idx].pass_k_trace[context.k] = [
            {"role": "user", "content": context.tool_chain[context.idx].query}
        ]

        # Load scenario
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id}"
            MCPManager.load_scenario(scenario=scenario, client_id=client_id)

        # Solve query
        for _ in range(self.config.max_solve_iterations):
            try:
                prompt = self.context_manager.get_prompt(agent_name, request_id)
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
                    tool_responses = self.execute(tools, request_id)

                    tools_text = ""
                    tool_responses_text = ""
                    for tool, tool_response in zip(tools, tool_responses):
                        if isinstance(tool, dict):
                            tool = json.dumps(tool)
                        tools_text += f"<tool_call>\n{tool}\n</tool_call>\n"
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
                    self.context_manager.add_prompt(agent_name, request_id, tool_responses_text)
                else: # stop
                    trace_len = len(context.tool_chain[context.idx].pass_k_trace[context.k])
                    context.tool_chain[context.idx].pass_k_decision[context.k] = trace_len > 1 # pass to the selector as long as it calls tools
                    context.tool_chain[context.idx].pass_k_trace[context.k].append({
                        "role": "assistant", 
                        "content": output_json.get("non_think"),
                        "think": output_json.get("think"),
                    })
                    break

            except Exception as e:
                traceback.print_exc()
                err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
                self.context_manager.add_prompt(agent_name, request_id, err_msg)
        
        # Save scenario
        final_scenario = {}
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id}"
            tool_response = MCPManager.call_tool(
                client_id=client_id,
                tool_name="save_scenario",
                tool_args={},
            )
            final_scenario[mcp_server] = json.loads(tool_response)
        context.tool_chain[context.idx].pass_k_scenario[context.k] = final_scenario

        # Close sessions and clients
        self.context_manager.close_session(request_id)
        for mcp_server, scenario in initial_scenario.items():
            client_id = f"{mcp_server}-{request_id}"
            MCPManager.close_client(client_id=client_id)

    async def filter(self, context: QueryGenContext, trajectory: list) -> list[dict]:
        agent = self.solution_selector
        request_id = f"{context.conversation_id}{context.idx}"
        session = self.context_manager.get_session(agent=agent.name, session_id=request_id)

        trajectory_str = ""
        for i, step in enumerate(trajectory):
            trajectory_str += f"- Step {i}[{step['role']}]: {step['content']}\n"

        prompt = SolutionSelector_Filter_Prompt.replace("{trajectory}", trajectory_str)
        for _ in range(self.config.max_retry):
            try: 
                output = await Runner.run(agent, input = prompt, session = session)
                output_json = await self.log(
                    conversation_id=context.conversation_id, 
                    idx=context.idx, 
                    agent=agent, 
                    output=output
                )

                assert 'steps' in output_json, "Your output must include the XML tag <steps></steps>."
                filtered_trajectory = [trajectory[0]] # step 0 is the user request
                selected_steps = output_json["steps"]
                for step in selected_steps:
                    # Validate
                    index = int(step["index"])
                    role = step["role"]
                    assert role in ["tool_call", "assistant"], f"The role must be either tool_call or assistant, got {role}."
                    assert role == trajectory[index]["role"], f"The role of selected step {index} does not match original trajectory."

                    # Construct
                    if role == "tool_call":
                        for tool_call in step['content']:
                            assert ("name" in tool_call) and \
                                    ("arguments" in tool_call) and \
                                    ("masked_arguments" in tool_call), f"You must output name, arguments, and masked_arguments for each tool call."
                        filtered_trajectory.append({
                            "role": "tool_call",
                            "content": step['content'],
                        })
                        filtered_trajectory.append({
                            "role": "tool_response",
                            "content": trajectory[index+1]["content"],
                        })
                    elif role == "assistant":
                        filtered_trajectory.append({
                            "role": "assistant",
                            "content": trajectory[index]["content"],
                        })
                        if index + 1 < len(trajectory):
                            filtered_trajectory.append({
                                "role": "user",
                                "content": trajectory[index+1]["content"],
                            })

                return filtered_trajectory

            except Exception as e:
                traceback.print_exc()
                err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
                prompt = err_msg
        
        return trajectory

    async def classify(self, context: QueryGenContext, trajectory: list) -> list[dict]:
        agent = self.solution_selector
        request_id = f"{context.conversation_id}{context.idx}"
        session = self.context_manager.get_session(agent=agent.name, session_id=request_id)

        trajectory_str = ""
        for i, step in enumerate(trajectory):
            trajectory_str += f"- Step {i}[{step['role']}]: {step['content']}\n"

        prompt = StepSelector_Prompt.replace("{trajectory}", trajectory_str)
        for _ in range(self.config.max_retry):
            try: 
                output = await Runner.run(agent, input = prompt, session = session)
                output_json = await self.log(
                    conversation_id=context.conversation_id, 
                    idx=context.idx, 
                    agent=agent, 
                    output=output
                )

                assert 'steps' in output_json, "Your output must include the XML tag <steps></steps>."
                steps = output_json["steps"]
                classified_steps = trajectory.copy()
                
                for i, step in enumerate(steps):
                    index = int(step["index"])
                    role = step["role"]
                    assert role in ["tool_call", "assistant"], f"The role must be either tool_call or assistant, got {role}."
                    assert role == classified_steps[index]["role"], f"The role of selected step {index} does not match original trajectory."
                    classified_steps[index]["type"] = step.get("type")

                break

            except Exception as e:
                traceback.print_exc()
                err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
                prompt = err_msg
        
        return classified_steps

    async def select(self, context: QueryGenContext) -> None:
        agent = self.solution_selector
        request_id = f"{context.conversation_id}{context.idx}"
        session = self.context_manager.get_session(agent=agent.name, session_id=request_id)

        for _ in range(self.config.max_retry):        
            try:
                prompt = self.context_manager.get_prompt(agent.name, request_id)
                if prompt is None:
                    prompt = SolutionSelector_User_Prompt.format(
                        conversation=context.tool_chain.get_conversation(turn_idx=context.idx),
                        solutions=get_solutions(
                            context.tool_chain[context.idx].pass_k_trace, context.tool_chain[context.idx].pass_k_decision,
                        ),
                    )
                output = await Runner.run(agent, input=prompt, session=session)
                output_json = await self.log(
                    conversation_id=context.conversation_id, 
                    idx=context.idx, 
                    agent=agent, 
                    output=output
                )

                assert 'decision' in output_json and 'selection' in output_json, \
                    "Your output must include the XML tag <decision></decision> and <selection></selection>."
                assert isinstance(output_json['decision'], dict), \
                    "The <decision></decision> must be a dict of idx to decision."

                try: # cast to int
                    selected_idx = int(output_json['selection'])
                except:
                    selected_idx = output_json['selection']
                if isinstance(selected_idx, int):
                    final_scenario = context.tool_chain[context.idx].pass_k_scenario[selected_idx]

                    if self.config.enable_filteration: # filter the selected trajectory
                        tool_trace = await self.filter(context, context.tool_chain[context.idx].pass_k_trace[selected_idx])
                    else: # no filter
                        # tool_trace = await self.classify(context, context.tool_chain[context.idx].pass_k_trace[selected_idx])
                        tool_trace = context.tool_chain[context.idx].pass_k_trace[selected_idx]

                    context.tool_chain.update_node(
                        context.idx,
                        decision=True,
                        steps=tool_trace,
                        final_scenario=final_scenario,
                    )
                    
                    acc = 0
                    for i, decision in output_json['decision'].items():
                        if decision:
                            acc += 1
                    context.tool_chain[context.idx].accuracy = acc / self.config.pass_k
                else:
                    context.tool_chain[context.idx].accuracy = 0

                break
            except Exception as e:
                traceback.print_exc()
                err_msg = f"Error attempt: {repr(e)}. Please retry...\n"
                self.context_manager.add_prompt(agent.name, request_id, err_msg)

    async def solve_and_select(self, context: QueryGenContext) -> QueryGenState:
        # Solve with pass@k sampling
        tasks = [
            asyncio.create_task(self.solve(QueryGenContext(
                config=self.config,
                tool_graph=self.tool_graph,
                tool_chain=context.tool_chain,
                idx=context.idx,
                conversation_id=context.conversation_id,
                k=k,
                user_tools=self.user_tools,
            )))
            for k in range(self.config.pass_k)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        # await asyncio.gather(*tasks, return_exceptions=False)

        # Select only if at least one valid trace
        if any(decision for decision in context.tool_chain[context.idx].pass_k_decision.values()):
            await self.select(context)

        return QueryGenState.Terminated

    async def terminate(self, context: QueryGenContext) -> None:
        """Save tool chain, dump logs, and close clients and sessions."""
        # Save tool chain
        file_name = f"{context.tool_chain.create_time}-{context.tool_chain.seed}-{self.config.model_name}.json"
        save_path = f"{self.config.save_folder}/{file_name}"
        os.makedirs(self.config.save_folder, exist_ok=True)
        context.tool_chain.save(save_path)

        # Dump logs
        self.logger.dump_log(
            conversation_id = context.conversation_id,
            log_name = file_name,
            overwrite = False,
        )

        # Close sessions
        request_id = f"{context.conversation_id}{context.idx}"
        self.context_manager.close_session(request_id)

    async def gen(self, tool_chain: ToolQueryChain | str) -> ToolQueryChain:
        # Step 0: Load from checkpoint and Prepare initial context
        if isinstance(tool_chain, str):
            tool_chain = ToolQueryChain.load(tool_chain)

        i = 0
        for i, node in enumerate(tool_chain):
            if not node.decision: # start from the first invalid turn
                break

        self.logger.logger.info(f"Starting Turn Index: {i}")
        conversation_id = uuid4().hex
        context = QueryGenContext(
            config=self.config,
            tool_graph=self.tool_graph,
            tool_chain=tool_chain,
            idx=i,
            conversation_id=conversation_id,
            user_tools=self.user_tools,
        )

        # Step 1: Split turns and generate scenario
        if i == 0:
            state = QueryGenState.Preparing
            for retry in range(self.config.max_retry):
                self.logger.logger.info(f"State: {state} | Turn Index: {context.idx} | Iteration: {retry}")
                if state == QueryGenState.Preparing:
                    state = await self.prepare(context)
                else:
                    break

        # Step 2: Repeat Generate -> Solve -> Select iteraively
        for idx in range(i, len(tool_chain)):
            context.idx = idx  # update context index for current turn
            
            state = QueryGenState.Starting
            for iter in range(self.config.max_iterations):
                self.logger.logger.info(f"State: {state} | Turn Index: {context.idx} | Iteration: {iter}")
                if state == QueryGenState.Starting:    
                    state = await self.start(context)
                elif state == QueryGenState.Generating:    
                    state = await self.generate(context)
                elif state == QueryGenState.Refining:    
                    state = await self.refine(context)
                elif state == QueryGenState.Solving:
                    state = await self.solve_and_select(context)
                else:
                    await self.terminate(context)
                    break

            if not tool_chain[idx].decision: # terminate if current turn is not valid
                break
        
        return tool_chain