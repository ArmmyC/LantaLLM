from __future__ import annotations

from pathlib import Path

from dashboard.backend.app import database
from dashboard.backend.app.database import REPO_ROOT, safe_artifact_path
from dashboard.backend.app.schemas import validate_case_id, validate_result_shape, validate_run_id


def test_artifact_resolver_rejects_path_traversal() -> None:
    assert safe_artifact_path("../../secret.txt") is None


def test_artifact_resolver_accepts_artifact_root_path() -> None:
    path = safe_artifact_path("benchmark/artifacts/run/case/raw_response.md")
    assert path == (REPO_ROOT / "benchmark/artifacts/run/case/raw_response.md").resolve()


def test_artifact_resolver_maps_repo_relative_path_to_docker_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_ARTIFACT_ROOT", str(tmp_path))
    path = database.safe_artifact_path("benchmark/artifacts/run/case/raw_response.md")
    assert path == (tmp_path / "run/case/raw_response.md").resolve()


def test_id_validation() -> None:
    assert validate_case_id("rtl_counter")
    assert not validate_case_id("../bad")
    assert validate_run_id("123e4567-e89b-12d3-a456-426614174000")
    assert not validate_run_id("not-a-run")


def test_result_shape_validation() -> None:
    assert validate_result_shape(
        {
            "run_id": "run",
            "case_id": "rtl_counter",
            "model_alias": "active-lanta-model",
            "status": "passed",
            "failure_category": "none",
        }
    )
    assert not validate_result_shape({"run_id": "run", "case_id": "rtl_counter", "model_alias": "m", "status": "bad"})
