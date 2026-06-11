$pidPath = Join-Path $PSScriptRoot ".tunnel-runtime\tunnel.pid"

if (-not (Test-Path $pidPath)) {
  Write-Host "No Lanta tunnel watchdog PID file was found."
  exit 0
}

$watchdogPid = Get-Content $pidPath -ErrorAction SilentlyContinue
if ($watchdogPid -and (Get-Process -Id $watchdogPid -ErrorAction SilentlyContinue)) {
  & taskkill.exe /PID $watchdogPid /T /F | Out-Null
  Write-Host "Stopped Lanta tunnel watchdog (PID $watchdogPid) and its SSH process."
} else {
  Write-Host "The saved tunnel watchdog process is no longer running."
}

Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
