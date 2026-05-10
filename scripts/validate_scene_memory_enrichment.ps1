# Validate PowerFlow V7.2 Scene Memory Enrichment
# Run from repo root:
#   .\scripts\validate_scene_memory_enrichment.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== py_compile ===" -ForegroundColor Cyan
python -m py_compile Core\pf_scene_registry.py
python -m py_compile Core\pf_memory_scene_enrichment.py
python -m py_compile Core\run_scene_memory_enrichment_once.py

Write-Host ""
Write-Host "=== Self-test ===" -ForegroundColor Cyan
python Core\run_scene_memory_enrichment_once.py --self-test --pretty

Write-Host ""
Write-Host "=== JSON validation ===" -ForegroundColor Cyan
python -m json.tool output\behavioral_alert_queue_scene_enriched.json | Out-Null
python -m json.tool output\scene_memory_enrichment_report.json | Out-Null

Write-Host ""
Write-Host "=== Live/default queue test ===" -ForegroundColor Cyan
python Core\run_scene_memory_enrichment_once.py --pretty

Write-Host ""
Write-Host "Scene memory enrichment validation OK." -ForegroundColor Green
