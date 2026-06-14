from __future__ import annotations

from html import escape
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from ..platform_status import build_platform_status, build_platform_usage

router = APIRouter()


@router.get("/api/platform/status")
def platform_status() -> dict[str, Any]:
    return build_platform_status()


@router.get("/api/platform/usage")
def platform_usage(window: str = Query("1h", pattern=r"^[0-9]+[smhd]$")) -> dict[str, Any]:
    return build_platform_usage(window)


@router.get("/status", response_class=HTMLResponse)
def status_page() -> HTMLResponse:
    data = build_platform_status()
    rows = []
    for name, item in data["components"].items():
        rows.append(
            "<tr>"
            f"<td>{escape(name)}</td>"
            f"<td class=\"status-{escape(str(item['status']))}\">{escape(str(item['status']))}</td>"
            f"<td>{escape(str(item['latency_ms']))}</td>"
            f"<td>{escape(str(item['message']))}</td>"
            "</tr>"
        )
    warnings = "".join(f"<li>{escape(item)}</li>" for item in data["warnings"]) or "<li>No warnings.</li>"
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lanta LLM Platform Status</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 32px; background: #f7f9f7; color: #172017; }}
    a {{ color: #245b2a; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #d9e2d8; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4ed; }}
    .metric {{ display: inline-block; margin: 8px 12px 8px 0; padding: 12px; background: white; border: 1px solid #d9e2d8; }}
    .status-ok {{ color: #166534; font-weight: 700; }}
    .status-degraded, .status-unknown {{ color: #92400e; font-weight: 700; }}
    .status-down {{ color: #991b1b; font-weight: 700; }}
  </style>
</head>
<body>
  <nav><a href="/">Benchmark Overview</a> | <a href="/status">Platform Status</a> | <a href="/usage">Usage</a> | <a href="/runs">Runs</a> | <a href="/cases">Cases</a></nav>
  <h1>Lanta LLM Platform Status</h1>
  <div class="metric"><strong>Overall</strong><br>{escape(str(data['overall_status']))}</div>
  <div class="metric"><strong>Public alias</strong><br>{escape(str(data['model']['public_alias']))}</div>
  <div class="metric"><strong>vLLM model</strong><br>{escape(str(data['model']['vllm_reported_model_id']))}</div>
  <div class="metric"><strong>Last checked</strong><br>{escape(str(data['timestamp']))}</div>
  <h2>Components</h2>
  <table><tr><th>Component</th><th>Status</th><th>Latency ms</th><th>Message</th></tr>{''.join(rows)}</table>
  <h2>Suggested Fixes</h2>
  <ul>{warnings}</ul>
  <h2>Usage</h2>
  <p><a href="/usage">Open usage summary</a>. Detailed charts are also available in Grafana.</p>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/usage", response_class=HTMLResponse)
def usage_page(window: str = Query("1h", pattern=r"^[0-9]+[smhd]$")) -> HTMLResponse:
    data = build_platform_usage(window)
    if data.get("error"):
        body = f"<p>{escape(str(data['detail']))}</p>"
    else:
        metric_names = [
            "requests_total",
            "requests_per_second",
            "errors_total",
            "error_rate",
            "input_tokens_total",
            "output_tokens_total",
            "output_tokens_per_second",
            "latency_p50_ms",
            "latency_p95_ms",
        ]
        metrics = "".join(
            f'<div class="metric"><strong>{escape(name)}</strong><br>{escape(str(data.get(name)))}</div>'
            for name in metric_names
        )
        key_rows = "".join(
            "<tr>"
            f"<td>{escape(str(item.get('api_key_alias', 'unknown')))}</td>"
            f"<td>{escape(str(item.get('user', 'unknown')))}</td>"
            f"<td>{escape(str(item.get('tokens_total', 0)))}</td>"
            "</tr>"
            for item in data.get("by_key", [])
        ) or '<tr><td colspan="3">No key-level usage labels available.</td></tr>'
        model_rows = "".join(
            "<tr>"
            f"<td>{escape(str(item.get('model', 'unknown')))}</td>"
            f"<td>{escape(str(item.get('tokens_total', 0)))}</td>"
            "</tr>"
            for item in data.get("by_model", [])
        ) or '<tr><td colspan="2">No model usage labels available.</td></tr>'
        body = (
            metrics
            + f"<h2>Usage By Key Alias/User</h2><table><tr><th>Key Alias</th><th>User</th><th>Tokens</th></tr>{key_rows}</table>"
            + f"<h2>Usage By Model</h2><table><tr><th>Model</th><th>Tokens</th></tr>{model_rows}</table>"
        )
    grafana_url = escape(str(data.get("grafana_url", "http://127.0.0.1:3002")))
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lanta LLM Usage</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 32px; background: #f7f9f7; color: #172017; }}
    a {{ color: #245b2a; }}
    table {{ border-collapse: collapse; width: 100%; background: white; margin-bottom: 24px; }}
    th, td {{ border: 1px solid #d9e2d8; padding: 8px; text-align: left; }}
    th {{ background: #edf4ed; }}
    .metric {{ display: inline-block; margin: 8px 12px 8px 0; padding: 12px; background: white; border: 1px solid #d9e2d8; }}
  </style>
</head>
<body>
  <nav><a href="/status">Platform Status</a> | <a href="/usage">Usage</a> | <a href="/runs">Benchmark Runs</a></nav>
  <h1>Lanta LLM Usage</h1>
  <p>Window: {escape(window)}. <a href="{grafana_url}">Open Grafana for time-series charts</a>.</p>
  {body}
</body>
</html>"""
    return HTMLResponse(html)
