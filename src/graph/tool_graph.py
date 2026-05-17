from __future__ import annotations

import pickle
import random
from collections import deque
from enum import Enum
from pathlib import Path
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
import networkx as nx
import numpy as np
from tqdm import tqdm

from src.graph.prompts import Build_Tool_Dependency_Prompt
from src.graph.tool_chain import ToolQueryChain
from src.graph.tool_node import Parameter, Tool, batch_embedding, batch_get_user_provided
from src.manager.llm_client_manager import LLMClient
from src.utils.utils import parse_structured_output


class NodeType(Enum):
    Tool = "tool"
    Parameter = "parameter"


class EdgeType(Enum):
    Tool_Input = "parameter_to_tool"
    Parameter_Relate = "parameter_to_parameter"
    Tool_Output = "tool_to_parameter"
    Tool_Depend = "tool_to_tool"


class ToolGraph:
    """
    ToolGraph represents a directed graph of tools and their parameters.

    The graph contains:
    - Tool nodes: Represent individual tools
    - Parameter nodes: Represent input/output parameters of tools
    - Edges: Represent relationships between tools and parameters
    """

    def __init__(
        self,
        graph: nx.Graph = None,
        ignore_tool_class: bool = False,
        build_edge_threshold: float = 0.85,
        merge_param_threshold: float = 0.92,
    ):
        """
        Initialize a ToolGraph.

        Args:
            graph: Optional existing NetworkX graph. If None, creates a new DiGraph.
            ignore_tool_class: If True, don't prefix tool names with class name.
            build_edge_threshold: Similarity threshold for building edges between tools.
            merge_param_threshold: Similarity threshold for merging similar parameters.
        """
        self.graph = graph or nx.DiGraph()
        self.ignore_tool_class = ignore_tool_class
        self.build_edge_threshold = build_edge_threshold
        self.merge_param_threshold = merge_param_threshold

    def build_tool_graph(
            self,
            metadata: list[dict],
            enable_merge: bool = False,
            enable_build_edge_with_llm: bool = True,
        ):
        """
        Build the tool graph from a list of tool metadata.

        Args:
            metadata: List of dictionaries, each containing 'class_name' and 'tools'.
            enable_merge: Whether to merge similar parameters.
            enable_build_edge_with_llm: Whether to build edges within the same servers using LLM.
        """
        self.graph.clear()

        # Create nodes and collect parameters by class
        tools = []
        self.server_to_tools = {}
        for data in metadata:
            class_name = data["class_name"]

            for tool in data["tools"]:
                tool['server'] = class_name
                if not self.ignore_tool_class:
                    tool["name"] = f"{class_name}-{tool['name']}"
                tools.append(tool)                           

        nodes, params = [], []
        for tool in tqdm(tools, desc="Creating nodes..."):
            # Tool node
            node = Tool(tool)
            nodes.append(node)
            self.graph.add_node(node, node_type=NodeType.Tool)  # tool is hashable

            if tool['server'] not in self.server_to_tools:
                self.server_to_tools[tool['server']] = []
            self.server_to_tools[tool['server']].append(node)

            # Parameter nodes
            for param in node.input_schema["parameters"]:
                self.graph.add_node(param, node_type=NodeType.Parameter)  # param is hashable
                
                # Determine if this parameter is required
                # Check if param.name is in required list, or if it's a nested parameter,
                # check if the base parameter name (before first '.') is in required list
                is_required = False
                required_list = node.input_schema.get("required", [])
                if param.name in required_list:
                    is_required = True
                elif "." in param.name:
                    # For nested parameters like "calendar_id.calendar_name", 
                    # check if base parameter "calendar_id" is required
                    base_param_name = param.name.split(".", 1)[0]
                    if base_param_name in required_list:
                        is_required = True
                
                self.graph.add_edge(param, node, edge_type=EdgeType.Tool_Input, required=is_required)
                params.append(param)

            for param in node.output_schema["parameters"]:
                self.graph.add_node(param, node_type=NodeType.Parameter)  # param is hashable
                self.graph.add_edge(node, param, edge_type=EdgeType.Tool_Output)
                params.append(param)

        # Embed the parameters
        batch_embedding(params)

        # Build parameter-to-tool mapping for better context in user_provided inference
        param_to_tool_map = {}
        for node in nodes:
            # Map input parameters to their tool
            for param in node.input_schema["parameters"]:
                param_to_tool_map[param] = node
            # Map output parameters to their tool
            for param in node.output_schema["parameters"]:
                param_to_tool_map[param] = node

        # Get user_provided in batch with tool context
        batch_get_user_provided(params, param_to_tool_map=param_to_tool_map)

        # Merge similar parameters
        if enable_merge:
            self._merge_parameters()

            # Update Tool after merging
            for node in nodes:
                output_params = []
                for succ in self.graph.successors(node):
                    if isinstance(succ, Parameter):
                        edge_data = self.graph.get_edge_data(node, succ)
                        if (
                            edge_data
                            and edge_data.get("edge_type") == EdgeType.Tool_Output
                        ):
                            output_params.append(succ)
                node.output_schema["parameters"] = output_params

                input_params = []
                for pred in self.graph.predecessors(node):
                    if isinstance(pred, Parameter):
                        edge_data = self.graph.get_edge_data(pred, node)
                        if (
                            edge_data
                            and edge_data.get("edge_type") == EdgeType.Tool_Input
                        ):
                            input_params.append(pred)
                node.input_schema["parameters"] = input_params

        # Build edges using input-output similarities for all tools
        for node_from in tqdm(nodes, desc="Building edges using similarities..."):
            self._build_edge_with_sim(node_from = node_from, nodes_to = nodes)
        
        # Build edges using LLM on tools from the same server
        if enable_build_edge_with_llm:
            for server, tools in tqdm(self.server_to_tools.items(), desc="Building edges using LLM..."):
                self._build_edge_with_llm(nodes=tools)

    def _merge_parameters(self):
        """Merge highly similar parameter nodes before creating Tool-Tool and Parameter-Parameter edges."""
        param_nodes = [node for node in self.graph.nodes() if isinstance(node, Parameter)]

        # Find groups of similar parameters to merge greedily
        merge_groups = []
        merged = set()

        for i, param1 in enumerate(param_nodes):
            if param1 in merged:
                continue

            # Find a group of similar parameters
            group = [param1]
            merged.add(param1)

            for j, param2 in enumerate(param_nodes[i + 1 :], i + 1):
                if param2 in merged:
                    continue

                similarity = param1.similarity(param2)
                if similarity > self.merge_param_threshold:
                    group.append(param2)
                    merged.add(param2)

            if len(group) > 1:
                merge_groups.append(group)

        def _redirect_and_remove(rep, other):
            """Merge two parameters by retaining the edge relationship"""
            # predecessors (x -> other) -> (x -> rep)
            for pred in list(self.graph.predecessors(other)):
                if pred != rep:
                    edge_data = self.graph.get_edge_data(pred, other)
                    if edge_data:
                        self.graph.add_edge(pred, rep, **edge_data)
                    else:
                        self.graph.add_edge(pred, rep)

            # successors (other -> y) -> (rep -> y)
            for succ in list(self.graph.successors(other)):
                if succ != rep:
                    edge_data = self.graph.get_edge_data(other, succ)
                    if edge_data:
                        self.graph.add_edge(rep, succ, **edge_data)
                    else:
                        self.graph.add_edge(rep, succ)

            # delete other
            if self.graph.has_node(other):
                self.graph.remove_node(other)

        # Merge parameters in each group
        for group in tqdm(merge_groups, desc="Merging parameters..."):
            rep = group[0]
            for other in group[1:]:
                _redirect_and_remove(rep, other)

    def _build_edge_with_llm(self, nodes: list[Tool], max_retry: int = 3):
        """Build edge inside a server with llm."""
        node_names = {node.name for node in nodes}
        names_to_nodes = {node.name: node for node in nodes}
        
        # Create tool descriptions and adjacency map
        tool_desc = ""
        adj_map = {}
        for src_node in nodes:
            tool_desc += f"{str(src_node)}\n"
            nodes_to = []
            for dst_node in nodes:
                if self.graph.has_edge(src_node, dst_node):
                    nodes_to.append(dst_node.name)
            adj_map[src_node.name] = nodes_to
        
        # Build prompt
        prompt = Build_Tool_Dependency_Prompt.format(
            tool_desc = tool_desc,
            adjacency_map = adj_map,
        )

        server = nodes[0].server
        for attempt in range(max_retry):
            try:
                output = LLMClient.inference(prompts=prompt, disable_progress_bar=True)[0]
                output_json = parse_structured_output(output)
                new_adj_map = output_json['adjacency_map']

                # Validate output
                for src, dsts in new_adj_map.items():
                    if not isinstance(dsts, list):
                        raise ValueError(f"Successors of '{src}' must be a list, got {type(dsts)}")
                    invalid = [d for d in dsts if d not in node_names]
                    if invalid:
                        raise ValueError(f"Invalid successors in '{src}': {invalid}")

                # Update edges
                for src, dsts in new_adj_map.items():
                    src_node = names_to_nodes[src]
                    for dst in dsts:
                        dst_node = names_to_nodes[dst]
                        if not self.graph.has_edge(src_node, dst_node):
                            self.graph.add_edge(src_node, dst_node, edge_type=EdgeType.Tool_Depend)
                break

            except Exception as e:
                error_msg = f"# Attempt: {output}\n"
                error_msg = f"Error: {e}. Please retry."
                prompt += error_msg

    def _build_edge_with_sim(self, node_from: Tool, nodes_to: list[Tool]):
        """Build edge between a source node and a list of destination nodes simultaneously using similarity."""
        params_from = node_from.output_schema["parameters"]
        if len(params_from) == 0:
            return
        params_to, params_to_pos = [], []

        # Prepare parameter lists and position mapping
        for idx, node_to in enumerate(nodes_to):
            if node_from is not node_to:
                params_temp = node_to.input_schema["parameters"]
                params_to.extend(params_temp)
                params_to_pos.extend([idx] * len(params_temp))

        # Compute similarity matrix [len(params_from) x len(params_to)]
        params_sim = LLMClient.similarity(
            emb1=np.array([param.embedding for param in params_from]),
            emb2=np.array([param.embedding for param in params_to]),
        )

        # Find all (i,j) pairs above threshold using vectorized operations
        threshold_mask = params_sim > self.build_edge_threshold
        rows, cols = np.where(threshold_mask) # sim[row][col] > threshold

        # Create edges
        tool_edges_needed = set()
        param_edges_needed = set()
        
        for i, j in zip(rows, cols):
            param_out = params_from[i]
            param_in = params_to[j]
            
            tool_edges_needed.add((node_from, nodes_to[params_to_pos[j]]))
            if param_out is not param_in:
                param_edges_needed.add((param_out, param_in))

        for src_node, dst_node in tool_edges_needed:
            if not self.graph.has_edge(src_node, dst_node):
                self.graph.add_edge(src_node, dst_node, edge_type=EdgeType.Tool_Depend)

        for param_out, param_in in param_edges_needed:
            if not self.graph.has_edge(param_out, param_in):
                self.graph.add_edge(param_out, param_in, edge_type=EdgeType.Parameter_Relate)

    def validate_parameter(self, param_in: Parameter, visited_nodes: list[Tool]) -> bool:
        """
        Check if an input parameter can be provided by users or visited tools.
        """
        # This param can be provided by user
        try:
            if param_in.user_provided:
                return True
        except Exception:
            pass  # Continue to check tool-provided

        # This param can be provided by visited tools
        for visited_node in visited_nodes:
            # Check 1: Is `param_in` a *direct output* of the visited_node?
            # (This handles cases where input/output params were merged)
            edge_data = self.graph.get_edge_data(visited_node, param_in)
            if edge_data and edge_data.get("edge_type") == EdgeType.Tool_Output:
                return True

            # Check 2: Is `param_in` fed by an *output parameter* of visited_node?
            # (Checks for Tool -> param_out -> param_in)
            for param_out in visited_node.output_schema["parameters"]:
                edge_data = self.graph.get_edge_data(param_out, param_in)
                if (
                    edge_data
                    and edge_data.get("edge_type") == EdgeType.Parameter_Relate
                ):
                    return True

        return False
    
    def validate_tool(self, tool: Tool, visited_nodes: list[Tool]) -> bool:
        params_in = tool.input_schema['parameters']
        return all([self.validate_parameter(param_in, visited_nodes) for param_in in params_in])

    def validate_tool_chain(self, tool_chain: list[Tool]) -> bool:
        """
        Validate that all parameters in the tool chain can be provided.
        Required parameters are checked first and must be satisfied.
        """
        for end in range(len(tool_chain)):
            prefix = tool_chain[:end]  # 只能用前面的工具
            tool = tool_chain[end]
            
            # Separate required and optional parameters
            required_params = []
            optional_params = []
            
            for param_in in tool.input_schema["parameters"]:
                # Check if this parameter is required by examining the edge
                edge_data = self.graph.get_edge_data(param_in, tool)
                is_required = edge_data.get("required", False) if edge_data else False
                
                if is_required:
                    required_params.append(param_in)
                else:
                    optional_params.append(param_in)
            
            # First, validate all required parameters (must be satisfied)
            for param_in in required_params:
                if not self.validate_parameter(param_in, visited_nodes=prefix):
                    return False
            
            # Then, validate optional parameters (should be satisfied if possible)
            for param_in in optional_params:
                if not self.validate_parameter(param_in, visited_nodes=prefix):
                    # Optional parameters can be missing, but we still check for completeness
                    pass
            
        return True

    def audit_and_patch_unfillable_parameters(
        self, auto_patch: bool = False
    ) -> list[dict]:
        """
        Audits input parameters to check if they can be filled by users or any tool in the graph.

        If auto_patch=True, this method automatically patches any "orphan" parameters
        by setting their 'user_provided' attribute to True, making the graph more robust.

        Args:
            auto_patch (bool):
                - False (default): Only checks and reports problems.
                - True: Checks and automatically patches problems by setting user_provided=True.

        Returns:
            list[dict]: A list of problematic parameter details, including patch status.
        """
        problematic_params = []

        # Get all tool nodes ONCE
        all_tool_nodes = [node for node in self.graph.nodes() if isinstance(node, Tool)]

        for tool in all_tool_nodes:
            # Find all *actual* input parameter nodes for this tool in the graph
            actual_input_params = []
            for node in self.graph.predecessors(tool):
                if isinstance(node, Parameter):
                    edge_data = self.graph.get_edge_data(node, tool)
                    if edge_data and edge_data.get("edge_type") == EdgeType.Tool_Input:
                        actual_input_params.append(node)

            for param_in in actual_input_params:
                # Get the edge data to check if this parameter is required
                edge_data_input = self.graph.get_edge_data(param_in, tool)
                is_required = edge_data_input.get("required", False) if edge_data_input else False

                # Check 1: Can it be provided by users?
                can_be_user_provided = param_in.user_provided if param_in.user_provided else False
                if can_be_user_provided:
                    continue

                # Check 2: Can it be provided by ANY tool in the graph?
                can_be_tool_provided = False
                providing_tools = []  # We need to capture this

                # Check against ALL tools in the graph
                for provider_tool in all_tool_nodes:

                    # Logic 2a: Is `param_in` a *direct output* of `provider_tool`?
                    edge_data_out = self.graph.get_edge_data(provider_tool, param_in)
                    if (
                        edge_data_out
                        and edge_data_out.get("edge_type") == EdgeType.Tool_Output
                    ):
                        can_be_tool_provided = True
                        if provider_tool not in providing_tools:
                            providing_tools.append(provider_tool)

                    # Logic 2b: Is `param_in` fed by an *output parameter* of `provider_tool`?
                    for param_out in provider_tool.output_schema["parameters"]:
                        edge_data_rel = self.graph.get_edge_data(param_out, param_in)
                        if (
                            edge_data_rel
                            and edge_data_rel.get("edge_type")
                            == EdgeType.Parameter_Relate
                        ):
                            can_be_tool_provided = True
                            if provider_tool not in providing_tools:
                                providing_tools.append(provider_tool)

                # If it's not user-provided AND not tool-provided, it's a problem.
                if not can_be_tool_provided:
                    problem_details = {
                        "tool": tool,
                        "parameter": param_in,
                        "is_required": is_required,
                        "can_be_user_provided": can_be_user_provided,
                        "can_be_tool_provided": False,
                        "providing_tools": [],
                        "patched": False,
                    }
                    if auto_patch:
                        param_in.set_user_provided(True)
                        problem_details["patched"] = True

                    problematic_params.append(problem_details)

        return problematic_params

    def subgraph(self, servers: list[str]) -> "ToolGraph":
        # Include tools
        tools = []
        for server in servers:
            tools.extend(self.server_to_tools[server])

        if not tools:
            return nx.DiGraph()
        
        # Include parameters
        params = set()
        for tool in tools:
            for pred in self.graph.predecessors(tool):
                if isinstance(pred, Parameter):
                    params.add(pred)
            for succ in self.graph.successors(tool):
                if isinstance(succ, Parameter):
                    params.add(succ)

        # Construct subgraph
        nodes = set(tools).union(params)
        subgraph = self.graph.subgraph(nodes).copy()
        return ToolGraph(
            graph = subgraph,
            ignore_tool_class = self.ignore_tool_class,
            build_edge_threshold = self.build_edge_threshold,
            merge_param_threshold = self.merge_param_threshold,
        )

    def sample(
        self, sampler, max_nodes: int = 10, start_node: Tool = None, seed: int = 42
    ) -> ToolQueryChain:
        """
        Starting from a node and perform BFS to randomly sample a tool chain.

        Args:
            sampler: Sampler instance to use for sampling.
            max_nodes: Maximum number of nodes in the sampled tool chain.
            start_node: Optional starting node name. If None, a random node is selected.
            seed: Optional random seed.

        Returns:
            A sampled tool chain.
        """
        random.seed(seed)

        # Select a starting node
        if start_node is None or start_node not in self.graph or not isinstance(start_node, Tool):
            start_node = random.choice([n for n in self.graph.nodes() if isinstance(n, Tool)])

        # Perform BFS to sample nodes
        visited = []
        queue = deque([start_node])

        while queue and len(visited) < max_nodes:
            current_node = queue.popleft()

            # Sample priors (dependencies)
            sampled_priors = sampler.sample_prior(
                self, current_node, visited_nodes=visited
            )
            for prior in sampled_priors:
                if prior not in visited:
                    visited.append(prior)

            visited.append(current_node)

            # Sample neighbors
            sampled_neighbors = sampler.sample(
                self, current_node, visited_nodes=visited
            )

            # Randomly sample another nodes in the same server
            if not sampled_neighbors:
                next_node = random.choice(
                    self.server_to_tools[current_node.server]
                )
                queue.append(next_node)

            for neighbor in sampled_neighbors:
                queue.append(neighbor)

        return ToolQueryChain(visited, seed=seed)

    def visualize(self, figsize: tuple = (20, 15), seed: int = 42, tool_only: bool = False, save_path: str = None):
            """
            Optimized visualization for ToolGraph to reduce clutter and improve readability.
            """
            plt.figure(figsize=figsize)
            
            # 1. Filter nodes
            if tool_only:
                nodes_to_draw = [n for n in self.graph.nodes() if isinstance(n, Tool)]
                subgraph = self.graph.subgraph(nodes_to_draw).copy()
                # Keep only Tool->Tool edges for cleaner view
                edges_to_keep = [(u, v) for u, v, d in subgraph.edges(data=True) 
                            if d.get("edge_type") == EdgeType.Tool_Depend]
                # Create a new graph with only these edges to avoid drawing isolated param edges
                temp_graph = nx.DiGraph()
                temp_graph.add_nodes_from(nodes_to_draw)
                temp_graph.add_edges_from(edges_to_keep)
                # Copy node attributes/edges data if needed, but for layout we just need structure
                subgraph = temp_graph
            else:
                subgraph = self.graph
                nodes_to_draw = list(subgraph.nodes())

            if len(nodes_to_draw) == 0:
                print("No nodes to visualize.")
                return

            # 2. Advanced Layout Calculation
            print("Calculating layout...")
            # Use Kamada-Kawai for better global structure (less clumping), fallback to Spring for very large graphs
            try:
                if len(nodes_to_draw) < 500:
                    pos = nx.kamada_kawai_layout(subgraph, scale=2.0)
                else:
                    # Optimized Spring Layout: high k value pushes nodes apart
                    pos = nx.spring_layout(subgraph, k=2.0, iterations=200, seed=seed, scale=2.0)
            except Exception:
                pos = nx.spring_layout(subgraph, k=2.0, iterations=200, seed=seed, scale=2.0)

            # 3. Categorize Nodes for Styling
            tools = [n for n in nodes_to_draw if isinstance(n, Tool)]
            params = [n for n in nodes_to_draw if isinstance(n, Parameter)]
            
            # Prepare Colors
            if hasattr(self, 'server_to_tools') and self.server_to_tools:
                unique_servers = sorted(list(self.server_to_tools.keys()))
            else:
                unique_servers = sorted(list(set(n.server for n in tools)))
            
            # Color map for servers
            cmap = cm.get_cmap('tab20', len(unique_servers) + 1)
            server_color_dict = {server: cmap(i) for i, server in enumerate(unique_servers)}
            
            # Tool Colors
            tool_colors = [server_color_dict.get(n.server, "lightgrey") for n in tools]
            
            # Parameter Colors & Sizes (Based on attributes)
            param_colors = []
            param_sizes = []
            for p in params:
                is_required_for_any = False
                for succ in subgraph.successors(p):
                    edge_data = subgraph.get_edge_data(p, succ)
                    if edge_data and edge_data.get("required", False):
                        is_required_for_any = True
                        break
                
                if p.user_provided:
                    param_colors.append("#90EE90") # Green
                    param_sizes.append(300)
                elif is_required_for_any:
                    param_colors.append("#FFB6C1") # Pink/Red
                    param_sizes.append(250)
                else:
                    param_colors.append("#E0E0E0") # Grey for optional
                    param_sizes.append(150)

            ax = plt.gca()

            # 4. Draw Edges (Draw first so they are behind nodes)
            # Split edges by type
            tool_edges = []
            param_edges = []
            
            for u, v, data in subgraph.edges(data=True):
                if isinstance(u, Tool) and isinstance(v, Tool):
                    tool_edges.append((u, v))
                else:
                    param_edges.append((u, v))

            # Draw Parameter Edges (Thinner, Lighter, Straight or slightly curved)
            if param_edges:
                nx.draw_networkx_edges(
                    subgraph, pos, edgelist=param_edges,
                    edge_color='#D3D3D3',  # Light Gray
                    width=0.8, alpha=0.4,
                    arrows=True, arrowsize=8,
                    node_size=300 # Helps arrows stop before center
                )

            # Draw Tool Edges (Thicker, darker, curved)
            if tool_edges:
                # Intra-server vs Inter-server styling could be added here
                nx.draw_networkx_edges(
                    subgraph, pos, edgelist=tool_edges,
                    edge_color='#555555', 
                    width=1.5, alpha=0.7,
                    connectionstyle="arc3,rad=0.15", # Curve to avoid overlap
                    arrowsize=15,
                    node_size=1500 # Helps arrows stop before center
                )

            # 5. Draw Nodes
            # Draw Parameters (Circles 'o')
            if params:
                nx.draw_networkx_nodes(
                    subgraph, pos, nodelist=params,
                    node_color=param_colors, node_size=param_sizes,
                    node_shape='o', alpha=0.85, linewidths=0.5, edgecolors='gray'
                )

            # Draw Tools (Squares 's') - Bigger and more distinct
            if tools:
                nx.draw_networkx_nodes(
                    subgraph, pos, nodelist=tools,
                    node_color=tool_colors, node_size=1500,
                    node_shape='s', alpha=1.0, linewidths=1.5, edgecolors='black'
                )

            # 6. Labels
            # Tool Labels (Bold, clear)
            tool_labels = {n: (n.name.split("-")[-1] if "-" in n.name else n.name) for n in tools}
            t_text = nx.draw_networkx_labels(subgraph, pos, labels=tool_labels, font_size=9, font_weight='bold')
            for _, t in t_text.items():
                t.set_bbox(dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

            # Parameter Labels (Smaller, only if not too cluttered)
            if len(nodes_to_draw) < 100: # Only label params if graph is not huge
                param_labels = {n: n.name for n in params}
                p_text = nx.draw_networkx_labels(subgraph, pos, labels=param_labels, font_size=7, font_color='#333333')
                for _, t in p_text.items():
                    t.set_bbox(dict(facecolor='white', alpha=0.4, edgecolor='none', pad=0.5))

            # 7. Legend (Outside plot)
            legend_handles = []
            for server, color in server_color_dict.items():
                legend_handles.append(mpatches.Patch(color=color, label=server))
            
            legend_handles.append(Line2D([0], [0], marker='s', color='w', markerfacecolor='grey', markeredgecolor='black', markersize=10, label='Tool'))
            legend_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='grey', markeredgecolor='grey', markersize=8, label='Parameter'))
            
            plt.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.02, 1), title="Components")
            
            plt.title(f"Tool Graph ({len(tools)} Tools, {len(params)} Params)", fontsize=16)
            plt.axis("off")
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Graph saved to {save_path}")
                
            plt.show()

    def visualize_interactive(self, filename: str = "tool_graph.html", tool_only: bool = False):
        """
        Final Optimized Visualization:
        - Dynamic Server Legend with colors.
        - Multi-server Checkbox Filtering.
        - Relational context preservation (Cross-server edges).
        - Clean Edges (No text labels).
        """
        try:
            from pyvis.network import Network
        except ImportError:
            print("Please install pyvis: pip install pyvis")
            return

        net = Network(height="900px", width="100%", directed=True, notebook=False)
        
        # 1. Physics & Stabilization (Optimized for complex graphs)
        options = {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -250, "centralGravity": 0.01,
                    "springLength": 150, "springStrength": 0.05,
                    "damping": 0.7, "overlap": 0
                },
                "solver": "forceAtlas2Based",
                "stabilization": {"enabled": True, "iterations": 1000, "fit": True},
                "minVelocity": 0.75
            },
            "edges": {"smooth": {"type": "cubicBezier", "roundness": 0.4}},
            "interaction": {"hover": True, "navigationButtons": True, "multiselect": True}
        }
        net.set_options(json.dumps(options))

        # 2. Node Processing
        tools_nodes = [n for n in self.graph.nodes() if isinstance(n, Tool)]
        unique_servers = sorted(list(set(t.server for t in tools_nodes)))
        cmap = cm.get_cmap('tab20', len(unique_servers))
        server_colors = {s: mcolors.to_hex(cmap(i)) for i, s in enumerate(unique_servers)}

        nodes_to_draw = tools_nodes if tool_only else list(self.graph.nodes())

        for node in nodes_to_draw:
            # Use id(node) for unique node ID to avoid collisions with same-name parameters
            node_id = str(id(node))
            if isinstance(node, Tool):
                label = node.name.split("-")[-1] if "-" in node.name else node.name
                color = server_colors.get(node.server, "#97C2FC")
                net.add_node(node_id, label=label, color=color, shape="box", size=30,
                            server=node.server, node_type="tool",
                            title=f"Tool: {node.name}\nServer: {node.server}")
            elif isinstance(node, Parameter):
                is_req = any(self.graph.get_edge_data(node, s).get('required', False)
                            for s in self.graph.successors(node) if self.graph.has_edge(node, s))
                # Color Mapping: Green (User Provided), Red (Required), Grey (Optional)
                bg_color = "#2ECC71" if node.user_provided else ("#E74C3C" if is_req else "#BDC3C7")
                # Include description in title for parameters to distinguish same-named ones
                title = f"Parameter: {node.name}\nType: {node.data_type}\nDescription: {node.description[:100]}{'...' if len(node.description) > 100 else ''}"
                net.add_node(node_id, label=node.name, color=bg_color, shape="dot", size=15,
                            node_type="parameter", title=title)

        # 3. Edge Processing (Removed Labels)
        subgraph = self.graph.subgraph(nodes_to_draw)
        for u, v, data in subgraph.edges(data=True):
            if tool_only and data.get("edge_type") != EdgeType.Tool_Depend: continue
            u_id, v_id = str(id(u)), str(id(v))
            
            edge_color = "#3498DB"
            width = 2
            
            if isinstance(u, Tool) and isinstance(v, Tool):
                if u.server != v.server:
                    edge_color = "#E67E22" # Visual distinction for cross-server
                    width = 3
            elif data.get("required"):
                edge_color = "#E74C3C" # Visual distinction for required path
                
            net.add_edge(u_id, v_id, color=edge_color, width=width)

        # 4. Constructing Server Checkboxes and Dynamic Legend
        server_checkboxes_html = ""
        server_legend_html = ""
        for s in unique_servers:
            color = server_colors[s]
            server_checkboxes_html += f"""
                <div style="margin-bottom: 3px;">
                    <input type="checkbox" class="server-checkbox" value="{s}" id="chk_{s}" checked onchange="applyRelationalFilter()">
                    <label for="chk_{s}" style="cursor:pointer;">{s}</label>
                </div>"""
            server_legend_html += f"""
                <div style="display: flex; align-items: center; margin-bottom: 2px;">
                    <span style="display:inline-block; width:12px; height:12px; background:{color}; margin-right:5px; border-radius:2px;"></span>
                    <span>{s}</span>
                </div>"""

        # 5. Injecting HTML/JS
        control_panel = f"""
        <div id="graph-control" style="
            position: absolute; top: 10px; right: 10px; width: 280px; max-height: 90vh;
            background: rgba(255,255,255,0.98); border: 1px solid #ccc; 
            padding: 15px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            font-size: 13px; z-index: 1000; overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15); border-radius: 10px;">
            
            <h3 style="margin: 0 0 12px 0; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px;">Tool Graph Explorer</h3>
            
            <button onclick="togglePhysics()" style="width:100%; padding:8px; margin-bottom:15px; cursor:pointer; background:#34495e; color:white; border:none; border-radius:4px; font-weight:bold;">
                Freeze / Unfreeze Layout
            </button>

            <div style="margin-bottom: 15px;">
                <b style="color: #34495e;">Filter Servers:</b>
                <div style="margin-top: 8px; background: #f9f9f9; padding: 10px; border-radius: 5px; border: 1px solid #eee;">
                    {server_checkboxes_html}
                </div>
                <button onclick="setAllCheckboxes(true)" style="margin-top:5px; font-size:11px; cursor:pointer;">Select All</button>
                <button onclick="setAllCheckboxes(false)" style="margin-top:5px; font-size:11px; cursor:pointer;">Clear All</button>
            </div>

            <div id="visual-legend" style="line-height: 1.5; border-top: 1px solid #eee; pt: 10px;">
                <b style="color: #34495e;">Server Map:</b><br>
                <div style="margin: 8px 0;">{server_legend_html}</div>
                
                <b style="color: #34495e;">Node Status:</b><br>
                <span style="color:#2ECC71;">●</span> User Provided<br>
                <span style="color:#E74C3C;">●</span> Required Parameter<br>
                <span style="color:#BDC3C7;">●</span> Optional Parameter<br>
                
                <b style="color: #34495e; display:block; margin-top:8px;">Edge Guide:</b>
                <div style="display:flex; align-items:center;"><div style="border-top: 2px solid #3498DB; width:20px; margin-right:8px;"></div> Internal</div>
                <div style="display:flex; align-items:center;"><div style="border-top: 3px solid #E67E22; width:20px; margin-right:8px;"></div> Cross-Server</div>
            </div>
        </div>

        <script>
        var physicsEnabled = true;
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
        }}

        function setAllCheckboxes(state) {{
            document.querySelectorAll('.server-checkbox').forEach(cb => cb.checked = state);
            applyRelationalFilter();
        }}

        function applyRelationalFilter() {{
            var checkedServers = Array.from(document.querySelectorAll('.server-checkbox:checked')).map(cb => cb.value);
            var allNodes = nodes.get();
            var allEdges = edges.get();
            
            if (checkedServers.length === 0) {{
                nodes.update(allNodes.map(n => ({{id: n.id, hidden: true}})));
                return;
            }}

            // 1. Target Tools: All tools in any of the checked servers
            var targetToolIds = allNodes.filter(n => n.node_type === 'tool' && checkedServers.includes(n.server)).map(n => n.id);
            
            // 2. Context: Anything directly connected to these tools
            var relevantNodeIds = new Set(targetToolIds);
            allEdges.forEach(edge => {{
                if (targetToolIds.includes(edge.from) || targetToolIds.includes(edge.to)) {{
                    relevantNodeIds.add(edge.from);
                    relevantNodeIds.add(edge.to);
                }}
            }});

            // 3. Update visibility
            nodes.update(allNodes.map(node => ({{
                id: node.id,
                hidden: !relevantNodeIds.has(node.id)
            }})));
            
            // Optional: network.fit(); // Uncomment if you want to zoom to results
        }}
        </script>
        """

        net.save_graph(filename)
        with open(filename, 'r') as f: html_content = f.read()
        updated_html = html_content.replace('</body>', f'{control_panel}</body>')
        with open(filename, 'w') as f: f.write(updated_html)
        print(f"Interactive ToolGraph optimized and saved to {filename}")

    def save(self, filepath: str | Path):
        """
        Save the ToolGraph to a file using pickle.

        Args:
            filepath: Path to save the graph (should have .pkl extension)
        """
        filepath = Path(filepath)
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data to save - include all instance attributes
        save_data = {
            "graph": self.graph,
            "ignore_tool_class": self.ignore_tool_class,
            "build_edge_threshold": self.build_edge_threshold,
            "merge_param_threshold": self.merge_param_threshold,
            "server_to_tools": getattr(self, 'server_to_tools', {}),  # Safely get server_to_tools if it exists
        }

        with open(filepath, "wb") as f:
            pickle.dump(save_data, f)

        # Calculate statistics for better output
        num_tools = len([n for n in self.graph.nodes() if isinstance(n, Tool)])
        num_params = len([n for n in self.graph.nodes() if isinstance(n, Parameter)])
        num_servers = len(save_data["server_to_tools"]) if save_data["server_to_tools"] else 0

        print(f"ToolGraph saved to {filepath}")
        print(f"  - Nodes: {self.graph.number_of_nodes()} (Tools: {num_tools}, Parameters: {num_params})")
        print(f"  - Edges: {self.graph.number_of_edges()}")
        if num_servers > 0:
            print(f"  - Servers: {num_servers}")

    @classmethod
    def load(cls, filepath: str | Path):
        """
        Load a ToolGraph from a saved file.

        Args:
            filepath: Path to the saved graph file

        Returns:
            Loaded ToolGraph instance
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Graph file not found: {filepath}")

        with open(filepath, "rb") as f:
            save_data = pickle.load(f)

        # Create new ToolGraph instance with loaded data
        # Use default values from __init__ for backward compatibility
        tool_graph = cls(
            graph=save_data["graph"],
            ignore_tool_class=save_data.get("ignore_tool_class", False),
            build_edge_threshold=save_data.get("build_edge_threshold", 0.75),
            merge_param_threshold=save_data.get("merge_param_threshold", 0.92),
        )

        # Restore server_to_tools if it exists in saved data
        server_to_tools = save_data.get("server_to_tools", {})
        if server_to_tools:
            tool_graph.server_to_tools = server_to_tools
        else:
            # Initialize empty dict if not present (for backward compatibility)
            tool_graph.server_to_tools = {}

        # Calculate statistics for better output
        num_tools = len([n for n in tool_graph.graph.nodes() if isinstance(n, Tool)])
        num_params = len([n for n in tool_graph.graph.nodes() if isinstance(n, Parameter)])
        num_servers = len(tool_graph.server_to_tools) if tool_graph.server_to_tools else 0

        # Print loading information
        print(f"ToolGraph loaded from {filepath}")
        print(f"  - Nodes: {tool_graph.graph.number_of_nodes()} (Tools: {num_tools}, Parameters: {num_params})")
        print(f"  - Edges: {tool_graph.graph.number_of_edges()}")
        if num_servers > 0:
            print(f"  - Servers: {num_servers}")
        print(f"  - Build edge threshold: {tool_graph.build_edge_threshold}")
        print(f"  - Merge param threshold: {tool_graph.merge_param_threshold}")
        print(f"  - Ignore tool class: {tool_graph.ignore_tool_class}")

        return tool_graph
