<#
PowerFlow V6 - VALIDATE_CORE_AFTER_CLEANUP.ps1
Mission: validate Core after cleanup.

Usage:
  powershell -ExecutionPolicy Bypass -File .\VALIDATE_CORE_AFTER_CLEANUP.ps1

Options:
  -SkipCockpit
  -SkipRadar
#>

param(
    [switch]$SkipCockpit,
    [switch]$SkipRadar
)

$ErrorActionPreference = "Continue"

Write-Host "============================================================"
Write-Host "PowerFlow V6 - Validate Core After Cleanup"
Write-Host ("Root: " + (Get-Location).Path)
Write-Host "============================================================"

$RequiredFiles = @(
    "capture_bridge.py",
    "powerflow.db",
    "pf_personalities.py",
    "pf_zone_dynamics.py",
    "pf_coalitions.py",
    "pf_coalition_relations.py",
    "pf_battlefield_radar.py",
    "pf_cockpit_field.py",
    "run_cockpit_field.py",
    "run_battlefield_radar_once.py"
)

$Missing = @()

Write-Host ""
Write-Host "--- FILE CHECK ---"
foreach ($File in $RequiredFiles) {
    if (Test-Path -LiteralPath $File) {
        Write-Host ("OK   " + $File)
    } else {
        Write-Host ("MISS " + $File)
        $Missing += $File
    }
}

if ($Missing.Count -gt 0) {
    Write-Host ""
    Write-Host "BLOCKED: missing required files."
    Write-Host ($Missing -join ", ")
    exit 2
}

Write-Host ""
Write-Host "--- PYTHON IMPORT CHECK ---"
python -c "import pf_personalities; import pf_zone_dynamics; import pf_coalitions; import pf_coalition_relations; import pf_battlefield_radar; import pf_cockpit_field; print('OK imports personality/zone/radar/cockpit')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL import check"
    exit 3
}
Write-Host "OK import check"

if (-not $SkipCockpit) {
    Write-Host ""
    Write-Host "--- COCKPIT FIELD VALIDATION ---"
    python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAIL cockpit field validation"
        exit 4
    }
    Write-Host "OK cockpit field validation"
}

if (-not $SkipRadar) {
    Write-Host ""
    Write-Host "--- BATTLEFIELD RADAR VALIDATION ---"
    python run_battlefield_radar_once.py --db powerflow.db --scan 240
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAIL battlefield radar validation"
        exit 5
    }
    Write-Host "OK battlefield radar validation"
}

Write-Host ""
Write-Host "============================================================"
Write-Host "VALIDATION COMPLETE"
Write-Host "Next target: test_pf_personality_zone_bridge.py"
Write-Host "============================================================"
exit 0
