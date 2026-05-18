$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0128_b9_native_retest_source_fields.py `
  --sequence-summary-json samples\b9_native_retest_source_fields_v0\sample_t009_sequence_summary_retest_candidate.json `
  --output-dir outputs\b9_native_retest_source_fields_v0
