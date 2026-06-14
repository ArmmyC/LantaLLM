# Feature Spec: Lanta LLM Hosting Platform - User Access, Keys, and Observability Dashboard

## 1. Goal

This project should focus on **hosting a private LLM on Lanta and making it easy for friends or internal users to use it safely**.

The primary purpose of this repository is no longer benchmark research. Benchmark tooling may remain in the repo as an optional side module, but it should not drive the next implementation phase.

The next milestone is to turn the current stack into a simple internal/private LLM hosting platform with:

1. **OpenWebUI** as the main browser chat UI.
2. **LiteLLM** as the central API gateway for OpenAI-compatible access, API keys, budgets, limits, usage, and metrics.
3. **A simple key management flow** so users can receive or request their own API keys without exposing the LiteLLM master key.
4. **A hosting/admin dashboard** for checking health, usage, errors, tokens, latency, active alias, users/keys, and service status.
5. **Prometheus + Grafana** for infrastructure and usage monitoring.
6. **Simple operations scripts** for startup, health checks, troubleshooting, and service management.

The main production-style flow remains:

```text
User / Friend
  |
  +--> OpenWebUI chat UI
  |
  +--> API client using LiteLLM virtual key

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

The public model name should remain stable:

```text
active-lanta-model
```

Model swapping can happen behind this alias. Users do not need to know the exact underlying model every time. Admins may optionally see the real model returned by vLLM, but automatic model-name synchronization is not a priority.

## 2. Product direction

### 2.1 What this project is

This project is a **private LLM hosting platform**.

It should answer these questions well:

1. Is the model online?
2. Can users chat from OpenWebUI?
3. Can users call the model through an API key?
4. Who has keys?
5. How much is each key/user using?
6. How many tokens are being used?
7. What is the request rate?
8. What is the latency?
9. What errors are happening?
10. Is the tunnel healthy?
11. Is LiteLLM healthy?
12. Is OpenWebUI healthy?
13. Is vLLM reachable?
14. Is the active alias working?
15. Are users over budget or rate limits?

### 2.2 What this project is not

This project is not primarily a benchmark research repo.

The existing `benchmark/` and `dashboard/` benchmark code can remain, but the next phase should focus on hosting and operations.

This project should not try to become:

1. A public SaaS company.
2. A billing product.
3. A full enterprise identity system.
4. A replacement for OpenWebUI.
5. A full benchmark leaderboard product.
6. A full RTL synthesis/EDA evaluation environment.
7. A Kubernetes platform.
8. A multi-model research arena as the main feature.

## 3. Current state snapshot

The repository already contains:

```text
litellm/              LiteLLM gateway, config, Docker Compose, .env example, README
openwebui/            OpenWebUI Docker Compose and .env example
observability/        Prometheus, Grafana, platform exporter, dashboard JSON
benchmark/            Optional HDL benchmark runner and cases
dashboard/            Existing benchmark dashboard/API foundation
scripts/check-platform.ps1
                      Local health checker for vLLM, LiteLLM, OpenWebUI, exporter, dashboard
