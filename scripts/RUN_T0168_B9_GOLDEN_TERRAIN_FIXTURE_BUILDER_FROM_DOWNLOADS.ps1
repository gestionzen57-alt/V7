param(
  [string]$Core = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
  [string]$GoldenCasesCsv = ""
)
$ErrorActionPreference = "Stop"
Set-Location $Core
if ([string]::IsNullOrWhiteSpace($GoldenCasesCsv)) {
  $candidate = Join-Path $Core "Docs\Reports\T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv"
  if (Test-Path $candidate) { $GoldenCasesCsv = $candidate }
  else { $GoldenCasesCsv = Join-Path $Core "samples\b9_golden_terrain_fixture_builder_v0\T0150_B9_GOLDEN_TERRAIN_CASES_V1_SAMPLE.csv" }
}
python tools\build_t0168_b9_golden_terrain_fixture_builder.py --golden-cases-csv $GoldenCasesCsv --output-dir outputs\b9_golden_terrain_fixture_builder_v0 --min-ready 1
