$ErrorActionPreference = "Stop"
$CorePath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Write-Host "[INFO] T0175 B9 Global Chain Contract Lock" -ForegroundColor Cyan
Set-Location $CorePath
python -m py_compile "tools\build_t0175_b9_global_chain_contract_lock.py"
python -m pytest "tests\test_t0175_b9_global_chain_contract_lock.py" -q
python "tools\build_t0175_b9_global_chain_contract_lock.py" --core-root . --output-dir "outputs\t0175_b9_global_chain_contract_lock_v0" --print-json
