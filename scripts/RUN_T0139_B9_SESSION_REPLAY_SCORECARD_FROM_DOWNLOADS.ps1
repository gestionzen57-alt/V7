param(
  [string]$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$OutputDir = "outputs\b9_session_replay_scorecard_v0"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $Core
$ScanCsv = Get-ChildItem "C:\Users\User\Downloads" -Directory -Filter "b9_replay_corpus_real_*" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  ForEach-Object { Get-ChildItem $_.FullName -Filter "B9_REPLAY_CORPUS_REAL_SCAN_*.csv" -ErrorAction SilentlyContinue | Select-Object -First 1 } |
  Select-Object -First 1
if ($ScanCsv) {
  python tools\build_t0139_b9_session_replay_scorecard.py --scan-root . --scan-csv $ScanCsv.FullName --output-dir $OutputDir
} elseif (Test-Path "outputs\b9_runtime_replay_pack_collector_v0\B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv") {
  python tools\build_t0139_b9_session_replay_scorecard.py --scan-root . --input-index-csv "outputs\b9_runtime_replay_pack_collector_v0\B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv" --output-dir $OutputDir
} else {
  python tools\build_t0139_b9_session_replay_scorecard.py --scan-root . --output-dir $OutputDir
}
