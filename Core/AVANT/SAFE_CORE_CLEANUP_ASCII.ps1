<#
PowerFlow V6 - SAFE_CORE_CLEANUP_ASCII.ps1
Mission: clean Core without moving active Python modules.

Default mode: DRY RUN.
No file is moved unless -Apply is provided.

Usage:
  powershell -ExecutionPolicy Bypass -File .\SAFE_CORE_CLEANUP_ASCII.ps1
  powershell -ExecutionPolicy Bypass -File .\SAFE_CORE_CLEANUP_ASCII.ps1 -Apply

Option:
  -MoveCockpitField moves cockpit_field.txt to output\cockpit_field.txt.
  Default: keep cockpit_field.txt in root.
#>

param(
    [switch]$Apply,
    [switch]$MoveCockpitField
)

$ErrorActionPreference = "Stop"

$RootPath = (Get-Location).Path
$DryRun = -not $Apply

Write-Host "============================================================"
Write-Host "PowerFlow V6 - Safe Core Cleanup ASCII"
Write-Host ("Root   : " + $RootPath)
if ($DryRun) {
    Write-Host "Mode   : DRY RUN / simulation"
} else {
    Write-Host "Mode   : APPLY / real move"
}
Write-Host "============================================================"

$Dirs = @(
    "Archive",
    "Archive\backups",
    "Archive\patches",
    "Archive\reports",
    "Archive\extracts",
    "Archive\quarantine",
    "docs",
    "output"
)

function Ensure-Dir {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        if ($script:DryRun) {
            Write-Host ("DRY mkdir " + $Path)
        } else {
            New-Item -ItemType Directory -Path $Path | Out-Null
            Write-Host ("OK  mkdir " + $Path)
        }
    }
}

function Move-OneFile {
    param(
        [System.IO.FileInfo]$File,
        [string]$DestinationDir
    )

    if ($null -eq $File) { return }
    if (-not (Test-Path -LiteralPath $File.FullName)) { return }

    Ensure-Dir $DestinationDir

    $DestPath = Join-Path $DestinationDir $File.Name

    if (Test-Path -LiteralPath $DestPath) {
        $Base = [System.IO.Path]::GetFileNameWithoutExtension($File.Name)
        $Ext  = [System.IO.Path]::GetExtension($File.Name)
        $Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $NewName = ("{0}_{1}{2}" -f $Base, $Stamp, $Ext)
        $DestPath = Join-Path $DestinationDir $NewName
    }

    if ($script:DryRun) {
        Write-Host ("DRY move " + $File.Name + " -> " + $DestinationDir)
    } else {
        Move-Item -LiteralPath $File.FullName -Destination $DestPath
        Write-Host ("OK  move " + $File.Name + " -> " + $DestinationDir)
    }
}

function Move-ByPattern {
    param(
        [string[]]$Patterns,
        [string]$DestinationDir
    )

    foreach ($Pattern in $Patterns) {
        Get-ChildItem -Path $script:RootPath -File -Filter $Pattern -ErrorAction SilentlyContinue |
            Where-Object { $_.DirectoryName -eq $script:RootPath } |
            ForEach-Object { Move-OneFile -File $_ -DestinationDir $DestinationDir }
    }
}

foreach ($Dir in $Dirs) {
    Ensure-Dir $Dir
}

Write-Host ""
Write-Host "--- BACKUPS to Archive\backups ---"
Move-ByPattern -Patterns @(
    "*_BACKUP_*.py",
    "*_BACKUP_before_*.py"
) -DestinationDir "Archive\backups"

Write-Host ""
Write-Host "--- PATCHES to Archive\patches ---"
Move-ByPattern -Patterns @(
    "*.patch",
    "PATCH_NOTE_*.md",
    "PF_*_NOTES.md",
    "INSTALL_runtime_patch_*.bat",
    "TEST_REPORT_*.txt"
) -DestinationDir "Archive\patches"

Write-Host ""
Write-Host "--- REPORTS to Archive\reports ---"
Move-ByPattern -Patterns @(
    "*_report.txt",
    "*_test_output.txt",
    "battlefield_map_day.txt",
    "battlefield_map_recent.txt",
    "powerflow_zone_brief*.txt",
    "session_zone_report.txt",
    "zone_evolution_report*.txt",
    "fractal_zone_stack_report.txt"
) -DestinationDir "Archive\reports"

Write-Host ""
Write-Host "--- EXTRACTS to Archive\extracts ---"
Move-ByPattern -Patterns @(
    "extract_*.json",
    "mini.json",
    "powerflow_extraction.json"
) -DestinationDir "Archive\extracts"

Write-Host ""
Write-Host "--- QUARANTINE to Archive\quarantine ---"
foreach ($Name in @("Copy-Item", "py", "desktop.ini", "test.db")) {
    $CandidatePath = Join-Path $script:RootPath $Name
    $Candidate = Get-Item -LiteralPath $CandidatePath -ErrorAction SilentlyContinue
    if ($Candidate -and -not $Candidate.PSIsContainer) {
        Move-OneFile -File $Candidate -DestinationDir "Archive\quarantine"
    }
}

Write-Host ""
Write-Host "--- COCKPIT FIELD ---"
$CockpitFieldPath = Join-Path $script:RootPath "cockpit_field.txt"
$CockpitField = Get-Item -LiteralPath $CockpitFieldPath -ErrorAction SilentlyContinue
if ($CockpitField) {
    if ($MoveCockpitField) {
        Move-OneFile -File $CockpitField -DestinationDir "output"
    } else {
        Write-Host "KEEP cockpit_field.txt stays in root"
    }
}

Write-Host ""
Write-Host "--- ACTIVE PYTHON MODULES ---"
Write-Host "KEEP no active .py module was moved by this script."
Write-Host "KEEP capture_bridge.py stays intact."
Write-Host "KEEP powerflow.db stays intact."

Write-Host ""
Write-Host "============================================================"
if ($DryRun) {
    Write-Host "Simulation complete. To apply:"
    Write-Host "powershell -ExecutionPolicy Bypass -File .\SAFE_CORE_CLEANUP_ASCII.ps1 -Apply"
} else {
    Write-Host "Cleanup applied. Next validation:"
    Write-Host "python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt"
    Write-Host "python run_battlefield_radar_once.py --db powerflow.db --scan 240"
}
Write-Host "============================================================"
