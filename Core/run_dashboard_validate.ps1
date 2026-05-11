param(
    [string]$CorePath = ".",
    [string]$Html = ".\dashboard_live_v7.2_final.html"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Core = Resolve-Path $CorePath
Set-Location $Core

python -m py_compile `
  .\dashboard_data_normalizer.py `
  .\dashboard_contract_validator.py `
  .\dashboard_output_coverage_doctor.py `
  .\dashboard_hydration_failure_doctor.py

powershell -ExecutionPolicy Bypass -File .\run_dashboard_live_stack.ps1 `
  -Root . `
  -Html $Html `
  -Normalize `
  -Validate `
  -Doctor

powershell -ExecutionPolicy Bypass -File .\run_hydration_failure_doctor.ps1 -CorePath .

Write-Host "Dashboard validation helper complete."
