<#
PowerFlow V7.2 Dashboard Cleanup Tool V2
Archives dashboard iteration artifacts out of Core without deleting them.
Safe by default: use -DryRun first.
#>
[CmdletBinding()]
param(
    [string]$CorePath = ".",
    [switch]$DryRun,
    [switch]$KeepInstallerTools
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-CorePath {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "CorePath not found: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

$core = Resolve-CorePath $CorePath
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $core "backups\dashboard_cleanup\$stamp"

# Canonical active files kept in Core.
$keep = @(
    "dashboard_live_v7.2_final.html",
    "dashboard_data_normalizer.py",
    "dashboard_contract_validator.py",
    "dashboard_output_coverage_doctor.py",
    "run_dashboard_live_stack.ps1",
    "install_powerflow_pack.ps1",
    "cleanup_powerflow_dashboard_artifacts.ps1",
    "POWERFLOW_PACKAGING_STANDARD.md"
)

# Iteration artifacts to archive if present.
$patterns = @(
    "dashboard_live_v7.2_max*.html",
    "dashboard_live_v7.2_committee.html",
    "dashboard_live_v7.2_final_PATCHED.html",
    "dashboard_data_normalizer_v*.py",
    "dashboard_contract_validator_v*.py",
    "run_dashboard_live_stack_v*.ps1",
    "DASHBOARD_V72_*REPORT.md",
    "DASHBOARD_V72_MAX_MISSION_SUITE.md",
    "P0_DASHBOARD_GO_NO_GO_CHECKLIST.md"
)

if (-not $KeepInstallerTools) {
    $patterns += @("_installer_tools")
}

$items = @()
foreach ($pattern in $patterns) {
    $found = @(Get-ChildItem -LiteralPath $core -Filter $pattern -Force -ErrorAction SilentlyContinue)
    foreach ($item in $found) {
        if ($keep -contains $item.Name) { continue }
        # Do not archive current final dashboard.
        if ($item.Name -eq "dashboard_live_v7.2_final.html") { continue }
        $items += $item
    }
}

# Deduplicate by FullName.
$items = @($items | Sort-Object FullName -Unique)

Write-Host "PowerFlow Dashboard Cleanup V2" -ForegroundColor Green
Write-Host "CorePath : $core"
Write-Host "Mode     : $(if ($DryRun) { 'DRY RUN' } else { 'ARCHIVE' })"
Write-Host "Found    : $($items.Count) artifact(s) to archive"

if ($items.Count -eq 0) {
    Write-Host "Nothing to archive." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Artifacts:" -ForegroundColor Cyan
foreach ($item in $items) {
    $kind = if ($item.PSIsContainer) { "DIR " } else { "FILE" }
    Write-Host (" - [{0}] {1}" -f $kind, $item.Name)
}

if ($DryRun) {
    Write-Host ""
    Write-Host "DryRun only. No file moved." -ForegroundColor Yellow
    Write-Host "Run without -DryRun to archive into: $backupDir"
    exit 0
}

Ensure-Dir $backupDir
foreach ($item in $items) {
    $dest = Join-Path $backupDir $item.Name
    if (Test-Path -LiteralPath $dest) {
        $dest = Join-Path $backupDir ("{0}_{1}" -f $stamp, $item.Name)
    }
    Move-Item -LiteralPath $item.FullName -Destination $dest -Force
}

Write-Host ""
Write-Host "Archived $($items.Count) artifact(s) to:" -ForegroundColor Green
Write-Host $backupDir
Write-Host ""
Write-Host "Canonical active files expected in Core:" -ForegroundColor Cyan
foreach ($name in $keep) {
    $path = Join-Path $core $name
    $status = if (Test-Path -LiteralPath $path) { "OK" } else { "missing" }
    Write-Host (" - {0}: {1}" -f $status, $name)
}
