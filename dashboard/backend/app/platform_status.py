from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STATUS_VALUES = {"ok", "degraded", "down", "unknown"}


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def http_probe(url: str, timeout: float, headers: dict[str, str] | None = None) -> tuple[str, float, str, dict[str, Any] | None]:
    started = time.time()
    try:
        request = Request(url, headers={"accept": "application/json", **(headers or {})})
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            latency = (time.time() - started) * 1000
            if response.status >= 400:
                return "down", latency, f"http {response.status}", None
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = None
            return "ok", latency, "ok", data
    except HTTPError as exc:
        return "down", (time.time() - started) * 1000, f"http {exc.code}", None
    except (URLError, TimeoutError, OSError) as exc:
        return "down", (time.time() - started) * 1000, str(exc), None


def component(status: str, latency: float, message: str) -> dict[str, Any]:
    return {
        "status": status if status in STATUS_VALUES else "unknown",
        "latency_ms": round(latency, 3),
        "message": message[:160],
    }


def platform_config() -> dict[str, str]:
    return {
        "public_alias": env("LITELLM_ACTIVE_MODEL", "active-lanta-model"),
        "openwebui_base_url": env("OPENWEBUI_BASE_URL", "http://openwebui:8080").rstrip("/"),
        "litellm_base_url": env("LITELLM_BASE_URL", "http://litellm:4000").rstrip("/"),
        "litellm_api_key": env("LITELLM_API_KEY", env("LITELLM_MASTER_KEY", "")),
        "vllm_base_url": env("VLLM_BASE_URL", "http://host.docker.internal:8000/v1").rstrip("/"),
        "platform_exporter_base_url": env("PLATFORM_EXPORTER_BASE_URL", "http://platform-exporter:9108").rstrip("/"),
        "prometheus_base_url": env("PROMETHEUS_BASE_URL", "http://prometheus:9090").rstrip("/"),
        "grafana_base_url": env("GRAFANA_BASE_URL", "http://grafana:3000").rstrip("/"),
        "grafana_public_url": env("GRAFANA_PUBLIC_URL", "http://127.0.0.1:3002").rstrip("/"),
    }


def build_platform_status() -> dict[str, Any]:
    cfg = platform_config()
    timeout = float(env("DASHBOARD_HEALTH_TIMEOUT_SECONDS", "3"))
    headers = auth_headers(cfg["litellm_api_key"])
    components: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    status, latency, message, _ = http_probe(f"{cfg['openwebui_base_url']}/", timeout)
    components["openwebui"] = component(status, latency, message)
    if status != "ok":
        warnings.append("OpenWebUI is not reachable. Check openwebui/docker-compose.yml, port 3000, and persisted provider settings.")

    status, latency, message, _ = http_probe(f"{cfg['litellm_base_url']}/health", timeout, headers)
    components["litellm"] = component(status, latency, message)
    if status != "ok":
        warnings.append("LiteLLM health failed. Check docker compose ps and docker compose logs --tail=150 litellm.")

    status, latency, message, data = http_probe(f"{cfg['litellm_base_url']}/v1/models", timeout, headers)
    litellm_model_ids = [str(item.get("id")) for item in (data or {}).get("data", []) if isinstance(item, dict)]
    if status == "ok" and cfg["public_alias"] not in litellm_model_ids:
        status = "degraded"
        message = f"{cfg['public_alias']} missing from LiteLLM models"
        warnings.append("LiteLLM is reachable but active-lanta-model is not listed. Check litellm/config.yaml and VLLM_MODEL_ID.")
    elif status == "ok":
        message = f"{cfg['public_alias']} available"
    components["litellm_models"] = component(status, latency, message)

    status, latency, message, data = http_probe(f"{cfg['vllm_base_url']}/models", timeout)
    vllm_model_id = "unknown"
    if status == "ok":
        vllm_model_id = str(((data or {}).get("data") or [{}])[0].get("id") or "unknown")
        message = "ok"
    else:
        warnings.append("vLLM tunnel is not reachable. Check the Windows tunnel watchdog and the Lanta Slurm job.")
    components["vllm_tunnel"] = component(status, latency, message)

    status, latency, message, _ = http_probe(f"{cfg['platform_exporter_base_url']}/healthz", timeout)
    components["platform_exporter"] = component(status, latency, message)
    if status != "ok":
        warnings.append("Platform exporter is down. Restart the observability stack.")

    status, latency, message, _ = http_probe(f"{cfg['prometheus_base_url']}/-/ready", timeout)
    components["prometheus"] = component(status, latency, message)
    if status != "ok":
        warnings.append("Prometheus is not ready. Check observability docker compose status and targets.")

    status, latency, message, _ = http_probe(f"{cfg['grafana_base_url']}/api/health", timeout)
    components["grafana"] = component(status, latency, message)
    if status != "ok":
        warnings.append("Grafana is not reachable. Check port 3002 and Grafana container logs.")

    components["dashboard"] = component("ok", 0, "ok")
    overall_status = "ok" if all(item["status"] == "ok" for item in components.values()) else "degraded"

    return {
        "timestamp": utc_timestamp(),
        "overall_status": overall_status,
        "model": {
            "public_alias": cfg["public_alias"],
            "vllm_reported_model_id": vllm_model_id,
        },
        "components": components,
        "warnings": warnings,
    }


