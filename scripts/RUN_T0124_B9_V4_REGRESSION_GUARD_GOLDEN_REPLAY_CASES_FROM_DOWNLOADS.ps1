$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0124_b9_v4_regression_guard_golden_replay_cases.py `
  --input-summary-json samples\b9_v4_regression_guard_golden_replay_cases_v0\sample_b9_v4_golden_replay_cases_input.json `
  --output-dir outputs\b9_v4_regression_guard_golden_replay_cases_v0
