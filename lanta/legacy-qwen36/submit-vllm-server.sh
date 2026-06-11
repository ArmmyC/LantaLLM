#!/bin/bash
set -euo pipefail

cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft
sbatch scripts/serve-vllm-qwen36.sbatch
