# Validate PowerFlow V7.2 Lab TF Profiles V0.3
# Run from repo root:
#   .\scripts\validate_lab_tf_profiles_v72.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== py_compile ===" -ForegroundColor Cyan
python -m py_compile Core\pf_lab_tf_profiles_v72.py
python -m py_compile Core\run_lab_profile_v72_once.py

Write-Host ""
Write-Host "=== Ensure self-test DB exists ===" -ForegroundColor Cyan
python Core\run_lab_engine_v72_once.py --self-test --pretty | Out-Null

Write-Host ""
Write-Host "=== Profile MTF without M1 ===" -ForegroundColor Cyan
python Core\run_lab_profile_v72_once.py `
  --db output\lab_engine_v72_selftest.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 10:59 `
  --tf-profile MTF `
  --m1 off `
  --pretty

Write-Host ""
Write-Host "=== Profile LTF with M1 zoom ===" -ForegroundColor Cyan
python Core\run_lab_profile_v72_once.py `
  --db output\lab_engine_v72_selftest.db `
  --symbol GBPUSD `
  --date 2026-05-08 `
  --start 09:00 `
  --end 10:59 `
  --tf-profile LTF `
  --m1 zoom `
  --max-m1-zooms 3 `
  --pretty

Write-Host ""
Write-Host "=== Validate latest profile summary ===" -ForegroundColor Cyan
$latest = Get-ChildItem .\output\lab_runs -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $latest) { throw "No lab run found." }

python -m json.tool "$($latest.FullName)\lab_profile_summary.json" | Out-Null

Write-Host ""
Write-Host "Latest profile run: $($latest.FullName)"
Get-ChildItem $latest.FullName | Where-Object {
    $_.Name -in @(
        "lab_profile_summary.json",
        "lab_report_key_events.html",
        "key_events.csv",
        "m1_zoom_index.json",
        "film_m1_zoom.md"
    )
}

Write-Host ""
Write-Host "Lab TF Profiles V0.3 validation OK." -ForegroundColor Green
