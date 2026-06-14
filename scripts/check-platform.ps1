param(
    [int]$TimeoutSeconds = 5
)

$ErrorActionPreference = "Stop"

function Write-CheckResult {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Message
    )

    $status = if ($Passed) { "PASS" } else { "FAIL" }
    Write-Host ("{0} {1} - {2}" -f $status, $Name, $Message)
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Uri,
        [hashtable]$Headers = @{}
    )

    try {
        $response = Invoke-WebRequest -Uri $Uri -Headers $Headers -TimeoutSec $TimeoutSeconds -UseBasicParsing
        $ok = [int]$response.StatusCode -ge 200 -and [int]$response.StatusCode -lt 400
        Write-CheckResult -Name $Name -Passed $ok -Message ("HTTP {0}" -f [int]$response.StatusCode)
        return $ok
    }
    catch {
        Write-CheckResult -Name $Name -Passed $false -Message $_.Exception.Message
        return $false
    }
}

function Test-JsonEndpoint {
    param(
        [string]$Name,
        [string]$Uri,
        [hashtable]$Headers = @{},
        [scriptblock]$Describe = $null,
        [scriptblock]$Validate = $null
    )

    try {
        $response = Invoke-WebRequest -Uri $Uri -Headers $Headers -TimeoutSec $TimeoutSeconds -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        $message = "HTTP {0}" -f [int]$response.StatusCode
        if ($Describe) {
            $extra = & $Describe $data
            if ($extra) {
                $message = $extra
            }
        }
        $ok = [int]$response.StatusCode -ge 200 -and [int]$response.StatusCode -lt 400
        if ($ok -and $Validate) {
            $ok = [bool](& $Validate $data)
        }
        Write-CheckResult -Name $Name -Passed $ok -Message $message
        return $ok
    }
    catch {
        Write-CheckResult -Name $Name -Passed $false -Message $_.Exception.Message
        return $false
    }
}

$allPassed = $true
$masterKey = $env:LITELLM_MASTER_KEY
$authHeaders = @{}

if (-not $masterKey) {
    Write-Host 'Missing LITELLM_MASTER_KEY. Set it first:'
    Write-Host '$env:LITELLM_MASTER_KEY="sk-your-key"'
    $allPassed = $false
}
else {
    $authHeaders = @{ Authorization = "Bearer $masterKey" }
}

$allPassed = (Test-JsonEndpoint -Name "vLLM tunnel" -Uri "http://127.0.0.1:8000/v1/models" -Describe {
    param($data)
    $model = $data.data[0].id
    if ($model) { return "HTTP 200, model=$model" }
    return "HTTP 200"
}) -and $allPassed
$allPassed = (Test-Endpoint -Name "LiteLLM health" -Uri "http://127.0.0.1:4000/health" -Headers $authHeaders) -and $allPassed

if ($masterKey) {
    $allPassed = (Test-JsonEndpoint -Name "LiteLLM models" -Uri "http://127.0.0.1:4000/v1/models" -Headers $authHeaders -Describe {
        param($data)
        $models = @($data.data | ForEach-Object { $_.id })
        if ($models -contains "active-lanta-model") {
            return "active-lanta-model available"
        }
        return "active-lanta-model missing"
    } -Validate {
        param($data)
        return @($data.data | ForEach-Object { $_.id }) -contains "active-lanta-model"
    }) -and $allPassed
}
else {
    Write-CheckResult -Name "LiteLLM models" -Passed $false -Message "missing LITELLM_MASTER_KEY"
}

$allPassed = (Test-Endpoint -Name "OpenWebUI homepage" -Uri "http://127.0.0.1:3000") -and $allPassed
$allPassed = (Test-Endpoint -Name "Platform exporter" -Uri "http://127.0.0.1:9108/healthz") -and $allPassed
$allPassed = (Test-Endpoint -Name "Prometheus" -Uri "http://127.0.0.1:9090/-/ready") -and $allPassed
$allPassed = (Test-JsonEndpoint -Name "Grafana" -Uri "http://127.0.0.1:3002/api/health" -Describe {
    param($data)
    if ($data.database) { return $data.database }
    if ($data.version) { return "ok" }
    return "HTTP 200"
}) -and $allPassed
$allPassed = (Test-Endpoint -Name "Dashboard API" -Uri "http://127.0.0.1:8088/api/healthz") -and $allPassed
$allPassed = (Test-JsonEndpoint -Name "Platform status" -Uri "http://127.0.0.1:8088/api/platform/status" -Describe {
    param($data)
    return ("{0}, alias={1}, vllm={2}" -f $data.overall_status, $data.model.public_alias, $data.model.vllm_reported_model_id)
} -Validate {
    param($data)
    return $data.overall_status -eq "ok"
}) -and $allPassed

if (-not $allPassed) {
    exit 1
}
