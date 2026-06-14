# LiteLLM Key Management

LiteLLM virtual keys are the supported way to give API access to friends or internal users. Do not share `LITELLM_MASTER_KEY` with normal users.

Users call:

```text
Base URL: http://<host>:4000/v1
Model: active-lanta-model
API key: sk-user-key
```

`active-lanta-model` is the stable public alias. Admins can swap the real vLLM model behind it without changing user instructions.

## Admin Setup

Set the master key only in your local admin shell:

```powershell
$env:LITELLM_MASTER_KEY="sk-your-master-key"
```

Verify LiteLLM:

```powershell
curl.exe http://127.0.0.1:4000/v1/models `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY"
```

## Create A User Key

```powershell
curl.exe http://127.0.0.1:4000/key/generate `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"models\":[\"active-lanta-model\"],\"metadata\":{\"user\":\"friend-name\",\"purpose\":\"personal testing\",\"created_by\":\"admin\"}}"
```

With a budget:

```powershell
curl.exe http://127.0.0.1:4000/key/generate `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"models\":[\"active-lanta-model\"],\"max_budget\":5,\"metadata\":{\"user\":\"friend-name\",\"purpose\":\"temporary testing\",\"created_by\":\"admin\"}}"
```

Copy the generated `sk-...` key once and send it to the user through a private channel.

## List Keys

```powershell
curl.exe http://127.0.0.1:4000/key/list `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY"
```

## Revoke A Key

```powershell
curl.exe http://127.0.0.1:4000/key/delete `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"keys\":[\"sk-user-key\"]}"
```

## User API Examples

PowerShell:

```powershell
$env:OPENAI_API_KEY="sk-user-key"

$body = @{
  model = "active-lanta-model"
  messages = @(@{
    role = "user"
    content = "Reply exactly: online"
  })
  temperature = 0
  max_tokens = 8
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Uri "http://127.0.0.1:4000/v1/chat/completions" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $env:OPENAI_API_KEY" } `
  -ContentType "application/json" `
  -Body $body
```

Python:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:4000/v1",
    api_key="sk-user-key",
)

response = client.chat.completions.create(
    model="active-lanta-model",
    messages=[{"role": "user", "content": "Reply exactly: online"}],
    temperature=0,
    max_tokens=8,
)
print(response.choices[0].message.content)
```

OpenAI-compatible clients should use:

```text
Base URL: http://<host>:4000/v1
API key: sk-user-key
Model: active-lanta-model
```

## Safety Notes

- Normal users get virtual keys only.
- Admin keeps the master key private.
- Generated keys should not be committed, pasted in logs, or stored in plaintext docs.
- Revoke lost or leaked keys immediately.
- OpenWebUI accounts are separate from LiteLLM API keys.
