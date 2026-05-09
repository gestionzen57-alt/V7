<#
SORT_POWERFLOW_DOCS_TO_WORKSPACE.ps1

Purpose:
Sort existing PowerFlow docs into the new PowerFlow_Workspace structure.

Default behavior:
- COPY files from Docs to PowerFlow_Workspace.
- Does NOT delete source files.
- Does NOT modify Core runtime.
- Creates a manifest CSV.
- Can be run multiple times.
- Use -Move only when you are sure.

Default paths:
SourceDocs:
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Docs

WorkspaceRoot:
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\PowerFlow_Workspace

Usage:
From C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT

Dry run:
powershell -ExecutionPolicy Bypass -File .\SORT_POWERFLOW_DOCS_TO_WORKSPACE.ps1 -WhatIf

Copy:
powershell -ExecutionPolicy Bypass -File .\SORT_POWERFLOW_DOCS_TO_WORKSPACE.ps1

Move:
powershell -ExecutionPolicy Bypass -File .\SORT_POWERFLOW_DOCS_TO_WORKSPACE.ps1 -Move

Copy and open workspace:
powershell -ExecutionPolicy Bypass -File .\SORT_POWERFLOW_DOCS_TO_WORKSPACE.ps1 -OpenExplorer

Important:
This script uses filename rules. It will not understand file contents.
Review the manifest after execution.
#>

param(
    [string]$SourceDocs = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Docs",
    [string]$WorkspaceRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\PowerFlow_Workspace",
    [switch]$Move,
    [switch]$OpenExplorer
)

$ErrorActionPreference = "Stop"

function Ensure-Folder {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "[CREATE] $Path"
    }
}

function Get-DatePathFromName {
    param([string]$Name)

    # Finds YYYY-MM-DD in filename.
    if ($Name -match '(20\d{2})-(\d{2})-(\d{2})') {
        return @{
            Year = $Matches[1]
            Month = "$($Matches[1])-$($Matches[2])"
            Day = "$($Matches[1])-$($Matches[2])-$($Matches[3])"
        }
    }

    # Finds YYYYMMDD in filename.
    if ($Name -match '(20\d{2})(\d{2})(\d{2})') {
        return @{
            Year = $Matches[1]
            Month = "$($Matches[1])-$($Matches[2])"
            Day = "$($Matches[1])-$($Matches[2])-$($Matches[3])"
        }
    }

    # Fallback: current known active date for this consolidation.
    return @{
        Year = "2026"
        Month = "2026-05"
        Day = "2026-05-05"
    }
}

function Get-UniqueDestination {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $Path
    }

    $dir = Split-Path -Parent $Path
    $base = [System.IO.Path]::GetFileNameWithoutExtension($Path)
    $ext = [System.IO.Path]::GetExtension($Path)

    $i = 1
    do {
        $candidate = Join-Path $dir ("{0}__DUP{1}{2}" -f $base, $i, $ext)
        $i++
    } while (Test-Path -LiteralPath $candidate)

    return $candidate
}

function Get-TargetRelativePath {
    param([string]$FileName)

    $n = $FileName.ToUpperInvariant()
    $date = Get-DatePathFromName -Name $FileName

    # Current / active truth files.
    if ($n -match 'CURRENT_STATE') {
        return "00_CURRENT"
    }
    if ($n -match 'ROADMAP') {
        return "00_CURRENT"
    }
    if ($n -match 'NEXT_ACTION') {
        return "00_CURRENT"
    }

    # Doctrine / lexique / manifeste / architecture active.
    if ($n -match 'DOCTRINE') {
        return "02_DOCS_ACTIVE\DOCTRINE"
    }
    if ($n -match 'LEXIQUE|GRAMMAIRE') {
        return "02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE"
    }
    if ($n -match 'MANIFESTE|REJETS') {
        return "02_DOCS_ACTIVE\MANIFESTE"
    }
    if ($n -match 'CARTOGRAPHIE|ARCHITECTURE') {
        return "02_DOCS_ACTIVE\ARCHITECTURE"
    }
    if ($n -match 'POWERFLOW_AGENT_SERVICE_REGISTER|IA_COLLABORATION|MULTI-IA|MULTI_IA') {
        return "02_DOCS_ACTIVE\IA_COLLABORATION"
    }

    # Checkpoints.
    if ($n -match '^CHECKPOINT|CHECKPOINT_') {
        return "04_CHECKPOINTS\$($date.Year)\$($date.Month)\$($date.Day)"
    }

    # Reports.
    if ($n -match '^RAPPORT|^REPORT') {
        return "03_REPORTS\$($date.Year)\$($date.Month)\$($date.Day)"
    }

    # Missions.
    if ($n -match '^MISSION') {
        if ($n -match 'DONE|TERMINE|FINI|COMPLET') {
            return "05_MISSIONS\MISSION_DONE"
        }
        return "05_MISSIONS\MISSION_ACTIVE"
    }

    # Specs.
    if ($n -match '^SPEC|_SPEC_|SPEC_') {
        return "07_SPECS\SPECS_ACTIVE"
    }

    # Patches.
    if ($n -match '^PATCH') {
        return "08_PATCHES\PATCH_DONE"
    }

    # Labs / notes / scenes.
    if ($n -match '^LAB_|LAB_|LIVE_005|SEQUENCE|SCENE|KINEMATICS|NOTES_NEXT_LABS') {
        return "06_LABS\SCENES_REELLES"
    }

    # Core inventory and maps.
    if ($n -match 'CORE_INVENTORY|CORE_CLEANUP|MODULE_REGISTRY|DEPENDENCIES') {
        return "09_CORE_MAP\CORE_INVENTORY"
    }

    # Old docs.
    if ($n -match 'README|OLD|ANCIEN|LEGACY') {
        return "90_LEGACY\DOCS_LEGACY"
    }

    # Fallback.
    return "01_INBOX_TO_CLASSIFY\FROM_TRADER"
}

