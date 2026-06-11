#!/bin/bash
#SBATCH --job-name=vllm-model
#SBATCH --partition=gpu
#SBATCH --account=zz992005
#SBATCH --qos=zz992005
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:a100:4
#SBATCH --mem=256G
#SBATCH --time=12:00:00
#SBATCH --output=/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/vllm-model-%j.out
#SBATCH --error=/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/vllm-model-%j.err

set -euo pipefail

module load cuda/12.6

ROOT=${ROOT:-/project/zz992000-zdevb/zz992005/ub127/SiliconCraft}
ENV=${ENV:-$ROOT/envs/silicon-craft}
MODEL_REPO=${MODEL_REPO:-Qwen/Qwen3.6-35B-A3B}
MODEL_NAME=${MODEL_NAME:-${MODEL_REPO##*/}}
MODEL_DIR=${MODEL_DIR:-$ROOT/models/$MODEL_NAME}
MODEL_ID=${MODEL_ID:-$MODEL_DIR}
SERVED_MODEL_NAME=${SERVED_MODEL_NAME:-$MODEL_NAME}
PORT=${PORT:-8000}
LISTEN_HOST=${LISTEN_HOST:-0.0.0.0}
TP=${TP:-4}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-131072}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.90}
REASONING_PARSER=${REASONING_PARSER:-}
TRUST_REMOTE_CODE=${TRUST_REMOTE_CODE:-1}
EXTRA_VLLM_ARGS=${EXTRA_VLLM_ARGS:-}

cd "$ROOT"
mkdir -p logs tmp models/.hf-cache

export TMPDIR=$ROOT/tmp
export HF_HOME=$ROOT/models/.hf-cache
export HUGGINGFACE_HUB_CACHE=$ROOT/models/.hf-cache/hub
export VLLM_WORKER_MULTIPROC_METHOD=spawn
PY_SITE=$("$ENV/bin/python" -c 'import site; print(site.getsitepackages()[0])')
NVIDIA_LIB_PATHS=$(find "$PY_SITE/nvidia" -maxdepth 3 -type d -name lib -printf '%p:' 2>/dev/null || true)
export CUDA_HOME=$(dirname "$(dirname "$(command -v nvcc)")")
export PATH="$ENV/bin:$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$PY_SITE/torch/lib:${NVIDIA_LIB_PATHS}$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"

if [ ! -d "$MODEL_DIR" ]; then
  echo "Model directory $MODEL_DIR is missing."
  echo "Run: MODEL_REPO=$MODEL_REPO bash scripts/download-model.sh"
  exit 1
fi

nvidia-smi
"$ENV/bin/python" - <<'PY'
import torch, vllm
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("cuda_devices", torch.cuda.device_count())
print("vllm", vllm.__version__)
PY

args=(
  serve "$MODEL_ID"
  --host "$LISTEN_HOST"
  --port "$PORT"
  --tensor-parallel-size "$TP"
  --max-model-len "$MAX_MODEL_LEN"
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
  --served-model-name "$SERVED_MODEL_NAME"
)

if [ "$TRUST_REMOTE_CODE" = "1" ]; then
  args+=(--trust-remote-code)
fi

if [ -n "$REASONING_PARSER" ]; then
  args+=(--reasoning-parser "$REASONING_PARSER")
fi

if [ -n "$EXTRA_VLLM_ARGS" ]; then
  # shellcheck disable=SC2206
  extra_args=($EXTRA_VLLM_ARGS)
  args+=("${extra_args[@]}")
fi

echo "Serving model repo: $MODEL_REPO"
echo "Model path: $MODEL_ID"
echo "Served model name: $SERVED_MODEL_NAME"
echo "Port: $PORT"

exec "$ENV/bin/vllm" "${args[@]}"
