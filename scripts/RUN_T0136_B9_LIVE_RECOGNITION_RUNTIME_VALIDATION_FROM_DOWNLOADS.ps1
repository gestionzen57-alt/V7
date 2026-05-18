param(
  [string]$CorePath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
)
$ErrorActionPreference = "Stop"
Set-Location $CorePath
Write-Host "=== RUN T0136 B9 LIVE RECOGNITION RUNTIME VALIDATION ===" -ForegroundColor Cyan
python tools\build_t0136_b9_live_recognition_runtime_validation.py --mode runtime --core-root . --output-dir outputs\b9_live_recognition_runtime_validation_v0 --execute-t0135
Write-Host "T0136 runtime validation complete." -ForegroundColor Green
