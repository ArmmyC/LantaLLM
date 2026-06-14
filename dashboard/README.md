# Lanta LLM Dashboard

Dashboard backend for the Lanta LLM platform. It keeps the existing benchmark APIs and adds hosting/admin status endpoints.

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

`/usage` reads current LiteLLM request, error, token, latency, key-alias, and model metrics from Prometheus. Grafana remains the detailed time-series dashboard.

The first implementation reads the local JSON fallback at `benchmark/results/benchmark-results.json`. PostgreSQL migrations are provided under `benchmark/storage/migrations/` for durable deployments.
