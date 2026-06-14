# Lanta LLM Hosting Project Summary

This document summarizes the current private LLM hosting setup for the `lanta-llm-hosting` project. It is intended as a handoff document that can be sent to ChatGPT or another assistant for context.

## Goal

Host large open-weight coding/chat models on the Lanta HPC GPU cluster using vLLM, expose them through an OpenAI-compatible API, connect to the API from a local Windows machine, and optionally provide a small private web UI or shared gateway for friends.

## Main Platforms

Local machine:

- OS: Windows
- Workspace root: `D:\ArmmyWorkspace\SiliconCraft`
- Main organized project folder: `D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting`
- Local API endpoint after tunnel: `http://127.0.0.1:8000/v1`
- Local web UI default: `http://127.0.0.1:5177`

Remote cluster:

- Platform: Lanta HPC cluster
- Login alias: `lanta`
- Remote working path: `/project/zz992000-zdevb/zz992005/ub127/SiliconCraft`
- Slurm account: `zz992005`
- Slurm QoS: `zz992005`
- GPU target: 1 node with 4x NVIDIA A100 GPUs
- vLLM port on compute node: `8000`

## High-Level Architecture

```text
Browser / CLI / Node frontend
        |
        | http://127.0.0.1:8000/v1
        v
Local SSH tunnel on Windows
        |
        | ssh lanta -> active Slurm GPU node
        v
vLLM OpenAI-compatible server on Lanta
        |
        v
Downloaded Hugging Face model under /project/.../SiliconCraft/models
```

Optional public sharing path:

```text
Friend browser
        |
        | HTTPS via Tailscale Funnel / authenticated gateway
        v
Local Windows gateway / website
        |
        v
Local SSH tunnel -> Lanta vLLM
```

## Tech Stack

Remote inference:

- Slurm for GPU job scheduling
- vLLM for model serving
- Hugging Face model downloads
- Conda environment: `silicon-craft`
- CUDA module loaded by Slurm script
- OpenAI-compatible API exposed by vLLM

Local tooling:

- PowerShell scripts for SSH tunnel watchdog
- Node.js scripts for CLI/web gateway
- Browser-based private chat UI
- Optional Tailscale Funnel sharing

Frontend/backend web UI:

- Minimal Node.js HTTP server
- Static HTML/CSS/JavaScript frontend
- Backend API routes:
  - `/api/chat`
  - `/api/models`
- The website proxies requests to the local OpenAI-compatible vLLM endpoint.
- The website uses `SITE_PASSWORD` as a simple access gate.

## Local Folder Structure

Main folder:

```text
lanta-llm-hosting/
  README.md
  HOW_TO_USE.md
  HOW_TO_SWAP.md
  PROJECT_SUMMARY_FOR_CHATGPT.md

  lanta/
    scripts/
      download-model.sh
      serve-model.sbatch
      submit-model.sh
      submit-preset.sh
      test-model-api.sh
    legacy-qwen36/
      older Qwen3.6-specific scripts kept for reference

  windows/
    tunnel/
      open-lanta-vllm-tunnel.ps1
      start-lanta-vllm-tunnel.ps1
      status-lanta-vllm-tunnel.ps1
      stop-lanta-vllm-tunnel.ps1
      test-local-vllm-api.ps1
      test-local-vllm-api.mjs

  website/
    package.json
    server.mjs
    api/
      chat.js
      models.js
    public/
      index.html
      app.js
      styles.css

  cli/
    qwen-chat.ps1
    qwen-chat-cli.mjs

  sharing/
    authenticated-openai-gateway.mjs
    run-authenticated-gateway.ps1
    start-tailscale-funnel-share.ps1
    stop-tailscale-funnel-share.ps1
    test-public-funnel-api.mjs

  docs/
    lanta-vllm-setup.md
    model-swap-guide.md
    friend-cli-usage.md
    open-webui-windows-setup.md
    website-ui-reference.md
```

## Remote Folder Structure

Remote root:

```text
/project/zz992000-zdevb/zz992005/ub127/SiliconCraft
```

Important remote folders:

```text
models/
  Qwen3.6-27B/
  Qwen3.6-35B-A3B/
  Qwen3-Coder-30B-A3B-Instruct/
  Qwen2.5-Coder-32B-Instruct/
  DeepSeek-Coder-V2-Lite-Instruct/
  .hf-cache/

envs/
  silicon-craft/

scripts/
  download-model.sh
  serve-model.sbatch
  submit-model.sh
  submit-preset.sh
  test-model-api.sh

logs/
  download-*.out
  download-*.err
  vllm-model-*.out
  vllm-model-*.err
```

The remote folder also contains older `lanta_qwen36/` files and benchmarking files. The organized local source-of-truth folder is currently `lanta-llm-hosting/`.

## Slurm Setup

The main Slurm serving script is:

```text
lanta/scripts/serve-model.sbatch
```

Important Slurm settings:

