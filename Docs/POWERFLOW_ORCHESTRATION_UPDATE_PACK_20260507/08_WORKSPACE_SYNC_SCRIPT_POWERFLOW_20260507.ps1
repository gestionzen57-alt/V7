<#
APPLY_POWERFLOW_ORCHESTRATION_UPDATE_20260507.ps1

Copie les fichiers du pack dans PowerFlow_Workspace.

Usage depuis C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT :

powershell -ExecutionPolicy Bypass -File .\POWERFLOW_ORCHESTRATION_UPDATE_PACK_20260507\08_WORKSPACE_SYNC_SCRIPT_POWERFLOW_20260507.ps1 -SourceFolder .\POWERFLOW_ORCHESTRATION_UPDATE_PACK_20260507 -OpenExplorer

Safe:
- ne touche pas Core
- ne touche pas powerflow.db
- copie seulement des fichiers .md
#>

param(
    [string]$WorkspaceRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\PowerFlow_Workspace",
    [string]$SourceFolder = ".",
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

function Copy-Required {
    param([string]$Source, [string]$Dest)
    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Host "[MISSING] $Source"
        return
    }
    Ensure-Folder -Path (Split-Path -Parent $Dest)
    Copy-Item -LiteralPath $Source -Destination $Dest -Force
    Write-Host "[COPY] $Source -> $Dest"
}

$src = Resolve-Path -LiteralPath $SourceFolder

$currentDir = Join-Path $WorkspaceRoot "00_CURRENT"
$lexiqueDir = Join-Path $WorkspaceRoot "02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE"
$checkpointDir = Join-Path $WorkspaceRoot "04_CHECKPOINTS\2026\2026-05\2026-05-07"
$missionDir = Join-Path $WorkspaceRoot "05_MISSIONS\MISSION_ACTIVE"
$reportDir = Join-Path $WorkspaceRoot "03_REPORTS\2026\2026-05\2026-05-07"

Ensure-Folder $currentDir
Ensure-Folder $lexiqueDir
Ensure-Folder $checkpointDir
Ensure-Folder $missionDir
Ensure-Folder $reportDir

Copy-Required (Join-Path $src "00_CURRENT_STATE_POWERFLOW_V6_ORCHESTRATION_20260507.md") (Join-Path $currentDir "CURRENT_STATE.md")
Copy-Required (Join-Path $src "01_CHECKPOINT_LATEST_POWERFLOW_V6_ORCHESTRATION_20260507.md") (Join-Path $currentDir "CHECKPOINT_LATEST.md")
Copy-Required (Join-Path $src "07_ROADMAP_ACTIVE_POWERFLOW_V6_20260507.md") (Join-Path $currentDir "ROADMAP_ACTIVE.md")

Copy-Required (Join-Path $src "01_CHECKPOINT_LATEST_POWERFLOW_V6_ORCHESTRATION_20260507.md") (Join-Path $checkpointDir "CHECKPOINT_LATEST_POWERFLOW_V6_ORCHESTRATION_20260507.md")
Copy-Required (Join-Path $src "02_REGISTRE_BRIQUES_DEPENDANCES_POWERFLOW_V6_20260507.md") (Join-Path $currentDir "REGISTRE_BRIQUES_DEPENDANCES_POWERFLOW_V6.md")
Copy-Required (Join-Path $src "03_PATCH_LEXIQUE_CONSOLIDE_POWERFLOW_V6_20260507.md") (Join-Path $lexiqueDir "PATCH_LEXIQUE_CONSOLIDE_POWERFLOW_V6_20260507.md")
Copy-Required (Join-Path $src "04_RAPPORT_CRITIQUE_SEVERE_POWERFLOW_V6_20260507.md") (Join-Path $reportDir "RAPPORT_CRITIQUE_SEVERE_POWERFLOW_V6_20260507.md")
Copy-Required (Join-Path $src "05_MISSION_P1_2_RELATIONAL_GRAVITY_BRIDGE_GUARD_20260507.md") (Join-Path $missionDir "MISSION_P1_2_RELATIONAL_GRAVITY_BRIDGE_GUARD_20260507.md")
Copy-Required (Join-Path $src "06_MISSION_RUNTIME_AUDIT_KINEMATICS_ENERGY_GRAVITY_20260507.md") (Join-Path $missionDir "MISSION_RUNTIME_AUDIT_KINEMATICS_ENERGY_GRAVITY_20260507.md")

Write-Host ""
Write-Host "DONE - PowerFlow Orchestration Update applied."
Write-Host "Check:"
Write-Host "  $currentDir"
Write-Host "  $lexiqueDir"
Write-Host "  $missionDir"

if ($OpenExplorer) {
    Start-Process -FilePath "explorer.exe" -ArgumentList $currentDir
}
