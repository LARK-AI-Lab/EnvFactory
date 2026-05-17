#!/bin/bash
# SGLang is a fast serving framework for large language models and vision language models.
# https://github.com/sgl-project/sglang

set -a
source .env
set +a

module load gcc/11.5 # Based on your own GCC version

export HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=0,1

echo "Serving SGLang model '$SGLANG_MODEL' at ${SGLANG_BASE_URL}"
python -m sglang.launch_server \
  --model-path "$SGLANG_MODEL" \
  --port "$SGLANG_BASE_URL_PORT" \
  --tp-size 2 \
  --mem-fraction-static 0.9 \
  --context-length 65536 \
  --dtype bfloat16 \
  --trust-remote-code \
  --api-key "$SGLANG_API_KEY" \
  --reasoning-parser qwen3
