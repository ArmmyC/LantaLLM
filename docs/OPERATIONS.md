# Lanta LLM Platform Operations

## Startup Order

1. Start Lanta vLLM job.
2. Start tunnel.
3. Start LiteLLM.
4. Start OpenWebUI.
5. Start observability stack.
6. Start the hosting dashboard.

## First Local Run

Create local environment files before starting the stack:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
Copy-Item litellm\.env.example litellm\.env
Copy-Item openwebui\.env.example openwebui\.env
Copy-Item observability\.env.example observability\.env
Copy-Item dashboard\.env.example dashboard\.env
```

Edit those `.env` files and change local secrets before use:

- LiteLLM: `LITELLM_MASTER_KEY`, `LITELLM_SALT_KEY`, `POSTGRES_PASSWORD`, and `LITELLM_DATABASE_URL`
- LiteLLM routing: `VLLM_MODEL_ID`, for example `openai/qwen36-27b`
- OpenWebUI: the web UI secret/session settings
- Observability: `GRAFANA_ADMIN_PASSWORD`

OpenWebUI asks you to create the first admin account on first launch. That is normal. The OpenWebUI account is separate from LiteLLM API keys; OpenWebUI login controls the web UI, while LiteLLM keys control access to the model gateway.

Set your local shell key for verification commands:

```powershell
$env:LITELLM_MASTER_KEY="sk-your-key"
```

Run the local platform check:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-platform.ps1
```

Key management docs:

```text
docs/KEY_MANAGEMENT.md
```

## 1. Start Lanta vLLM

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen36-35b-a3b"
```

Check status:

```powershell
ssh lanta "squeue -u ub127"
```

## 2. Start Tunnel

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\status-lanta-vllm-tunnel.ps1
```

Expected endpoint:

```text
http://127.0.0.1:8000/v1
```

## 3. Start LiteLLM

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\litellm
Copy-Item .env.example .env
notepad .env
docker compose up -d
```

Verify:

```powershell
curl.exe http://127.0.0.1:4000/v1/models -H "Authorization: Bearer $env:LITELLM_MASTER_KEY"
```

Callers should use the stable public model alias:

```text
active-lanta-model
```

The upstream vLLM served model is controlled by `VLLM_MODEL_ID` in `litellm/.env`. The value must include LiteLLM's provider prefix and match the model returned by the vLLM tunnel, for example:

```env
VLLM_MODEL_ID=openai/qwen36-27b
```

After changing `.env`, recreate the container:

```powershell
docker compose up -d --force-recreate litellm
```

## 4. Start OpenWebUI

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\openwebui
Copy-Item .env.example .env
notepad .env
docker compose up -d
```

Open:

```text
http://127.0.0.1:3000
```

If automatic provider configuration fails, add an OpenAI-compatible provider manually:

```text
Base URL: http://host.docker.internal:4000/v1
API key: LiteLLM virtual key
```

## 5. Start Observability

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\observability
docker compose up -d
```

Ports:

```text
Prometheus: http://127.0.0.1:9090
Grafana: http://127.0.0.1:3002
Platform exporter: http://127.0.0.1:9108
```

Grafana dashboard:

```text
Lanta LLM Operations
```

Hosting dashboard:

```text
Status: http://127.0.0.1:8088/status
Usage:  http://127.0.0.1:8088/usage
API:    http://127.0.0.1:8088/api/platform/status
```

Request, error, token, and latency metrics come from LiteLLM through Prometheus. Slurm and GPU panels are optional and remain empty until Lanta-side exporters are configured.

## 6. Start Hosting Dashboard

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\dashboard
docker compose up -d --build
```

Open:

```text
http://127.0.0.1:8088/status
http://127.0.0.1:8088/usage
```

## LiteLLM Virtual Keys

See [Key Management](KEY_MANAGEMENT.md) for the full admin and user flow. The short version is below.

Create:

```powershell
curl.exe http://127.0.0.1:4000/key/generate `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"models\":[\"active-lanta-model\"],\"max_budget\":10}"
```

List:

```powershell
curl.exe http://127.0.0.1:4000/key/list -H "Authorization: Bearer $env:LITELLM_MASTER_KEY"
```

Revoke:

```powershell
curl.exe http://127.0.0.1:4000/key/delete `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"keys\":[\"sk-user-key\"]}"
```

“API generation” means creating and managing LiteLLM virtual keys.

## Troubleshooting

### `curl: (52) Empty reply from server`

This usually means the container accepted a connection while LiteLLM was still starting, migrating its database, or restarting. Check:

```powershell
docker compose ps
docker compose logs --tail=150 litellm
```

Wait 30-60 seconds after recreating LiteLLM before testing.

### Wrong LiteLLM key

If `/v1/models` returns 401, verify the key in your shell matches the key inside the running container:

```powershell
$env:LITELLM_MASTER_KEY="sk-your-key"
docker compose exec litellm printenv
```

Do not paste secrets into issues or commits.

### `.env` changed but Docker still uses old values

Docker does not change environment variables inside an existing container after a plain restart. Recreate the service:

```powershell
docker compose up -d --force-recreate litellm
```

### Postgres password mismatch after changing `.env`

The Postgres Docker volume keeps the password from first initialization. If you change `POSTGRES_PASSWORD` later, LiteLLM may fail database auth. For a local reset only when safe, remove the local volume:

```powershell
docker compose down -v
docker compose up -d
```

This deletes the local LiteLLM database volume. Do not use it if you need to keep stored keys or usage history.

### Wrong upstream model name

If LiteLLM returns a model-not-found error from upstream, compare:

```powershell
curl.exe http://127.0.0.1:8000/v1/models
```

with `VLLM_MODEL_ID` in `litellm/.env`. If vLLM serves `qwen36-27b`, set:

```env
VLLM_MODEL_ID=openai/qwen36-27b
```

Then recreate LiteLLM:

```powershell
docker compose up -d --force-recreate litellm
```

## Compatibility Gateways

The existing `website/` and `sharing/` flows remain available for demos and compatibility. LiteLLM is now the preferred gateway for new users, scripts, and benchmark runs.