website/              Existing fallback demo UI
sharing/              Existing sharing/API gateway compatibility tools
lanta/scripts/        Lanta Slurm/vLLM scripts
windows/tunnel/       Windows SSH tunnel tools
```

The next phase should reuse as much as possible rather than rewriting everything.

## 4. Non-goals

Do **not** prioritize:

1. Automatic model sync as a required feature.
2. Showing the exact model name in OpenWebUI instead of `active-lanta-model`.
3. Expanding HDL benchmark cases as the main work item.
4. Building a full benchmark UI.
5. Building model-vs-model arena comparison as the main work item.
6. Adding complex user roles beyond admin/user for now.
7. Public registration without admin control.
8. Exposing the LiteLLM master key to users.
9. Allowing anonymous key generation.
10. Deleting or replacing existing `website/`, `sharing/`, `lanta/scripts/`, or `windows/tunnel/`.

## 5. Assumptions

1. Only one Lanta vLLM model is active on the main tunnel at a time.
2. The local vLLM tunnel remains:

```text
http://127.0.0.1:8000/v1
```

3. Docker services reach that tunnel through:

```text
http://host.docker.internal:8000/v1
```

4. OpenWebUI remains the main browser UI.
5. LiteLLM remains the main API gateway.
6. LiteLLM virtual keys are the correct way to give users API access.
7. The stable public model alias remains:

```text
active-lanta-model
```

8. Users should not need to know the exact underlying hosted model.
9. Admins may optionally inspect the actual vLLM model through `/v1/models`.
10. Metrics from LiteLLM are the source of truth for API usage, token counts, request rate, and errors.
11. GPU metrics are optional and should not block the hosting platform.
12. `.env` files are local-only and must never be committed.

## 6. User stories

### 6.1 Friend / user using chat

* As a friend, I want to open OpenWebUI and chat with the hosted model without setting up anything complicated.
* As a friend, I want a normal web UI where I can log in and keep my chat history.
* As a friend, I do not care whether the backend is Qwen, DeepSeek, or another model unless the admin tells me.

### 6.2 Friend / user using API

* As a friend, I want my own API key so I can use the hosted model from my own app, script, OpenAI-compatible client, or tool.
* As a friend, I want simple instructions showing the base URL, model name, and curl/Python examples.
* As a friend, I should not need the LiteLLM master key.

### 6.3 Admin operating the platform

* As an admin, I want to see if the platform is healthy.
* As an admin, I want to create, list, revoke, and inspect user API keys.
* As an admin, I want to set key budgets or request limits.
* As an admin, I want to see usage by key/user.
* As an admin, I want to see token usage, request count, error rate, and latency.
* As an admin, I want to see whether OpenWebUI, LiteLLM, vLLM, the tunnel, Prometheus, Grafana, and the dashboard are up.
* As an admin, I want simple troubleshooting instructions when something breaks.

### 6.4 Developer maintaining the repo

* As a developer, I want a clear architecture document.
* As a developer, I want a simple health check script.
* As a developer, I want tests for any new dashboard/API logic.
* As a developer, I want secrets to stay out of GitHub.

## 7. UX / UI requirements

### 7.1 OpenWebUI user experience

OpenWebUI remains the main user-facing chat UI.

Required behavior:

1. User opens:

```text
http://127.0.0.1:3000
```

2. First launch asks the admin to create the first account.
3. The first account becomes the OpenWebUI admin.
4. Users can chat with the model exposed by LiteLLM.
5. OpenWebUI calls LiteLLM, not vLLM directly.
6. OpenWebUI may show:

```text
active-lanta-model
```

7. Docs must explain that `active-lanta-model` means “whatever model is currently hosted behind LiteLLM.”
8. Docs must explain that OpenWebUI login is separate from LiteLLM API keys.

### 7.2 API user experience

Users should receive:

```text
Base URL: http://<host>:4000/v1
Model: active-lanta-model
API key: sk-...
```

Minimum examples:

1. `curl` chat completion.
2. Python OpenAI SDK style call.
3. OpenWebUI or other OpenAI-compatible client configuration.

Example curl:

```bash
curl http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-user-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "active-lanta-model",
    "messages": [
      {"role": "user", "content": "Reply exactly: online"}
    ],
    "temperature": 0,
    "max_tokens": 8
  }'
