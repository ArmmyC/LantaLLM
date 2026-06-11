param(
  [string]$Node = "",
  [string]$JobName = "",
  [int]$LocalPort = 8000,
  [int]$RemotePort = 8000,
  [int]$RetryDelaySeconds = 10,
  [switch]$Once
)

function Invoke-BoundedSshCommand {
  param(
    [string]$RemoteCommand,
    [int]$TimeoutSeconds = 20
  )

  $job = $null
  try {
    $job = Start-Job -ScriptBlock {
      param($Command)
      $output = & ssh.exe `
        -o BatchMode=yes `
        -o ConnectTimeout=10 `
        -o ServerAliveInterval=5 `
        -o ServerAliveCountMax=2 `
        lanta $Command 2>&1
      [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = @($output | ForEach-Object { $_.ToString() })
      }
    } -ArgumentList $RemoteCommand

    if (-not (Wait-Job -Job $job -Timeout $TimeoutSeconds)) {
      Stop-Job -Job $job -ErrorAction SilentlyContinue
      throw "SSH query timed out after $TimeoutSeconds seconds."
    }

    $result = Receive-Job -Job $job
    if ($result.ExitCode -ne 0) {
      throw "SSH query failed with exit code $($result.ExitCode): $($result.Output -join ' ')"
    }
    return @($result.Output)
  } finally {
    if ($job) {
      Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
  }
}

function Find-VllmNode {
  param([string]$RequestedNode, [string]$RequestedJobName)

  if (-not [string]::IsNullOrWhiteSpace($RequestedNode)) {
    return $RequestedNode
  }

  $detectedNode = ""
  try {
    if ([string]::IsNullOrWhiteSpace($RequestedJobName)) {
      Write-Host "Detecting running vLLM Slurm node from Lanta..."
      $jobs = Invoke-BoundedSshCommand "squeue -u ub127 -h -t R -o '%j %N'"
      foreach ($line in $jobs) {
        $parts = $line -split "\s+"
        if ($parts.Count -ge 2 -and ($parts[0] -eq "vllm-model" -or $parts[0] -eq "qwen36-vllm")) {
          $detectedNode = $parts[1]
          break
        }
      }
    } else {
      Write-Host "Detecting running $RequestedJobName Slurm node from Lanta..."
      $nodes = Invoke-BoundedSshCommand "squeue -u ub127 -h -n $RequestedJobName -t R -o %N"
      if ($nodes) {
        $detectedNode = ($nodes | Select-Object -First 1).Trim()
      }
    }
  } catch {
    Write-Warning "Could not query Lanta: $($_.Exception.Message)"
  }

  return $detectedNode
}

$requestedNode = $Node
$mutex = New-Object System.Threading.Mutex($false, "Local\LantaVllmTunnel-$LocalPort")
$ownsMutex = $false

try {
  $ownsMutex = $mutex.WaitOne(0, $false)
} catch [System.Threading.AbandonedMutexException] {
  $ownsMutex = $true
}

if (-not $ownsMutex) {
  Write-Error "Another Lanta tunnel watchdog is already managing local port $LocalPort."
  exit 2
}

try {
while ($true) {
  $Node = Find-VllmNode -RequestedNode $requestedNode -RequestedJobName $JobName

  if ([string]::IsNullOrWhiteSpace($JobName)) {
    $jobDescription = "vLLM"
  } else {
    $jobDescription = $JobName
  }

  if ([string]::IsNullOrWhiteSpace($Node)) {
    Write-Warning "No running $jobDescription job found on Lanta."
    if ($Once) {
      exit 1
    }
    Write-Host "Checking again in $RetryDelaySeconds seconds. Press Ctrl+C to stop."
    Start-Sleep -Seconds $RetryDelaySeconds
    continue
  }

  Write-Host "Opening SSH tunnel:"
  Write-Host "  http://localhost:$LocalPort/v1 -> http://$Node`:$RemotePort/v1"
  Write-Host "Automatic reconnect is enabled. Press Ctrl+C to stop."

  & ssh `
    -N `
    -o ExitOnForwardFailure=yes `
    -o ServerAliveInterval=20 `
    -o ServerAliveCountMax=3 `
    -o TCPKeepAlive=yes `
    -o ConnectTimeout=15 `
    -L "$LocalPort`:$Node`:$RemotePort" `
    lanta

  $exitCode = $LASTEXITCODE
  if ($Once) {
    exit $exitCode
  }

  Write-Warning "SSH tunnel stopped with exit code $exitCode. Reconnecting in $RetryDelaySeconds seconds..."
  Start-Sleep -Seconds $RetryDelaySeconds
}
} finally {
  if ($ownsMutex) {
    $mutex.ReleaseMutex()
  }
  $mutex.Dispose()
}
