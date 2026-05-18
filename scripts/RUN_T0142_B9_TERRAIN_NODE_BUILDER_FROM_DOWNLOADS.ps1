$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0142_b9_terrain_node_builder.py `
  --sequence-summary-json samples\b9_terrain_node_builder_v0\sample_t009_sequence_summary_terrain_nodes.json `
  --output-dir outputs\b9_terrain_node_builder_v0
