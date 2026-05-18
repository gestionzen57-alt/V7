$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0155_b9_trader_attention_packet.py `
  --input-json samples\b9_trader_attention_packet_v0\sample_b9_trader_attention_input.json `
  --output-dir outputs\b9_trader_attention_packet_v0
