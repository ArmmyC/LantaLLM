# Feature Spec: Lanta LLM Hosting Platform - Status Landing Page, Key Access, and Grafana-First Observability

## 1. Goal

This project is a **private LLM hosting platform** for running one active model on Lanta and making it easy for friends or internal users to access that model through either a browser chat UI or an OpenAI-compatible API key.

The project should not become a second Grafana, a benchmark research product, or a complex SaaS portal.

The target platform should be simple:

```text
Friends / Users
  |
  +--> OpenWebUI for browser chat
  |
  +--> LiteLLM virtual key for API access

Admin
  |
  +--> /status custom landing page for health and links
  |
  +--> Grafana for metrics, usage, tokens, latency, and errors
  |
  +--> LiteLLM key APIs for key creation/list/revoke
```

Core components:

1. **OpenWebUI** is the chat UI.
2. **LiteLLM** is the API gateway, model alias layer, virtual key system, usage source, and Prometheus metrics source.
3. **Grafana** is the real metrics and usage dashboard.
4. **Prometheus** stores and queries time-series metrics.
5. **Custom dashboard `/status`** is only a lightweight admin landing page and health summary.
6. **`scripts/check-platform.ps1`** is the command-line health checker.
7. **`docs/KEY_MANAGEMENT.md`** is the first supported key management flow.
8. **Benchmark tooling remains optional** and should not drive this phase.

The main inference path remains:

```text
OpenWebUI or API Client
  |
  v
LiteLLM Gateway
  |
  v
Local SSH Tunnel
  |
  v
vLLM on Lanta
  |
  v
Active hosted model
```

The stable public model name remains:

```text
active-lanta-model
```

Users should call `active-lanta-model`. The exact underlying hosted model can change behind the alias. Automatic model sync is not required for this phase.

## 2. Product direction

### 2.1 What this project is

This project is for hosting and sharing access to a private LLM.

It should answer:

1. Is the hosted model reachable?
2. Is OpenWebUI reachable?
3. Is LiteLLM reachable?
4. Is the vLLM tunnel reachable?
5. Is Prometheus running?
6. Is Grafana running?
7. What URLs should I open?
8. What URL, model name, and key should I give a friend?
9. How do I create a virtual API key?
10. How do I revoke a virtual API key?
11. Where do I view usage and token charts?
12. Where do I troubleshoot failures?

### 2.2 What this project is not

This project is not primarily:

1. A benchmark research platform.
2. A Grafana replacement.
3. A public SaaS billing portal.
4. A full user-management system.
5. A full model comparison arena.
6. A full EDA evaluation environment.
7. A Kubernetes production deployment.
8. A multi-model router for many simultaneous models.
9. A replacement for OpenWebUI.
10. A place to expose the LiteLLM master key.

## 3. Current state snapshot

The repository currently includes:

```text
litellm/              LiteLLM gateway, config, Docker Compose, .env example, README
openwebui/            OpenWebUI Docker Compose and .env example
observability/        Prometheus, Grafana, platform exporter, dashboard JSON
benchmark/            Optional HDL benchmark runner and cases
dashboard/            FastAPI app currently containing benchmark APIs plus platform status pages
scripts/check-platform.ps1
                      Local health checker for vLLM, LiteLLM, OpenWebUI, exporter, Prometheus, Grafana, dashboard
website/              Existing fallback demo UI
sharing/              Existing sharing/API gateway compatibility tools
lanta/scripts/        Lanta Slurm/vLLM scripts
windows/tunnel/       Windows SSH tunnel tools
docs/KEY_MANAGEMENT.md
                      LiteLLM virtual key admin/user guide
```

The current custom dashboard has `/status`, `/usage`, `/api/platform/status`, and `/api/platform/usage`. The next phase should **de-emphasize `/usage`** because usage charts belong in Grafana.

## 4. Non-goals

Do **not** prioritize:

1. Building a custom metrics dashboard that duplicates Grafana.
2. Keeping `/usage` as a full custom usage dashboard.
3. Building custom time-series charts in FastAPI/HTML.
4. Implementing automatic model sync as a required feature.
5. Renaming `active-lanta-model` every time the backend model changes.
6. Expanding the benchmark suite as the main feature.
7. Building a benchmark leaderboard.
8. Building a key self-service portal open to normal users.
9. Allowing anonymous key generation.
10. Storing generated user keys in plaintext dashboard files.
11. Exposing the LiteLLM master key in any UI.
12. Replacing OpenWebUI.
13. Deleting existing `website/`, `sharing/`, `lanta/scripts/`, or `windows/tunnel/`.

