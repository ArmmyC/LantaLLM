from __future__ import annotations

from html import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from ..database import load_store
from ..schemas import validate_case_id, validate_run_id
from .summary import summary as summary_data

router = APIRouter()


def page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 32px; background: #f7f9f7; color: #172017; }}
    a {{ color: #245b2a; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #d9e2d8; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf4ed; }}
    pre {{ background: #111827; color: #f9fafb; padding: 12px; overflow: auto; }}
    .metric {{ display: inline-block; margin: 8px 12px 8px 0; padding: 12px; background: white; border: 1px solid #d9e2d8; }}
  </style>
</head>
<body>
  <nav><a href="/status">Platform Status</a> | <a href="/benchmarks">Benchmark Overview</a> | <a href="/runs">Runs</a> | <a href="/cases">Cases</a></nav>
  {body}
</body>
</html>"""
    )


@router.get("/", include_in_schema=False)
def dashboard_root() -> RedirectResponse:
    return RedirectResponse(url="/status", status_code=307)


@router.get("/benchmarks", response_class=HTMLResponse)
def overview() -> HTMLResponse:
    stats = summary_data()
    if stats["total_runs"] == 0:
        return page("Benchmark Overview", "<h1>Benchmark Overview</h1><p>No benchmark runs yet. Run <code>python -m benchmark.runners.run_suite --suite smoke</code>.</p>")
    metrics = "".join(f'<div class="metric"><strong>{escape(str(key))}</strong><br>{escape(str(value))}</div>' for key, value in stats.items() if key not in {"by_model", "failure_categories"})
    return page("Benchmark Overview", f"<h1>Benchmark Overview</h1>{metrics}<h2>By Model</h2><pre>{escape(str(stats['by_model']))}</pre><h2>Failure Categories</h2><pre>{escape(str(stats['failure_categories']))}</pre>")


@router.get("/runs", response_class=HTMLResponse)
def runs_page() -> HTMLResponse:
    rows = []
    for run in load_store()["runs"]:
        rows.append(
            "<tr>"
            f"<td><a href=\"/runs/{escape(str(run['id']))}\">{escape(str(run['id']))}</a></td>"
            f"<td>{escape(str(run.get('started_at', '')))}</td>"
            f"<td>{escape(str(run.get('suite_name', '')))}</td>"
            f"<td>{escape(str(run.get('model_alias', '')))}</td>"
            f"<td>{escape(str(run.get('prompt_version', '')))}</td>"
            f"<td>{escape(str(run.get('status', '')))}</td>"
            f"<td>{escape(str(run.get('passed_cases', 0)))}</td>"
            f"<td>{escape(str(run.get('failed_cases', 0)))}</td>"
            f"<td>{escape(str(run.get('total_cases', 0)))}</td>"
            f"<td>{escape(str(run.get('duration_ms', '')))}</td>"
            "</tr>"
        )
    table = "<table><tr><th>Run ID</th><th>Created</th><th>Suite</th><th>Model</th><th>Prompt</th><th>Status</th><th>Passed</th><th>Failed</th><th>Total</th><th>Duration ms</th></tr>" + "".join(rows) + "</table>"
    return page("Benchmark Runs", f"<h1>Benchmark Runs</h1>{table}")


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail_page(run_id: str) -> HTMLResponse:
    if not validate_run_id(run_id):
        raise HTTPException(status_code=404, detail="benchmark run not found")
    data = load_store()
    run = next((item for item in data["runs"] if item.get("id") == run_id), None)
    if not run:
        raise HTTPException(status_code=404, detail="benchmark run not found")
    rows = []
    for result in [item for item in data["results"] if item.get("run_id") == run_id]:
        rows.append(
            "<tr>"
            f"<td>{escape(str(result.get('case_id', '')))}</td>"
            f"<td>{escape(str(result.get('status', '')))}</td>"
            f"<td>{escape(str(result.get('failure_category', '')))}</td>"
            f"<td>{escape(str(result.get('compile_status', '')))}</td>"
            f"<td>{escape(str(result.get('simulation_status', '')))}</td>"
            f"<td>{escape(str(result.get('latency_ms', '')))}</td>"
            f"<td>{escape(str(result.get('total_tokens', '')))}</td>"
            "</tr>"
        )
    return page("Benchmark Run Detail", f"<h1>Run {escape(run_id)}</h1><pre>{escape(str(run))}</pre><table><tr><th>Case</th><th>Status</th><th>Failure</th><th>Compile</th><th>Simulation</th><th>Latency</th><th>Tokens</th></tr>{''.join(rows)}</table>")


@router.get("/cases", response_class=HTMLResponse)
def cases_page() -> HTMLResponse:
    rows = []
    for case in load_store()["cases"]:
        rows.append(
            "<tr>"
            f"<td><a href=\"/cases/{escape(str(case['id']))}\">{escape(str(case['id']))}</a></td>"
            f"<td>{escape(str(case.get('title', '')))}</td>"
            f"<td>{escape(str(case.get('task_type', '')))}</td>"
            f"<td>{escape(str(case.get('expected_module_name', '')))}</td>"
            "</tr>"
        )
    return page("Benchmark Cases", f"<h1>Benchmark Cases</h1><table><tr><th>ID</th><th>Title</th><th>Task Type</th><th>Expected Module</th></tr>{''.join(rows)}</table>")


@router.get("/cases/{case_id}", response_class=HTMLResponse)
def case_detail_page(case_id: str) -> HTMLResponse:
    if not validate_case_id(case_id):
        raise HTTPException(status_code=404, detail="benchmark case not found")
    data = load_store()
    case = next((item for item in data["cases"] if item.get("id") == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="benchmark case not found")
    latest = [item for item in data["results"] if item.get("case_id") == case_id][-10:]
    return page("Benchmark Case Detail", f"<h1>{escape(str(case.get('title')))}</h1><pre>{escape(str(case))}</pre><h2>Latest Results</h2><pre>{escape(str(latest))}</pre>")
