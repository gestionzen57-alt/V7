$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0172_b9_live_chain_contract_validator.py --core-root . --output-dir outputs\b9_live_chain_contract_validator_v0 --print-json
