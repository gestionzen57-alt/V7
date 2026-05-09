<#
PowerFlow V6 — SAFE_CORE_CLEANUP.ps1
Mission : nettoyer le dossier Core sans toucher les modules actifs.

Mode par défaut : DRY-RUN.
Rien n'est déplacé tant que -Apply n'est pas fourni.

Usage recommandé :
  powershell -ExecutionPolicy Bypass -File .\SAFE_CORE_CLEANUP.ps1
  powershell -ExecutionPolicy Bypass -File .\SAFE_CORE_CLEANUP.ps1 -Apply

Option :
  -MoveCockpitField : déplace cockpit_field.txt vers output\cockpit_field.txt
                       par défaut on le garde en racine pour ne pas casser le cockpit.
#>

param(
    [switch]$Apply,
    [switch]$MoveCockpitField
)

$ErrorActionPreference = "Stop"

$Root = Get-Location
$DryRun = -not $Apply

Write-Host "============================================================"
Write-Host "PowerFlow V6 — Safe Core Cleanup"
Write-Host "Root   : $Root"
Write-Host "Mode   : $(if ($DryRun) { 'DRY-RUN / simulation' } else { 'APPLY / déplacement réel' })"
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

    if (-not (Test-Path $Path)) {
        if ($DryRun) {
            Write-Host "[DRY] mkdir $Path"
        } else {
            New-Item -ItemType Directory -Path $Path | Out-Null
            Write-Host "[OK]  mkdir $Path"
        }
    }
}

function Move-OneFile {
    param(
        [System.IO.FileInfo]$File,
        [string]$DestinationDir
    )

    if (-not $File) { return }
    if (-not (Test-Path $File.FullName)) { return }

    Ensure-Dir $DestinationDir

    $DestPath = Join-Path $DestinationDir $File.Name

    if (Test-Path $DestPath) {
        $Base = [System.IO.Path]::GetFileNameWithoutExtension($File.Name)
        $Ext  = [System.IO.Path]::GetExtension($File.Name)
        $Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $DestPath = Join-Path $DestinationDir ("{0}_{1}{2}" -f $Base, $Stamp, $Ext)
    }

    if ($DryRun) {
        Write-Host "[DRY] move $($File.Name) -> $DestinationDir"
    } else {
        Move-Item -LiteralPath $File.FullName -Destination $DestPath
        Write-Host "[OK]  move $($File.Name) -> $DestinationDir"
    }
}

function Move-ByPattern {
    param(
        [string[]]$Patterns,
        [string]$DestinationDir
    )

    foreach ($Pattern in $Patterns) {
        Get-ChildItem -Path $Root -File -Filter $Pattern -ErrorAction SilentlyContinue |
            Where-Object { $_.DirectoryName -eq $Root.Path } |
            ForEach-Object { Move-OneFile -File $_ -DestinationDir $DestinationDir }
    }
}

foreach ($Dir in $Dirs) {
    Ensure-Dir $Dir
}

Write-Host ""
Write-Host "--- BACKUPS -> Archive\backups ---"
Move-ByPattern -Patterns @(
    "*_BACKUP_*.py",
    "*_BACKUP_before_*.py"
) -DestinationDir "Archive\backups"

Write-Host ""
Write-Host "--- PATCHES -> Archive\patches ---"
Move-ByPattern -Patterns @(
    "*.patch",
    "PATCH_NOTE_*.md",
    "PF_*_NOTES.md",
    "INSTALL_runtime_patch_*.bat",
    "TEST_REPORT_*.txt"
) -DestinationDir "Archive\patches"

Write-Host ""
Write-Host "--- REPORTS -> Archive\reports ---"
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
Write-Host "--- EXTRACTS -> Archive\extracts ---"
Move-ByPattern -Patterns @(
    "extract_*.json",
    "mini.json",
    "powerflow_extraction.json"
) -DestinationDir "Archive\extracts"

Write-Host ""
Write-Host "--- QUARANTINE -> Archive\quarantine ---"
foreach ($Name in @("Copy-Item", "py", "desktop.ini", "test.db")) {
    $Candidate = Get-Item -LiteralPath (Join-Path $Root $Name) -ErrorAction SilentlyContinue
    if ($Candidate -and -not $Candidate.PSIsContainer) {
        Move-OneFile -File $Candidate -DestinationDir "Archive\quarantine"
    }
}

Write-Host ""
Write-Host "--- COCKPIT FIELD ---"
$CockpitField = Get-Item -LiteralPath (Join-Path $Root "cockpit_field.txt") -ErrorAction SilentlyContinue
if ($CockpitField) {
    if ($MoveCockpitField) {
        Move-OneFile -File $CockpitField -DestinationDir "output"
    } else {
        Write-Host "[KEEP] cockpit_field.txt reste en racine"
    }
}

Write-Host ""
Write-Host "--- ACTIVE PYTHON MODULES ---"
Write-Host "[KEEP] Aucun .py actif n'a été déplacé par ce script."
Write-Host "[KEEP] capture_bridge.py reste intact."
Write-Host "[KEEP] powerflow.db reste intact."

Write-Host ""
Write-Host "============================================================"
if ($DryRun) {
    Write-Host "Simulation terminée. Pour appliquer :"
    Write-Host "powershell -ExecutionPolicy Bypass -File .\SAFE_CORE_CLEANUP.ps1 -Apply"
} else {
    Write-Host "Ménage appliqué. Prochaine validation :"
    Write-Host "python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt"
    Write-Host "python run_battlefield_radar_once.py --db powerflow.db --scan 240"
}
Write-Host "============================================================"
