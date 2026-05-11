param(
    [string]$CorePath = ".",
    [string]$Log = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Core = Resolve-Path $CorePath
Set-Location $Core

if ($Log -ne "") {
    python .\dashboard_hydration_failure_doctor.py --root . --log $Log
} else {
    python .\dashboard_hydration_failure_doctor.py --root .
}

Get-Content .\output\DASHBOARD_HYDRATION_FAILURE_DOCTOR.md
