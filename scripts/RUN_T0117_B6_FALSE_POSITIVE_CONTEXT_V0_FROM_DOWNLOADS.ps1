$ErrorActionPreference = "Stop"

$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
Set-Location $Core

$Input = "outputs\b6_similarity_query_v0\B6_SIMILARITY_QUERY_RESULT_V0.json"
if (-not (Test-Path $Input)) {
  $Input = "samples\b6_false_positive_context_v0\sample_t0115_similarity_query_result_v0.json"
}

python tools\build_t0117_b6_false_positive_context_v0.py `
  --query-result-json $Input `
  --output-dir outputs\b6_false_positive_context_v0 `
  --top-k 5
