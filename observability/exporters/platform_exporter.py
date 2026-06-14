from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    import psutil
except Exception:  # pragma: no cover - optional runtime dependency
    psutil = None


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def http_json(url: str, timeout: float, headers: dict[str, str] | None = None) -> tuple[bool, float, dict[str, Any] | None, str]:
    started = time.time()
    try:
        request_headers = {"accept": "application/json"}
        if headers:
            request_headers.update(headers)
        request = Request(url, headers=request_headers)
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            latency = (time.time() - started) * 1000
            if response.status >= 400:
                return False, latency, None, f"http {response.status}"
            return True, latency, json.loads(body or "{}"), "ok"
    except Exception as exc:
        return False, (time.time() - started) * 1000, None, str(exc)


def label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def metric(name: str, value: int | float, labels: dict[str, str] | None = None) -> str:
    if labels:
        rendered = ",".join(f'{key}="{label_value(str(val))}"' for key, val in sorted(labels.items()))
        return f"{name}{{{rendered}}} {value}"
    return f"{name} {value}"


def collect_slurm_metrics() -> list[str]:
    lines: list[str] = []
    if not shutil.which("squeue"):
        lines.append(metric("lanta_slurm_available", 0, {"state": "unknown"}))
        lines.append(metric("lanta_slurm_vllm_job_running", 0, {"job_id": "unknown", "state": "unknown"}))
        return lines

    user = env("SLURM_USER", "")
    job_name = env("SLURM_JOB_NAME", "vllm-model")
    command = ["squeue", "-h", "-n", job_name, "-o", "%i|%T|%M|%N"]
    if user:
        command[1:1] = ["-u", user]
    try:
        output = subprocess.check_output(command, text=True, timeout=3).strip()
    except Exception as exc:
        lines.append(metric("lanta_slurm_available", 0, {"state": "error", "message": str(exc)[:80]}))
        lines.append(metric("lanta_slurm_vllm_job_running", 0, {"job_id": "unknown", "state": "unknown"}))
        return lines

    lines.append(metric("lanta_slurm_available", 1, {"state": "ok"}))
    if not output:
        lines.append(metric("lanta_slurm_vllm_job_running", 0, {"job_id": "none", "state": "none"}))
        return lines

    first = output.splitlines()[0]
    job_id, state, runtime, node = (first.split("|") + ["unknown"] * 4)[:4]
    running = 1 if state.upper() in {"RUNNING", "R"} else 0
    lines.append(metric("lanta_slurm_vllm_job_running", running, {"job_id": job_id, "state": state, "node": node, "runtime": runtime}))
    lines.append(metric("lanta_slurm_active_vllm_job_id", int(job_id) if job_id.isdigit() else 0, {"state": state, "node": node}))
    return lines


def collect_metrics() -> str:
    timeout = float(env("HEALTH_TIMEOUT_SECONDS", "3"))
    litellm_base = env("LITELLM_BASE_URL", "http://127.0.0.1:4000").rstrip("/")
    litellm_api_key = env("LITELLM_API_KEY", "")
    vllm_base = env("VLLM_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
    lines = [
        "# HELP lanta_platform_up Platform exporter health.",
        "# TYPE lanta_platform_up gauge",
        metric("lanta_platform_up", 1),
    ]

    litellm_headers = {"Authorization": f"Bearer {litellm_api_key}"} if litellm_api_key else None
    ok, latency, _, message = http_json(f"{litellm_base}/health", timeout, litellm_headers)
    lines.append(metric("lanta_litellm_reachable", 1 if ok else 0, {"message": message[:80]}))
    lines.append(metric("lanta_litellm_latency_ms", round(latency, 3)))

    ok, latency, data, message = http_json(f"{vllm_base}/models", timeout)
    active_model = "unknown"
    if ok and data:
        active_model = str((data.get("data") or [{}])[0].get("id") or "unknown")
    lines.append(metric("lanta_vllm_reachable", 1 if ok else 0, {"active_model": active_model, "message": message[:80]}))
    lines.append(metric("lanta_ssh_tunnel_healthy", 1 if ok else 0, {"target": vllm_base}))
    lines.append(metric("lanta_vllm_active_model", 1 if ok else 0, {"model": active_model}))
    lines.append(metric("lanta_vllm_latency_ms", round(latency, 3)))
    lines.append(metric("lanta_last_successful_health_check_timestamp", int(time.time()) if ok else 0, {"component": "vllm"}))

    if psutil is not None:
        process = psutil.Process(os.getpid())
        lines.append(metric("lanta_platform_process_cpu_percent", process.cpu_percent(interval=None)))
        lines.append(metric("lanta_platform_process_ram_bytes", process.memory_info().rss))
        lines.append(metric("lanta_local_cpu_percent", psutil.cpu_percent(interval=None)))
        memory = psutil.virtual_memory()
        lines.append(metric("lanta_local_ram_used_bytes", memory.used))
        lines.append(metric("lanta_local_ram_total_bytes", memory.total))
        disk = psutil.disk_usage(os.getcwd())
        lines.append(metric("lanta_local_disk_used_bytes", disk.used))
        lines.append(metric("lanta_local_disk_total_bytes", disk.total))
    else:
        lines.append(metric("lanta_local_cpu_percent", 0, {"state": "unknown"}))
        lines.append(metric("lanta_local_ram_used_bytes", 0, {"state": "unknown"}))
        lines.append(metric("lanta_local_disk_used_bytes", 0, {"state": "unknown"}))

    lines.extend(collect_slurm_metrics())
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true,"service":"platform-exporter"}')
            return
        if self.path == "/metrics":
            body = collect_metrics().encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    port = int(env("PLATFORM_EXPORTER_PORT", "9108"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"platform exporter listening on :{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
