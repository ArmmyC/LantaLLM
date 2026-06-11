# Lanta LLM Hosting Commands

## Start Qwen3.6-27B Job

```powershell
ssh lanta
```

```bash
cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft
MODEL_REPO=Qwen/Qwen3.6-27B SERVED_MODEL_NAME=qwen36-27b TP=4 MAX_MODEL_LEN=131072 sbatch --time=09:00:00 --export=ALL,MODEL_REPO=Qwen/Qwen3.6-27B,SERVED_MODEL_NAME=qwen36-27b,TP=4,MAX_MODEL_LEN=131072 scripts/serve-model.sbatch
```

## Check Job

```bash
squeue -u ub127
squeue --start -j JOB_ID
scontrol show job JOB_ID
tail -f /project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/vllm-model-JOB_ID.out
tail -f /project/zz992000-zdevb/zz992005/ub127/SiliconCraft/logs/vllm-model-JOB_ID.err
```

## Stop Job

```bash
scancel JOB_ID
```

```bash
scancel -n vllm-model
exit
```

## Start Hidden Tunnel

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
```

## Check Tunnel

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\status-lanta-vllm-tunnel.ps1
Invoke-RestMethod http://127.0.0.1:8000/v1/models
```

## Stop Tunnel

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\stop-lanta-vllm-tunnel.ps1
```

## Test Local API

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\test-local-vllm-api.ps1
```

## Start Website

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\website
$env:QWEN_BASE_URL="http://127.0.0.1:8000/v1"
$env:QWEN_API_KEY="EMPTY"
$env:QWEN_MODEL="qwen36-27b"
$env:SITE_PASSWORD="YOUR_SITE_PASSWORD"
npm run dev
```

```powershell
Start-Process http://127.0.0.1:5177
```

## Check Website

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5177
```

## Stop Website

```powershell
Get-NetTCPConnection -LocalPort 5177 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

## Start Public Website Funnel

```powershell
tailscale funnel --bg --https=443 http://127.0.0.1:5177
```

## Check Public Funnel

```powershell
tailscale funnel status
Start-Process https://armmy.tail35169a.ts.net
```

## Stop Public Funnel

```powershell
tailscale funnel --https=443 off
```

## Start Authenticated Public API Funnel

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\sharing\start-tailscale-funnel-share.ps1 -ApiTokens "YOUR_API_TOKEN"
```

## Stop Authenticated Public API Funnel

```powershell
powershell -ExecutionPolicy Bypass -File .\sharing\stop-tailscale-funnel-share.ps1
```
