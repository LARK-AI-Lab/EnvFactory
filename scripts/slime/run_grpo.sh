#!/usr/bin/env bash
# GRPO | Qwen3 | slime (Megatron + SGLang) | EnvFactory multi-turn tool agent.
# Override paths and sizes through the environment; extra slime flags pass through "$@".

set -euo pipefail
die() { echo "$*" >&2; exit 1; }

# Optional: a script that activates the slime runtime (conda env, CUDA toolchain, ...).
if [ -n "${SLIME_ACTIVATE_SCRIPT:-}" ]; then
    source "$SLIME_ACTIVATE_SCRIPT"
fi

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SLIME_DIR=${SLIME_DIR:-$PROJECT_DIR/slime}
MEGATRON_LM_DIR=${MEGATRON_LM_DIR:?Set MEGATRON_LM_DIR to a Megatron-LM checkout compatible with slime.}
MODEL_SIZE=${MODEL_SIZE:-4B}  # 1.7B | 4B | 8B
MODEL_PATH=${MODEL_PATH:?Set MODEL_PATH to the HF checkpoint (e.g. the EnvFactory SFT model).}
REF_LOAD=${REF_LOAD:-$MODEL_PATH}  # slime loads the HF checkpoint directly; a torch_dist copy also works.
TRAIN_FILE=${TRAIN_FILE:-$PROJECT_DIR/data/rl_train.jsonl}
VAL_FILE=${VAL_FILE:-$PROJECT_DIR/data/rl_val.jsonl}
CUSTOM_CONFIG=${CUSTOM_CONFIG:-$PROJECT_DIR/configs/slime/envfactory.yaml}
CKPT_DIR=${CKPT_DIR:-$PROJECT_DIR/checkpoints_slime}
NNODES=${NNODES:-1}
NGPUS_PER_NODE=${NGPUS_PER_NODE:-8}
MASTER_ADDR=${MASTER_ADDR:-127.0.0.1}

project_name=${PROJECT_NAME:-EnvFactory}
# Rerunning with the same EXPERIMENT_NAME resumes from its latest checkpoint.
experiment_name=${EXPERIMENT_NAME:-${project_name}-Qwen3-${MODEL_SIZE}-grpo-$(date +%Y%m%d-%H%M)}

########################### user-adjustable ###########################
rollout_batch_size=256
n_samples_per_prompt=8
global_batch_size=512  # 4 optimizer steps per rollout.
max_prompt_length=16384  # Longer prompts are skipped (masked out), as verl's filter_overlong_prompts did.
max_response_length=8192  # Generated tokens per trajectory; observations only consume context.
max_context_length=$((max_prompt_length + max_response_length))

actor_lr=1e-6
kl_loss_coef=0.001
rollout_temperature=0.7

num_epoch=10
save_interval=20
eval_interval=5

case ${MODEL_SIZE} in
    1.7B) TP_SIZE=1; ROLLOUT_GPUS_PER_ENGINE=1; MEM_FRACTION=0.8 ;;
    4B)   TP_SIZE=2; ROLLOUT_GPUS_PER_ENGINE=1; MEM_FRACTION=0.75 ;;
    8B)   TP_SIZE=4; ROLLOUT_GPUS_PER_ENGINE=2; MEM_FRACTION=0.7 ;;
    *) die "Unknown MODEL_SIZE: ${MODEL_SIZE} (expected 1.7B, 4B or 8B)." ;;
esac
########################### end user-adjustable ###########################

[ -f "$SLIME_DIR/train.py" ] || die "Slime submodule missing at $SLIME_DIR; run: git submodule update --init."
[ -d "$MEGATRON_LM_DIR" ] || die "Megatron-LM not found at $MEGATRON_LM_DIR."
[ -d "$MODEL_PATH" ] || die "HF checkpoint not found at $MODEL_PATH."
[ -d "$REF_LOAD" ] || die "Reference checkpoint not found at $REF_LOAD."
[ -f "$TRAIN_FILE" ] || die "Training data not found at $TRAIN_FILE; run examples/process_data.sh."
[ -f "$CUSTOM_CONFIG" ] || die "Custom config not found at $CUSTOM_CONFIG."

# The Ray job runs from an uploaded copy of the repo, so every path it reads must be absolute.
mkdir -p "$CKPT_DIR"
MODEL_PATH=$(realpath "$MODEL_PATH") REF_LOAD=$(realpath "$REF_LOAD") TRAIN_FILE=$(realpath "$TRAIN_FILE")
CUSTOM_CONFIG=$(realpath "$CUSTOM_CONFIG") CKPT_DIR=$(realpath "$CKPT_DIR")
[ -f "$VAL_FILE" ] && VAL_FILE=$(realpath "$VAL_FILE")

source "${SLIME_DIR}/scripts/models/qwen3-${MODEL_SIZE}.sh"

CKPT_ARGS=(
   --hf-checkpoint "${MODEL_PATH}"
   --ref-load "${REF_LOAD}"
   --load "${CKPT_DIR}/${experiment_name}"
   --save "${CKPT_DIR}/${experiment_name}"
   --save-interval ${save_interval}
)

ROLLOUT_ARGS=(
   --prompt-data "${TRAIN_FILE}"
   --input-key prompt
   --label-key label
   --rollout-shuffle
   --num-epoch ${num_epoch}
   --rollout-batch-size ${rollout_batch_size}
   --n-samples-per-prompt ${n_samples_per_prompt}
   --global-batch-size ${global_batch_size}
   --rollout-max-context-len ${max_context_length}
   --rollout-max-prompt-len ${max_prompt_length}
   --rollout-max-response-len ${max_response_length}
   --rollout-temperature ${rollout_temperature}
   --balance-data
   --router-policy consistent_hashing
)

