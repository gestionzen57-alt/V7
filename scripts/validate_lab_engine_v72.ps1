# Validate PowerFlow V7.2 Lab Engine
# Run from repo root:
#   .\scripts\validate_lab_engine_v72.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== py_compile ===" -ForegroundColor Cyan
python -m py_compile Core\pf_lab_engine_v72.py
python -m py_compile Core\run_lab_engine_v72_once.py

Write-Host ""
Write-Host "=== Self-test full lab run ===" -ForegroundColor Cyan
$result = python Core\run_lab_engine_v72_once.py --self-test --pretty
$result

Write-Host ""
Write-Host "=== Locate latest lab run ===" -ForegroundColor Cyan
$latest = Get-ChildItem .\output\lab_runs -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $latest) {
    throw "No lab run directory found."
}
Write-Host "Latest: $($latest.FullName)"

Write-Host ""
Write-Host "=== JSON validation ===" -ForegroundColor Cyan
python -m json.tool "$($latest.FullName)\replay_raw.json" | Out-Null
python -m json.tool "$($latest.FullName)\replay_enriched.json" | Out-Null
python -m json.tool "$($latest.FullName)\scene_timeline.json" | Out-Null
python -m json.tool "$($latest.FullName)\cause_consequence.json" | Out-Null
python -m json.tool "$($latest.FullName)\lab_metrics.json" | Out-Null

Write-Host ""
Write-Host "=== Generated files ===" -ForegroundColor Cyan
Get-ChildItem $latest.FullName

Write-Host ""
Write-Host "Lab Engine V7.2 validation OK." -ForegroundColor Green