## 5. Assumptions

1. One active vLLM model is served on the main tunnel at a time.
2. The local vLLM tunnel is:

```text
http://127.0.0.1:8000/v1
```

3. Docker containers reach the local tunnel through:

```text
http://host.docker.internal:8000/v1
```

4. OpenWebUI remains the main browser chat UI.
5. LiteLLM remains the main API gateway.
6. LiteLLM virtual keys are the supported way to give friends/API users access.
7. Grafana is the source of truth for usage charts.
8. The custom dashboard is a status and links page only.
9. The public model alias remains:

```text
active-lanta-model
```

10. Users do not need to know the exact underlying backend model.
11. Admins may optionally see the vLLM-reported model on `/status`.
12. GPU metrics are optional and should not block the platform.
13. Slurm metrics are optional and should not block the platform.
14. `.env` files are local-only and must not be committed.
15. The first supported key management flow can be documentation and LiteLLM curl commands.
16. A key management UI is optional and must be admin-only if implemented.

## 6. User stories

### 6.1 Friend using browser chat

* As a friend, I want to open OpenWebUI and chat with the hosted model.
* As a friend, I want the admin to give me a URL and login instructions.
* As a friend, I do not want to know Slurm, vLLM, SSH tunnels, or LiteLLM internals.
* As a friend, I can simply choose or use `active-lanta-model`.

### 6.2 Friend using API key

* As a friend, I want an API key so I can use the hosted model in my own scripts, tools, or OpenAI-compatible clients.
* As a friend, I want copy-paste instructions with base URL, model name, and example requests.
* As a friend, I should only receive my own virtual key, never the master key.

### 6.3 Admin hosting the model

* As an admin, I want one page that tells me if the platform is healthy.
* As an admin, I want one command that checks all major services.
* As an admin, I want to see links to OpenWebUI, Grafana, Prometheus, LiteLLM API, and key docs.
* As an admin, I want Grafana to show requests, tokens, latency, and errors.
* As an admin, I want to create, list, and revoke LiteLLM virtual keys.
* As an admin, I want clear warnings when a service is down.
* As an admin, I want clear docs for sharing access with friends.

### 6.4 Developer maintaining the repo

* As a developer, I want the repo direction to be clear: hosting first, benchmark optional.
* As a developer, I want tests for platform status and health checks.
* As a developer, I want the custom dashboard to remain simple.
* As a developer, I want to avoid duplicating Grafana functionality.

## 7. Component responsibilities

### 7.1 OpenWebUI

OpenWebUI is responsible for:

1. Browser chat UI.
2. User login for the chat UI.
3. Chat history.
4. User-facing model selection.
5. Calling LiteLLM through the OpenAI-compatible API.

OpenWebUI is **not** responsible for:

1. API key creation for external users.
2. Prometheus metrics storage.
3. Admin health dashboard.
4. Lanta model management.

### 7.2 LiteLLM

LiteLLM is responsible for:

1. OpenAI-compatible gateway.
2. Stable model alias:

```text
active-lanta-model
```

3. Virtual key creation.
4. Virtual key list/revoke.
5. Model restrictions per key.
6. Budgets/limits where supported.
7. Usage metrics.
8. Prometheus metrics endpoint.
9. Routing to vLLM through the tunnel.

LiteLLM is **not** responsible for:

1. Browser chat UI.
2. Human dashboard pages.
3. Long-term Grafana charts.

### 7.3 Grafana

Grafana is responsible for:

1. Usage dashboard.
2. Request rate charts.
3. Total request charts.
4. Error rate charts.
5. Latency charts.
6. Input/output token charts.
7. Output token/s charts.
8. Usage by API key/user if LiteLLM labels are available.
9. Usage by model alias.
10. Tunnel and service health over time.
11. Optional GPU/Slurm panels if exporters are configured.

Grafana is the **source of truth for charts**.

### 7.4 Prometheus

Prometheus is responsible for:

