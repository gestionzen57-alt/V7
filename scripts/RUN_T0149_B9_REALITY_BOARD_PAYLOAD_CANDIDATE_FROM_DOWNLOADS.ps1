$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
$Input = "outputs\b9_live_brief_once_runner_v0\B9_LIVE_BRIEF_ONCE_V0.json"
if (-not (Test-Path $Input)) {
  Write-Host "Runtime input missing, using sample input." -ForegroundColor Yellow
  $Input = "samples\b9_reality_board_payload_candidate_v0\sample_b9_live_brief_once_ready.json"
}
python tools\build_t0149_b9_reality_board_payload_candidate.py --live-brief-json $Input --output-dir outputs\b9_reality_board_payload_candidate_v0
