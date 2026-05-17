# EnvFactory
This is the official implementation of EnvFactory: Scaling Tool-Use Agents via Executable Environments Synthesis and Robust RL.

## Quick Start
### Environment Setup
```
conda create -n EnvFactory python=3.12
conda activate EnvFactory

git clone https://github.com/LARK-AI-Lab/EnvFactory
cd EnvFactory

pip install -e .[vllm] 
```

### Set Environment Variables
Create a `.env` with your API keys as follow:
```
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
* Refer to `PROVIDER_MAPPING` from `EnvFactory/src/gen/__init__.py`.
* Use `src/serve/sglang.sh` and `src/serve/vllm.sh` to serve local models.

## Environment Construction
TODO (@Zilin)

## Tool-use Trajectories Synthesis
Firstly, following the example from `examples/load_tool_graph.ipynb` to save `graph.pkl` locally.
Next, you may use the example from `examples/sythesize_query.py` to sythesize tool-use trajectories.

## Data Process
After generation, you can use `bash examples/process_data.sh` to convert to the SFT and RL training format.
If you want to visualize the generation pipeline, you can use `src/app/app.py`.

## SFT
We use LlamaFactory (https://github.com/hiyouga/LLaMAFactory) to conduct SFT training.
You need to include data info as follow:
```
"env_factory_sft": {
    "file_name": "env_factory_sft.json",
    "formatting": "alpaca",
    "columns": {
        "prompt": "instruction",
        "query": "input",
        "response": "output",
        "history": "history",
        "system": "system",
    }
}
```
We use the SFT config from `configs/llamafactory_sft.yaml`

## RL
TODO (@Minrui)