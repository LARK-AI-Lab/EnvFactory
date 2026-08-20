#!/usr/bin/env bash
set -euo pipefail

# A small process supervisor for a single-GPU MoLab base model or named LoRA.
# Configuration is provided through environment variables so no API key appears
# in argv or logs.
ACTION="${1:-}"
if [[ -z "$ACTION" ]]; then
  echo "usage: $0 {start|health|status|stop}" >&2
  exit 2
fi

: "${MOLAB_VLLM_RUN_DIR:?set MOLAB_VLLM_RUN_DIR to the current run directory}"

MOLAB_VLLM_MODEL="${MOLAB_VLLM_MODEL:-Qwen/Qwen3-14B}"
MOLAB_VLLM_PORT="${MOLAB_VLLM_PORT:-8000}"
MOLAB_VLLM_MAX_MODEL_LEN="${MOLAB_VLLM_MAX_MODEL_LEN:-16384}"
MOLAB_VLLM_GPU_MEMORY_UTILIZATION="${MOLAB_VLLM_GPU_MEMORY_UTILIZATION:-0.85}"
MOLAB_VLLM_MAX_NUM_SEQS="${MOLAB_VLLM_MAX_NUM_SEQS:-4}"
MOLAB_VLLM_CONFIG="${MOLAB_VLLM_CONFIG:-configs/mini/pipeline.toml}"
MOLAB_VLLM_PYTHON="${MOLAB_VLLM_PYTHON:-.venv-mini-runtime/bin/python}"
MOLAB_VLLM_EXECUTABLE="${MOLAB_VLLM_EXECUTABLE:-.venv-mini-runtime/bin/vllm}"
MOLAB_VLLM_STOP_TIMEOUT_SECONDS="${MOLAB_VLLM_STOP_TIMEOUT_SECONDS:-60}"
MOLAB_VLLM_VRAM_TOLERANCE_MIB="${MOLAB_VLLM_VRAM_TOLERANCE_MIB:-512}"
MOLAB_VLLM_LORA_MODULE="${MOLAB_VLLM_LORA_MODULE:-}"
MOLAB_VLLM_MAX_LORA_RANK="${MOLAB_VLLM_MAX_LORA_RANK:-64}"
MOLAB_VLLM_EXPECTED_MODEL="${MOLAB_VLLM_EXPECTED_MODEL:-$MOLAB_VLLM_MODEL}"

case "$MOLAB_VLLM_PORT" in (*[!0-9]*|'') echo "MOLAB_VLLM_PORT must be an integer" >&2; exit 2;; esac
case "$MOLAB_VLLM_MAX_MODEL_LEN" in (*[!0-9]*|'') echo "MOLAB_VLLM_MAX_MODEL_LEN must be an integer" >&2; exit 2;; esac
case "$MOLAB_VLLM_MAX_NUM_SEQS" in (*[!0-9]*|'') echo "MOLAB_VLLM_MAX_NUM_SEQS must be an integer" >&2; exit 2;; esac
case "$MOLAB_VLLM_MAX_LORA_RANK" in (*[!0-9]*|'') echo "MOLAB_VLLM_MAX_LORA_RANK must be an integer" >&2; exit 2;; esac
if [[ "$MOLAB_VLLM_GPU_MEMORY_UTILIZATION" != 0.* && "$MOLAB_VLLM_GPU_MEMORY_UTILIZATION" != 1.0 ]]; then
  echo "MOLAB_VLLM_GPU_MEMORY_UTILIZATION must be between 0 and 1" >&2
  exit 2
fi

LOG_DIR="$MOLAB_VLLM_RUN_DIR/logs"
LOG_PATH="$LOG_DIR/model_server.log"
PID_PATH="$LOG_DIR/model_server.pid"
BASELINE_PATH="$LOG_DIR/model_server_baseline_used_mib"
mkdir -p "$LOG_DIR"

gpu_used_mib() {
  nvidia-smi --id=0 --query-gpu=memory.used --format=csv,noheader,nounits | head -n 1 | tr -d ' '
}

running_pid() {
  [[ -f "$PID_PATH" ]] || return 1
  local pid
  pid="$(<"$PID_PATH")"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  printf '%s\n' "$pid"
}

health() {
  : "${VLLM_API_KEY:?set VLLM_API_KEY without placing its value in a command}"
  export VLLM_API_KEY
  ENVFACTORY_MINI_TEACHER_BASE_URL="http://127.0.0.1:${MOLAB_VLLM_PORT}/v1" \
    "$MOLAB_VLLM_PYTHON" -m src.mini.doctor \
      --config "$MOLAB_VLLM_CONFIG" \
      --require-model \
      --expected-model "$MOLAB_VLLM_EXPECTED_MODEL"
}

