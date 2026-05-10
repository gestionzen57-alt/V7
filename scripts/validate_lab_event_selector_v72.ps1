# Validate PowerFlow V7.2 Lab Event Selector V0.2
# Run from repo root:
#   .\scripts\validate_lab_event_selector_v72.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== py_compile ===" -ForegroundColor Cyan
python -m py_compile Core\pf_lab_event_selector_v72.py
python -m py_compile Core\run_lab_event_selector_v72_once.py

Write-Host ""
Write-Host "=== Ensure a lab run exists ===" -ForegroundColor Cyan
if (!(Test-Path .\output\lab_runs)) {
    Write-Host "No lab_runs folder. Running Lab Engine self-test first." -ForegroundColor Yellow
    python Core\run_lab_engine_v72_once.py --self-test --pretty | Out-Null
}

$latest = Get-ChildItem .\output\lab_runs -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $latest) {
    throw "No lab run directory found."
}

Write-Host "Latest lab run: $($latest.FullName)"

Write-Host ""
Write-Host "=== Run selector ===" -ForegroundColor Cyan
python Core\run_lab_event_selector_v72_once.py --lab-run "$($latest.FullName)" --pretty

Write-Host ""
Write-Host "=== JSON validation ===" -ForegroundColor Cyan
python -m json.tool "$($latest.FullName)\events_index_full.json" | Out-Null
python -m json.tool "$($latest.FullName)\key_events.json" | Out-Null
python -m json.tool "$($latest.FullName)\key_scene_clusters.json" | Out-Null
python -m json.tool "$($latest.FullName)\event_selector_metrics.json" | Out-Null

Write-Host ""
Write-Host "=== Generated V0.2 files ===" -ForegroundColor Cyan
Get-ChildItem $latest.FullName | Where-Object {
    $_.Name -in @(
        "events_index_full.json",
        "key_events.json",
        "key_events.csv",
        "key_scene_clusters.json",
        "film_key_events.md",
        "lab_report_key_events.html",
        "event_selector_metrics.json"
    )
}

Write-Host ""
Write-Host "Lab Event Selector V0.2 validation OK." -ForegroundColor Green
