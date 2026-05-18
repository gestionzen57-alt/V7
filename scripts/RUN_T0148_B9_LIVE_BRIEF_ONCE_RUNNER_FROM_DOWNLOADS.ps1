$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0148_b9_live_brief_once_runner.py `
  --latest-scene-json outputs\b9_live_scene_candidate_queue_v0\B9_LATEST_SCENE_CANDIDATE_V0.json `
  --queue-json outputs\b9_live_scene_candidate_queue_v0\B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.json `
  --adapter-json outputs\b6_live_scene_adapter_v0\B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json `
  --similarity-query-json outputs\b6_similarity_query_v0\B6_SIMILARITY_QUERY_RESULT_V0.json `
  --false-positive-json outputs\b6_false_positive_context_v0\B6_FALSE_POSITIVE_CONTEXT_V0.json `
  --terrain-synthesis-json outputs\b6_human_terrain_synthesis_v0\B6_HUMAN_TERRAIN_SYNTHESIS_V0.json `
  --french-report-json outputs\b9_french_trader_scene_report_v0\B9_FRENCH_TRADER_SCENE_REPORT_V0.json `
  --output-dir outputs\b9_live_brief_once_runner_v0 `
  --top-k 3
