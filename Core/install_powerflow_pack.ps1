<#
PowerFlow V7.2 - Pack Installer
Role: install a delivered ZIP without polluting Core.

Usage:
  .\install_powerflow_pack.ps1 -ZipPath .\POWERFLOW_PACK.zip -CorePath . -RunDashboardStack

Principles:
  - Extracts into .powerflow_packs/<zip-name>/
  - Backs up overwritten Core files into backups/packs/<timestamp>/
  - Copies only runtime-approved files to Core
  - Archives docs into docs/packs/<zip-name>/
  - Leaves old versions untouched unless -ArchiveOldDashboardArtifacts is set
  - Never touches powerflow.db or capture_bridge.py
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ZipPath,

    [string]$CorePath = ".",

    [switch]$RunDashboardStack,
    [switch]$Serve,
    [switch]$ArchiveOldDashboardArtifacts,
    [string]$HtmlTarget = "dashboard_live_v7.2_final.html"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "[PowerFlow Pack] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Ensure-Dir($path) { if (!(Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null } }
function Copy-WithBackup($src, $dst, $backupDir) {
    if (Test-Path $dst) {
        Ensure-Dir $backupDir
        Copy-Item $dst (Join-Path $backupDir (Split-Path $dst -Leaf)) -Force
    }
    Copy-Item $src $dst -Force
}

$CorePath = (Resolve-Path $CorePath).Path
if (!(Test-Path $ZipPath)) { throw "ZIP not found: $ZipPath" }
$ZipPath = (Resolve-Path $ZipPath).Path

$zipName = [IO.Path]::GetFileNameWithoutExtension($ZipPath)
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$packsRoot = Join-Path $CorePath ".powerflow_packs"
$extractDir = Join-Path $packsRoot $zipName
$backupDir = Join-Path $CorePath "backups\packs\$timestamp"
$docsDir = Join-Path $CorePath "docs\packs\$zipName"
$toolsDir = Join-Path $CorePath "tools\dashboard"

Write-Step "Core: $CorePath"
Write-Step "ZIP : $ZipPath"
Ensure-Dir $packsRoot
Ensure-Dir $backupDir
Ensure-Dir $docsDir
Ensure-Dir $toolsDir

if (Test-Path $extractDir) {
    $old = "${extractDir}_old_$timestamp"
    Write-Warn "Existing extract dir found. Moving to $old"
    Move-Item $extractDir $old
}

Write-Step "Extracting to $extractDir"
Expand-Archive -Path $ZipPath -DestinationPath $extractDir -Force

# Optional cleanup before deploy.
if ($ArchiveOldDashboardArtifacts) {
    $archiveDir = Join-Path $CorePath "backups\dashboard_artifacts_$timestamp"
    Ensure-Dir $archiveDir
    $patterns = @(
        "dashboard_live_v7.2_max*.html",
        "dashboard_live_v7.2_committee.html",
        "dashboard_contract_validator*.py",
        "dashboard_data_normalizer*.py",
        "dashboard_output_coverage_doctor.py",
        "run_dashboard_live_stack*.ps1",
        "DASHBOARD_V72_*REPORT.md"
    )
    foreach ($p in $patterns) {
        Get-ChildItem -Path $CorePath -Filter $p -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Name -ne $HtmlTarget) {
                Move-Item $_.FullName (Join-Path $archiveDir $_.Name) -Force
            }
        }
    }
    Write-Step "Archived old dashboard artifacts to $archiveDir"
}

# Deploy policy: runtime scripts to Core, docs to docs/packs, dashboard tools to tools/dashboard.
$allFiles = Get-ChildItem -Path $extractDir -Recurse -File
$deployed = @()
$documented = @()
$toolCopied = @()

foreach ($f in $allFiles) {
    $name = $f.Name

    if ($name -match '^dashboard_live_v7\.2_.*\.html$') {
        $dst = Join-Path $CorePath $HtmlTarget
        Copy-WithBackup $f.FullName $dst $backupDir
        $deployed += "$name -> $HtmlTarget"
        continue
    }

    if ($name -match '^run_dashboard_live_stack.*\.ps1$') {
        $dst = Join-Path $CorePath "run_dashboard_live_stack.ps1"
        Copy-WithBackup $f.FullName $dst $backupDir
        $deployed += "$name -> run_dashboard_live_stack.ps1"
        continue
    }

    if ($name -match '^dashboard_(contract_validator|data_normalizer|output_coverage_doctor).*\.py$') {
        $dstTool = Join-Path $toolsDir $name
        Copy-Item $f.FullName $dstTool -Force
        $toolCopied += "$name -> tools/dashboard/$name"

        # Also copy latest operational names expected by wrappers if applicable.
        if ($name -match 'normalizer') {
            Copy-WithBackup $f.FullName (Join-Path $CorePath "dashboard_data_normalizer.py") $backupDir
            $deployed += "$name -> dashboard_data_normalizer.py"
        } elseif ($name -match 'validator') {
            Copy-WithBackup $f.FullName (Join-Path $CorePath "dashboard_contract_validator.py") $backupDir
            $deployed += "$name -> dashboard_contract_validator.py"
        } elseif ($name -match 'doctor') {
            Copy-WithBackup $f.FullName (Join-Path $CorePath "dashboard_output_coverage_doctor.py") $backupDir
            $deployed += "$name -> dashboard_output_coverage_doctor.py"
        }
        continue
    }

    if ($name -match '\.(md|txt)$') {
        Copy-Item $f.FullName (Join-Path $docsDir $name) -Force
        $documented += "$name -> docs/packs/$zipName/$name"
        continue
    }

    if ($name -match '\.(json)$') {
        Copy-Item $f.FullName (Join-Path $docsDir $name) -Force
        $documented += "$name -> docs/packs/$zipName/$name"
        continue
    }
}

Write-Step "Deploy summary"
Write-Host "Deployed runtime files:" -ForegroundColor Cyan
if ($deployed.Count -eq 0) { Write-Host "  none" } else { $deployed | ForEach-Object { Write-Host "  $_" } }
Write-Host "Copied tool archive:" -ForegroundColor Cyan
if ($toolCopied.Count -eq 0) { Write-Host "  none" } else { $toolCopied | ForEach-Object { Write-Host "  $_" } }
Write-Host "Archived docs/config:" -ForegroundColor Cyan
if ($documented.Count -eq 0) { Write-Host "  none" } else { $documented | ForEach-Object { Write-Host "  $_" } }
Write-Host "Backup dir: $backupDir" -ForegroundColor DarkCyan

if ($RunDashboardStack) {
    $runner = Join-Path $CorePath "run_dashboard_live_stack.ps1"
    if (!(Test-Path $runner)) { throw "Dashboard stack runner not found after deploy: $runner" }
    Write-Step "Running dashboard stack Normalize + Validate + Doctor"
    & $runner -Root $CorePath -Html (Join-Path $CorePath $HtmlTarget) -Normalize -Validate -Doctor
}

if ($Serve) {
    $runner = Join-Path $CorePath "run_dashboard_live_stack.ps1"
    if (!(Test-Path $runner)) { throw "Dashboard stack runner not found after deploy: $runner" }
    Write-Step "Serving dashboard"
    & $runner -Root $CorePath -Html (Join-Path $CorePath $HtmlTarget) -Serve
}

Write-Step "Done"
