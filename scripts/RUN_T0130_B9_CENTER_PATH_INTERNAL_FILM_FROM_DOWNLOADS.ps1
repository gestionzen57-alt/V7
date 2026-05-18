$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0130_b9_center_path_internal_film.py `
  --sequence-summary-json samples\b9_center_path_internal_film_v0\sample_t009_sequence_summary_center_path.json `
  --output-dir outputs\b9_center_path_internal_film_v0
