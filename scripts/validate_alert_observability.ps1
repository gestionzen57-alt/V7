# Validate PowerFlow V7.2 Alert Observability Metrics
# Run from repo root:
#   .\scripts\validate_alert_observability.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== py_compile ===" -ForegroundColor Cyan
python -m py_compile Core\pf_alert_observability_metrics.py
python -m py_compile Core\run_alert_observability_metrics_once.py

Write-Host ""
Write-Host "=== Self-test ===" -ForegroundColor Cyan
python Core\run_alert_observability_metrics_once.py --self-test --pretty

Write-Host ""
Write-Host "=== JSON validation ===" -ForegroundColor Cyan
python -m json.tool output\alert_metrics.json | Out-Null

Write-Host ""
Write-Host "=== Generated files ===" -ForegroundColor Cyan
Get-Item output\alert_metrics.json
Get-Item output\alert_metrics.md

Write-Host ""
Write-Host "Alert observability validation OK." -ForegroundColor Green
