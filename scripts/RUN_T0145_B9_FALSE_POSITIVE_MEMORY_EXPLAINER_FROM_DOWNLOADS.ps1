$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0145_b9_false_positive_memory_explainer.py --sequence-summary-json samples\b9_false_positive_memory_explainer_v0\sample_t009_sequence_summary_false_positive_memory.json --output-dir outputs\b9_false_positive_memory_explainer_v0
