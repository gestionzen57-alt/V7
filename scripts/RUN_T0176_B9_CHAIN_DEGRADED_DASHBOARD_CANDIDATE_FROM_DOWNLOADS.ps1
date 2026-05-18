$ErrorActionPreference = "Stop"
$CorePath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Write-Host "[INFO] RUN T0176 from Downloads helper"
Set-Location $CorePath
python -m py_compile tools\build_t0176_b9_chain_degraded_dashboard_candidate.py
python -m pytest tests\test_t0176_b9_chain_degraded_dashboard_candidate.py -q
python tools\build_t0176_b9_chain_degraded_dashboard_candidate.py --core-root . --output-dir outputs\t0176_b9_chain_degraded_dashboard_candidate_v0 --print-json