EVAL_ARGS=()
if [ -f "$VAL_FILE" ]; then
   EVAL_ARGS=(
      --eval-interval ${eval_interval}
      --eval-prompt-data envfactory "${VAL_FILE}"
      --eval-temperature 0  # Greedy, as verl's validation.
      --eval-max-response-len ${max_response_length}
      --eval-max-context-len ${max_context_length}
   )
fi

PERF_ARGS=(
   --tensor-model-parallel-size ${TP_SIZE}
   --sequence-parallel
   --recompute-granularity full
   --recompute-method uniform
   --recompute-num-layers 1
   --use-dynamic-batch-size
   --max-tokens-per-gpu ${max_context_length}  # One full trajectory must fit a GPU.
   --log-probs-chunk-size 2048
)

GRPO_ARGS=(
   --advantage-estimator grpo
   --calculate-per-token-loss
   --use-kl-loss
   --kl-loss-coef ${kl_loss_coef}
   --kl-loss-type low_var_kl
)

OPTIMIZER_ARGS=(
   --optimizer adam
   --lr ${actor_lr}
   --lr-decay-style constant
)

SGLANG_ARGS=(
   --rollout-num-gpus-per-engine ${ROLLOUT_GPUS_PER_ENGINE}
   --sglang-mem-fraction-static ${MEM_FRACTION}
)

MISC_ARGS=(
   --bf16
   --attention-dropout 0.0
   --hidden-dropout 0.0
   --accumulate-allreduce-grads-in-fp32
   --attention-softmax-in-fp32
   --attention-backend flash
)

export TENSORBOARD_DIR=${TENSORBOARD_DIR:-$PROJECT_DIR/tensorboard_log/${project_name}/${experiment_name}}
LOG_ARGS=(
   --use-tensorboard
   --tb-project-name "${project_name}"
   --tb-experiment-name "${experiment_name}"
)

CUSTOM_ARGS=(
   --custom-config-path "${CUSTOM_CONFIG}"
   --custom-generate-function-path src.rollout.slime.generate.generate
   --custom-rm-path src.rollout.slime.reward.reward
   --custom-rollout-log-function-path src.rollout.slime.reward.log_rollout_metrics
   --reward-key score
)

export PYTHONUNBUFFERED=1  # `ray job submit` streams the job log to this script's stdout.
PYTHONPATH_RUNTIME="${PROJECT_DIR}:${SLIME_DIR}:${MEGATRON_LM_DIR}"
NVLINKS=$(nvidia-smi topo -m 2>/dev/null | grep -c 'NV[0-9]' || true)
RUNTIME_ENV_JSON=$(python3 - "$PROJECT_DIR" "$PYTHONPATH_RUNTIME" "$TENSORBOARD_DIR" "${NCCL_NVLS_ENABLE:-$(( ${NVLINKS:-0} > 0 ? 1 : 0 ))}" <<'PY'
import json, os, sys
root, pythonpath, tensorboard_dir, nvls = sys.argv[1:]
env_vars = {
    "PYTHONPATH": pythonpath, "CUDA_DEVICE_MAX_CONNECTIONS": "1", "NCCL_NVLS_ENABLE": nvls,
    "HF_HUB_OFFLINE": "1", "PYTHONUNBUFFERED": "1", "TENSORBOARD_DIR": tensorboard_dir,
}
# Toolchain settings from SLIME_ACTIVATE_SCRIPT (CUDA libs, JIT compilers) must reach every worker.
for name in ("CUDA_HOME", "LD_LIBRARY_PATH", "CPATH", "SSL_CERT_FILE", "TORCH_CUDA_ARCH_LIST", "CC", "CXX", "NVCC_CCBIN", "TRITON_CACHE_DIR"):
    if name in os.environ:
        env_vars[name] = os.environ[name]
print(json.dumps({
    "working_dir": root,
    "excludes": ["/slime"],  # Ray already skips .git and .gitignore'd data, checkpoints, and logs.
    "env_vars": env_vars,
}))
PY
)

# Ray, SGLang, and Megatron start thousands of threads; a low soft nproc limit (2048 on some
# Slurm nodes) makes thread creation fail and Ray job submission hang.
ulimit -u "$(ulimit -Hu)" 2>/dev/null || true

ray start --head --node-ip-address "${MASTER_ADDR}" --num-gpus "${NGPUS_PER_NODE}" \
   --disable-usage-stats --dashboard-host=0.0.0.0 --dashboard-port=8265

ray job submit --address="http://127.0.0.1:8265" --runtime-env-json="${RUNTIME_ENV_JSON}" \
   -- python3 "${SLIME_DIR}/train.py" \
   --actor-num-nodes ${NNODES} \
   --actor-num-gpus-per-node ${NGPUS_PER_NODE} \
   --colocate \
   "${MODEL_ARGS[@]}" \
   "${CKPT_ARGS[@]}" \
   "${ROLLOUT_ARGS[@]}" \
   ${EVAL_ARGS[@]+"${EVAL_ARGS[@]}"} \
   "${PERF_ARGS[@]}" \
   "${GRPO_ARGS[@]}" \
   "${OPTIMIZER_ARGS[@]}" \
   "${SGLANG_ARGS[@]}" \
   "${MISC_ARGS[@]}" \
   "${LOG_ARGS[@]}" \
   "${CUSTOM_ARGS[@]}" \
   "$@"
