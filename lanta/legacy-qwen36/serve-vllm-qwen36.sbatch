#!/bin/bash
#SBATCH --job-name=qwen36-vllm
#SBATCH --partition=gpu
#SBATCH --account=zz992005
#SBATCH --qos=zz992005
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:a100:4
#SBATCH --mem=256G
#SBATCH --time=12:00:00
#SBATCH --output=/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/qwen36-vllm-%j.out
#SBATCH --error=/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/qwen36-vllm-%j.err

set -euo pipefail

ROOT=/project/zz992000-zdevb/zz992005/ub127/SiliconCraft
ENV=$ROOT/envs/silicon-craft
MODEL_DIR=$ROOT/models/Qwen3.6-35B-A3B
MODEL_ID=${MODEL_ID:-$MODEL_DIR}
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
TP=${TP:-4}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-131072}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.90}

cd "$ROOT"
mkdir -p logs tmp models/.hf-cache

export TMPDIR=$ROOT/tmp
export HF_HOME=$ROOT/models/.hf-cache
export HUGGINGFACE_HUB_CACHE=$ROOT/models/.hf-cache/hub
export VLLM_WORKER_MULTIPROC_METHOD=spawn

if [ ! -d "$MODEL_DIR" ]; then
  echo "Model directory $MODEL_DIR is missing. Run scripts/download-qwen36-model.sh first."
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

exec "$ENV/bin/vllm" serve "$MODEL_ID" \
  --host "$HOST" \
  --port "$PORT" \
  --tensor-parallel-size "$TP" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --reasoning-parser qwen3 \
  --trust-remote-code
