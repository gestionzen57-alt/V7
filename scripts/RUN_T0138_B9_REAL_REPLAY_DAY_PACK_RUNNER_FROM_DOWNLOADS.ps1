param(
  [string]$CoreRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$InputIndexCsv = "outputs\b9_runtime_replay_pack_collector_v0\B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv",
  [string]$OutputDir = "outputs\b9_real_replay_day_pack_runner_v0"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $CoreRoot
if (Test-Path $InputIndexCsv) {
  python tools\build_t0138_b9_real_replay_day_pack_runner.py --scan-root . --input-index-csv $InputIndexCsv --output-dir $OutputDir
} else {
  Write-Host "Input index not found, falling back to full repo scan: $InputIndexCsv" -ForegroundColor Yellow
  python tools\build_t0138_b9_real_replay_day_pack_runner.py --scan-root . --output-dir $OutputDir
}
