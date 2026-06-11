#!/bin/bash
set -euo pipefail

ROOT=/project/zz992000-zdevb/zz992005/ub127/SiliconCraft
ENV=$ROOT/envs/silicon-craft
MODEL_DIR=$ROOT/models/Qwen3.6-35B-A3B

cd "$ROOT"
mkdir -p "$MODEL_DIR" models/.hf-cache tmp logs

export TMPDIR=$ROOT/tmp
export HF_HOME=$ROOT/models/.hf-cache
export HUGGINGFACE_HUB_CACHE=$ROOT/models/.hf-cache/hub
export HF_XET_HIGH_PERFORMANCE=1

"$ENV/bin/hf" download Qwen/Qwen3.6-35B-A3B \
  --local-dir "$MODEL_DIR"
