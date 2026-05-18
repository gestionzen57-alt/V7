$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0173_b9_live_chain_missing_input_resolver.py --core-root . --output-dir outputs\b9_live_chain_missing_input_resolver_v0 --print-json
