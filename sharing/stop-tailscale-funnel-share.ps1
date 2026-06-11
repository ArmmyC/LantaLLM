param(
  [int]$FunnelPort = 443,
  [int]$GatewayPort = 3001
)

Write-Host "Stopping Tailscale Funnel on HTTPS port $FunnelPort..."
tailscale funnel --https=$FunnelPort off

Write-Host "Stopping local Node gateway processes that mention authenticated-openai-gateway.mjs..."
$processes = Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -like "*authenticated-openai-gateway.mjs*" -or
    $_.CommandLine -like "*run-authenticated-gateway.ps1*"
  }

foreach ($process in $processes) {
  Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Done."
