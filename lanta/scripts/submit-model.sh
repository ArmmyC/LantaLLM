#!/bin/bash
set -euo pipefail

cd "${ROOT:-/project/zz992000-zdevb/zz992005/ub127/SiliconCraft}"
sbatch scripts/serve-model.sbatch
