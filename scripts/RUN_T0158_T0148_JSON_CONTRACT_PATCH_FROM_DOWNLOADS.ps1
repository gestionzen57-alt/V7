$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
Write-Host "=== RUN T0158 T0148 JSON CONTRACT PATCH ===" -ForegroundColor Cyan
python -m py_compile tools\apply_t0158_t0148_json_contract_patch.py
python -m pytest tests\test_t0158_t0148_json_contract_patch.py
python tools\apply_t0158_t0148_json_contract_patch.py --target pf_t009_live_brief_once_runner.py --output-report outputs\t0148_json_contract_patch_v0\T0158_T0148_JSON_CONTRACT_PATCH_REPORT.json
python -m py_compile pf_t009_live_brief_once_runner.py
Write-Host "T0158 run complete." -ForegroundColor Green