case "$ACTION" in
  start)
    : "${VLLM_API_KEY:?set VLLM_API_KEY without placing its value in a command}"
    export VLLM_API_KEY
    if pid="$(running_pid)"; then
      echo "model server is already running with PID $pid" >&2
      exit 1
    fi
    command -v nvidia-smi >/dev/null
    if [[ ! -x "$MOLAB_VLLM_EXECUTABLE" ]]; then
      echo "vLLM executable is not available: $MOLAB_VLLM_EXECUTABLE" >&2
      exit 1
    fi
    baseline="$(gpu_used_mib)"
    printf '%s\n' "$baseline" > "$BASELINE_PATH"
    export CUDA_VISIBLE_DEVICES=0
    export ENVFACTORY_MINI_TEACHER_BASE_URL="http://127.0.0.1:${MOLAB_VLLM_PORT}/v1"
    extra_args=()
    if [[ -n "$MOLAB_VLLM_LORA_MODULE" ]]; then
      if [[ "$MOLAB_VLLM_LORA_MODULE" != *=* ]]; then
        echo "MOLAB_VLLM_LORA_MODULE must use name=/absolute/adapter/path" >&2
        exit 2
      fi
      lora_name="${MOLAB_VLLM_LORA_MODULE%%=*}"
      lora_path="${MOLAB_VLLM_LORA_MODULE#*=}"
      if [[ -z "$lora_name" || "$lora_path" != /* || ! -d "$lora_path" ]]; then
        echo "MOLAB_VLLM_LORA_MODULE must name an existing absolute adapter directory" >&2
        exit 2
      fi
      if [[ "$MOLAB_VLLM_EXPECTED_MODEL" != "$lora_name" ]]; then
        echo "MOLAB_VLLM_EXPECTED_MODEL must equal the named LoRA module" >&2
        exit 2
      fi
      extra_args=(--enable-lora --lora-modules "$MOLAB_VLLM_LORA_MODULE" --max-lora-rank "$MOLAB_VLLM_MAX_LORA_RANK")
    fi
    nohup "$MOLAB_VLLM_EXECUTABLE" serve "$MOLAB_VLLM_MODEL" \
      --host 127.0.0.1 \
      --port "$MOLAB_VLLM_PORT" \
      --tensor-parallel-size 1 \
      --dtype bfloat16 \
      --max-model-len "$MOLAB_VLLM_MAX_MODEL_LEN" \
      --gpu-memory-utilization "$MOLAB_VLLM_GPU_MEMORY_UTILIZATION" \
      --max-num-seqs "$MOLAB_VLLM_MAX_NUM_SEQS" \
      --disable-log-requests \
      "${extra_args[@]}" \
      >> "$LOG_PATH" 2>&1 &
    pid=$!
    printf '%s\n' "$pid" > "$PID_PATH"
    echo "started model server PID $pid; log: $LOG_PATH"
    ;;
  health)
    health
    ;;
  status)
    if pid="$(running_pid)"; then
      echo "model server is running with PID $pid"
    else
      echo "model server is not running"
      exit 1
    fi
    ;;
  stop)
    if ! pid="$(running_pid)"; then
      echo "model server is not running"
      exit 0
    fi
    kill -TERM "$pid"
    deadline=$((SECONDS + MOLAB_VLLM_STOP_TIMEOUT_SECONDS))
    while kill -0 "$pid" 2>/dev/null && (( SECONDS < deadline )); do
      sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "graceful stop timed out; force-stopping PID $pid" >&2
      kill -KILL "$pid"
    fi
    wait "$pid" 2>/dev/null || true
    rm -f "$PID_PATH"

    if [[ -f "$BASELINE_PATH" ]] && command -v nvidia-smi >/dev/null; then
      baseline="$(<"$BASELINE_PATH")"
      target=$((baseline + MOLAB_VLLM_VRAM_TOLERANCE_MIB))
      deadline=$((SECONDS + MOLAB_VLLM_STOP_TIMEOUT_SECONDS))
      used="$(gpu_used_mib)"
      while (( used > target && SECONDS < deadline )); do
        sleep 1
        used="$(gpu_used_mib)"
      done
      if (( used > target )); then
        echo "VRAM did not return near baseline: ${used} MiB used, target <= ${target} MiB" >&2
        exit 1
      fi
      echo "model server stopped; GPU memory returned to ${used} MiB used"
    else
      echo "model server stopped; no GPU baseline was available"
    fi
    ;;
  *)
    echo "usage: $0 {start|health|status|stop}" >&2
    exit 2
    ;;
esac