1. Scraping LiteLLM `/metrics`.
2. Scraping platform exporter `/metrics`.
3. Storing time-series metrics.
4. Serving queries to Grafana.

Prometheus is not a user-facing dashboard.

### 7.5 Custom dashboard service

The custom dashboard is responsible for:

1. Lightweight admin landing page.
2. Current health summary.
3. Links to OpenWebUI, Grafana, Prometheus, docs, and API endpoints.
4. Public alias display.
5. vLLM-reported model display if available.
6. Component status checks.
7. Friend access instructions.
8. Optional admin-only key helper if safe.

The custom dashboard is **not** responsible for:

1. Time-series charts.
2. Replacing Grafana.
3. Full usage analytics.
4. Benchmark research UI as the main purpose.

### 7.6 Benchmark module

Benchmark is optional.

It may remain available for smoke testing or another report/project, but it should not block hosting features.

## 8. UX / UI requirements

### 8.1 OpenWebUI user experience

Required behavior:

1. User opens:

```text
http://127.0.0.1:3000
```

2. First launch asks the admin to create the first OpenWebUI admin account.
3. Users log in through OpenWebUI.
4. Users use `active-lanta-model`.
5. OpenWebUI talks to LiteLLM, not directly to vLLM.
6. Docs explain that OpenWebUI accounts are separate from LiteLLM API keys.
7. Docs explain that OpenWebUI settings can persist after first launch.

### 8.2 API user experience

Users should receive instructions like:

```text
Base URL: http://<host>:4000/v1
Model: active-lanta-model
API key: sk-user-key
```

Minimum examples in docs:

1. PowerShell request.
2. Python OpenAI SDK request.
3. OpenAI-compatible client settings.

The docs must say:

```text
Do not share the LiteLLM master key. Users receive virtual keys only.
```

### 8.3 Admin landing page `/status`

Keep:

```text
GET /status
GET /api/platform/status
```

The `/status` page should be the custom dashboard's main page.

It should show:

1. Overall status.
2. Public model alias.
3. vLLM-reported model, if available.
4. OpenWebUI health.
5. LiteLLM health.
6. LiteLLM model alias availability.
7. vLLM tunnel health.
8. Platform exporter health.
9. Prometheus health.
10. Grafana health.
11. Dashboard health.
12. Last checked timestamp.
13. Suggested fixes.
14. Links to:
    * OpenWebUI
    * Grafana
    * Prometheus
    * LiteLLM models endpoint docs
    * Key management docs
    * Operations docs

It should not show long charts.

### 8.4 Usage page behavior

The custom `/usage` page should **not** duplicate Grafana.

Choose one of these acceptable behaviors:

#### Preferred behavior

Make `/usage` a simple redirect or link page to Grafana.

Example content:

```text
Usage charts live in Grafana.
Open Grafana: http://127.0.0.1:3002
Dashboard: Lanta LLM Operations
```

It may include a tiny summary if already available, but should not grow into a chart dashboard.

#### Acceptable fallback behavior

Keep `/api/platform/usage` only as a machine-readable diagnostic endpoint, but do not treat it as the main usage dashboard.

Rules:

1. Grafana remains the documented usage dashboard.
2. `/usage` must clearly say that Grafana is the source of truth.
3. Remove complex table/charts if they duplicate Grafana.
4. Do not spend more engineering effort expanding custom usage analytics unless Grafana cannot meet a specific need.

### 8.5 Friend access page

Add a simple page if useful:

```text
/friend-access
```

or include the content in `/status`.

It should show:

1. Chat URL.
2. API base URL.
3. Model name.
4. Link to key management docs.
5. Example curl or PowerShell request.
6. Reminder: users need their own virtual key.

Do not show any real secret.

## 9. Functional requirements

### 9.1 Keep stable model alias

Keep:

```text
active-lanta-model
```

Requirements:

1. OpenWebUI uses `active-lanta-model`.
2. API users use `active-lanta-model`.
3. LiteLLM exposes `active-lanta-model`.
4. Dashboard status verifies that `active-lanta-model` is present in LiteLLM `/v1/models`.
5. Docs explain that this alias points to the currently hosted backend model.
6. Do not require automatic model-sync scripts for this phase.

### 9.2 Key management documentation

Keep and improve:

```text
docs/KEY_MANAGEMENT.md
```

