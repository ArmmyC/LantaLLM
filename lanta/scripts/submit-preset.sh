#!/bin/bash
set -euo pipefail

ROOT=${ROOT:-/project/zz992000-zdevb/zz992005/ub127/SiliconCraft}
PRESET=${1:-}
RUN_TIME=${RUN_TIME:-09:00:00}
PORT=${PORT:-8000}
TP=${TP:-4}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.90}
CANCEL_EXISTING=${CANCEL_EXISTING:-1}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/submit-preset.sh PRESET

Presets:
  qwen36-27b
  qwen36-35b-a3b
  qwen3-coder-30b-a3b
  qwen25-coder-32b
  deepseek-coder-v2-lite

Optional environment overrides:
  RUN_TIME=09:00:00
  PORT=8000
  TP=4
  MAX_MODEL_LEN=...
  CANCEL_EXISTING=0
EOF
}

case "$PRESET" in
  qwen36-27b)
    MODEL_REPO=${MODEL_REPO:-Qwen/Qwen3.6-27B}
    SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-qwen36-27b}
    MAX_MODEL_LEN=${MAX_MODEL_LEN:-131072}
    REASONING_PARSER=${REASONING_PARSER:-qwen3}
    EXTRA_VLLM_ARGS=${EXTRA_VLLM_ARGS:-}
    ;;
  qwen36-35b-a3b)
    MODEL_REPO=${MODEL_REPO:-Qwen/Qwen3.6-35B-A3B}
    SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-qwen36-35b-a3b}
    MAX_MODEL_LEN=${MAX_MODEL_LEN:-131072}
    REASONING_PARSER=${REASONING_PARSER:-qwen3}
    EXTRA_VLLM_ARGS=${EXTRA_VLLM_ARGS:-}
    ;;
  qwen3-coder-30b-a3b)
    MODEL_REPO=${MODEL_REPO:-Qwen/Qwen3-Coder-30B-A3B-Instruct}
    SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-qwen3-coder-30b-a3b}
    MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
    REASONING_PARSER=${REASONING_PARSER:-}
    EXTRA_VLLM_ARGS=${EXTRA_VLLM_ARGS:-}
    ;;
  qwen25-coder-32b)
    MODEL_REPO=${MODEL_REPO:-Qwen/Qwen2.5-Coder-32B-Instruct}
    SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-qwen25-coder-32b}
    MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
    REASONING_PARSER=${REASONING_PARSER:-}
    EXTRA_VLLM_ARGS=${EXTRA_VLLM_ARGS:-}
    ;;
  deepseek-coder-v2-lite)
    MODEL_REPO=${MODEL_REPO:-deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct}
    SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-deepseek-coder-v2-lite}
    MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
    REASONING_PARSER=${REASONING_PARSER:-}
    EXTRA_VLLM_ARGS=${EXTRA_VLLM_ARGS:---enforce-eager}
    ;;
  ""|-h|--help|help)
    usage
    exit 0
    ;;
  *)
    echo "Unknown preset: $PRESET" >&2
    usage >&2
    exit 2
    ;;
esac

cd "$ROOT"

MODEL_NAME=${MODEL_NAME:-${MODEL_REPO##*/}}
MODEL_DIR=${MODEL_DIR:-$ROOT/models/$MODEL_NAME}
if [ ! -d "$MODEL_DIR" ]; then
  echo "Model is missing: $MODEL_DIR" >&2
  echo "Download it first:" >&2
  echo "  MODEL_REPO=$MODEL_REPO bash scripts/download-model.sh" >&2
  exit 1
fi

if [ "$CANCEL_EXISTING" = "1" ]; then
  existing_jobs=$(squeue -u "$USER" -h -n vllm-model -o '%i' || true)
  if [ -n "$existing_jobs" ]; then
    echo "Canceling existing vLLM job(s): $existing_jobs"
    # shellcheck disable=SC2086
    scancel $existing_jobs
    for _ in $(seq 1 60); do
      remaining=$(squeue -u "$USER" -h -n vllm-model -o '%i' || true)
      [ -z "$remaining" ] && break
      sleep 2
    done
  fi
fi

export MODEL_REPO MODEL_NAME MODEL_DIR SERVED_MODEL_NAME PORT TP MAX_MODEL_LEN
export GPU_MEMORY_UTILIZATION REASONING_PARSER EXTRA_VLLM_ARGS

echo "Submitting preset: $PRESET"
echo "Model repo: $MODEL_REPO"
echo "Served model: $SERVED_MODEL_NAME"
echo "Port: $PORT"
echo "Max model length: $MAX_MODEL_LEN"
echo "Run time: $RUN_TIME"

sbatch --time="$RUN_TIME" scripts/serve-model.sbatch
