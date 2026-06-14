# Lanta LLM Hosting

Host a private LLM on Lanta with OpenWebUI for chat users, LiteLLM virtual keys for API users, and local health and usage dashboards for the admin.

## Repository Layout

```text
lanta-llm-hosting/
  website/              Browser chat application and backend proxy.
  cli/                  OpenAI-compatible command-line chat client.
  windows/tunnel/       Hidden SSH tunnel watchdog and local API tests.
  sharing/              Authenticated API gateway and Tailscale Funnel tools.
  litellm/              Preferred OpenAI-compatible gateway, keys, usage, metrics.
  openwebui/            Primary browser chat UI backed by LiteLLM.
  observability/        Prometheus, Grafana, and platform exporter.
  benchmark/            HDL benchmark cases, runner, schemas, and artifacts.
  dashboard/            Hosting status/usage pages plus optional benchmark APIs.
  lanta/scripts/        Generic model download, serve, submit, and test scripts.
  lanta/legacy-qwen36/  Older Qwen3.6-specific scripts kept for reference.
  docs/                 Setup, model swapping, UI, and friend usage guides.
  HOW_TO_USE.md         Command-only operations runbook.
  HOW_TO_SWAP.md        Same-endpoint model swap runbook.
```

## Quick Start

Start the hidden tunnel after the Lanta vLLM job is running:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
```

Start LiteLLM, OpenWebUI, observability, and the admin dashboard:

```powershell
cd litellm
docker compose up -d

cd ..\openwebui
docker compose up -d

cd ..\observability
docker compose up -d

cd ..\dashboard
docker compose up -d --build
```

Open:

```text
Chat:   http://127.0.0.1:3000
Status: http://127.0.0.1:8088/status
Usage:  http://127.0.0.1:8088/usage
Grafana: http://127.0.0.1:3002
```

See [HOW_TO_USE.md](HOW_TO_USE.md) for the complete operational command list and [HOW_TO_SWAP.md](HOW_TO_SWAP.md) for model swapping.

## Platform Stack

The production-oriented path is now:

```text
OpenWebUI -> LiteLLM -> local SSH tunnel -> vLLM on Lanta
```

Start order:

1. Start Lanta vLLM job.
2. Start tunnel.
3. Start LiteLLM.
4. Start OpenWebUI.
5. Start observability stack.
6. Start the hosting dashboard.

Key docs:

- [Architecture](docs/ARCHITECTURE.md)
- [Operations](docs/OPERATIONS.md)
- [Key Management](docs/KEY_MANAGEMENT.md)
- [Benchmarking](docs/BENCHMARKING.md)

Local stack check:

```powershell
$env:LITELLM_MASTER_KEY="sk-your-key"
powershell -ExecutionPolicy Bypass -File .\scripts\check-platform.ps1
```

The existing `website/` remains as a fallback compatibility/demo UI. Benchmark tooling is optional and does not drive the hosting dashboard.

## Lanta Deployment

Copy the files in `lanta/scripts/` to the remote project's `scripts/` directory. The remote project path remains:

```text
/project/zz992000-zdevb/zz992005/ub127/SiliconCraft
```

The local repository rename does not require moving downloaded models or Conda environments on Lanta.
