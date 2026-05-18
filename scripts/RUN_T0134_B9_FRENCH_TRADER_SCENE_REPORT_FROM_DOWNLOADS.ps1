$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0134_b9_french_trader_scene_report.py --sequence-summary-json samples\b9_french_trader_scene_report_v0\sample_t009_sequence_summary_french_report.json --memory-brief-json samples\b9_french_trader_scene_report_v0\sample_b9_memory_brief_v0.json --output-dir outputs\b9_french_trader_scene_report_v0
