[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
  [string[]]$Prompt,
  [string]$BaseUrl = $env:OPENAI_BASE_URL,
  [string]$ApiKey = $env:OPENAI_API_KEY,
  [string]$Model = $env:MODEL,
  [string]$System = $env:SYSTEM_PROMPT,
  [string[]]$File = @(),
  [int]$MaxTokens = 8192,
  [double]$Temperature = 0.7,
  [switch]$Thinking,
  [switch]$NoStream
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$argsList = @()

if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) {
  $argsList += @("--base-url", $BaseUrl)
}

if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
  $argsList += @("--api-key", $ApiKey)
}

if (-not [string]::IsNullOrWhiteSpace($Model)) {
  $argsList += @("--model", $Model)
}

if (-not [string]::IsNullOrWhiteSpace($System)) {
  $argsList += @("--system", $System)
}

foreach ($path in $File) {
  if (-not [string]::IsNullOrWhiteSpace($path)) {
    $argsList += @("--file", $path)
  }
}

$argsList += @("--max-tokens", "$MaxTokens", "--temperature", "$Temperature")

if ($Thinking) {
  $argsList += "--thinking"
}

if ($NoStream) {
  $argsList += "--no-stream"
}

if ($Prompt.Count -gt 0) {
  $argsList += $Prompt
}

node "$scriptDir\qwen-chat-cli.mjs" @argsList
