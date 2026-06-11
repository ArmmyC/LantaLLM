#!/bin/bash
set -euo pipefail

ROOT=${ROOT:-/project/zz992000-zdevb/zz992005/ub127/SiliconCraft}
ENV=${ENV:-$ROOT/envs/silicon-craft}
MODEL_REPO=${MODEL_REPO:-Qwen/Qwen3.6-35B-A3B}
MODEL_NAME=${MODEL_NAME:-${MODEL_REPO##*/}}
SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-$MODEL_NAME}
PORT=${PORT:-8000}
JOB_NAME=${JOB_NAME:-vllm-model}

cd "$ROOT"

if [ -z "${OPENAI_BASE_URL:-}" ]; then
  NODE=$(squeue -u "$USER" -h -n "$JOB_NAME" -t R -o "%N" | awk 'NF { print $1; exit }')
  if [ -z "$NODE" ]; then
    echo "No running $JOB_NAME Slurm job found."
    echo "Start it with: MODEL_REPO=$MODEL_REPO bash scripts/submit-model.sh"
    exit 1
  fi
  OPENAI_BASE_URL="http://$NODE:$PORT/v1"
fi

export OPENAI_BASE_URL
export OPENAI_API_KEY=${OPENAI_API_KEY:-EMPTY}
export MODEL=${MODEL:-$SERVED_MODEL_NAME}

echo "Testing vLLM API at: $OPENAI_BASE_URL"
echo "Model: $MODEL"
echo
echo "1. Checking /v1/models..."
curl -fsS --max-time 10 "$OPENAI_BASE_URL/models" | "$ENV/bin/python" -m json.tool

echo
echo "2. Sending chat completion..."
"$ENV/bin/python" scripts/test-vllm-chat.py

echo
echo "OK: vLLM API test passed."
