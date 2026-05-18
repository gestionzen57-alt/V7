$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0141_b9_zone_memory_object_builder.py --sequence-summary-json samples\b9_zone_memory_object_builder_v0\sample_t009_sequence_summary_zone_memory.json --output-dir outputs\b9_zone_memory_object_builder_v0
