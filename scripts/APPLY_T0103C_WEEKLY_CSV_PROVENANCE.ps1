param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
    [string]$OutputRoot = "C:\Users\User\Downloads\_b9_force_snapshot_derived_raw_calibration_shift0_outputs"
)

$ErrorActionPreference = "Stop"

Write-Host "=== APPLY T0103C WEEKLY CSV PROVENANCE ===" -ForegroundColor Cyan
Write-Host "RepoRoot  : $RepoRoot"
Write-Host "OutputRoot: $OutputRoot"

if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
if (!(Test-Path $OutputRoot)) { throw "OutputRoot not found: $OutputRoot" }

Set-Location $RepoRoot

$Tool = Join-Path $RepoRoot "tools\t0103c_propagate_weekly_provenance.py"
if (!(Test-Path $Tool)) { throw "Tool not found: $Tool" }

python $Tool --output-root $OutputRoot
if ($LASTEXITCODE -ne 0) { throw "T0103C provenance propagation failed" }

Write-Host "T0103C complete." -ForegroundColor Green
