$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\apply_t0174_t0169_import_path_hotfix.py --core-root . --output-dir outputs\t0174_t0169_import_path_hotfix_v0 --apply --print-json
