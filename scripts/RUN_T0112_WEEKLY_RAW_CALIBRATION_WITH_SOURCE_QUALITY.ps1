param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
    [string[]]$SummaryRoot,
    [string]$TickDb = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\tick_archive.db",
    [string]$Downloads = "C:\Users\User\Downloads"
)

$ErrorActionPreference = "Stop"

if (!$SummaryRoot -or $SummaryRoot.Count -eq 0) {
    throw "Provide -SummaryRoot"
}

Set-Location $RepoRoot

$Runner = Join-Path $RepoRoot "scripts\RUN_T0103C_WEEKLY_RAW_CALIBRATION_V36_WITH_PROVENANCE.ps1"
if (!(Test-Path $Runner)) {
    throw "T0103C runner not found: $Runner"
}

powershell -ExecutionPolicy Bypass -File $Runner `
  -RepoRoot $RepoRoot `
  -SummaryRoot $SummaryRoot `
  -TickDb $TickDb `
  -Downloads $Downloads

if ($LASTEXITCODE -ne 0) { throw "T0103C runner failed" }

$OutputRoot = Join-Path $Downloads "_b9_weekly_raw_calibration_v36_outputs"
$Apply = Join-Path $RepoRoot "scripts\APPLY_T0112_PROXY_RAW_AGREEMENT_SOURCE_QUALITY.ps1"

powershell -ExecutionPolicy Bypass -File $Apply `
  -RepoRoot $RepoRoot `
  -OutputRoot $OutputRoot

if ($LASTEXITCODE -ne 0) { throw "T0112 post-process failed" }
