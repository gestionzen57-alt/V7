param(
  [string]$InputJson = "samples\b9_source_quality_hard_gate_v0\sample_t009_sequence_summary_source_quality.json",
  [string]$OutputDir = "outputs\b9_source_quality_hard_gate_v0"
)
$ErrorActionPreference = "Stop"
Set-Location "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
python tools\build_t0133_b9_source_quality_hard_gate.py --sequence-summary-json $InputJson --output-dir $OutputDir
