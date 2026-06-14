from __future__ import annotations

from typing import Any

from dashboard.backend.app import platform_status


def test_platform_status_response_shape(monkeypatch) -> None:
    def fake_probe(url: str, timeout: float, headers: dict[str, str] | None = None) -> tuple[str, float, str, dict[str, Any] | None]:
        if url.endswith("/v1/models") and "litellm" in url:
            return "ok", 10.0, "ok", {"data": [{"id": "active-lanta-model"}]}
        if url.endswith("/models"):
            return "ok", 11.0, "ok", {"data": [{"id": "qwen36-27b"}]}
        return "ok", 5.0, "ok", {}

    monkeypatch.setenv("LITELLM_API_KEY", "sk-test-secret")
    monkeypatch.setattr(platform_status, "http_probe", fake_probe)
    data = platform_status.build_platform_status()

    assert data["overall_status"] == "ok"
    assert data["model"]["public_alias"] == "active-lanta-model"
    assert data["model"]["vllm_reported_model_id"] == "qwen36-27b"
    assert data["components"]["litellm_models"]["status"] == "ok"
    assert data["links"]["grafana"] == "http://127.0.0.1:3002"
    assert data["links"]["openwebui"] == "http://127.0.0.1:3000"
    assert "sk-test-secret" not in str(data)


def test_platform_status_degrades_when_alias_missing(monkeypatch) -> None:
    def fake_probe(url: str, timeout: float, headers: dict[str, str] | None = None) -> tuple[str, float, str, dict[str, Any] | None]:
        if url.endswith("/v1/models") and "litellm" in url:
            return "ok", 10.0, "ok", {"data": [{"id": "other-model"}]}
        if url.endswith("/models"):
            return "ok", 11.0, "ok", {"data": [{"id": "qwen36-27b"}]}
        return "ok", 5.0, "ok", {}

    monkeypatch.setattr(platform_status, "http_probe", fake_probe)
    data = platform_status.build_platform_status()

    assert data["overall_status"] == "degraded"
    assert data["components"]["litellm_models"]["status"] == "degraded"
    assert data["warnings"]


def test_platform_status_is_down_when_core_inference_is_down(monkeypatch) -> None:
    def fake_probe(url: str, timeout: float, headers: dict[str, str] | None = None) -> tuple[str, float, str, dict[str, Any] | None]:
        if url.endswith("/models") and "host.docker.internal" in url:
            return "down", 10.0, "connection refused", None
        if url.endswith("/v1/models"):
            return "ok", 10.0, "ok", {"data": [{"id": "active-lanta-model"}]}
        return "ok", 5.0, "ok", {}

    monkeypatch.setattr(platform_status, "http_probe", fake_probe)
    data = platform_status.build_platform_status()
    assert data["overall_status"] == "down"


def test_platform_usage_reports_unavailable_without_prometheus(monkeypatch) -> None:
    monkeypatch.setattr(platform_status, "prometheus_query", lambda query, timeout: None)
    data = platform_status.build_platform_usage("1h")
    assert data["experimental"] is True
    assert data["error"] == "metrics_unavailable"
    assert "grafana_url" in data


def test_platform_usage_returns_prometheus_values(monkeypatch) -> None:
    monkeypatch.setattr(platform_status, "prometheus_query", lambda query, timeout: 1.0)

    values = iter([508.0, 0.06, 83.0, 0.01, 13169.0, 13602.0, 0.07, 300.0, 480.0])
    monkeypatch.setattr(platform_status, "prometheus_first", lambda queries, timeout: next(values))

    def fake_breakdown(query: str, timeout: float, label_keys: list[str]):
        if "api_key_alias" in query:
            return [
                {"api_key_alias": "friend", "user": "friend-user", "tokens_total": 100.0},
                {"api_key_alias": "litellm-internal-health-check", "user": "unknown", "tokens_total": 10.0},
            ]
        return [{"model": "qwen36-27b", "tokens_total": 110.0}]

    monkeypatch.setattr(platform_status, "prometheus_breakdown", fake_breakdown)
    data = platform_status.build_platform_usage("1h")

    assert data["experimental"] is True
    assert "Grafana is the source of truth" in data["detail"]
    assert data["requests_total"] == 508.0
    assert data["input_tokens_total"] == 13169.0
    assert data["latency_p95_ms"] == 480.0
    assert data["by_key"] == [{"api_key_alias": "friend", "user": "friend-user", "tokens_total": 100.0}]
    assert data["by_model"][0]["model"] == "qwen36-27b"
