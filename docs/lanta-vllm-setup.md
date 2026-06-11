# Qwen3.6 vLLM on Lanta

Project root: `/project/zz992000-zdevb/zz992005/ub127/SiliconCraft`

## Download model

```bash
cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft
bash scripts/download_qwen36.sh
```

The legacy local copy is `lanta/legacy-qwen36/download-qwen36-model.sh`.

Model path: `/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models/Qwen3.6-35B-A3B`

## Start vLLM on 4 A100s

```bash
cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft
bash scripts/submit_qwen36_vllm.sh
```

The legacy local copy is `lanta/legacy-qwen36/submit-vllm-server.sh`.

The Slurm job uses `--account=zz992005 --qos=zz992005`, partition `gpu`, and `--gres=gpu:a100:4`.

Default API: `http://<allocated-node>:8000/v1`

Defaults can be overridden at submit time, for example:

```bash
MAX_MODEL_LEN=65536 PORT=8000 sbatch scripts/serve-vllm-qwen36.sbatch
```

## Node frontend call

From a machine that can reach the allocated node:

```bash
export OPENAI_BASE_URL=http://<allocated-node>:8000/v1
export OPENAI_API_KEY=EMPTY
node scripts/test-vllm-chat-node.mjs
```

Lanta's login environment may not have `node` installed. For a smoke test from Lanta, use Python:

```bash
cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft
export OPENAI_BASE_URL=http://<allocated-node>:8000/v1
export OPENAI_API_KEY=EMPTY
envs/silicon-craft/bin/python scripts/test-vllm-chat.py
```

For outside access, expose the allocated compute node and port through your site firewall, reverse proxy, SSH tunnel, or cluster-approved ingress. The vLLM server binds to `0.0.0.0`, so it is ready for external routing once networking permits it.

## If compute nodes are private

Find the allocated node after the job starts:

```bash
squeue -j <job-id> -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
```

Then run this on the frontend/server machine that needs API access:

```bash
ssh -N -L 8000:<allocated-node>:8000 lanta
```

Point Node/OpenAI SDK clients at:

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=EMPTY
```
