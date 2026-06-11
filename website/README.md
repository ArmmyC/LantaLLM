# Lanta LLM Hosting Website

A small deployable chat website for your OpenAI-compatible vLLM endpoint.

The browser talks to `/api/chat`; the backend proxy adds the real upstream API key from environment variables. Do not put the upstream token in frontend JavaScript.

## Local Run

Keep the Lanta tunnel open:

```powershell
powershell -ExecutionPolicy Bypass -File ..\windows\tunnel\start-lanta-vllm-tunnel.ps1
```

Start the web app:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\website
$env:QWEN_BASE_URL="http://127.0.0.1:8000/v1"
$env:QWEN_API_KEY="EMPTY"
$env:QWEN_MODEL="qwen36-27b"
$env:SITE_PASSWORD="pick-a-password"
npm run dev
```

Open:

```text
http://127.0.0.1:5177
```

## Deploy To Vercel

Set these environment variables in Vercel:

```text
QWEN_BASE_URL=https://armmy.tail35169a.ts.net/v1
QWEN_API_KEY=<your gateway token>
QWEN_MODEL=qwen36-27b
SITE_PASSWORD=<password friends type into the page>
```

Deploy the `website` folder.

The deployed website depends on your upstream path being alive:

```text
Vercel site -> Tailscale Funnel -> your local gateway -> SSH tunnel -> Lanta vLLM
```

## Features

- Chat history in the browser session.
- Thinking mode toggle for Qwen models.
- Max token and temperature controls.
- Local file attachment as explicit context.
- Optional site password.
