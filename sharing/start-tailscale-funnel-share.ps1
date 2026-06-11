param(
  [string]$ApiTokens = "",
  [int]$GatewayPort = 3001,
  [int]$FunnelPort = 443,
  [string]$OpenAIBaseUrl = "http://127.0.0.1:8000/v1",
  [switch]$StartTunnel
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$logsDir = Join-Path $rootDir "logs"
$latestFile = Join-Path $logsDir "public-api-funnel.txt"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

function New-ApiToken {
  $bytes = New-Object byte[] 32
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
  } finally {
    $rng.Dispose()
  }
  return [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

if ([string]::IsNullOrWhiteSpace($ApiTokens)) {
  $ApiTokens = New-ApiToken
}

if ($FunnelPort -notin @(443, 8443, 10000)) {
  throw "Tailscale Funnel public port must be 443, 8443, or 10000."
}

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
  throw "Node.js was not found in PATH."
}

$tailscaleCmd = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $tailscaleCmd) {
  throw "tailscale CLI was not found in PATH."
}

try {
  Invoke-RestMethod -Method Get -Uri "$OpenAIBaseUrl/models" -TimeoutSec 5 | Out-Null
} catch {
  if (-not $StartTunnel) {
    Write-Output "The local Lanta tunnel is not reachable at $OpenAIBaseUrl."
    Write-Output "Open it in another terminal first:"
    Write-Output "  powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1"
    Write-Output ""
    Write-Output "Or rerun this script with -StartTunnel."
    exit 1
  }

  Write-Output "Starting hidden Lanta SSH tunnel..."
  Start-Process `
    -FilePath "powershell" `
    -ArgumentList @(
      "-NoProfile",
      "-ExecutionPolicy", "Bypass",
      "-File", "$rootDir\windows\tunnel\start-lanta-vllm-tunnel.ps1"
    ) `
    -WorkingDirectory $rootDir `
    -WindowStyle Hidden | Out-Null

  Start-Sleep -Seconds 5
  Invoke-RestMethod -Method Get -Uri "$OpenAIBaseUrl/models" -TimeoutSec 15 | Out-Null
}

$gatewayLog = Join-Path $logsDir "qwen36_gateway.out.log"
$gatewayErr = Join-Path $logsDir "qwen36_gateway.err.log"

Write-Output "Starting hidden local API gateway on http://127.0.0.1:$GatewayPort ..."
Start-Process `
  -FilePath "powershell" `
  -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "$scriptDir\run-authenticated-gateway.ps1",
    "-ApiTokens", $ApiTokens,
    "-OpenAIBaseUrl", $OpenAIBaseUrl,
    "-Port", "$GatewayPort"
  ) `
  -WorkingDirectory $rootDir `
  -WindowStyle Hidden `
  -RedirectStandardOutput $gatewayLog `
  -RedirectStandardError $gatewayErr | Out-Null

Start-Sleep -Seconds 2
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$GatewayPort/healthz" -TimeoutSec 10 | Out-Null

Write-Output "Starting Tailscale Funnel..."
tailscale funnel --bg --https=$FunnelPort "http://127.0.0.1:$GatewayPort"

$funnelStatus = tailscale funnel status
$funnelUrl = "https://YOUR-DEVICE.YOUR-TAILNET.ts.net"
foreach ($line in $funnelStatus) {
  if ($line -match "https://[^\s]+") {
    $funnelUrl = $Matches[0]
    break
  }
}
$summary = @(
  "Authenticated LLM API Funnel is running.",
  "",
  "Funnel status:",
  $funnelStatus,
  "",
  "API token:",
  $ApiTokens,
  "",
  "Friends should send:",
  "Authorization: Bearer $ApiTokens",
  "",
  "OpenAI-compatible base URL is the Funnel URL plus /v1.",
  "For this run, use:",
  "$funnelUrl/v1"
)

$summary | Set-Content -Path $latestFile
$summary | Write-Output
