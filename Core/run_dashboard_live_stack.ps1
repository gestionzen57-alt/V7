param(
    [string]$Root = ".",
    [string]$Html = ".\dashboard_live_v7.2_final.html",
    [int]$StaleSeconds = 180,
    [switch]$Normalize,
    [switch]$Validate,
    [switch]$Doctor,
    [switch]$Serve
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Core = Resolve-Path $Root
Set-Location $Core

function Invoke-Checked {
    param(
        [string]$Label,
        [string]$Exe,
        [string[]]$ArgsList
    )

    Write-Host "RUN $Label"
    & $Exe @ArgsList
    $code = $LASTEXITCODE

    if ($null -ne $code -and $code -ne 0) {
        throw "$Label failed with exit code $code"
    }

    Write-Host "OK  $Label"
}

if ($Normalize) {
    Invoke-Checked "dashboard_data_normalizer" "python" @(
        ".\dashboard_data_normalizer.py",
        "--root", ".",
        "--stale-seconds", "$StaleSeconds"
    )
}

if ($Validate) {
    Invoke-Checked "dashboard_contract_validator" "python" @(
        ".\dashboard_contract_validator.py",
        "--html", $Html,
        "--root", ".",
        "--stale-seconds", "$StaleSeconds",
        "--json-out", ".\output\dashboard_contract_validation.json",
        "--md-out", ".\output\DASHBOARD_CONTRACT_VALIDATION.md"
    )
}

if ($Doctor) {
    Invoke-Checked "dashboard_output_coverage_doctor" "python" @(
        ".\dashboard_output_coverage_doctor.py",
        "--root", "."
    )
}

if ($Serve) {
    Write-Host "Dashboard server: http://localhost:8787/dashboard_live_v7.2_final.html"
    python -m http.server 8787
}
