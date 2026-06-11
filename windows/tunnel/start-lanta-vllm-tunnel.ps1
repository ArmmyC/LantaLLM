param(
  [int]$LocalPort = 8000,
  [int]$RemotePort = 8000,
  [string]$JobName = ""
)

$runtimeDir = Join-Path $PSScriptRoot ".tunnel-runtime"
$pidPath = Join-Path $runtimeDir "tunnel.pid"
$stdoutPath = Join-Path $runtimeDir "tunnel.log"
$stderrPath = Join-Path $runtimeDir "tunnel-error.log"
$watchdogPath = Join-Path $PSScriptRoot "open-lanta-vllm-tunnel.ps1"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

if (Test-Path $pidPath) {
  $existingPid = Get-Content $pidPath -ErrorAction SilentlyContinue
  if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
    Write-Host "Lanta tunnel watchdog is already running (PID $existingPid)."
    exit 0
  }
  Remove-Item $pidPath -Force
}

$arguments = @(
  "-NoProfile"
  "-WindowStyle", "Hidden"
  "-ExecutionPolicy", "Bypass"
  "-File", $watchdogPath
  "-LocalPort", $LocalPort
  "-RemotePort", $RemotePort
)
if (-not [string]::IsNullOrWhiteSpace($JobName)) {
  $arguments += @("-JobName", $JobName)
}

$process = Start-Process `
  -FilePath "powershell.exe" `
  -ArgumentList $arguments `
  -WindowStyle Hidden `
  -RedirectStandardOutput $stdoutPath `
  -RedirectStandardError $stderrPath `
  -PassThru

Set-Content -Path $pidPath -Value $process.Id
Write-Host "Lanta tunnel watchdog started (PID $($process.Id))."
Write-Host "Tunnel: http://127.0.0.1:$LocalPort/v1"
Write-Host "Status: powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\status-lanta-vllm-tunnel.ps1`""
Write-Host "Stop:   powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\stop-lanta-vllm-tunnel.ps1`""
