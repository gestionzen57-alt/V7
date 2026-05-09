<#
APPLY_POWERFLOW_MEMORY_SERENE_20260506.ps1

Copie les fichiers mémoire PowerFlow dans PowerFlow_Workspace.

Usage:
powershell -ExecutionPolicy Bypass -File .\APPLY_POWERFLOW_MEMORY_SERENE_20260506.ps1 -SourceFolder ".\powerflow_memory_serene_20260506"

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
$todayDir = Join-Path $WorkspaceRoot "04_CHECKPOINTS\2026\2026-05\2026-05-06"

Ensure-Folder -Path (Join-Path $WorkspaceRoot "00_CURRENT")
Ensure-Folder -Path (Join-Path $WorkspaceRoot "02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE")
Ensure-Folder -Path $todayDir

Copy-Required -Source (Join-Path $src "CURRENT_STATE_POWERFLOW_V6_ACTIVE_20260506.md") -Dest (Join-Path $WorkspaceRoot "00_CURRENT\CURRENT_STATE.md")
Copy-Required -Source (Join-Path $src "CHECKPOINT_LATEST_POWERFLOW_V6_20260506.md") -Dest (Join-Path $WorkspaceRoot "00_CURRENT\CHECKPOINT_LATEST.md")
Copy-Required -Source (Join-Path $src "ROADMAP_ACTIVE_POWERFLOW_V6_20260506.md") -Dest (Join-Path $WorkspaceRoot "00_CURRENT\ROADMAP_ACTIVE.md")
Copy-Required -Source (Join-Path $src "LEXIQUE_UPDATE_QUEUE_POWERFLOW_V6_20260506.md") -Dest (Join-Path $WorkspaceRoot "00_CURRENT\LEXIQUE_UPDATE_QUEUE.md")
Copy-Required -Source (Join-Path $src "MEMORY_PROTOCOL_POWERFLOW_V6_20260506.md") -Dest (Join-Path $WorkspaceRoot "00_CURRENT\MEMORY_PROTOCOL_POWERFLOW_V6_20260506.md")

Copy-Required -Source (Join-Path $src "CHECKPOINT_LATEST_POWERFLOW_V6_20260506.md") -Dest (Join-Path $todayDir "CHECKPOINT_LATEST_POWERFLOW_V6_20260506.md")
Copy-Required -Source (Join-Path $src "PATCH_LEXIQUE_POWERFLOW_NODE_ENERGY_RELEASE_20260506.md") -Dest (Join-Path $WorkspaceRoot "02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE\PATCH_LEXIQUE_POWERFLOW_NODE_ENERGY_RELEASE_20260506.md")

Write-Host ""
Write-Host "DONE — PowerFlow memory updated."
Write-Host "Check 00_CURRENT."
if ($OpenExplorer) {
    Start-Process explorer.exe (Join-Path $WorkspaceRoot "00_CURRENT")
}
