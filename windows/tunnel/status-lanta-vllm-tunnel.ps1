param([int]$LocalPort = 8000)

$runtimeDir = Join-Path $PSScriptRoot ".tunnel-runtime"
$pidPath = Join-Path $runtimeDir "tunnel.pid"
$stdoutPath = Join-Path $runtimeDir "tunnel.log"
$stderrPath = Join-Path $runtimeDir "tunnel-error.log"

$watchdogPid = if (Test-Path $pidPath) { Get-Content $pidPath -ErrorAction SilentlyContinue } else { $null }
$process = if ($watchdogPid) { Get-Process -Id $watchdogPid -ErrorAction SilentlyContinue } else { $null }

if ($process) {
  Write-Host "Watchdog: running (PID $watchdogPid)"
} else {
  Write-Host "Watchdog: stopped"
}

try {
  $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$LocalPort/v1/models" -TimeoutSec 5
  Write-Host "API:      online (HTTP $($response.StatusCode))"
} catch {
  Write-Host "API:      offline ($($_.Exception.Message))"
}

if (Test-Path $stdoutPath) {
  Write-Host "Log:      $stdoutPath"
}
if (Test-Path $stderrPath) {
  Write-Host "Errors:   $stderrPath"
}