It must include:

1. Master key vs virtual key explanation.
2. Create key command.
3. Create key with budget command.
4. List keys command.
5. Revoke key command.
6. User PowerShell example.
7. User Python example.
8. OpenAI-compatible client settings.
9. Safety notes.
10. Warning not to commit or paste secrets.

### 9.3 Optional key management UI

A custom `/keys` UI is optional.

If implemented, it must be admin-only.

Requirements if implemented:

1. Disabled unless `DASHBOARD_ADMIN_TOKEN` is set.
2. Requires admin token on every key operation.
3. Uses LiteLLM master key only server-side.
4. Never exposes LiteLLM master key.
5. Shows generated user key only once.
6. Does not store full generated key in plaintext.
7. Lists keys with masked key aliases only.
8. Supports revoke.
9. Includes warning that docs are the safer initial flow.

If this cannot be implemented safely, do not implement it yet. Keep docs only.

### 9.4 Platform status API

Keep and improve:

```text
GET /api/platform/status
```

Response shape:

```json
{
  "timestamp": "2026-06-14T00:00:00Z",
  "overall_status": "ok",
  "model": {
    "public_alias": "active-lanta-model",
    "vllm_reported_model_id": "qwen36-35b-a3b"
  },
  "components": {
    "openwebui": { "status": "ok", "latency_ms": 20, "message": "ok" },
    "litellm": { "status": "ok", "latency_ms": 25, "message": "ok" },
    "litellm_models": { "status": "ok", "latency_ms": 30, "message": "active-lanta-model available" },
    "vllm_tunnel": { "status": "ok", "latency_ms": 40, "message": "ok" },
    "platform_exporter": { "status": "ok", "latency_ms": 5, "message": "ok" },
    "prometheus": { "status": "ok", "latency_ms": 12, "message": "ok" },
    "grafana": { "status": "ok", "latency_ms": 20, "message": "ok" },
    "dashboard": { "status": "ok", "latency_ms": 0, "message": "ok" }
  },
  "links": {
    "openwebui": "http://127.0.0.1:3000",
    "grafana": "http://127.0.0.1:3002",
    "prometheus": "http://127.0.0.1:9090",
    "status": "http://127.0.0.1:8088/status"
  },
  "warnings": []
}
```

Status rules:

1. `overall_status = ok` only if required components are ok.
2. `overall_status = degraded` if at least one component is down but the status endpoint still works.
3. `overall_status = down` only if core inference path is unavailable and detected as unavailable.
4. HTTP status should usually be `200` when a status object is returned.
5. Do not expose secrets.
6. Error messages should be truncated to avoid leaking sensitive environment values.

### 9.5 Platform links API

Optional but useful:

```text
GET /api/platform/links
```

Response:

```json
{
  "chat_url": "http://127.0.0.1:3000",
  "api_base_url": "http://127.0.0.1:4000/v1",
  "model": "active-lanta-model",
  "grafana_url": "http://127.0.0.1:3002",
  "prometheus_url": "http://127.0.0.1:9090",
  "status_url": "http://127.0.0.1:8088/status",
  "key_docs": "docs/KEY_MANAGEMENT.md"
}
```

This endpoint must not include keys.

### 9.6 Usage handling

Do not build a custom Grafana replacement.

Change current usage behavior as follows:

1. `/usage` should become a simple Grafana landing/link page.
2. `/api/platform/usage` may remain for diagnostics, but docs must not present it as the primary usage dashboard.
3. README and operations docs must say:

```text
Use Grafana for usage, token, latency, and error charts.
```

4. If `/api/platform/usage` remains, label it as:

```text
experimental summary endpoint
```

5. No custom charts should be added to the dashboard service.

### 9.7 Grafana dashboard requirements

Grafana dashboard name:

```text
Lanta LLM Operations
```

Grafana must be the documented place for:

1. LiteLLM request rate.
2. Total requests.
3. Error rate.
4. p50 latency.
5. p95 latency.
6. Input tokens/min.
7. Output tokens/min.
8. Output token/s.
9. Total tokens.
10. Usage by key/user if labels exist.
11. Usage by model alias.
12. LiteLLM uptime.
13. vLLM tunnel health.
14. Platform exporter health.
15. Optional GPU metrics.
16. Optional Slurm metrics.