```bash
#SBATCH --job-name=vllm-model
#SBATCH --partition=gpu
#SBATCH --account=zz992005
#SBATCH --qos=zz992005
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:a100:4
#SBATCH --mem=256G
```

The job serves vLLM on port `8000` on the allocated GPU node.

## Model Preset System

Model swapping is handled by:

```text
lanta/scripts/submit-preset.sh
```

The script:

- Accepts a preset name.
- Cancels existing `vllm-model` jobs by default.
- Starts a new Slurm job using the selected model.
- Keeps the endpoint port the same: `8000`.
- Keeps the local API URL the same after the tunnel is refreshed: `http://127.0.0.1:8000/v1`.

General command:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh PRESET_NAME"
```

Available presets:

```text
qwen36-27b
qwen36-35b-a3b
qwen3-coder-30b-a3b
qwen25-coder-32b
deepseek-coder-v2-lite
```

## Downloaded Models

The following models are downloaded under:

```text
/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models
```

Models:

```text
Qwen/Qwen3.6-27B
Qwen/Qwen3.6-35B-A3B
Qwen/Qwen3-Coder-30B-A3B-Instruct
Qwen/Qwen2.5-Coder-32B-Instruct
deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct
```

## Tested Model Status

These models have been launched through vLLM and tested with `/v1/models` plus a chat completion:

```text
qwen3-coder-30b-a3b
qwen25-coder-32b
deepseek-coder-v2-lite
qwen36-35b-a3b
```

Test prompt used:

```text
Reply with exactly: coder online
```

Expected successful response contains:

```text
coder online
```

Known tested settings:

| Preset | HF repo | Served model name | Context | Notes |
|---|---|---:|---:|---|
| `qwen3-coder-30b-a3b` | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | `qwen3-coder-30b-a3b` | `32768` | Tested working |
| `qwen25-coder-32b` | `Qwen/Qwen2.5-Coder-32B-Instruct` | `qwen25-coder-32b` | `32768` | Tested working |
| `deepseek-coder-v2-lite` | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | `deepseek-coder-v2-lite` | `32768` | Tested working, uses `--enforce-eager` |
| `qwen36-35b-a3b` | `Qwen/Qwen3.6-35B-A3B` | `qwen36-35b-a3b` | `131072` | Tested working, uses Qwen reasoning parser |
| `qwen36-27b` | `Qwen/Qwen3.6-27B` | `qwen36-27b` | `131072` | Previously used as baseline |

For Qwen reasoning models, responses may include a separate reasoning field. The test helper was updated to accept either `content`, `reasoning`, or `reasoning_content`.

## Current Runtime Notes

The last confirmed active model during testing was:

```text
qwen36-35b-a3b
```

Last confirmed Slurm job during testing:

```text
Job ID: 5860302
Node: lanta-g-034
Endpoint: http://lanta-g-034:8000/v1
Local tunnel: http://127.0.0.1:8000/v1
```

Because Slurm jobs were submitted with a 9-hour runtime, the job may expire and need resubmission later.

## Core Commands

Start or swap to Qwen3.6 35B A3B:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen36-35b-a3b"
```

Start or swap to Qwen3 Coder 30B A3B:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen3-coder-30b-a3b"
```

Start or swap to Qwen2.5 Coder 32B:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen25-coder-32b"
```

Start or swap to DeepSeek Coder V2 Lite:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh deepseek-coder-v2-lite"
```

Check Slurm job:

```powershell
ssh lanta "squeue -u ub127"
```

Check estimated start:

```powershell
ssh lanta "squeue --start -j JOB_ID"
```

Watch logs:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && tail -f logs/vllm-model-JOB_ID.out"
```

Run remote model API test:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && MODEL=qwen36-35b-a3b bash scripts/test-model-api.sh"
```

Start local tunnel watchdog:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
```

Check tunnel status:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\status-lanta-vllm-tunnel.ps1
```

Stop tunnel:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\stop-lanta-vllm-tunnel.ps1
```

