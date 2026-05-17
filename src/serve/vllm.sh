#!/bin/bash
# vLLM is a high-throughput and memory-efficient inference and serving engine for LLMs.
# https://github.com/vllm-project/vllm

set -a
source .env
set +a

export HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=4,5

echo "Serving model '$VLLM_MODEL' at ${VLLM_BASE_URL}"
vllm serve "$VLLM_MODEL" \
  --port $VLLM_BASE_URL_PORT \
  --tensor-parallel-size 2 \
  --data-parallel-size 1 \
  --gpu-memory-utilization 0.92 \
  --enable-expert-parallel \
  --max-model-len 65536 \
  --dtype bfloat16 \
  --trust-remote-code \
  --disable-log-requests
