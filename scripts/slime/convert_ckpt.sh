#!/usr/bin/env bash
# HF Qwen3 -> Megatron torch_dist reference checkpoint for scripts/slime/run_grpo.sh.
set -euo pipefail
die() { echo "$*" >&2; exit 1; }

if [ -n "${SLIME_ACTIVATE_SCRIPT:-}" ]; then
    source "$SLIME_ACTIVATE_SCRIPT"
fi

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SLIME_DIR=${SLIME_DIR:-$PROJECT_DIR/slime}
MEGATRON_LM_DIR=${MEGATRON_LM_DIR:?Set MEGATRON_LM_DIR to a Megatron-LM checkout compatible with slime.}
MODEL_SIZE=${MODEL_SIZE:-4B}  # 1.7B | 4B | 8B
MODEL_PATH=${MODEL_PATH:?Set MODEL_PATH to the HF checkpoint.}
REF_LOAD=${REF_LOAD:-${MODEL_PATH}_torch_dist}

[ -d "$MODEL_PATH" ] || die "HF checkpoint not found at $MODEL_PATH."
[ -f "$SLIME_DIR/tools/convert_hf_to_torch_dist.py" ] || die "Slime converter not found under $SLIME_DIR; run: git submodule update --init."
[ -f "$SLIME_DIR/scripts/models/qwen3-${MODEL_SIZE}.sh" ] || die "No slime model definition for qwen3-${MODEL_SIZE}."

export PYTHONPATH="${SLIME_DIR}:${MEGATRON_LM_DIR}:${PYTHONPATH:-}"
export HF_HUB_OFFLINE=1 CUDA_DEVICE_MAX_CONNECTIONS=1
source "${SLIME_DIR}/scripts/models/qwen3-${MODEL_SIZE}.sh"

cd "${SLIME_DIR}"
python3 -m torch.distributed.run --nproc-per-node 1 tools/convert_hf_to_torch_dist.py \
    "${MODEL_ARGS[@]}" \
    --hf-checkpoint "${MODEL_PATH}" \
    --save "${REF_LOAD}"