Panel labels must be clear:

1. Token metrics are LiteLLM-observed, not direct GPU metrics.
2. GPU panels require optional Lanta-side exporter.
3. Slurm panels may be unavailable from local Docker.
4. No-data states should tell the admin to generate a request or check Prometheus targets.

### 9.8 Prometheus requirements

Prometheus should scrape:

```text
litellm:4000/metrics
platform-exporter:9108/metrics
```

Optional exporters can be added later, but they must not be required for core platform health.

### 9.9 Platform exporter requirements

The platform exporter should expose:

```text
/healthz
/metrics
```

It should report:

1. Platform exporter up.
2. LiteLLM reachable.
3. LiteLLM latency.
4. vLLM reachable.
5. vLLM latency.
6. SSH tunnel health.
7. Active vLLM model label if available.
8. Local/container CPU/RAM/disk.
9. Slurm status if available.

It must not crash if Slurm or GPU tools are unavailable.

### 9.10 Check script requirements

Keep and improve:

```text
scripts/check-platform.ps1
```

It should check:

1. vLLM tunnel `/v1/models`.
2. LiteLLM `/health`.
3. LiteLLM `/v1/models` with auth.
4. OpenWebUI homepage.
5. Platform exporter `/healthz`.
6. Prometheus `/-/ready`.
7. Grafana `/api/health`.
8. Dashboard `/api/healthz`.
9. Dashboard `/api/platform/status`.

Output example:

```text
PASS vLLM tunnel - HTTP 200, model=qwen36-35b-a3b
PASS LiteLLM health - HTTP 200
PASS LiteLLM models - active-lanta-model available
PASS OpenWebUI homepage - HTTP 200
PASS Platform exporter - HTTP 200
PASS Prometheus - ready
PASS Grafana - ok
PASS Dashboard API - HTTP 200
PASS Platform status - ok, alias=active-lanta-model, vllm=qwen36-35b-a3b
```

Rules:

1. Do not print secrets.
2. Print clear failure messages.
3. Return exit code `0` when required checks pass.
4. Return exit code `1` when required checks fail.
5. Do not fail because optional GPU/Slurm metrics are missing.

### 9.11 Documentation requirements

Update docs so the architecture is easy to understand.

Required docs:

1. README.
2. `docs/ARCHITECTURE.md`.
3. `docs/OPERATIONS.md`.
4. `docs/KEY_MANAGEMENT.md`.
5. `openwebui/README.md`.
6. `litellm/README.md`.
7. `observability/README.md`.
8. `dashboard/README.md`.
9. `HOW_TO_USE.md`.
10. `HOW_TO_SWAP.md` if model swap language is affected.

Docs must clearly say:

```text
OpenWebUI = chat UI
LiteLLM = API gateway and keys
Grafana = usage and metrics dashboard
Custom /status = admin health landing page
Benchmark = optional
```

## 10. Environment variables

### 10.1 LiteLLM

```env
LITELLM_MASTER_KEY=sk-change-this-master-key
LITELLM_SALT_KEY=change-this-salt-key
LITELLM_DATABASE_URL=postgresql://litellm:litellm_dev_password@postgres:5432/litellm
LITELLM_PORT=4000
VLLM_BASE_URL=http://host.docker.internal:8000/v1
VLLM_API_KEY=EMPTY
VLLM_MODEL_ID=openai/qwen36-27b
LITELLM_ACTIVE_MODEL=active-lanta-model
POSTGRES_USER=litellm
POSTGRES_PASSWORD=litellm_dev_password
POSTGRES_DB=litellm
```

### 10.2 OpenWebUI

```env
OPEN_WEBUI_PORT=3000
OPENAI_API_BASE_URL=http://litellm:4000/v1
OPENAI_API_KEY=sk-change-this-master-key
WEBUI_SECRET_KEY=change-this-openwebui-secret
```

### 10.3 Observability

```env
PLATFORM_EXPORTER_PORT=9108
LITELLM_BASE_URL=http://litellm:4000
LITELLM_API_KEY=sk-change-this-master-key
VLLM_BASE_URL=http://host.docker.internal:8000/v1
SLURM_JOB_NAME=vllm-model
SLURM_USER=ub127
HEALTH_TIMEOUT_SECONDS=3
PROMETHEUS_PORT=9090
GRAFANA_PORT=3002
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your-grafana-password
```

