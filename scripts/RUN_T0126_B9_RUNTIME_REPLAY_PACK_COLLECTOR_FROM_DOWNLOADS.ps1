$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
Write-Host "=== RUN T0126 B9 RUNTIME REPLAY PACK COLLECTOR ===" -ForegroundColor Cyan
python tools\build_t0126_b9_runtime_replay_pack_collector.py --scan-root . --output-dir outputs\b9_runtime_replay_pack_collector_v0
