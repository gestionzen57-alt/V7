$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0176_b9_dashboard_operational_degraded_gate.py --core-root . --output-dir outputs\t0176_b9_dashboard_operational_degraded_gate_v0 --print-json
