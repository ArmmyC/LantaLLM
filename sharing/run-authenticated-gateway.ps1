param(
  [string]$ApiTokens = $env:API_TOKENS,
  [string]$OpenAIBaseUrl = "http://127.0.0.1:8000/v1",
  [int]$Port = 3001,
  [string]$HostName = "127.0.0.1",
  [string]$CorsOrigin = "*"
)

if ([string]::IsNullOrWhiteSpace($ApiTokens)) {
  Write-Host "API token is required. Pass -ApiTokens or set API_TOKENS."
  exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:API_TOKENS = $ApiTokens
$env:OPENAI_BASE_URL = $OpenAIBaseUrl
$env:OPENAI_API_KEY = "EMPTY"
$env:PORT = "$Port"
$env:HOST = $HostName
$env:CORS_ORIGIN = $CorsOrigin

node "$scriptDir\authenticated-openai-gateway.mjs"