function Copy-ToCurrentAlias {
    param(
        [string]$SourcePath,
        [string]$FileName,
        [string]$WorkspaceRoot
    )

    $n = $FileName.ToUpperInvariant()
    $currentDir = Join-Path $WorkspaceRoot "00_CURRENT"

    if ($n -match 'CURRENT_STATE') {
        $dest = Join-Path $currentDir "CURRENT_STATE.md"
        Copy-Item -LiteralPath $SourcePath -Destination $dest -Force
        Write-Host "[ALIAS]   00_CURRENT\CURRENT_STATE.md"
    }

    if ($n -match '^CHECKPOINT|CHECKPOINT_') {
        # Prefer the most recent visible checkpoint files. This may be overwritten by later sorted files.
        $dest = Join-Path $currentDir "CHECKPOINT_LATEST.md"
        Copy-Item -LiteralPath $SourcePath -Destination $dest -Force
        Write-Host "[ALIAS]   00_CURRENT\CHECKPOINT_LATEST.md"
    }

    if ($n -match 'ROADMAP') {
        $dest = Join-Path $currentDir "ROADMAP_ACTIVE.md"
        Copy-Item -LiteralPath $SourcePath -Destination $dest -Force
        Write-Host "[ALIAS]   00_CURRENT\ROADMAP_ACTIVE.md"
    }
}

if (-not (Test-Path -LiteralPath $SourceDocs)) {
    throw "SourceDocs not found: $SourceDocs"
}

if (-not (Test-Path -LiteralPath $WorkspaceRoot)) {
    throw "WorkspaceRoot not found. Run CREATE_POWERFLOW_WORKSPACE_STRUCTURE.ps1 first: $WorkspaceRoot"
}

Write-Host ""
Write-Host "==============================================="
Write-Host " POWERFLOW DOCS SORTER"
Write-Host "==============================================="
Write-Host "SourceDocs    : $SourceDocs"
Write-Host "WorkspaceRoot : $WorkspaceRoot"
Write-Host "Mode          : $(if ($Move) { 'MOVE' } else { 'COPY' })"
Write-Host ""

$manifestDir = Join-Path $WorkspaceRoot "09_CORE_MAP\CORE_INVENTORY"
Ensure-Folder -Path $manifestDir

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$manifestPath = Join-Path $manifestDir ("DOCS_SORT_MANIFEST_{0}.csv" -f $timestamp)

$rows = New-Object System.Collections.Generic.List[Object]

$files = Get-ChildItem -LiteralPath $SourceDocs -File | Sort-Object Name

foreach ($file in $files) {
    $relativeTarget = Get-TargetRelativePath -FileName $file.Name
    $targetDir = Join-Path $WorkspaceRoot $relativeTarget
    Ensure-Folder -Path $targetDir

    $targetPath = Join-Path $targetDir $file.Name
    $finalTargetPath = Get-UniqueDestination -Path $targetPath

    if ($Move) {
        Move-Item -LiteralPath $file.FullName -Destination $finalTargetPath
        $action = "MOVED"
    } else {
        Copy-Item -LiteralPath $file.FullName -Destination $finalTargetPath
        $action = "COPIED"
    }

    Write-Host ("[{0}] {1} -> {2}" -f $action, $file.Name, $relativeTarget)

    # Create quick aliases in 00_CURRENT for current/checkpoint/roadmap.
    try {
        Copy-ToCurrentAlias -SourcePath $finalTargetPath -FileName $file.Name -WorkspaceRoot $WorkspaceRoot
    } catch {
        Write-Host "[WARN] Alias failed for $($file.Name): $($_.Exception.Message)"
    }

    $rows.Add([PSCustomObject]@{
        Action = $action
        Source = $file.FullName
        Target = $finalTargetPath
        Bucket = $relativeTarget
        SizeBytes = $file.Length
        LastWriteTime = $file.LastWriteTime
    })
}

$rows | Export-Csv -Path $manifestPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "==============================================="
Write-Host " DONE"
Write-Host "==============================================="
Write-Host "Files processed : $($rows.Count)"
Write-Host "Manifest        : $manifestPath"
Write-Host ""

Write-Host "Recommended checks:"
Write-Host "1. Open 00_CURRENT\CURRENT_STATE.md"
Write-Host "2. Open 00_CURRENT\CHECKPOINT_LATEST.md"
Write-Host "3. Open 09_CORE_MAP\CORE_INVENTORY\DOCS_SORT_MANIFEST_*.csv"
Write-Host ""

if ($OpenExplorer) {
    Start-Process explorer.exe $WorkspaceRoot
}
