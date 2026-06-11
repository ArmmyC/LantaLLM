#!/bin/bash
set -euo pipefail

ROOT=/project/zz992000-zdevb/zz992005/ub127/SiliconCraft
ENV=$ROOT/envs/silicon-craft
MODEL=${MODEL:-$ROOT/models/Qwen3.6-35B-A3B}
PORT=${PORT:-8000}

cd "$ROOT"

if [ -z "${OPENAI_BASE_URL:-}" ]; then
  NODE=$(squeue -u "$USER" -h -n qwen36-vllm -t R -o "%N" | awk 'NF { print $1; exit }')
  if [ -z "$NODE" ]; then
    echo "No running qwen36-vllm Slurm job found."
    echo "Start it with: bash scripts/submit-vllm-server.sh"
    exit 1
  fi
  OPENAI_BASE_URL="http://$NODE:$PORT/v1"
fi

export OPENAI_BASE_URL
export OPENAI_API_KEY=${OPENAI_API_KEY:-EMPTY}
export MODEL

echo "Testing Qwen API at: $OPENAI_BASE_URL"
echo
echo "1. Checking /v1/models..."
curl -fsS --max-time 10 "$OPENAI_BASE_URL/models" | "$ENV/bin/python" -m json.tool

echo
echo "2. Sending chat completion..."
"$ENV/bin/python" scripts/test-vllm-chat.py

echo
echo "OK: Qwen API test passed."
