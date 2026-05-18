param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
    [string]$OutputDir = "outputs\b9_french_event_display_contract_v0",
    [switch]$StrictExit
)

$ErrorActionPreference = "Stop"

Write-Host "=== RUN T0159 B9 FRENCH EVENT DISPLAY CONTRACT ===" -ForegroundColor Cyan
Write-Host "RepoRoot : $RepoRoot"
Write-Host "OutputDir: $OutputDir"

if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
Set-Location $RepoRoot

$Tool = ".\tools\build_t0159_b9_french_event_display_contract.py"
if (!(Test-Path $Tool)) { throw "Tool not found: $Tool" }

$Args = @("--output-dir", $OutputDir)
if ($StrictExit) { $Args += "--strict-exit" }

python $Tool @Args
if ($LASTEXITCODE -ne 0) { throw "T0159 French display contract generation failed." }

Write-Host "Done." -ForegroundColor Green
