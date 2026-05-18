$ErrorActionPreference = "Stop"

$CoreRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
if (-not (Test-Path $CoreRoot)) {
  $CoreRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
}
if (-not (Test-Path $CoreRoot)) {
  throw "Core introuvable: C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
}

Set-Location $CoreRoot
Write-Host "[T0162B-RUN] Core: $CoreRoot"
python tools\build_t0162_b9_market_compare_board.py --mode runtime --core-root . --output-dir outputs\b9_market_compare_board_v0 --top-k 8
Write-Host "[T0162B-RUN] Board genere dans outputs\b9_market_compare_board_v0"
