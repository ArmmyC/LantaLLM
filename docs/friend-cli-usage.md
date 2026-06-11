# Qwen3.6 CLI For Friends

This is an OpenAI-compatible CLI for the shared Qwen3.6 API.

## Setup

Install Node.js 20 or newer.

Set the shared API endpoint and token from the repository's `cli/` directory:

PowerShell:

```powershell
$env:OPENAI_BASE_URL="https://armmy.tail35169a.ts.net/v1"
$env:OPENAI_API_KEY="PASTE_TOKEN_HERE"
```

macOS/Linux:

```bash
export OPENAI_BASE_URL="https://armmy.tail35169a.ts.net/v1"
export OPENAI_API_KEY="PASTE_TOKEN_HERE"
```

## Ask Once

```bash
node qwen-chat-cli.mjs "Explain this model in simple terms"
```

## Interactive Chat

```bash
node qwen-chat-cli.mjs
```

Commands:

```text
/read README.md
/files
/clear
/exit
```

## Read A File

One-shot:

```bash
node qwen-chat-cli.mjs --file README.md "Summarize this file"
```

Multiple files:

```bash
node qwen-chat-cli.mjs --file package.json --file src/app.js "Find likely bugs"
```

Interactive:

```text
You> /read README.md
You> Summarize the file
```

The CLI only reads files you explicitly pass with `--file` or `/read`.

Default max file size is 200 KB. Override if needed:

PowerShell:

```powershell
$env:MAX_FILE_BYTES="500000"
```

macOS/Linux:

```bash
export MAX_FILE_BYTES=500000
```
