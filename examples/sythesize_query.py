import asyncio
import random
from src.graph.tool_graph import ToolGraph
from src.graph.sampler import RandomWalkSampler, TopologySampler
from src.gen.query_gen import QueryGenConfig, QueryGen
from src.gen.query_gen.preset_config import SFT_NON_CONV, SFT_CONV, RL_NON_CONV # preset configurations for convenience

random.seed(42)

# 1. Load your tool graph
graph = ToolGraph.load("graph.pkl")

# 2. Define the sampler you want to use
sampler = TopologySampler() # or RandomWalkSampler()

# 3. Define your own generation config or use preset configurations
config = SFT_CONV

# 4. Define number of trajectories you want to generate
N = 200

# Helper functions
async def generate_query(tool_chain, semaphore):
    async with semaphore:
        query_gen = QueryGen(graph, config)
        return await query_gen.gen(tool_chain)

async def main():
    seeds = random.sample(range(1, 100000), N)
    semaphore = asyncio.Semaphore(5)
    
    tasks = []
    for seed in seeds:
        tool_chain = graph.sample(sampler, max_nodes=15, seed=seed)
        tasks.append(generate_query(tool_chain, semaphore))

    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":
    asyncio.run(main())