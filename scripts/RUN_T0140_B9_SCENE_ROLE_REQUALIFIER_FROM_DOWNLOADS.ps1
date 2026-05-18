param(
  [string]$SequenceSummaryJson = "samples\b9_scene_role_requalifier_v0\sample_t009_sequence_summary_scene_roles.json",
  [string]$OutputDir = "outputs\b9_scene_role_requalifier_v0"
)
$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0140_b9_scene_role_requalifier.py --sequence-summary-json $SequenceSummaryJson --output-dir $OutputDir
