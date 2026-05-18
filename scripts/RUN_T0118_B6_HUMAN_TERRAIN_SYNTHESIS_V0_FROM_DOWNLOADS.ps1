$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0118_b6_human_terrain_synthesis_v0.py `
  --film-cards-json outputs\b6_film_library_v0\B6_FILM_CARDS_V0.json `
  --false-positive-json outputs\b6_false_positive_context_v0\B6_FALSE_POSITIVE_CONTEXT_V0.json `
  --output-dir outputs\b6_human_terrain_synthesis_v0
