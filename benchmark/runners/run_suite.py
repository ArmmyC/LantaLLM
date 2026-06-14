from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from benchmark.evaluators.compile_sv import compile_systemverilog
from benchmark.evaluators.extract_code import extract_code_block
from benchmark.evaluators.score import classify_static_failure, numeric_score
from benchmark.evaluators.simulate import simulate_vvp
from benchmark.storage.db import result_store
from benchmark.storage.models import BenchmarkResult, BenchmarkRun, utc_now

BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BENCHMARK_ROOT.parent
ALLOWED_TASK_TYPES = {"rtl_generation", "testbench_generation", "rtl_debugging", "low_power_rewrite"}


def load_case(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("PyYAML is required to load benchmark case YAML files") from exc
    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: benchmark case must be a YAML mapping")
    data.setdefault("expected_language", "systemverilog")
    data.setdefault("timeout_seconds", 120)
    data.setdefault("evaluator_config", {})
    validate_case(data, path)
    data["case_file_path"] = str(path)
    return data


def validate_case(data: dict[str, Any], path: Path | None = None) -> None:
    import re

    prefix = f"{path}: " if path else ""
    case_id = data.get("id")
    if not isinstance(case_id, str) or not re.match(r"^[a-z0-9][a-z0-9_-]{2,80}$", case_id):
        raise ValueError(prefix + "id must match ^[a-z0-9][a-z0-9_-]{2,80}$")
    if not data.get("title"):
        raise ValueError(prefix + "title is required")
    if data.get("task_type") not in ALLOWED_TASK_TYPES:
        raise ValueError(prefix + f"task_type must be one of {sorted(ALLOWED_TASK_TYPES)}")
    if not data.get("prompt"):
        raise ValueError(prefix + "prompt is required")
    if data["task_type"] == "rtl_generation" and not data.get("expected_module_name"):
        raise ValueError(prefix + "expected_module_name is required for RTL generation")
    timeout = data.get("timeout_seconds")
    if not isinstance(timeout, int) or timeout < 1 or timeout > 600:
        raise ValueError(prefix + "timeout_seconds must be between 1 and 600")
    if not isinstance(data.get("evaluator_config", {}), dict):
        raise ValueError(prefix + "evaluator_config must be an object")


def load_suite(suite: str) -> list[dict[str, Any]]:
    suite_dir = BENCHMARK_ROOT / "cases" / suite
    if not suite_dir.exists():
        raise ValueError(f"suite not found: {suite}")
    return [load_case(path) for path in sorted(suite_dir.glob("*.yaml"))]


def load_prompt_version(prompt_version: str) -> str:
    path = BENCHMARK_ROOT / "prompts" / f"{prompt_version}.md"
    if not path.exists():
        raise ValueError(f"prompt version not found: {prompt_version}")
    return path.read_text(encoding="utf-8")


def build_prompt(system_prompt: str, case: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": case["prompt"]},
    ]


def build_chat_payload(messages: list[dict[str, str]], model: str) -> dict[str, Any]:
    return {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": int(os.environ.get("BENCHMARK_MAX_TOKENS", "2048")),
    }


def parse_usage(data: dict[str, Any]) -> dict[str, int | None]:
    usage = data.get("usage") or {}
    return {
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def call_litellm(messages: list[dict[str, str]], model: str, timeout: int) -> tuple[str, dict[str, int | None]]:
    base_url = os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000/v1").rstrip("/")
    api_key = os.environ.get("LITELLM_API_KEY") or os.environ.get("LITELLM_MASTER_KEY")
    if not api_key:
        raise RuntimeError("LITELLM_API_KEY or LITELLM_MASTER_KEY is required")
    payload = build_chat_payload(messages, model)
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", "authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    message = data["choices"][0]["message"]
    text = (message.get("content") or "") + "\n" + (message.get("reasoning") or message.get("reasoning_content") or "")
    return text.strip(), parse_usage(data)


def write_artifact(root: Path, run_id: str, case_id: str, name: str, content: str) -> str:
    artifact_dir = root / "benchmark" / "artifacts" / run_id / case_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / name
    path.write_text(content, encoding="utf-8")
    return str(path.relative_to(root))


def auxiliary_paths(case: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for raw_path in case.get("evaluator_config", {}).get("auxiliary_files", []):
        path = Path(str(raw_path))
        if not path.is_absolute():
            path = REPO_ROOT / path
        if not path.exists():
            raise FileNotFoundError(f"auxiliary file not found: {path}")
        paths.append(path)
    return paths


def run_case(case: dict[str, Any], run: BenchmarkRun, system_prompt: str, args: argparse.Namespace) -> BenchmarkResult:
    result = BenchmarkResult(run_id=run.id, case_id=case["id"], model_alias=args.model, prompt_version=args.prompt_version)
    messages = build_prompt(system_prompt, case)
    result.request_started_at = utc_now()
    started = time.time()
    try:
        if args.dry_run:
            module_name = case.get("expected_module_name") or "tb_dry_run"
            required = "\n".join(f"// {term}" for term in case.get("evaluator_config", {}).get("required_terms", []))
            response_text = f"```systemverilog\nmodule {module_name};\n{required}\nendmodule\n```"
            usage = {"input_tokens": None, "output_tokens": None, "total_tokens": None}
        else:
            response_text, usage = call_litellm(messages, args.model, case["timeout_seconds"])
        result.request_finished_at = utc_now()
        result.latency_ms = int((time.time() - started) * 1000)
        result.input_tokens = usage.get("input_tokens")
        result.output_tokens = usage.get("output_tokens")
        result.total_tokens = usage.get("total_tokens")
        result.raw_response_path = write_artifact(REPO_ROOT, run.id, case["id"], "raw_response.md", response_text)
        extraction = extract_code_block(response_text)
        if extraction.code:
            result.extracted_code_path = write_artifact(REPO_ROOT, run.id, case["id"], "extracted_code.sv", extraction.code)
        status, failure = classify_static_failure(
            extraction.code,
            case.get("expected_module_name"),
            case.get("evaluator_config", {}).get("required_terms"),
        )
        if extraction.failure_category:
            status, failure = "failed", extraction.failure_category
        result.status = status
        result.failure_category = failure
        result.score = numeric_score(status)
        if extraction.code and not args.skip_compile:
            source_path = REPO_ROOT / str(result.extracted_code_path)
            compile_status, compile_log, compiled_path = compile_systemverilog(source_path, case["timeout_seconds"], auxiliary_paths(case))
            result.compile_status = compile_status
            result.compile_log_path = write_artifact(REPO_ROOT, run.id, case["id"], "compile.log", compile_log)
            if compile_status == "failed":
                result.status = "failed"
                result.failure_category = "compile_error"
                result.score = numeric_score(result.status)
            elif compile_status == "timeout":
                result.status = "failed"
                result.failure_category = "timeout"
                result.score = numeric_score(result.status)
            elif compile_status == "passed":
                simulation_status, simulation_log = simulate_vvp(compiled_path, case["timeout_seconds"])
                result.simulation_status = simulation_status
                result.simulation_log_path = write_artifact(REPO_ROOT, run.id, case["id"], "simulation.log", simulation_log)
                if simulation_status == "failed":
                    result.status = "failed"
                    result.failure_category = "simulation_mismatch"
                    result.score = numeric_score(result.status)
                elif simulation_status == "timeout":
                    result.status = "failed"
                    result.failure_category = "timeout"
                    result.score = numeric_score(result.status)
                elif simulation_status in {"passed", "tool_missing", "not_run"} and result.status == "passed":
                    result.failure_category = "none"
            else:
                result.simulation_status = "not_run"
        else:
            result.compile_status = "not_run"
            result.simulation_status = "not_run"
    except TimeoutError as exc:
        result.status = "error"
        result.failure_category = "timeout"
        result.failure_message = str(exc)
    except (HTTPError, URLError, RuntimeError) as exc:
        result.status = "error"
        result.failure_category = "upstream_error"
        result.failure_message = str(exc)
    except Exception as exc:
        result.status = "error"
        result.failure_category = "unknown"
        result.failure_message = str(exc)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Lanta LLM benchmark suite.")
    parser.add_argument("--suite", default="smoke")
    parser.add_argument("--model", default="active-lanta-model")
    parser.add_argument("--prompt-version", default="rfid_low_power_v1")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-on-benchmark-fail", action="store_true")
    parser.add_argument("--skip-compile", action="store_true")
    args = parser.parse_args(argv)

    try:
        cases = load_suite(args.suite)
        system_prompt = load_prompt_version(args.prompt_version)
    except ValueError as exc:
        print(f"invalid benchmark configuration: {exc}", file=sys.stderr)
        return 2

    store = result_store(REPO_ROOT)
    run = BenchmarkRun(suite_name=args.suite, model_alias=args.model, prompt_version=args.prompt_version, total_cases=len(cases), config={"dry_run": args.dry_run})
    store.record_run(run)
    for case in cases:
        store.record_case(case)
        result = run_case(case, run, system_prompt, args)
        store.record_result(result)
        if result.status == "passed":
            run.passed_cases += 1
        elif result.status == "failed":
            run.failed_cases += 1
        else:
            run.error_cases += 1
        print(f"{case['id']}: {result.status} ({result.failure_category})")

    run.status = "completed"
    run.finished_at = utc_now()
    started_at = datetime.fromisoformat(run.started_at.replace("Z", "+00:00"))
    run.duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    store.record_run(run)
    print(json.dumps(asdict(run), indent=2))
    if args.fail_on_benchmark_fail and (run.failed_cases or run.error_cases):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
