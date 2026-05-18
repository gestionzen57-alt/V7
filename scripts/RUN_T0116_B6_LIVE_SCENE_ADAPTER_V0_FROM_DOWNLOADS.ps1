param(
  [string]$InputJson = "",
  [string]$TopK = "5"
)

$ErrorActionPreference = "Stop"

$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
if (-not $InputJson) { $InputJson = Join-Path $Core "samples\b6_live_scene_adapter_v0\sample_b9_live_scene_v0.json" }
$OutputDir = Join-Path $Core "outputs\b6_live_scene_adapter_v0"
$IndexPath = Join-Path $Core "outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json"
$T0115Script = Join-Path $Core "tools\build_t0115_b6_similarity_query_v0.py"
$T0116Script = Join-Path $Core "tools\build_t0116_b6_live_scene_adapter_v0.py"

Write-Host "=== RUN T0116 B6 LIVE SCENE ADAPTER V0 ===" -ForegroundColor Cyan
Set-Location $Core

python $T0116Script --input-json $InputJson --output-dir $OutputDir

$QueryJson = Join-Path $OutputDir "B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json"
if ((Test-Path $T0115Script) -and (Test-Path $IndexPath)) {
  Write-Host "=== Optional compatibility query through T0115 ===" -ForegroundColor Cyan
  python $T0115Script --similarity-index $IndexPath --query-json $QueryJson --output-dir "outputs\b6_live_scene_adapter_v0_t0115_query_validation" --top-k $TopK
} else {
  Write-Host "T0115 script or index not found; adapter output only." -ForegroundColor Yellow
}
