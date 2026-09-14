param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Prompt,
    [double]$MaxCost = 2,
    [ValidateSet("agent", "plan", "ask")][string]$Mode = "agent"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sessionsDir = Join-Path $repoRoot "bob_sessions"
New-Item -ItemType Directory -Path $sessionsDir -Force | Out-Null

if (-not $env:BOB_API_KEY) {
    $keyFile = Join-Path $env:USERPROFILE ".cdr\bob-api-key.txt"
    if (Test-Path $keyFile) {
        $env:BOB_API_KEY = (Get-Content $keyFile -Raw).Trim()
    }
}
if (-not $env:BOB_API_KEY) {
    throw "BOB_API_KEY is not set. Configure it as a user environment variable or in ~/.cdr/bob-api-key.txt"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outFile = Join-Path $sessionsDir "bobshell-$Name-$timestamp.json"

Write-Output "[bob-task] starting '$Name' (mode=$Mode, max-cost=$MaxCost Bobcoins)"
Push-Location $repoRoot
try {
    $output = bob run --trust --accept-license --format json --mode $Mode --max-cost $MaxCost $Prompt 2>&1
    $output | Out-File -FilePath $outFile -Encoding utf8
    Write-Output $output
    Write-Output "[bob-task] evidence saved to $outFile"
}
finally {
    Pop-Location
}
