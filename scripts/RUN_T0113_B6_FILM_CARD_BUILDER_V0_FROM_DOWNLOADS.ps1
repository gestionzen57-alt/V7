param(
  [string]$RepoCore = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$InputCsv = "",
  [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RepoCore)) {
  throw "Repo core introuvable: $RepoCore"
}

Set-Location $RepoCore

if ([string]::IsNullOrWhiteSpace($InputCsv)) {
  $InputCsv = Join-Path $RepoCore "outputs\b6_memory_candidate_board_v0\B6_MEMORY_CANDIDATE_BOARD_V0.csv"
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
  $OutputDir = Join-Path $RepoCore "outputs\b6_film_library_v0_regenerated"
}

if (-not (Test-Path $InputCsv)) {
  throw "B6 board CSV introuvable: $InputCsv"
}

python "tools\build_t0113_b6_film_card_builder_v0.py" --input-csv $InputCsv --output-dir $OutputDir

Write-Host "T0113 B6 Film Card Builder V0 OK" -ForegroundColor Green
Write-Host "Output: $OutputDir" -ForegroundColor Cyan
