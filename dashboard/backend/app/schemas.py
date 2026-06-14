from __future__ import annotations

import re
from datetime import datetime

CASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,80}$")
UUID_RE = re.compile(r"^[0-9a-fA-F-]{32,36}$")
TASK_TYPES = {"rtl_generation", "testbench_generation", "rtl_debugging", "low_power_rewrite"}
RUN_STATUSES = {"running", "completed", "failed", "cancelled"}
RESULT_STATUSES = {"passed", "failed", "error", "skipped"}
FAILURE_CATEGORIES = {
    None,
    "none",
    "no_code_block",
    "wrong_module_name",
    "missing_port",
    "missing_required_term",
    "syntax_error",
    "compile_error",
    "simulation_mismatch",
    "timeout",
    "upstream_error",
    "invalid_case",
    "unknown",
}


def validate_case_id(case_id: str) -> bool:
    return bool(CASE_ID_RE.match(case_id))


def validate_run_id(run_id: str) -> bool:
    return bool(UUID_RE.match(run_id))


def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_result_shape(result: dict[str, object]) -> bool:
    return (
        bool(result.get("run_id"))
        and bool(result.get("case_id"))
        and bool(result.get("model_alias"))
        and result.get("status") in RESULT_STATUSES
        and result.get("failure_category") in FAILURE_CATEGORIES
    )
