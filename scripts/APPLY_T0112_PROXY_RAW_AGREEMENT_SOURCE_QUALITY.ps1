param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
    [string]$OutputRoot = "C:\Users\User\Downloads_b9_force_snapshot_shift0_outputs"
)

$ErrorActionPreference = "Stop"

Write-Host "=== APPLY T0112 PROXY/RAW AGREEMENT SOURCE QUALITY ===" -ForegroundColor Cyan
Write-Host "RepoRoot  : $RepoRoot"
Write-Host "OutputRoot: $OutputRoot"

if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
if (!(Test-Path $OutputRoot)) { throw "OutputRoot not found: $OutputRoot" }

Set-Location $RepoRoot

$Tool = Join-Path $RepoRoot "tools\t0112_proxy_raw_agreement_source_quality.py"
if (!(Test-Path $Tool)) { throw "Tool not found: $Tool" }

python $Tool --output-root $OutputRoot
if ($LASTEXITCODE -ne 0) { throw "T0112 apply failed" }

Write-Host "T0112 complete." -ForegroundColor Green