```

### 7.3 Key management experience

The platform should support an admin-controlled key flow.

There are two acceptable levels:

#### Level 1: Admin-only key generation

Admin uses LiteLLM API to create keys.

Required operations:

1. Create key.
2. List keys.
3. Revoke key.
4. Set allowed models.
5. Set budget where supported.
6. Set metadata such as owner name or purpose.

#### Level 2: Simple key portal

A small local admin page can sit on top of LiteLLM.

Potential page:

```text
http://127.0.0.1:8088/keys
```

Required behavior:

1. Admin logs in or uses an admin-only local secret.
2. Admin enters user name, purpose, optional budget, optional expiry.
3. Backend calls LiteLLM key generation using the master key stored in environment variables.
4. Page shows the generated key once.
5. Key is not stored in plaintext by the dashboard unless explicitly needed.
6. Users cannot generate unlimited keys anonymously.

Important security rule:

```text
Never expose LITELLM_MASTER_KEY to normal users.
```

### 7.4 Admin dashboard experience

The hosting dashboard should be simple and practical.

Add or repurpose the existing `dashboard/` service to include a hosting/admin status area.

Minimum pages:

```text
/status
/keys
/usage
```

If implementing all pages is too much, prioritize:

```text
/status
```

#### Page: `/status`

Shows:

1. Overall platform status.
2. OpenWebUI status.
3. LiteLLM health.
4. LiteLLM `/v1/models` status.
5. vLLM tunnel status.
6. Active public alias.
7. vLLM reported model if available.
8. Prometheus status.
9. Grafana status.
10. Platform exporter status.
11. Dashboard API status.
12. Last checked timestamp.
13. Suggested fix for failed components.

#### Page: `/keys`

Admin-only if implemented.

Shows:

1. Key list from LiteLLM if available.
2. Key owner metadata.
3. Allowed models.
4. Budget.
5. Spend/usage where available.
6. Revoke action.
7. Create key form.

#### Page: `/usage`

Shows:

1. Total requests.
2. Requests over time.
3. Total tokens.
4. Input tokens.
5. Output tokens.
6. Output token/s.
7. Usage by API key/user.
8. Usage by model alias.
9. Error rate.
10. p50/p95 latency.

This page may read from Prometheus, LiteLLM API, or both.

## 8. Functional requirements

### 8.1 Keep stable model alias

Keep the LiteLLM public model name:

```text
active-lanta-model
```

Do not require OpenWebUI to show the exact backend model name.

Required behavior:

1. OpenWebUI shows/calls `active-lanta-model`.
2. API users call `active-lanta-model`.
3. Benchmark scripts, if used, can still call `active-lanta-model`.
4. Admin docs explain that this alias points to the currently hosted model.
5. Admin dashboard may show the real vLLM model separately.

### 8.2 LiteLLM key management

LiteLLM must remain the source of truth for API keys.

Required docs and/or dashboard actions:

1. Generate a user key.
2. Generate a key with model restriction:

```json
{
  "models": ["active-lanta-model"]
}
```

3. Generate a key with budget if LiteLLM supports the configured budget fields.
4. List keys.
5. Delete/revoke a key.
6. Explain master key vs virtual key.

Recommended key metadata:

```json
{
  "user": "friend-name",
  "purpose": "personal app testing",
  "created_by": "admin",
  "notes": "temporary access"
}
```

### 8.3 Dashboard API for platform status

Add:

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
    "dashboard": { "status": "ok", "latency_ms": 5, "message": "ok" }
  },
  "warnings": []
}
```

Allowed status values:

```text
ok
degraded
down
unknown
```

Rules:

1. Return HTTP `200` when the status object is generated, even if some components are degraded.
2. Return HTTP `500` only if the status endpoint itself crashes.
3. Do not expose secrets.
4. Include fix suggestions in warnings when possible.

### 8.4 Dashboard API for usage summary

Add:

```text
GET /api/platform/usage
```

This can start as a wrapper around Prometheus queries or LiteLLM API data.

Response shape:

```json
{
  "timestamp": "2026-06-14T00:00:00Z",
  "window": "1h",
  "requests_total": 120,
  "requests_per_second": 0.3,
  "errors_total": 2,
  "error_rate": 0.016,
  "input_tokens_total": 50000,
  "output_tokens_total": 80000,
  "output_tokens_per_second": 12.5,
  "latency_p50_ms": 4200,
  "latency_p95_ms": 11000,
  "by_key": [],
  "by_model": []
}
```

If Prometheus metrics are unavailable, return:

```json
{
  "error": "metrics_unavailable",
  "detail": "Prometheus or LiteLLM metrics are not reachable"
}
```

### 8.5 Dashboard key management API

Optional but recommended.

Add admin-only endpoints:

```text
GET /api/platform/keys
POST /api/platform/keys
DELETE /api/platform/keys/{key_id_or_token}
```

Security requirements:

1. These endpoints must be disabled by default unless an admin secret is configured.
2. Admin secret must come from environment variable.
3. Do not expose `LITELLM_MASTER_KEY`.
4. Do not log generated keys.
5. Generated key should be shown only once.
6. If secure implementation is not possible, document LiteLLM curl commands instead and skip the dashboard key UI.

Environment variables:

```env
DASHBOARD_ADMIN_TOKEN=change-this-admin-token
LITELLM_MASTER_KEY=sk-admin-master-key
LITELLM_BASE_URL=http://litellm:4000
```

### 8.6 Improve `scripts/check-platform.ps1`

Keep and improve:

```text
scripts/check-platform.ps1
```

It should check:

1. vLLM tunnel:

