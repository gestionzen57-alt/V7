param(
  [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$DbPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\powerflow.db",
  [string]$OutputRoot = "C:\Users\User\Downloads\B9_FORCE_SNAPSHOT_DERIVED_SUMMARIES_20260504_20260514",
  [string]$Symbol = "GBPUSD",
  [string]$Dates = "2026-05-04,2026-05-05,2026-05-07,2026-05-08,2026-05-11,2026-05-12,2026-05-13,2026-05-14"
)

$ErrorActionPreference = "Stop"
Write-Host "T009 FORCE SNAPSHOT SCENE GENERATION" -ForegroundColor Cyan
Set-Location $RepoRoot

python .\run_t009_force_snapshot_scene_generation.py `
  --db $DbPath `
  --output $OutputRoot `
  --symbol $Symbol `
  --dates $Dates `
  --preferred-timeframes "1,5,15,30,60" `
  --max-window-min 60

Write-Host "DONE" -ForegroundColor Green
Write-Host "Output: $OutputRoot"
