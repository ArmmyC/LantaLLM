# Lanta LLM Platform Architecture

## Target Architecture

```text
User Browser
  |
  v
OpenWebUI
  |
  v
LiteLLM Proxy
  |
  v
Local SSH Tunnel
  |
  v
vLLM on Lanta Slurm
  |
  v
Active Hugging Face model
```

Monitoring:

```text
LiteLLM /metrics
Platform exporter /metrics
  |
  v
Prometheus
  |
  v
Grafana
```

Optional benchmarking:

```text
Benchmark Runner
  |
  v
LiteLLM /v1/chat/completions
  |
  v
Code extraction and evaluator checks
  |
  v
PostgreSQL or local JSON fallback
  |
  v
Benchmark Dashboard API
```

## Components

- `lanta/scripts/`: keeps the existing Slurm/vLLM model serving and swap flow.
- `windows/tunnel/`: keeps the existing auto-reconnecting local SSH tunnel.
- `litellm/`: preferred OpenAI-compatible API gateway, virtual keys, usage, budgets, and metrics.
- `openwebui/`: primary human chat UI.
- `observability/`: Prometheus, Grafana, and platform exporter.
- `benchmark/`: optional HDL benchmark cases, runner, evaluators, schemas, migrations, and artifacts.
- `dashboard/`: hosting status and usage pages plus retained benchmark APIs.
- `website/`: existing fallback demo UI, intentionally retained.
- `sharing/`: existing compatibility gateway, retained but no longer preferred.

## Stable Endpoint Contract

The active vLLM model is exposed locally through the tunnel at:

```text
http://127.0.0.1:8000/v1
```

LiteLLM routes to the Docker-visible form:

```text
http://host.docker.internal:8000/v1
```

Tools and users should call LiteLLM:

```text
http://127.0.0.1:4000/v1
```

The model alias exposed to users is:

```text
active-lanta-model
```

Only one Lanta vLLM model is served on port `8000` at a time in the current design.