```text
http://127.0.0.1:8000/v1/models
```

2. LiteLLM health:

```text
http://127.0.0.1:4000/health
```

3. LiteLLM models with auth:

```text
http://127.0.0.1:4000/v1/models
```

4. OpenWebUI homepage:

```text
http://127.0.0.1:3000
```

5. Platform exporter:

```text
http://127.0.0.1:9108/healthz
```

6. Prometheus readiness:

```text
http://127.0.0.1:9090/-/ready
```

7. Grafana health:

```text
http://127.0.0.1:3002/api/health
```

8. Dashboard API:

```text
http://127.0.0.1:8088/api/healthz
```

9. New platform status endpoint:

```text
http://127.0.0.1:8088/api/platform/status
```

Output should look like:

```text
PASS vLLM tunnel - HTTP 200, model=qwen36-35b-a3b
PASS LiteLLM health - HTTP 200
PASS LiteLLM models - active-lanta-model available
PASS OpenWebUI homepage - HTTP 200
PASS Platform exporter - HTTP 200
PASS Prometheus - ready
PASS Grafana - ok
PASS Dashboard API - HTTP 200
```

Do not print secrets.

### 8.7 Observability requirements

Keep Prometheus and Grafana.

The dashboard should clearly show:

1. Active public alias.
2. vLLM tunnel health.
3. LiteLLM health.
4. LiteLLM request rate.
5. Total requests.
6. Error rate.
7. p50 latency.
8. p95 latency.
9. Input tokens/min.
10. Output tokens/min.
11. Output token/s.
12. Usage by key/user if labels are available.
13. Usage by model alias.
14. OpenWebUI health if available through status checks.
15. Dashboard health.
16. Prometheus health.
17. Grafana health.

GPU metrics are optional.

If GPU panels remain, label them clearly:

```text
GPU metrics require optional Lanta-side exporter. If not configured, this panel will show no data.
```

Do not imply GPU metrics are working unless they are actually scraped.

### 8.8 OpenWebUI documentation

Docs must explain:

1. First launch asks to create admin account.
2. OpenWebUI admin account is not the same as LiteLLM admin key.
3. OpenWebUI uses LiteLLM as OpenAI-compatible provider.
4. Default model is `active-lanta-model`.
5. If OpenWebUI provider settings do not update from `.env`, update them in OpenWebUI admin settings.
6. Do not delete OpenWebUI Docker volume unless okay losing accounts, chats, and settings.

### 8.9 Keep benchmark optional

Benchmark remains available, but is not the main focus.

Required behavior:

1. Do not delete `benchmark/`.
2. Do not delete existing benchmark dashboard APIs.
3. Do not prioritize adding new benchmark cases unless directly useful for smoke testing the hosted model.
4. Docs should say benchmark is optional and may be used by another project/report.
5. Hosting dashboard should not depend on benchmark data existing.

## 9. Technical architecture

### 9.1 Hosting architecture

```text
Friend / User
  |
  +--> Browser chat through OpenWebUI
  |
  +--> API call through LiteLLM virtual key

OpenWebUI / API Client
  |
  v
LiteLLM
  |
  v
Local SSH Tunnel
  |
  v
vLLM on Lanta
```

### 9.2 Admin/monitoring architecture

```text
LiteLLM /metrics ------------+
Platform exporter /metrics --+--> Prometheus --> Grafana
Dashboard status checks ------+
```

### 9.3 Key management architecture

```text
Admin
  |
  v
Dashboard key page or LiteLLM curl command
  |
  v
LiteLLM key generation API
  |
  v
Virtual API key for user
  |
  v
User can call active-lanta-model
```

Security rule:

```text
Users get virtual keys. Only admin keeps the master key.
```

## 10. API contracts

### 10.1 Platform status

Path:

```text
GET /api/platform/status
```

