param(
  [string]$CorePath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$IndexPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json",
  [string]$OutputDir = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\outputs\b6_similarity_query_v0",
  [string]$QueryFilmId = "B6FC_20260505_1413_BDE6E508",
  [int]$TopK = 5
)

$ErrorActionPreference = "Stop"
Set-Location $CorePath

Write-Host "=== T0115 B6 Similarity Query CLI/API V0 ===" -ForegroundColor Cyan
Write-Host "Core: $CorePath"
Write-Host "Index: $IndexPath"
Write-Host "Output: $OutputDir"

if (-not (Test-Path $IndexPath)) {
  throw "Missing similarity index: $IndexPath. Install/run T0114 first or copy B6_SIMILARITY_INDEX_V0.json into outputs\b6_similarity_index_v0."
}

python -m py_compile tools\build_t0115_b6_similarity_query_v0.py
python tools\build_t0115_b6_similarity_query_v0.py `
  --similarity-index $IndexPath `
  --query-film-id $QueryFilmId `
  --output-dir $OutputDir `
  --top-k $TopK

Write-Host "T0115 query outputs written to $OutputDir" -ForegroundColor Green
