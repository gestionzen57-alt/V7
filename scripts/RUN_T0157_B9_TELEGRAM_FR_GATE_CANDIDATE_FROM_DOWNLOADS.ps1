$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
$RuntimeInput = "outputs\b9_reality_board_integration_candidate_v0\B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json"
if (-not (Test-Path $RuntimeInput)) {
  $RuntimeInput = "samples\b9_telegram_fr_gate_candidate_v0\sample_b9_reality_board_integration_candidate.json"
}
python tools\build_t0157_b9_telegram_fr_gate_candidate.py --reality-board-payload-json $RuntimeInput --output-dir outputs\b9_telegram_fr_gate_candidate_v0