Test local tunnel:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\test-local-vllm-api.ps1
```

## Local Web UI

The private website lives in:

```text
D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\website
```

It is a Node.js app with:

- `server.mjs` as the local server
- `api/chat.js` for chat proxying
- `api/models.js` for active model detection
- `public/index.html`, `public/app.js`, and `public/styles.css` for the UI

Run locally:

```powershell
cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting\website
$env:QWEN_BASE_URL="http://127.0.0.1:8000/v1"
$env:QWEN_API_KEY="EMPTY"
$env:QWEN_MODEL="qwen36-35b-a3b"
$env:SITE_PASSWORD="<choose-a-password>"
npm run dev
```

Open:

```text
http://127.0.0.1:5177
```

The website checks `/api/models` and can auto-detect the active served model after a swap.

## Web UI Features

Implemented UI behavior includes:

- Fixed ChatGPT-style layout
- Scrollable chat history
- Compact composer with textarea max height
- Enter sends message
- Ctrl+Enter inserts newline
- File attachment inside the composer
- Attached file is sent as `file_context`
- File attachment is cleared after send
- Attached filename is shown in chat history
- Markdown-like rendering for model responses
- Streaming-style word reveal effect in the frontend
- Saved chat history in local storage
- Thinking mode toggle
- System prompt focused on low-power digital IC RTL design

## System Prompt

The site uses a system prompt oriented around:

- Low-power digital IC RTL design
- RFID tag/baseband logic
- Synthesizable SystemVerilog
- Area and power priority over speed
- Serial/FSM/resource-shared architectures
- Clear design workflow before RTL
- Short clarification behavior when the user only greets or gives an unclear task

Important behavior:

- If the user gives a complete RTL task, follow the full design workflow.
- If the user only greets or gives an unclear request, ask briefly for the missing block specification.
- Do not produce architecture analysis or RTL until a concrete design task is provided.

## CLI Usage

There is also a local CLI:

```text
lanta-llm-hosting/cli/qwen-chat.ps1
lanta-llm-hosting/cli/qwen-chat-cli.mjs
```

Typical environment:

```powershell
$env:OPENAI_BASE_URL="http://127.0.0.1:8000/v1"
$env:OPENAI_API_KEY="EMPTY"
$env:MODEL="qwen36-35b-a3b"
```

Run one-shot:

```powershell
.\cli\qwen-chat.ps1 "Hello"
```

Run interactive:

```powershell
.\cli\qwen-chat.ps1
```

CLI supports:

- Continuing chat in one session
- `/exit`
- `/clear`
- `/read PATH` to attach a file as context
- Thinking toggle support added earlier

## Public Sharing

The project has a sharing gateway under:

```text
lanta-llm-hosting/sharing
```

Files:

```text
authenticated-openai-gateway.mjs
run-authenticated-gateway.ps1
start-tailscale-funnel-share.ps1
stop-tailscale-funnel-share.ps1
test-public-funnel-api.mjs
```

Intended purpose:

- Allow 2-3 friends to use the local gateway without installing Tailscale.
- Protect access with a token/password.
- Use Tailscale Funnel to expose HTTPS publicly.

Security note:

- Do not expose raw vLLM directly to the internet.
- Put the authenticated gateway or website in front of it.
- Keep `SITE_PASSWORD` or sharing token private.

## Model Swapping Workflow

The intended workflow is:

1. Submit a preset.
2. The preset cancels the previous `vllm-model` Slurm job.
3. Slurm starts the new job on a GPU node.
4. vLLM serves the new model on port `8000`.
5. Restart or refresh the local tunnel watchdog if needed.
6. Local endpoint remains `http://127.0.0.1:8000/v1`.
7. Website or CLI uses `/v1/models` to detect the active model.

Example:

```powershell
ssh lanta "cd /project/zz992000-zdevb/zz992005/ub127/SiliconCraft && bash scripts/submit-preset.sh qwen3-coder-30b-a3b"

cd D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\stop-lanta-vllm-tunnel.ps1
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1
powershell -ExecutionPolicy Bypass -File .\windows\tunnel\status-lanta-vllm-tunnel.ps1
```

## Important Observations

- The local endpoint stays stable even when the remote node changes.
- The tunnel watchdog may show offline while vLLM is still booting.
- After swapping models, the tunnel sometimes needs a stop/start because the previous SSH forwarding session can become stale.
- vLLM startup can take several minutes due to weight loading, `torch.compile`, CUDA graph capture, and KV cache profiling.
- Qwen3.6 35B A3B successfully ran with 131k context on 4x A100.
- Coder models are configured with 32k context by default for reliable startup.
- DeepSeek Coder V2 Lite is configured with `--enforce-eager`.

## Git / Repo Notes

Recommended repo root:

```text
D:\ArmmyWorkspace\SiliconCraft\lanta-llm-hosting
```

Recommended to track:

- Scripts
- Website source
- CLI source
- Docs
- HOWTO files

Recommended to ignore:

- Model weights
- Logs
- Conda environments
- `.venv-openwebui`
- Runtime tunnel files
- Secrets and password files

Useful current docs:

```text
HOW_TO_USE.md
HOW_TO_SWAP.md
docs/lanta-vllm-setup.md
docs/model-swap-guide.md
docs/friend-cli-usage.md
docs/website-ui-reference.md
```

## Quick Handoff Summary

This project hosts multiple Hugging Face LLMs on Lanta using vLLM and Slurm. A preset script swaps models while preserving the OpenAI-compatible endpoint shape. A Windows SSH tunnel maps the remote vLLM API to `http://127.0.0.1:8000/v1`. A local Node.js website and CLI talk to that endpoint. Tested working models include Qwen3-Coder 30B A3B, Qwen2.5-Coder 32B, DeepSeek Coder V2 Lite, and Qwen3.6 35B A3B. The website includes a private chat UI with file context, saved chat, thinking mode, and an RTL-design-oriented system prompt.