### 10.4 Dashboard

Dashboard should only need enough configuration to perform health checks and render links.

```env
DASHBOARD_PORT=8088
DASHBOARD_CORS_ORIGINS=http://127.0.0.1:8088,http://localhost:8088
DASHBOARD_HEALTH_TIMEOUT_SECONDS=3
LITELLM_ACTIVE_MODEL=active-lanta-model
LITELLM_BASE_URL=http://litellm:4000
LITELLM_API_KEY=sk-change-this-master-key
OPENWEBUI_BASE_URL=http://openwebui:8080
PLATFORM_EXPORTER_BASE_URL=http://platform-exporter:9108
PROMETHEUS_BASE_URL=http://prometheus:9090
GRAFANA_BASE_URL=http://grafana:3000
GRAFANA_PUBLIC_URL=http://127.0.0.1:3002
VLLM_BASE_URL=http://host.docker.internal:8000/v1
PUBLIC_CHAT_URL=http://127.0.0.1:3000
PUBLIC_API_BASE_URL=http://127.0.0.1:4000/v1
PUBLIC_STATUS_URL=http://127.0.0.1:8088/status
```

Benchmark-related dashboard variables can remain for compatibility, but hosting status should not depend on benchmark data.

## 11. Routes and API contract

### 11.1 Keep

```text
GET /status
GET /api/platform/status
GET /api/healthz
```

### 11.2 Change/de-emphasize

```text
GET /usage
GET /api/platform/usage
```

Preferred changes:

1. `/usage` becomes a simple Grafana link page.
2. `/api/platform/usage` is either removed, kept as experimental, or documented as diagnostic only.
3. Docs do not tell users that custom `/usage` replaces Grafana.

### 11.3 Optional

```text
GET /friend-access
GET /api/platform/links
```

These should contain public URLs and examples only, no keys.

### 11.4 Do not add unless safe

```text
GET /keys
POST /api/platform/keys
DELETE /api/platform/keys/{id}
```

Only add these with admin protection.

## 12. Files likely involved

Modify:

```text
docs/specs/llm-platform-control-plane.md
README.md
docs/ARCHITECTURE.md
docs/OPERATIONS.md
docs/KEY_MANAGEMENT.md
HOW_TO_USE.md
HOW_TO_SWAP.md
openwebui/README.md
litellm/README.md
observability/README.md
dashboard/README.md
dashboard/.env.example
dashboard/docker-compose.yml
dashboard/backend/app/platform_status.py
dashboard/backend/app/routers/platform.py
dashboard/backend/app/routers/pages.py
scripts/check-platform.ps1
observability/grafana/dashboards/lanta-llm-operations.json
observability/prometheus/prometheus.yml
tests/test_platform_dashboard.py
tests/test_platform_exporter.py
```

Keep but do not prioritize:

```text
benchmark/
dashboard benchmark run APIs
```

Do not delete:

```text
website/
sharing/
lanta/scripts/
windows/tunnel/
```

## 13. Edge cases

1. vLLM tunnel is down.
2. Lanta job is pending but tunnel exists.
3. vLLM `/models` works but chat fails.
4. LiteLLM `/health` works but `/v1/models` requires auth and fails.
5. LiteLLM key in dashboard `.env` is wrong.
6. OpenWebUI is reachable but configured with old API key.
7. User changed `.env` but did not recreate containers.
8. Postgres password mismatch after volume initialization.
9. Prometheus has no data before first request.
10. Grafana panels show no data because targets are down.
11. LiteLLM metric names change across versions.
12. API key labels are missing from LiteLLM metrics.
13. GPU panels show no data because no GPU exporter exists.
14. Slurm metrics unavailable in local Docker.
15. Dashboard `/status` should still render even if Prometheus is down.
16. Dashboard should not fail if benchmark JSON is missing.
17. User accidentally shares master key.
18. User key is revoked but user still tries to call API.
19. User key lacks access to `active-lanta-model`.
20. Local port conflicts.
21. `curl: (52) Empty reply from server` during LiteLLM startup.
22. OpenWebUI volume persists old settings.
23. Dashboard accidentally logs secrets in warnings.
24. `/usage` becomes confusing because it duplicates Grafana.

