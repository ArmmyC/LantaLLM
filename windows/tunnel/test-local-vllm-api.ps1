param(
  [string]$BaseUrl = $env:OPENAI_BASE_URL,
  [string]$ApiKey = $env:OPENAI_API_KEY,
  [string]$Model = $env:MODEL
)

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
  $BaseUrl = "http://localhost:8000/v1"
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  $ApiKey = "EMPTY"
}

if ([string]::IsNullOrWhiteSpace($Model)) {
  $Model = "/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models/Qwen3.6-35B-A3B"
}

$BaseUrl = $BaseUrl.TrimEnd("/")
$headers = @{
  Authorization = "Bearer $ApiKey"
}

Write-Host "Testing Qwen API at: $BaseUrl"
Write-Host ""

try {
  Write-Host "1. Checking /v1/models..."
  $models = Invoke-RestMethod -Method Get -Uri "$BaseUrl/models" -Headers $headers -TimeoutSec 15
  $models | ConvertTo-Json -Depth 10

  Write-Host ""
  Write-Host "2. Sending chat completion..."
  $body = @{
    model = $Model
    messages = @(
      @{
        role = "user"
        content = "Reply in exactly five words: Lanta LLM API is online."
      }
    )
    max_tokens = 32
    temperature = 0.2
    chat_template_kwargs = @{
      enable_thinking = $false
    }
  } | ConvertTo-Json -Depth 10

  $completion = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/chat/completions" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 120

  Write-Host $completion.choices[0].message.content
  Write-Host ""
  Write-Host "OK: local Qwen API test passed."
} catch {
  Write-Host ""
  Write-Host "Qwen API test failed."
  Write-Host $_.Exception.Message
  Write-Host ""
  Write-Host "If you are testing from local Windows, open a separate terminal first:"
  Write-Host "  powershell -ExecutionPolicy Bypass -File .\windows\tunnel\start-lanta-vllm-tunnel.ps1"
  exit 1
}