Success response:

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
    "vllm_tunnel": { "status": "ok", "latency_ms": 40, "message": "ok" },
    "prometheus": { "status": "ok", "latency_ms": 10, "message": "ok" },
    "grafana": { "status": "ok", "latency_ms": 20, "message": "ok" }
  },
  "warnings": []
}
```

### 10.2 Usage summary

Path:

```text
GET /api/platform/usage?window=1h
```

Success response:

```json
{
  "timestamp": "2026-06-14T00:00:00Z",
  "window": "1h",
  "requests_total": 120,
  "requests_per_second": 0.3,
  "errors_total": 2,
  "error_rate": 0.016,
  "input_tokens_total": 50000,
  "output_tokens_total": 80000,
  "output_tokens_per_second": 12.5,
  "latency_p50_ms": 4200,
  "latency_p95_ms": 11000,
  "by_key": [],
  "by_model": []
}
```

### 10.3 Key creation

Optional endpoint:

```text
POST /api/platform/keys
```

Request:

```json
{
  "owner": "friend-name",
  "purpose": "personal testing",
  "models": ["active-lanta-model"],
  "max_budget": 5,
  "duration": "30d"
}
```

Response:

```json
{
  "key": "sk-...",
  "owner": "friend-name",
  "models": ["active-lanta-model"],
  "message": "Copy this key now. It will not be shown again."
}
```

Rules:

1. Admin-only.
2. Requires dashboard admin token or equivalent local protection.
3. Do not log key value.
4. Do not expose LiteLLM master key.

### 10.4 Key list

Optional endpoint:

```text
GET /api/platform/keys
```

Response should not expose full key values.

Example:

```json
{
  "items": [
    {
      "key_alias": "sk-...abcd",
      "owner": "friend-name",
      "models": ["active-lanta-model"],
      "budget": 5,
      "spend": 1.25,
      "created_at": "2026-06-14T00:00:00Z"
    }
  ]
}
```

## 11. Files likely involved

Create or modify:

```text
docs/specs/llm-platform-control-plane.md
README.md
docs/ARCHITECTURE.md
docs/OPERATIONS.md
HOW_TO_USE.md
HOW_TO_SWAP.md
litellm/README.md
openwebui/README.md
observability/README.md
scripts/check-platform.ps1
dashboard/backend/app/main.py
dashboard/backend/app/routers/platform_status.py
dashboard/backend/app/routers/platform_usage.py
dashboard/backend/app/routers/platform_keys.py optional
dashboard/backend/app/routers/pages.py
dashboard/backend/app/schemas.py
dashboard/.env.example
observability/grafana/dashboards/lanta-llm-operations.json
observability/prometheus/prometheus.yml
tests/test_dashboard_helpers.py
tests/test_platform_exporter.py
```

Keep but deprioritize:

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

## 12. Environment variables

### 12.1 LiteLLM

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

`VLLM_MODEL_ID` may remain manually managed. It does not need automatic sync for this phase.

### 12.2 OpenWebUI

```env
OPEN_WEBUI_PORT=3000
OPENAI_API_BASE_URL=http://litellm:4000/v1
OPENAI_API_KEY=sk-change-this-master-key
WEBUI_SECRET_KEY=change-this-openwebui-secret
```

### 12.3 Observability

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

### 12.4 Dashboard

```env
DASHBOARD_PORT=8088
DASHBOARD_CORS_ORIGINS=http://127.0.0.1:8088,http://localhost:8088
BENCHMARK_JSON_STORE=/data/benchmark-results.json
DASHBOARD_ARTIFACT_ROOT=/artifacts
DASHBOARD_DATABASE_URL=
DASHBOARD_ADMIN_TOKEN=change-this-admin-token
LITELLM_BASE_URL=http://litellm:4000
LITELLM_MASTER_KEY=sk-change-this-master-key
OPENWEBUI_BASE_URL=http://openwebui:8080
PROMETHEUS_BASE_URL=http://prometheus:9090
GRAFANA_BASE_URL=http://grafana:3000
VLLM_BASE_URL=http://host.docker.internal:8000/v1
```

If key management endpoints are not implemented, `DASHBOARD_ADMIN_TOKEN` and `LITELLM_MASTER_KEY` are not required in dashboard.

## 13. Edge cases

1. vLLM tunnel is down.
2. LiteLLM is running but vLLM is unreachable.
3. OpenWebUI is running but LiteLLM key is wrong.
4. User changed LiteLLM master key but did not update OpenWebUI `OPENAI_API_KEY`.
5. User changed `.env` but did not recreate Docker container.
6. Postgres password changed after volume was initialized.
7. LiteLLM `/health` works but `/v1/models` fails.
8. LiteLLM metrics names change across versions.
9. Prometheus has no data until at least one request is made.
10. Grafana panels show no data because Prometheus target is down.
11. User tries to generate keys without admin protection.
12. User shares master key instead of virtual key.
13. User key is valid but does not have access to `active-lanta-model`.
14. User exceeds budget.
15. User loses generated key after it is shown once.
16. Dashboard cannot reach LiteLLM from Docker network.
17. OpenWebUI persisted old provider settings.
18. Local ports conflict with another service.
19. `curl: (52) Empty reply from server` during LiteLLM startup or restart.
20. GPU metrics panels show no data because no GPU exporter exists.

## 14. Testing plan

### 14.1 Unit tests

Add or update tests for:

1. Platform status response shape.
2. Component health aggregation.
3. Overall status calculation.
4. Warning generation.
5. No secret leakage in status response.
6. Usage summary parsing with missing metrics.
7. Key list masking if key endpoints are implemented.
8. Dashboard admin token validation if key endpoints are implemented.
9. Artifact path safety remains working.
10. Platform exporter metric formatting remains working.

### 14.2 Integration tests

Add tests for:

1. Dashboard `/api/healthz`.
2. Dashboard `/api/platform/status`.
3. Dashboard `/status` HTML page.
4. Optional `/api/platform/usage` with mocked Prometheus response.
5. Optional `/api/platform/keys` with mocked LiteLLM response.
6. Docker Compose config validation.

### 14.3 Manual checks

Run:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
$env:LITELLM_MASTER_KEY="sk-your-key"
powershell -ExecutionPolicy Bypass -File .\scripts\check-platform.ps1
```