## 14. Testing plan

### 14.1 Unit tests

Add/update tests for:

1. Platform status response shape.
2. Overall status calculation.
3. Component health warnings.
4. LiteLLM alias detection.
5. vLLM model extraction.
6. No secret leakage in status response.
7. `/usage` page links to Grafana instead of duplicating charts.
8. Optional `/api/platform/usage` is marked experimental or handles missing metrics gracefully.
9. Platform links response contains no keys.
10. Existing benchmark helper tests still pass.

### 14.2 Integration tests

Add/update tests for:

1. `GET /api/healthz`.
2. `GET /api/platform/status`.
3. `GET /status` page renders.
4. `GET /usage` returns Grafana guidance or redirect-style page.
5. Docker Compose config validates.
6. Grafana dashboard JSON is valid JSON.

### 14.3 Manual tests

Run:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
$env:LITELLM_MASTER_KEY="sk-your-key"
powershell -ExecutionPolicy Bypass -File .\scripts\check-platform.ps1
```

Check status page:

```powershell
curl.exe http://127.0.0.1:8088/api/platform/status
```

Open:

```text
http://127.0.0.1:8088/status
http://127.0.0.1:3002
http://127.0.0.1:3000
```

Create test user key:

```powershell
curl.exe http://127.0.0.1:4000/key/generate `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"models\":[\"active-lanta-model\"],\"metadata\":{\"user\":\"friend-test\",\"purpose\":\"manual smoke test\"}}"
```

Call model with user key:

```powershell
$env:OPENAI_API_KEY="sk-user-key"
curl.exe http://127.0.0.1:4000/v1/chat/completions `
  -H "Authorization: Bearer $env:OPENAI_API_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"active-lanta-model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply exactly: online\"}],\"temperature\":0,\"max_tokens\":8}"
```

Then check Grafana for request/token metrics.

### 14.4 Validation commands

Run:

```bash
python -m compileall benchmark dashboard observability
python -m pytest
docker compose -f litellm/docker-compose.yml config
docker compose -f openwebui/docker-compose.yml config
docker compose -f observability/docker-compose.yml config
docker compose -f dashboard/docker-compose.yml config
```

## 15. Definition of done

This phase is complete when:

1. README clearly says this is a hosting/user-access platform.
2. Docs clearly say Grafana is the metrics and usage dashboard.
3. Custom dashboard is described as a status/admin landing page only.
4. `/status` and `/api/platform/status` work.
5. `/usage` no longer appears to be a Grafana replacement.
6. `scripts/check-platform.ps1` checks all major services.
7. `docs/KEY_MANAGEMENT.md` explains how to create/list/revoke keys.
8. Users can be given base URL, model name, and virtual key instructions.
9. `active-lanta-model` remains the stable public alias.
10. Benchmark tooling remains optional and does not block hosting dashboard functionality.
11. Grafana dashboard labels clearly explain LiteLLM metrics and optional GPU/Slurm metrics.
12. No real secrets are committed.
13. Existing `website/`, `sharing/`, `lanta/scripts/`, and `windows/tunnel/` remain usable.
14. Tests pass or any skipped tests are documented.

## 16. Codex implementation instructions

Implement this spec in small safe steps.

Priority order:

1. Update docs to clarify the component split:

```text
OpenWebUI = chat UI
LiteLLM = API gateway and virtual keys
Grafana = metrics and usage dashboard
Custom dashboard = /status admin landing page
Benchmark = optional
```

2. Change `/usage` so it does not duplicate Grafana. Prefer a simple Grafana link/guide page.
3. Keep `/api/platform/status` and `/status`.
4. Add or improve links on `/status` for OpenWebUI, Grafana, Prometheus, key docs, and operations docs.
5. Keep `active-lanta-model` stable.
6. Do not implement automatic model sync as a required feature.
7. Do not expand benchmarks unless needed for smoke testing.
8. Improve Grafana labels and no-data messages.
9. Update tests for the status page and usage behavior.

At the end, summarize:

1. Files changed.
2. What the custom dashboard does now.
3. What Grafana is responsible for.
4. How a friend uses OpenWebUI.
5. How a friend uses an API key.
6. How admin checks health.
7. How admin checks usage.
8. Tests run and tests not run.
