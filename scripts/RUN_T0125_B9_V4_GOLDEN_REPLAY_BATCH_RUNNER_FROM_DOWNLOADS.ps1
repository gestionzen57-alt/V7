$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0125_b9_v4_golden_replay_batch_runner.py --input-dir samples\b9_v4_golden_replay_batch_runner_v0 --output-dir outputs\b9_v4_golden_replay_batch_runner_v0
