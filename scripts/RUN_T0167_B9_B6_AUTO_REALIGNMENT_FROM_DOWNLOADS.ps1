param(
  [string]$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
)
$ErrorActionPreference = "Stop"
Set-Location $Core
python tools\build_t0167_b9_b6_auto_realignment_runner.py `
  --latest-scene-json outputs\b9_live_scene_candidate_queue_v0\B9_LATEST_SCENE_CANDIDATE_V0.json `
  --b6-index-json outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json `
  --film-cards-json outputs\b6_film_library_v0\B6_FILM_CARDS_V0.json `
  --output-dir outputs\b9_b6_auto_realignment_v0 `
  --top-k 5
