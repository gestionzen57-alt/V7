param(
  [string]$Root = ".",
  [string]$Html = ".\dashboard_live_v7.2_final.html",
  [switch]$Normalize,
  [switch]$Validate,
  [switch]$Doctor,
  [switch]$Serve,
  [int]$Port = 8787,
  [int]$StaleSeconds = 180
)

Set-Location $Root

if ($Normalize) {
  python .\dashboard_data_normalizer_v04.py --root . --stale-seconds $StaleSeconds
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($Validate) {
  python .\dashboard_contract_validator_v5.py --html $Html --root . --stale-seconds $StaleSeconds --json-out .\output\dashboard_contract_validation.json --md-out .\output\DASHBOARD_CONTRACT_VALIDATION.md
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($Doctor) {
  python .\dashboard_output_coverage_doctor.py --root . --out .\output\DASHBOARD_OUTPUT_COVERAGE_DOCTOR.md
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($Serve) {
  Write-Host "Dashboard server: http://localhost:$Port/dashboard_live_v7.2_final.html"
  python -m http.server $Port
}
