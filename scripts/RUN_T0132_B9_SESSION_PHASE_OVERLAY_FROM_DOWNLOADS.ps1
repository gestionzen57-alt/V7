$ErrorActionPreference = "Stop"
Set-Location "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
python tools\build_t0132_b9_session_phase_overlay.py --sequence-summary-json samples\b9_session_phase_overlay_v0\sample_t009_sequence_summary_session_overlay.json --output-dir outputs\b9_session_phase_overlay_v0
