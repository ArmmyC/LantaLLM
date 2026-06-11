#!/bin/bash
set -euo pipefail

ROOT=${ROOT:-/project/zz992000-zdevb/zz992005/ub127/SiliconCraft}
ENV=${ENV:-$ROOT/envs/silicon-craft}
MODEL_REPO=${MODEL_REPO:?Set MODEL_REPO, for example MODEL_REPO=Qwen/Qwen3.6-35B-A3B}
MODEL_NAME=${MODEL_NAME:-${MODEL_REPO##*/}}
MODEL_DIR=${MODEL_DIR:-$ROOT/models/$MODEL_NAME}
REVISION=${REVISION:-}

cd "$ROOT"
mkdir -p "$MODEL_DIR" models/.hf-cache tmp logs

export TMPDIR=$ROOT/tmp
export HF_HOME=$ROOT/models/.hf-cache
export HUGGINGFACE_HUB_CACHE=$ROOT/models/.hf-cache/hub
export HF_XET_HIGH_PERFORMANCE=1

echo "Downloading $MODEL_REPO"
echo "Target: $MODEL_DIR"

args=(download "$MODEL_REPO" --local-dir "$MODEL_DIR")
if [ -n "$REVISION" ]; then
  args+=(--revision "$REVISION")
fi

"$ENV/bin/hf" "${args[@]}"

echo
echo "Downloaded model to $MODEL_DIR"
