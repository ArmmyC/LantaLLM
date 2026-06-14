from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORE = REPO_ROOT / "benchmark" / "results" / "benchmark-results.json"


def artifact_root() -> Path:
    return Path(os.environ.get("DASHBOARD_ARTIFACT_ROOT", str(REPO_ROOT / "benchmark" / "artifacts"))).resolve()


def load_store() -> dict[str, Any]:
    database_url = os.environ.get("DASHBOARD_DATABASE_URL") or os.environ.get("BENCHMARK_DATABASE_URL")
    if database_url:
        return load_postgres_store(database_url)
    path = Path(os.environ.get("BENCHMARK_JSON_STORE", str(DEFAULT_STORE)))
    if not path.exists():
        return {"runs": [], "results": [], "cases": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_postgres_store(database_url: str) -> dict[str, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - deployment dependency
        raise RuntimeError("psycopg is required for DASHBOARD_DATABASE_URL") from exc
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, suite_name, model_alias, prompt_version, status,
                       started_at, finished_at, duration_ms, total_cases, passed_cases,
                       failed_cases, error_cases, config
                FROM benchmark_runs
                ORDER BY started_at DESC
                LIMIT 1000
                """
            )
            runs = [serialize_row(row) for row in cur.fetchall()]
            cur.execute(
                """
                SELECT id::text, run_id::text, case_id, model_alias, prompt_version, status,
                       failure_category, failure_message, request_started_at, request_finished_at,
                       latency_ms, input_tokens, output_tokens, total_tokens, raw_response_path,
                       extracted_code_path, compile_status, compile_log_path, simulation_status,
                       simulation_log_path, score, metadata, created_at
                FROM benchmark_results
                ORDER BY created_at DESC
                LIMIT 5000
                """
            )
            results = [serialize_row(row) for row in cur.fetchall()]
            cur.execute(
                """
                SELECT id, title, task_type, description, prompt, expected_language,
                       expected_module_name, timeout_seconds, evaluator_config, case_file_path,
                       created_at, updated_at
                FROM benchmark_cases
                ORDER BY id
                """
            )
            cases = [serialize_row(row) for row in cur.fetchall()]
    return {"runs": runs, "results": results, "cases": cases}


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in row.items():
        if hasattr(value, "isoformat"):
            serialized[key] = value.isoformat().replace("+00:00", "Z")
        elif hasattr(value, "__float__") and value.__class__.__name__ == "Decimal":
            serialized[key] = float(value)
        else:
            serialized[key] = value
    return serialized


def safe_artifact_path(relative_path: str) -> Path | None:
    if not relative_path:
        return None
    raw = Path(relative_path)
    root = artifact_root()
    if raw.is_absolute():
        candidate = raw.resolve()
    else:
        parts = raw.parts
        if len(parts) >= 2 and parts[0] == "benchmark" and parts[1] == "artifacts":
            candidate = root.joinpath(*parts[2:]).resolve()
        else:
            candidate = (REPO_ROOT / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate
