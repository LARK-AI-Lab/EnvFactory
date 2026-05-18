# EnvFactory
This is the official implementation of **EnvFactory: Scaling Tool-Use Agents via Executable Environments Synthesis and Robust RL**.
<div align="center">

<a href="https://github.com/LARK-AI-Lab/EnvFactory" style="padding-right: 8px;"><img src="https://img.shields.io/badge/GitHub-Repo-black?style=flat&logo=github" alt="GitHub"></a>
<a href="https://huggingface.co/LARK-AI-Lab" style="padding-right: 8px;"><img src="https://img.shields.io/badge/HuggingFace-LARK--AI--Lab-yellow?style=flat&logo=huggingface" alt="HuggingFace"></a>
<a href="TODO" style="padding-right: 8px;"><img src="https://img.shields.io/badge/ArXiv-Paper-red?style=flat&logo=arxiv" alt="Arxiv"></a>
<a href="https://lark-ai-lab.github.io/envfactory.github.io/"><img src="https://img.shields.io/badge/Homepage-Website-blue?style=flat&logo=googlechrome" alt="Homepage"></a>

</div>

## Table of Contents

- [Quick Start](#quick-start)
- [Environment Construction](#environment-construction)
- [Tool-use Trajectories Synthesis](#tool-use-trajectories-synthesis)
- [Data Processing](#data-processing)
- [SFT Training](#sft)
- [RL Training](#rl)

## Quick Start
### Environment Setup
```bash
conda create -n EnvFactory python=3.12
conda activate EnvFactory

git clone https://github.com/LARK-AI-Lab/EnvFactory
cd EnvFactory

pip install -e ".[sglang]"
```

### Set Environment Variables
Create a `.env` file with your API keys as follows:

```dotenv
# 1. Default MCP configuration path
MCP_CONFIG_PATH=configs/mcp_server.json

# 2. General embedding and chat models
EMBEDDING_URL=https://api.siliconflow.cn/v1/embeddings
EMBEDDING_API_KEY=...
EMBEDDING_MODEL=BAAI/bge-m3

CHAT_URL=https://api.deepseek.com
CHAT_API_KEY=...
CHAT_MODEL=deepseek-chat

# 3. Provider configuration (pick one)
# DeepSeek
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 4. SGLang or vLLM
SGLANG_BASE_URL_PORT=8000
SGLANG_BASE_URL=http://localhost:${SGLANG_BASE_URL_PORT}/v1
SGLANG_API_KEY=placeholder
SGLANG_MODEL=Qwen/Qwen3-30B-A3B-Thinking-2507
```

- Refer to `PROVIDER_MAPPING` in [`src/gen/__init__.py`](src/gen/__init__.py) for supported providers.
- Use [`src/serve/sglang.sh`](src/serve/sglang.sh) and [`src/serve/vllm.sh`](src/serve/vllm.sh) to serve local models.

## Environment Construction
Environment construction follows a discovery-to-validation pipeline:

1. Discover new schema sketches with [`mcp-sketch-discovery`](mcp-sketch-discovery/SKILL.md). The workflow scans existing sketches, searches for non-AI utility APIs, and drafts new candidates under [`envs/schema_sketch`](envs/schema_sketch).

2. Generate standardized MCP metadata from a schema sketch:

```bash
python -m src.gen.mcp_schema_gen envs/schema_sketch/calendar_server.py \
  --output envs/metadata/Calendar_metadata.json
```

If `--output` is omitted, the metadata is saved to `envs/metadata/{class_name}_metadata.json`.

3. Generate and validate the executable MCP environment:

```bash
python -m src.gen.env_gen envs/metadata/Calendar_metadata.json
```

This step generates the MCP tool implementation, creates validation scenarios, registers the server in [`configs/mcp_server.json`](configs/mcp_server.json), and runs a validation-revision loop.

Generated artifacts are saved under:

- [`envs/schema_sketch`](envs/schema_sketch): schema sketches and discovery notes.
- [`envs/metadata`](envs/metadata): standardized MCP metadata.
- [`envs/tools`](envs/tools): executable MCP tool servers.
- [`envs/intermediate`](envs/intermediate): checkpoints for resume and debugging.

For batch generation or recovery:

```bash
python -m src.gen.env_gen envs/metadata/*.json --max-concurrent-files 5
python -m src.gen.env_gen --resume envs/intermediate/Calendar_checkpoint.json
```

## Tool-use Trajectories Synthesis
1. Follow the example in [`examples/load_tool_graph.ipynb`](examples/load_tool_graph.ipynb) to save `graph.pkl` locally.
2. Run [`examples/synthesize_query.py`](examples/sythesize_query.py) to synthesize tool-use trajectories.

## Data Processing
After generation, run [`examples/process_data.sh`](examples/process_data.sh) to convert the data into SFT and RL training formats:

```bash
bash examples/process_data.sh
```

To visualize the generation pipeline, run [`src/app/app.py`](src/app/app.py).

## SFT
We use [LlamaFactory](https://github.com/hiyouga/LLaMAFactory) for SFT training. Add the following entry to your dataset config:

```json
"env_factory_sft": {
    "file_name": "env_factory_sft.json",
    "formatting": "alpaca",
    "columns": {
        "prompt": "instruction",
        "query": "input",
        "response": "output",
        "history": "history",
        "system": "system"
    }
}
```

The SFT configuration is provided in [`configs/llamafactory_sft.yaml`](configs/llamafactory_sft.yaml).

## RL
We use the forked [VeRL](https://github.com/RolandXMR/verl) for RL training. Please refer to the [README](https://github.com/RolandXMR/verl/tree/main/EnvFactory) for files we modified.

## Citation
If you find our work helpful, please consider citing:
```
@misc{xu2026envfactoryscalingtooluseagents,
  title         = {EnvFactory: Scaling Tool-Use Agents via Executable Environments Synthesis and Robust RL},
  author        = {Minrui Xu and Zilin Wang and Mengyi Deng and Zhiwei Li and Zhicheng Yang and Xiao Zhu and Yinhong Liu and Boyu Zhu and Baiyu Huang and Chao Chen and Heyuan Deng and Fei Mi and Lifeng Shang and Xingshan Zeng and Zhijiang Guo},
  year          = {2026},
  eprint        = {todo},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {todo}
}
```