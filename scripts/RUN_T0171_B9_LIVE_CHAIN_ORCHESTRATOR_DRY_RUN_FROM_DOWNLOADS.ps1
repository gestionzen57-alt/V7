param(
  [string]$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$OutputDir = "outputs\b9_live_chain_orchestrator_dry_run_v0"
)
$ErrorActionPreference = "Stop"
Set-Location $Core
python tools\build_t0171_b9_live_chain_orchestrator_dry_run.py --core-root . --output-dir $OutputDir --print-json
