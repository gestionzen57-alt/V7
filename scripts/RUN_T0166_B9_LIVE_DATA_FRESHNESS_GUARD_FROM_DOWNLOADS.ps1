$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0166_b9_live_data_freshness_guard.py --core-root . --output-dir outputs\b9_live_data_freshness_guard_v0 --freshness-seconds 300
