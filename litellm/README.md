# LiteLLM Gateway

LiteLLM is the preferred OpenAI-compatible gateway for this project. It sits between OpenWebUI, scripts, benchmark runners, and the local vLLM tunnel.

## Start

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\litellm
Copy-Item .env.example .env
notepad .env
docker compose up -d
```

Required values in `.env`:

- `LITELLM_MASTER_KEY`
- `LITELLM_SALT_KEY`
- `POSTGRES_PASSWORD`
- `VLLM_BASE_URL`, normally `http://host.docker.internal:8000/v1` on Docker Desktop for Windows

## Verify

```powershell
$env:LITELLM_MASTER_KEY="sk-change-this-master-key"
curl.exe http://127.0.0.1:4000/v1/models -H "Authorization: Bearer $env:LITELLM_MASTER_KEY"
```

## Virtual Keys

API generation in this repo means generating LiteLLM virtual keys.

Create a key:

```powershell
curl.exe http://127.0.0.1:4000/key/generate `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"models\":[\"active-lanta-model\"],\"max_budget\":10}"
```

List keys:

```powershell
curl.exe http://127.0.0.1:4000/key/list -H "Authorization: Bearer $env:LITELLM_MASTER_KEY"
```

Revoke a key:

```powershell
curl.exe http://127.0.0.1:4000/key/delete `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"keys\":[\"sk-user-key\"]}"
```

Call the model:

```powershell
curl.exe http://127.0.0.1:4000/v1/chat/completions `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"active-lanta-model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply exactly: online\"}],\"temperature\":0,\"max_tokens\":8}"
```

Metrics are exposed at:

```text
http://127.0.0.1:4000/metrics
```
