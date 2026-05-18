$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core

python tools\build_t0156_b9_reality_board_integration_candidate.py `
  --attention-packet-json samples\b9_reality_board_integration_candidate_v0\sample_b9_trader_attention_packet.json `
  --output-dir outputs\b9_reality_board_integration_candidate_v0
