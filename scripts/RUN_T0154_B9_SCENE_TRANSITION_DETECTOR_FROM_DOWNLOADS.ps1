$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0154_b9_scene_transition_detector.py --sequence-summary-json samples\b9_scene_transition_detector_v0\sample_t009_sequence_summary_scene_transitions.json --output-dir outputs\b9_scene_transition_detector_v0
