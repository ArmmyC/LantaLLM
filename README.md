# Lanta LLM Hosting

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![PowerShell](https://img.shields.io/badge/PowerShell-Windows-5391FE?style=flat-square&logo=powershell&logoColor=white)](https://learn.microsoft.com/powershell/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-Gateway-111827?style=flat-square)](https://www.litellm.ai/)
[![OpenWebUI](https://img.shields.io/badge/OpenWebUI-Chat_UI-10a37f?style=flat-square)](https://openwebui.com/)
[![Grafana](https://img.shields.io/badge/Grafana-Observability-f46800?style=flat-square&logo=grafana&logoColor=white)](https://grafana.com/)

Private LLM hosting stack for serving a Lanta-hosted vLLM model through **OpenWebUI**, **LiteLLM virtual keys**, **Grafana metrics**, and a lightweight **admin status page**.

> [!IMPORTANT]
> Do not expose raw vLLM directly to the public internet. Share access through OpenWebUI for chat users or LiteLLM virtual keys for API users.

## Contents

[Overview](#overview) • [Architecture](#architecture) • [Features](#features) • [Quick start](#quick-start) • [Share with friends](#share-with-friends) • [API keys](#api-keys) • [Keep the job alive](#keep-the-job-alive) • [Observability](#observability) • [Project layout](#project-layout) • [Troubleshooting](#troubleshooting)

## Overview

Lanta LLM Hosting is a small control plane for running one active Hugging Face model on Lanta Slurm and making it usable from a local Windows host.

It is designed around a simple split:

| Component | Purpose |
| --- | --- |
| **OpenWebUI** | Browser chat UI for friends or internal users. |
| **LiteLLM** | OpenAI-compatible API gateway, stable model alias, virtual keys, budgets, and usage metrics. |
| **vLLM on Lanta** | Actual model serving process running inside a Slurm GPU job. |
| **Windows SSH tunnel** | Local bridge from your machine to the Lanta vLLM port. |
| **Grafana + Prometheus** | Metrics, usage, tokens, latency, and error dashboards. |
| **Admin `/status` page** | Lightweight health and links page. |
| **Benchmark module** | Optional HDL benchmark tooling retained for experiments. |

The public model name users should call is always:

```text
active-lanta-model
```

The real model behind that alias can be swapped without changing user instructions.

## Architecture

```text
Users / Friends
  |
  +--> OpenWebUI chat
  |
  +--> OpenAI-compatible API clients
            |
            v
        LiteLLM gateway
            |
            v
      Local SSH tunnel
            |
            v
       vLLM on Lanta
            |
            v
      Active hosted model
```

Monitoring flow:

```text
LiteLLM /metrics + platform exporter /metrics
  |
  v
Prometheus
  |
  v
Grafana: Lanta LLM Operations
```

Local service URLs:

| Service | URL |
| --- | --- |
| OpenWebUI chat | `http://127.0.0.1:3000` |
| LiteLLM API | `http://127.0.0.1:4000/v1` |
| vLLM tunnel | `http://127.0.0.1:8000/v1` |
| Admin status | `http://127.0.0.1:8088/status` |
| Grafana | `http://127.0.0.1:3002` |
| Prometheus | `http://127.0.0.1:9090` |

## Features

- **Private model hosting** on Lanta Slurm with vLLM.
- **OpenWebUI chat** for browser users.
- **LiteLLM gateway** for OpenAI-compatible clients.
- **Stable model alias** with `active-lanta-model`.
- **Virtual API keys** for friends or internal users.
- **Usage tracking** through LiteLLM and Prometheus.
- **Grafana dashboard** for requests, tokens, latency, errors, and key/model usage.
- **Admin status page** for service health and useful links.
- **Windows tunnel scripts** for keeping the local vLLM endpoint reachable.
- **Lanta job watchdogs** for resubmitting the Slurm job when it ends.
- **Optional benchmark runner** for HDL/model smoke tests.

## Quick start

### Prerequisites

- Windows host with PowerShell.
- Docker Desktop with Docker Compose.
- SSH alias named `lanta` that can reach the Lanta login node.
- Model files already downloaded under the remote Lanta project path.
- Optional: Tailscale for sharing OpenWebUI publicly.

> [!NOTE]
> The remote Lanta project path used by the scripts is `/project/zz992000-zdevb/zz992005/ub127/SiliconCraft`.

### 1. Start the Lanta vLLM job

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen36-35b-a3b"
```

Check the job:

```powershell
ssh lanta "squeue -u ub127"
```

### 2. Start the local SSH tunnel

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
```

Verify vLLM locally:

```powershell
curl.exe http://127.0.0.1:8000/v1/models
```

### 3. Start LiteLLM, OpenWebUI, observability, and the admin dashboard

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\litellm
docker compose up -d

cd ..\openwebui
docker compose up -d

cd ..\observability
docker compose up -d

cd ..\dashboard
docker compose up -d --build
```

### 4. Check the full platform

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
$env:LITELLM_MASTER_KEY="sk-your-key"
powershell -ExecutionPolicy Bypass -File .\scripts\check-platform.ps1
```

Open:

```text
Chat:          http://127.0.0.1:3000
Admin status:  http://127.0.0.1:8088/status
Grafana:       http://127.0.0.1:3002
```

## Share with friends

The recommended public sharing path is OpenWebUI through Tailscale Funnel.

First stop any old Funnel route:

```powershell
tailscale funnel --https=443 off
```

Then expose OpenWebUI:

```powershell
tailscale funnel --bg --https=443 http://127.0.0.1:3000
tailscale funnel status
```

Your friends open the Funnel URL and sign in through OpenWebUI.

> [!TIP]
> Keep OpenWebUI signup set to `pending` or manually approve users from the OpenWebUI admin panel. Disable signup again after invited users have created accounts.

> [!CAUTION]
> Do not Funnel Grafana, Prometheus, the admin dashboard, or raw vLLM for normal users. Keep those admin-only unless you intentionally secure them.

## API keys

API access goes through LiteLLM virtual keys. Users should receive:

```text
Base URL: http://<host>:4000/v1
Model: active-lanta-model
API key: sk-user-key
```

Create a user key:

```powershell
curl.exe http://127.0.0.1:4000/key/generate `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"models\":[\"active-lanta-model\"],\"max_budget\":10,\"metadata\":{\"user\":\"friend-name\"}}"
```

Call the hosted model:

```powershell
curl.exe http://127.0.0.1:4000/v1/chat/completions `
  -H "Authorization: Bearer sk-user-key" `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"active-lanta-model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply exactly: online\"}],\"temperature\":0,\"max_tokens\":8}"
```

See [docs/KEY_MANAGEMENT.md](docs/KEY_MANAGEMENT.md) for create, list, revoke, budget, PowerShell, and Python examples.

## Keep the job alive

Slurm jobs end when their time limit expires. The foreground watchdog can resubmit the preset when no pending or running `vllm-model` job exists.

Recommended Windows watchdog:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\watch-lanta-job.ps1 -Preset qwen36-35b-a3b
```

One-shot dry run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\watch-lanta-job.ps1 -Preset qwen36-35b-a3b -Once -DryRun
```

Optional Lanta-side polling wrapper:

```bash
cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft
bash scripts/watch-preset.sh --preset qwen36-35b-a3b
```

> [!WARNING]
> The watchdog only checks job existence. It does not prove vLLM is ready. After resubmission, allow several minutes for model loading, then run `scripts/check-platform.ps1`.

Stop either watchdog with `Ctrl+C`. When hosting is finished, stop the watchdog before canceling the Slurm job.

## Observability

Use Grafana as the source of truth for usage and metrics:

```text
http://127.0.0.1:3002
Dashboard: Lanta LLM Operations
```

Grafana shows LiteLLM-observed:

- request rate and total requests;
- failed requests and error rate;
- input/output tokens and output token/s;
- p50 and p95 latency;
- usage by API key/user when labels are available;
- usage by model alias.

The custom dashboard is intentionally small:

```text
http://127.0.0.1:8088/status
```

It checks OpenWebUI, LiteLLM, LiteLLM models, the vLLM tunnel, platform exporter, Prometheus, Grafana, and itself.

> [!NOTE]
> Slurm and GPU panels may show no data until Lanta-side exporters or direct metric collection are configured. That does not necessarily mean chat/API inference is down.

## Project layout

```text
lanta-llm-hosting/
  litellm/              LiteLLM gateway, virtual keys, usage, metrics
  openwebui/            Main browser chat UI backed by LiteLLM
  observability/        Prometheus, Grafana, and platform exporter
  dashboard/            Admin /status page plus optional benchmark APIs
  windows/tunnel/       Auto-reconnecting SSH tunnel utilities
  lanta/scripts/        Slurm/vLLM download, serve, submit, and watch scripts
  scripts/              Local platform checks and Windows watchdog
  benchmark/            Optional HDL benchmark runner and artifacts
  sharing/              Older compatibility sharing gateway
  website/              Older fallback/demo website
  docs/                 Architecture, operations, keys, setup guides
  HOW_TO_USE.md         Command-first runbook
  HOW_TO_SWAP.md        Model swap runbook
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Operations](docs/OPERATIONS.md)
- [Key management](docs/KEY_MANAGEMENT.md)
- [Benchmarking](docs/BENCHMARKING.md)
- [LiteLLM gateway](litellm/README.md)
- [OpenWebUI setup](openwebui/README.md)
- [Observability](observability/README.md)
- [Dashboard](dashboard/README.md)
- [Command runbook](HOW_TO_USE.md)
- [Model swap runbook](HOW_TO_SWAP.md)

## Troubleshooting

### `curl: (52) Empty reply from server`

LiteLLM may still be starting, migrating its database, or restarting. Check logs:

```powershell
cd litellm
docker compose ps
docker compose logs --tail=150 litellm
```

### OpenWebUI still uses old provider settings

OpenWebUI persists admin settings in its Docker volume. Update the provider in the OpenWebUI admin panel instead of deleting the volume, unless losing users/chats/settings is acceptable.

### LiteLLM model-not-found error

Compare the vLLM model name:

```powershell
curl.exe http://127.0.0.1:8000/v1/models
```

with `VLLM_MODEL_ID` in `litellm/.env`. The LiteLLM value usually needs the `openai/` provider prefix.

### Full platform check

```powershell
$env:LITELLM_MASTER_KEY="sk-your-key"
powershell -ExecutionPolicy Bypass -File .\scripts\check-platform.ps1
```
