# Swap Models On The Same Endpoint

These commands keep the same API endpoint:

```text
http://127.0.0.1:8000/v1
```

The swap helper cancels the previous `vllm-model` Slurm job and submits a new one on port `8000`.

## Available Presets

```text
qwen36-27b
qwen36-35b-a3b
qwen3-coder-30b-a3b
qwen25-coder-32b
deepseek-coder-v2-lite
```

## Check Current Job

```powershell
ssh lanta "squeue -u ub127 -o '%i %j %t %M %N %R'"
```

## Swap To Qwen3 Coder 30B-A3B

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen3-coder-30b-a3b"
```

## Swap To Qwen2.5 Coder 32B

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen25-coder-32b"
```

## Swap To DeepSeek Coder V2 Lite

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh deepseek-coder-v2-lite"
```

## Swap Back To Qwen3.6 27B

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen36-27b"
```

## Swap To Qwen3.6 35B-A3B

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen36-35b-a3b"
```

## Watch Queue

```powershell
ssh lanta "squeue -u ub127 -o '%i %j %t %M %N %R'"
```

## Watch Logs

```powershell
ssh lanta "tail -f /project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/vllm-model-JOB_ID.out"
```

```powershell
ssh lanta "tail -f /project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/vllm-model-JOB_ID.err"
```

## Restart Local Tunnel Watchdog

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\stop-lanta-vllm-tunnel.ps1
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\status-lanta-vllm-tunnel.ps1
```

The watchdog waits while the Slurm job is pending and reconnects after the job starts.

## Confirm Served Model

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/models
```

## Website Behavior

Use the same website URL:

```text
http://127.0.0.1:5177
```

Click `Check connection` after a swap. The website asks vLLM for `/v1/models` and updates the model field to the active served model name.

## Notes

- Only one model is served on port `8000` at a time.
- Swapping cancels the previous `vllm-model` job.
- Existing browser chat history remains visible, but very old messages may not be sent as model context.
- `DeepSeek-Coder-V2-Lite-Instruct` uses a shorter default context length: `32768`.
## Context Defaults

The coder presets use `MAX_MODEL_LEN=32768` by default so swaps start reliably on the 4x A100 40GB Lanta node. You can test a larger context later by prefixing the submit command, for example:

```bash
MAX_MODEL_LEN=65536 bash scripts/submit-preset.sh qwen3-coder-30b-a3b
```

Keep the same `SERVED_MODEL_NAME` if you want the website to keep auto-detecting the active model through `/api/models`.
