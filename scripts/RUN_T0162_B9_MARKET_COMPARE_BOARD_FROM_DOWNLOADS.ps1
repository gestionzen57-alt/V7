$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0162_b9_market_compare_board.py --mode runtime --core-root . --output-dir outputs\b9_market_compare_board_v0 --top-k 8
