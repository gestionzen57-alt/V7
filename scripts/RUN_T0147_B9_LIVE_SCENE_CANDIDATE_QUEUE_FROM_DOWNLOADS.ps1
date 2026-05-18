$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0147_b9_live_scene_candidate_queue.py --sequence-summary-json samples\b9_live_scene_candidate_queue_v0\sample_t009_sequence_summary_live_queue.json --output-dir outputs\b9_live_scene_candidate_queue_v0 --max-candidates 12
