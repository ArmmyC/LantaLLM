# Lanta LLM Dashboard

Lightweight admin landing/status service for the Lanta LLM platform. It keeps the existing benchmark APIs, but Grafana remains the metrics and usage dashboard.

## Start

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\dashboard\backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Open API:

```text
http://127.0.0.1:8088/api/healthz
http://127.0.0.1:8088/api/platform/status
http://127.0.0.1:8088/api/platform/usage
http://127.0.0.1:8088/api/benchmark/runs
http://127.0.0.1:8088/api/benchmark/cases
http://127.0.0.1:8088/api/benchmark/summary
```

Open pages:

```text
http://127.0.0.1:8088/status
http://127.0.0.1:8088/usage
http://127.0.0.1:8088/runs
http://127.0.0.1:8088/cases
```

`/status` checks OpenWebUI, LiteLLM, LiteLLM models, the vLLM tunnel, platform exporter, Prometheus, Grafana, and the dashboard itself.

`/usage` is a simple Grafana link/guide page and does not duplicate charts. `/api/platform/usage` is an experimental machine-readable diagnostic summary only.

The first implementation reads the local JSON fallback at `benchmark/results/benchmark-results.json`. PostgreSQL migrations are provided under `benchmark/storage/migrations/` for durable deployments.