Check LiteLLM:

```powershell
curl.exe http://127.0.0.1:4000/v1/models -H "Authorization: Bearer $env:LITELLM_MASTER_KEY"
```

Check chat:

```powershell
curl.exe http://127.0.0.1:4000/v1/chat/completions `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"active-lanta-model\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply exactly: online\"}],\"temperature\":0,\"max_tokens\":8}"
```

Check dashboard:

```powershell
curl.exe http://127.0.0.1:8088/api/healthz
curl.exe http://127.0.0.1:8088/api/platform/status
```

Check observability:

```powershell
curl.exe http://127.0.0.1:9108/metrics
curl.exe http://127.0.0.1:9090/-/ready
curl.exe http://127.0.0.1:3002/api/health
```

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

1. The project direction is clearly hosting/user-access/dashboard first.
2. Docs explain stable alias `active-lanta-model`.
3. Docs no longer imply benchmark expansion is the main priority.
4. `scripts/check-platform.ps1` checks all major services.
5. Dashboard exposes `/api/platform/status`.
6. Dashboard has a readable `/status` page.
7. Admin can see health of OpenWebUI, LiteLLM, vLLM tunnel, Prometheus, Grafana, exporter, and dashboard.
8. Admin can see usage metrics through Grafana and/or dashboard.
9. Key generation is documented or implemented behind safe admin protection.
10. Users can receive virtual keys and use them with OpenAI-compatible clients.
11. Master key is never exposed to normal users.
12. Grafana clearly shows token usage, requests, error rate, and latency.
13. GPU panels are clearly marked optional if no real GPU exporter exists.
14. Existing benchmark features still work but are not required for hosting dashboard functionality.
15. Existing `website/`, `sharing/`, `lanta/scripts/`, and `windows/tunnel/` remain usable.
16. No real secrets are committed.

## 16. Codex implementation instructions

Implement this phase in this priority order:

1. Update docs to reflect the new product focus: hosting, user access, keys, and dashboard.
2. Improve `scripts/check-platform.ps1`.
3. Add dashboard `/api/platform/status`.
4. Add dashboard `/status` page.
5. Add usage summary endpoint or document Grafana as the usage dashboard if endpoint is too much.
6. Add safe key management docs first.
7. Add key management dashboard/API only if it can be done without exposing the master key.
8. Improve Grafana panel labels and no-data explanations.
9. Keep benchmark code working but do not expand it unless needed for smoke testing.

Do not implement automatic model sync as a required feature.

Keep `active-lanta-model` as the stable public model name.

At the end, summarize:

1. Files changed.
2. How a friend uses OpenWebUI.
3. How a friend uses an API key.
4. How admin creates or manages keys.
5. Where admin checks health.
6. Where admin checks usage.
7. Which metrics are real now.
8. Which metrics are optional or future work.
9. Tests run and tests not run.
