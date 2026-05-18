param(
    [string]$CorePath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
)

$ErrorActionPreference = "Stop"
Set-Location $CorePath
python tools\build_t0178_b9_relock_after_runtime_regen.py --core-root . --output-dir outputs\t0178_b9_relock_after_runtime_regen_v0 --execute --print-json
