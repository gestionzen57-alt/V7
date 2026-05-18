$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0129_b9_effort_result_progress_scorer.py --sequence-summary-json samples\b9_effort_result_progress_scorer_v0\sample_t009_sequence_summary_effort_result_progress.json --output-dir outputs\b9_effort_result_progress_scorer_v0
