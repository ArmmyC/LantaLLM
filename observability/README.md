# Observability

This stack runs Prometheus, Grafana, and a small platform exporter.

## Start

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\observability
docker compose up -d
```

## Ports

```text
Prometheus: http://127.0.0.1:9090
Grafana: http://127.0.0.1:3002
Platform exporter: http://127.0.0.1:9108
```

Grafana dashboard:

```text
Lanta LLM Operations
```

## Metrics

Prometheus scrapes:

- LiteLLM metrics from `litellm:4000/metrics` on the shared Docker network
- Platform exporter metrics from `platform-exporter:9108/metrics`

Real LiteLLM metrics currently used by Grafana include:

- total requests and request rate
- failed requests and error rate
- input, output, and total tokens
- output tokens per second
- p50 and p95 request latency
- usage grouped by key alias/user when LiteLLM labels are available
- usage grouped by model label

The platform exporter checks:

- LiteLLM reachability
- vLLM `/models` reachability through the tunnel
- active model name
- local CPU/RAM/disk where available
- Slurm job state where Slurm is available

If Slurm is unavailable, Slurm metrics report unknown or zero health instead of crashing.

Slurm and GPU panels are optional. They require Lanta-side exporters or direct Slurm metric collection. No data in those panels is expected until those exporters are configured.
