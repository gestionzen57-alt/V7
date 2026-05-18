$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core

python tools\build_t0120_b9_native_summarizer_v4_contract_patch.py `
  --sequence-summary-json samples\b9_native_summarizer_v4_contract_patch_v0\sample_t009_sequence_summary_raw_calibrated.json `
  --output-dir outputs\b9_native_summarizer_v4_contract_patch_v0
