$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0146_b9_memory_confidence_ladder.py --sequence-summary-json samples\b9_memory_confidence_ladder_v0\sample_t009_sequence_summary_memory_confidence.json --output-dir outputs\b9_memory_confidence_ladder_v0
