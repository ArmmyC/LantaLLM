# OpenWebUI

OpenWebUI is the primary chat UI. It should call LiteLLM, not vLLM directly.

## Start

Start the Lanta model, tunnel, and LiteLLM first. Then:

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

On first launch, OpenWebUI asks you to create the first account. That first account becomes the OpenWebUI admin. This login is separate from LiteLLM API keys.

## Provider Configuration

Automatic environment configuration points OpenWebUI to:

```text
http://litellm:4000/v1
```

If configuring manually in the OpenWebUI admin panel, use:

```text
OpenAI-compatible API URL: http://host.docker.internal:4000/v1
API key: a LiteLLM virtual key or the LiteLLM master key for admin testing
```

Default model:

```text
active-lanta-model
```

If OpenWebUI keeps old provider settings after `.env` changes, update the provider in the OpenWebUI admin settings. Do not delete the OpenWebUI Docker volume unless you are okay losing accounts, chats, and saved settings.

OpenWebUI stores chats and users. LiteLLM and Prometheus are the source of truth for usage metrics, API keys, budgets, and request telemetry.
