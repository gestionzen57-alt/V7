param(
  [string]$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $Core
python tools\build_t0153_b9_scene_state_machine.py --sequence-summary-json samples\b9_scene_state_machine_v0\sample_t009_sequence_summary_scene_state.json --output-dir outputs\b9_scene_state_machine_v0