def prometheus_result(query: str, timeout: float) -> list[dict[str, Any]] | None:
    cfg = platform_config()
    url = f"{cfg['prometheus_base_url']}/api/v1/query?{urlencode({'query': query})}"
    status, _, _, data = http_probe(url, timeout)
    if status != "ok" or not data or data.get("status") != "success":
        return None
    return (data.get("data") or {}).get("result") or []


def prometheus_query(query: str, timeout: float) -> float | None:
    result = prometheus_result(query, timeout)
    if not result:
        return None
    try:
        return float(result[0]["value"][1])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def prometheus_first(queries: list[str], timeout: float) -> float | None:
    for query in queries:
        value = prometheus_query(query, timeout)
        if value is not None:
            return value
    return None


def prometheus_breakdown(query: str, timeout: float, label_keys: list[str]) -> list[dict[str, Any]]:
    result = prometheus_result(query, timeout) or []
    items: list[dict[str, Any]] = []
    for series in result:
        metric = series.get("metric") or {}
        try:
            value = float(series["value"][1])
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        item = {key: str(metric.get(key) or "unknown") for key in label_keys}
        item["tokens_total"] = value
        items.append(item)
    return items


def build_platform_usage(window: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9]+[smhd]", window):
        window = "1h"
    timeout = float(env("DASHBOARD_HEALTH_TIMEOUT_SECONDS", "3"))
    up = prometheus_query("up", timeout)
    if up is None:
        return {
            "timestamp": utc_timestamp(),
            "window": window,
            "error": "metrics_unavailable",
            "detail": "Prometheus is not reachable from the dashboard. Use Grafana after observability is running.",
            "grafana_url": platform_config()["grafana_public_url"],
        }
    requests_total = prometheus_first(
        ["sum(litellm_proxy_total_requests_metric_total)", "sum(litellm_proxy_total_requests_metric)"], timeout
    )
    requests_per_second = prometheus_first(
        [
            f"sum(rate(litellm_proxy_total_requests_metric_total[{window}]))",
            f"sum(rate(litellm_proxy_total_requests_metric[{window}]))",
        ],
        timeout,
    )
    errors_total = prometheus_first(
        ["sum(litellm_proxy_failed_requests_metric_total)", "sum(litellm_proxy_failed_requests_metric)"], timeout
    )
    error_rate = prometheus_first(
        [
            f"sum(rate(litellm_proxy_failed_requests_metric_total[{window}])) / clamp_min(sum(rate(litellm_proxy_total_requests_metric_total[{window}])), 0.000001)",
            f"sum(rate(litellm_proxy_failed_requests_metric[{window}])) / clamp_min(sum(rate(litellm_proxy_total_requests_metric[{window}])), 0.000001)",
        ],
        timeout,
    )
    input_tokens_total = prometheus_first(
        ["sum(litellm_input_tokens_metric_total)", "sum(litellm_input_tokens_metric)"], timeout
    )
    output_tokens_total = prometheus_first(
        ["sum(litellm_output_tokens_metric_total)", "sum(litellm_output_tokens_metric)"], timeout
    )
    output_tokens_per_second = prometheus_first(
        ["sum(rate(litellm_output_tokens_metric_total[1m]))", "sum(rate(litellm_output_tokens_metric[1m]))"], timeout
    )
    latency_p50_ms = prometheus_first(
        [
            f"histogram_quantile(0.50, sum(rate(litellm_request_total_latency_metric_bucket[{window}])) by (le)) * 1000",
            f"histogram_quantile(0.50, sum(rate(litellm_request_latency_seconds_bucket[{window}])) by (le)) * 1000",
        ],
        timeout,
    )
    latency_p95_ms = prometheus_first(
        [
            f"histogram_quantile(0.95, sum(rate(litellm_request_total_latency_metric_bucket[{window}])) by (le)) * 1000",
            f"histogram_quantile(0.95, sum(rate(litellm_request_latency_seconds_bucket[{window}])) by (le)) * 1000",
        ],
        timeout,
    )
    by_key = prometheus_breakdown(
        "sum by (api_key_alias, user) (litellm_total_tokens_metric_total)", timeout, ["api_key_alias", "user"]
    )
    by_key = [item for item in by_key if item["api_key_alias"] != "litellm-internal-health-check"]
    by_model = prometheus_breakdown(
        "sum by (model) (litellm_total_tokens_metric_total)", timeout, ["model"]
    )
    return {
        "timestamp": utc_timestamp(),
        "window": window,
        "requests_total": requests_total,
        "requests_per_second": requests_per_second,
        "errors_total": errors_total,
        "error_rate": error_rate,
        "input_tokens_total": input_tokens_total,
        "output_tokens_total": output_tokens_total,
        "output_tokens_per_second": output_tokens_per_second,
        "latency_p50_ms": latency_p50_ms,
        "latency_p95_ms": latency_p95_ms,
        "by_key": by_key,
        "by_model": by_model,
        "detail": "Values come from Prometheus metrics exported by LiteLLM. Null means that metric is unavailable in the running LiteLLM version.",
        "grafana_url": platform_config()["grafana_public_url"],
    }
