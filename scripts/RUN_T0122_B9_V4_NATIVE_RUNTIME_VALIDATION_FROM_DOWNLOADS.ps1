$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0122_b9_v4_native_runtime_validation.py `
  --sequence-summary-json samples\b9_v4_native_runtime_validation_v0\sample_t009_sequence_summary_v4_candidate.json `
  --summarizer-py pf_t009_sequence_summarizer.py `
  --output-dir outputs\b9_v4_native_runtime_validation_v0
