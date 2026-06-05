<div align="center">

# EnvFactory

**EnvFactory: Scaling Tool-Use Agents via Executable Environments Synthesis and Robust RL**

<a href="https://github.com/LARK-AI-Lab/EnvFactory"><img src="https://img.shields.io/badge/GitHub-Repo-black?style=for-the-badge&logo=github" alt="GitHub"></a>
<a href="https://huggingface.co/collections/LARK-Lab/envfactory"><img src="https://img.shields.io/badge/HuggingFace-Models-yellow?style=for-the-badge&logo=huggingface" alt="HuggingFace"></a>
<a href="https://arxiv.org/abs/2605.18703"><img src="https://img.shields.io/badge/ArXiv-Paper-red?style=for-the-badge&logo=arxiv" alt="Arxiv"></a>
<a href="https://lark-ai-lab.github.io/envfactory.github.io/"><img src="https://img.shields.io/badge/Homepage-Website-blue?style=for-the-badge&logo=googlechrome" alt="Homepage"></a>

---

</div>

## 📒 Models & Dataset

<div align="center">

| | Type | Name | Size |
|:---:|:---:|------|:-----------:|
| 🤖 | Model | [EnvFactory-1.7B](https://huggingface.co/LARK-Lab/EnvFactory-1.7B) | 1.7B |
| 🤖 | Model | [EnvFactory-4B](https://huggingface.co/LARK-Lab/EnvFactory-4B) | 4B |
| 🤖 | Model | [EnvFactory-8B](https://huggingface.co/LARK-Lab/EnvFactory-8B) | 8B |
| 📂 | Dataset | [EnvFactory-RL](https://huggingface.co/datasets/LARK-Lab/EnvFactory-RL) | RL Data (3.09k) |
| 📂 | Dataset | [EnvFactory-SFT-FILTERED](https://huggingface.co/datasets/LARK-Lab/EnvFactory-SFT-FILTERED) | Filtered SFT Data (53.4k) |
| 📂 | Dataset | [EnvFactory-SFT-ALL](https://huggingface.co/datasets/LARK-Lab/EnvFactory-SFT-ALL) | Full SFT Data (26.5k) |

</div>

---

## 🔧 Quick Start

### Environment Setup

```bash
conda create -n EnvFactory python=3.12
conda activate EnvFactory

git clone https://github.com/LARK-AI-Lab/EnvFactory
cd EnvFactory

pip install -e ".[sglang]" # or pip install -e ".[vllm]"
```
* Note that if you want to host models locally, you may use `SGLang` or `vLLM` depends on your settings. In our experiments, we use `SGLang==0.5.9` and serve models through [`src/serve/sglang.sh`](src/serve/sglang.sh). Any version of SGLang and vLLM are supported as long as it can successfully serve your local models.

### Environment Variables

Create a `.env` file with your API keys:

```dotenv
# Default MCP configuration path
MCP_CONFIG_PATH=configs/mcp_server.json

# Embedding model
EMBEDDING_URL=https://api.siliconflow.cn/v1/embeddings
EMBEDDING_API_KEY=...
EMBEDDING_MODEL=BAAI/bge-m3

# Chat model
CHAT_URL=https://api.deepseek.com
CHAT_API_KEY=...
CHAT_MODEL=deepseek-chat

# Provider: DeepSeek
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Provider: SGLang / vLLM
SGLANG_BASE_URL_PORT=8000
SGLANG_BASE_URL=http://localhost:${SGLANG_BASE_URL_PORT}/v1
SGLANG_API_KEY=placeholder
SGLANG_MODEL=Qwen/Qwen3-30B-A3B-Thinking-2507
```

> [!TIP]
> - See `PROVIDER_MAPPING` in [`src/gen/__init__.py`](src/gen/__init__.py) for supported providers.
> - Use [`src/serve/sglang.sh`](src/serve/sglang.sh) and [`src/serve/vllm.sh`](src/serve/vllm.sh) to serve local models.

---

## 🌍 Environment Construction

Environment construction follows a **discovery-to-validation** pipeline:

```
Schema Sketch  →  MCP Metadata  →  Executable Environment  →  Validation
```

**1. Discover** new schema sketches with [`mcp-sketch-discovery`](mcp-sketch-discovery/SKILL.md). The workflow scans existing sketches, searches for non-AI utility APIs, and drafts new candidates under [`envs/schema_sketch`](envs/schema_sketch).

**2. Generate** standardized MCP metadata from a schema sketch:

```bash
python -m src.gen.mcp_schema_gen envs/schema_sketch/calendar_server.py \
  --output envs/metadata/Calendar_metadata.json
```

> If `--output` is omitted, the metadata is saved to `envs/metadata/{class_name}_metadata.json`.

**3. Validate** the executable MCP environment:

```bash
python -m src.gen.env_gen envs/metadata/Calendar_metadata.json
```

This generates the MCP tool implementation, creates validation scenarios, registers the server in [`configs/mcp_server.json`](configs/mcp_server.json), and runs a validation-revision loop.

**Generated artifacts:**

| Directory | Contents |
|-----------|----------|
| [`envs/schema_sketch`](envs/schema_sketch) | Schema sketches and discovery notes |
| [`envs/metadata`](envs/metadata) | Standardized MCP metadata |
| [`envs/tools`](envs/tools) | Executable MCP tool servers |
| [`envs/intermediate`](envs/intermediate) | Checkpoints for resume and debugging |

**Batch generation & recovery:**

```bash
python -m src.gen.env_gen envs/metadata/*.json --max-concurrent-files 5
python -m src.gen.env_gen --resume envs/intermediate/Calendar_checkpoint.json
```

---

## 📦 Tool-use Trajectories Synthesis

1. Follow the example in [`examples/load_tool_graph.ipynb`](examples/load_tool_graph.ipynb) to save `graph.pkl` locally.
2. Run [`examples/synthesize_query.py`](examples/sythesize_query.py) to synthesize tool-use trajectories.

---

## 📊 Data Processing

After generation, convert the data into SFT and RL training formats:

```bash
bash examples/process_data.sh
```

To visualize the generation pipeline, run [`src/app/app.py`](src/app/app.py).

---

## 🚄 SFT

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

---

## 🚄 RL

We use the forked [VeRL](https://github.com/RolandXMR/verl) for RL training. Please refer to the [README](https://github.com/RolandXMR/verl/tree/main/EnvFactory) for files we modified.

---

## ✨ Citation

If you find our work helpful, please consider citing:

```bibtex
@misc{xu2026envfactoryscalingtooluseagents,
      title={EnvFactory: Scaling Tool-Use Agents via Executable Environments Synthesis and Robust RL}, 
      author={Minrui Xu and Zilin Wang and Mengyi DENG and Zhiwei Li and Zhicheng Yang and Xiao Zhu and Yinhong Liu and Boyu Zhu and Baiyu Huang and Chao Chen and Heyuan Deng and Fei Mi and Lifeng Shang and Xingshan Zeng and Zhijiang Guo},
      year={2026},
      eprint={2605.18703},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2605.18703}, 
}
```
