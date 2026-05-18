$ErrorActionPreference = "Stop"
$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core
python tools\build_t0135_b9_live_scene_recognition_loop.py `
  --live-scene-json samples\b9_live_scene_recognition_loop_v0\sample_b9_live_scene_query_payload.json `
  --similarity-query-json samples\b9_live_scene_recognition_loop_v0\sample_t0115_similarity_query_result.json `
  --false-positive-json samples\b9_live_scene_recognition_loop_v0\sample_t0117_false_positive_context.json `
  --terrain-synthesis-json samples\b9_live_scene_recognition_loop_v0\sample_t0118_human_terrain_synthesis.json `
  --french-report-json samples\b9_live_scene_recognition_loop_v0\sample_b9_french_trader_scene_report.json `
  --output-dir outputs\b9_live_scene_recognition_loop_v0 `
  --top-k 3
