from abc import ABC, abstractmethod
import random
from src.graph.tool_graph import Parameter, Tool, ToolGraph

class Sampler(ABC):
    """Abstract base class for tool sampling strategies."""

    def sample_prior(self, graph: ToolGraph, node: Tool, *args, **kwargs) -> list[Tool]:
        """
        Sample prior nodes (dependencies) given a target node.
        The prior nodes are sampled BEFORE executing the target node itself.

        Args:
            graph: The ToolGraph instance.
            node: The Tool node to find dependencies for.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list[Tool]: List of sampled Tool priors.
        """
        return []

    @abstractmethod
    def sample(self, graph: ToolGraph, node: Tool, *args, **kwargs) -> list[Tool]:
        """
        Sample successor neighbors from a node.
        The neighbors are sampled AFTER executing the target node itself.

        Args:
            graph: The ToolGraph instance.
            node: The Tool node to sample neighbors from.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list[Tool]: List of sampled Tool neighbors.
        """
        pass


class RandomWalkSampler(Sampler):
    """
    Random walk sampler that picks a single random successor neighbor.
    """

    def sample(self, graph: ToolGraph, node: Tool, *args, **kwargs) -> list[Tool]:
        """
        Sample a single random successor neighbor from the current node.

        Args:
            graph: The ToolGraph instance.
            node: The current Tool node.
            visited_nodes (kwargs): List of tools already visited.

        Returns:
            list[Tool]: A list containing one randomly chosen successor (or empty).
        """
        visited_nodes = kwargs.get('visited_nodes', [])
        candidates = [
            succ for succ in graph.graph.successors(node)
            if isinstance(succ, Tool) and succ not in visited_nodes
        ]
        if not candidates:
            return []
        return [random.choice(candidates)]


class TopologySampler(Sampler):
    """
    Topology-based sampler that recursively samples nodes based on dependency rules.
    It attempts to fill input parameters by finding previous tools that output them.
    """

    def __init__(self, max_servers: int = 3, max_recursion_depth: int = 5):
        """
        Initialize the TopologySampler.

        Args:
            max_servers: Maximum number of distinct servers allowed in the chain.
            max_recursion_depth: Maximum depth for recursive dependency sampling.
        """
        super().__init__()
        self.max_servers = max_servers
        self.max_recursion_depth = max_recursion_depth

    def _get_servers(self, tools: list[Tool]) -> list[str]:
        """Extract a list of unique server names from a list of tools."""
        servers = set()
        for tool in tools:
            servers.add(tool.server)
        return list(servers)

    def _get_priors(self, graph: ToolGraph, param: Parameter, tool: Tool) -> list[Tool]:
        """
        Find all tools that output the specific parameter `param`, excluding the `tool` itself.
        It checks direct Tool->Param edges and indirect Tool->Param->Param relations.
        """
        priors = []
        # Check direct predecessors of the parameter
        for pre in graph.graph.predecessors(param):
            if isinstance(pre, Tool) and pre != tool and pre not in priors:
                    priors.append(pre)
            elif isinstance(pre, Parameter):
                # Handle parameter merging (Param -> Param -> Tool)
                for pre2 in graph.graph.predecessors(pre):
                    if isinstance(pre2, Tool) and pre2 != tool and pre2 not in priors:
                        priors.append(pre2)
        return priors

    def choice(self, visited_nodes: list[Tool], candidate_nodes: list[Tool]) -> Tool | None:
        """
        Choose a tool from candidates, respecting the max_servers constraint.

        Args:
            visited_nodes: List of tools already in the chain.
            candidate_nodes: List of potential tools to pick next.

        Returns:
            Tool: The chosen tool, or None if no valid candidate exists.
        """
        servers = self._get_servers(visited_nodes)

        # If we reached the server limit, filter candidates to only allow tools from existing servers
        if len(servers) >= self.max_servers:
            candidate_nodes = [node for node in candidate_nodes if node.server in servers]

        if not candidate_nodes:
            return None

        return random.choice(candidate_nodes)

    def sample_prior(self, graph: ToolGraph, node: Tool, *args, **kwargs) -> list[Tool]:
        """
        Recursively sample priors for all required and invalid parameters of the given node.
        """
        visited_nodes = kwargs.get('visited_nodes', [])
        recursion_depth = kwargs.get('recursion_depth', 0)
        if recursion_depth >= self.max_recursion_depth:
            return []

        sampled_nodes = []
        current_visited_set = set(visited_nodes)
        parameters_in = node.input_schema['parameters']

        for param_in in parameters_in:
            # Check if parameter is required
            edge_data = graph.graph.get_edge_data(param_in, node)
            is_required = edge_data.get("required", False) if edge_data else False

            # Skip optional parameter with 60% chance
            if not is_required and random.random() < 0.6:
                continue

            # Check if parameter is valid
            is_valid = graph.validate_parameter(param_in, list(current_visited_set))

            # Skip valid parameter with 90% chance
            if is_valid and random.random() < 0.9:
                continue

            # Sample a prior for current parameter
            priors = self._get_priors(graph, param_in, node)
            prior = self.choice(list(current_visited_set), priors)

            # Recursively sample the prior for the prior
            if prior and prior not in current_visited_set:
                priors_of_prior = self.sample_prior(
                    graph,
                    prior,
                    visited_nodes=list(current_visited_set),
                    recursion_depth=recursion_depth + 1,
                )

                for prior_of_prior in priors_of_prior:
                    if prior_of_prior not in current_visited_set:
                        sampled_nodes.append(prior_of_prior)
                        current_visited_set.add(prior_of_prior)

                if prior not in current_visited_set:
                    sampled_nodes.append(prior)
                    current_visited_set.add(prior)

        return sampled_nodes

    def sample(self, graph: ToolGraph, node: Tool, *args, **kwargs) -> list[Tool]:
        """
        Sample one or few neighbors.

        Args:
            graph: The ToolGraph instance.
            node: The current Tool node.
            visited_nodes (kwargs): List of tools already visited.

        Returns:
            list[Tool]: A list of chosen neighbors.
        """
        visited_nodes = kwargs.get('visited_nodes', [])
        candidate_nodes = []

        # Identify successors in the graph
        for succ in graph.graph.successors(node):
            if isinstance(succ, Tool) and succ not in visited_nodes:
                candidate_nodes.append(succ)

        # Apply server constraint
        servers = self._get_servers(visited_nodes)
        if len(servers) >= self.max_servers:
            candidate_nodes = [n for n in candidate_nodes if n.server in servers]

        if not candidate_nodes:
            return []

        # Sample 1 to all outgoing neighbors uniformly
        num_to_sample = random.randint(1, len(candidate_nodes))
        return random.sample(candidate_nodes, num_to_sample)
