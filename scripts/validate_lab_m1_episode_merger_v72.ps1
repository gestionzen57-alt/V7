# Validate PowerFlow V7.2 M1 Episode Merger V0.4
# Run from repo root:
#   .\scripts\validate_lab_m1_episode_merger_v72.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== py_compile ===" -ForegroundColor Cyan
python -m py_compile Core\pf_lab_m1_episode_merger_v72.py
python -m py_compile Core\run_lab_m1_episode_merger_v72_once.py

Write-Host ""
Write-Host "=== Locate latest lab run with M1 zoom index ===" -ForegroundColor Cyan
$latest = Get-ChildItem .\output\lab_runs -Directory |
  Where-Object { Test-Path "$($_.FullName)\m1_zoom_index.json" } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if ($null -eq $latest) {
    throw "No lab run with m1_zoom_index.json found. Run Lab V0.3 with --m1 zoom first."
}

Write-Host "Latest M1 zoom run: $($latest.FullName)"

Write-Host ""
Write-Host "=== Run M1 episode merger ===" -ForegroundColor Cyan
python Core\run_lab_m1_episode_merger_v72_once.py --lab-run "$($latest.FullName)" --pretty

Write-Host ""
Write-Host "=== JSON validation ===" -ForegroundColor Cyan
python -m json.tool "$($latest.FullName)\m1_episodes.json" | Out-Null
python -m json.tool "$($latest.FullName)\m1_episode_merger_metrics.json" | Out-Null

Write-Host ""
Write-Host "=== Generated V0.4 files ===" -ForegroundColor Cyan
Get-ChildItem $latest.FullName | Where-Object {
    $_.Name -in @(
        "m1_episodes.json",
        "film_m1_episodes.md",
        "lab_report_m1_episodes.html",
        "m1_episode_merger_metrics.json"
    )
}

Write-Host ""
Write-Host "Lab M1 Episode Merger V0.4 validation OK." -ForegroundColor Green
