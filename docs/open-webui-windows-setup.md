# Open WebUI On Windows

Open WebUI currently requires Python `>=3.11,<3.13`.

If `pip install open-webui` says:

```text
ERROR: No matching distribution found for open-webui
```

then your active `python` is probably Python 3.13 or newer.

## Recommended: Python 3.12 venv

Install Python 3.12 from:

```text
https://www.python.org/downloads/release/python-312/
```

Then run from this workspace:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
py -3.12 -m venv .venv-openwebui
.\.venv-openwebui\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install open-webui
$env:WEBUI_SECRET_KEY=(Get-Content .\.webui_secret_key -Raw).Trim()
open-webui serve
```

The virtual environment and secret file live inside the repository but are excluded from Git.

Open:

```text
http://localhost:8080
```

Connect it to your vLLM endpoint:

```text
Base URL: http://127.0.0.1:8000/v1
API Key: EMPTY
Model: qwen36-27b
```

Make sure the Lanta tunnel is open first:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
```

## Alternative: Docker

If Docker Desktop is installed:

```powershell
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
```

Open:

```text
http://localhost:3000
```

Use this base URL inside Open WebUI when it runs in Docker:

```text
http://host.docker.internal:8000/v1
```
