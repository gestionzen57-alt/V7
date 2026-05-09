param(
    [string]$WorkspaceRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\PowerFlow_Workspace",
    [string]$SourceFolder = ".\powerflow_memory_rg_guard_20260506",
    [switch]$OpenExplorer
)

$ErrorActionPreference = "Stop"

$CurrentDir = Join-Path $WorkspaceRoot "00_CURRENT"
$LexiqueDir = Join-Path $WorkspaceRoot "02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE"
$CheckpointDir = Join-Path $WorkspaceRoot "04_CHECKPOINTS\2026\2026-05\2026-05-06"
$ReportsDir = Join-Path $WorkspaceRoot "04_CHECKPOINTS\2026\2026-05\2026-05-06"

New-Item -ItemType Directory -Force $CurrentDir | Out-Null
New-Item -ItemType Directory -Force $LexiqueDir | Out-Null
New-Item -ItemType Directory -Force $CheckpointDir | Out-Null
New-Item -ItemType Directory -Force $ReportsDir | Out-Null

Copy-Item (Join-Path $SourceFolder "CURRENT_STATE_POWERFLOW_V6_ACTIVE_20260506_RG_GUARD.md") (Join-Path $CurrentDir "CURRENT_STATE.md") -Force
Copy-Item (Join-Path $SourceFolder "CHECKPOINT_LATEST_POWERFLOW_V6_20260506_RG_GUARD.md") (Join-Path $CurrentDir "CHECKPOINT_LATEST.md") -Force
Copy-Item (Join-Path $SourceFolder "ROADMAP_ACTIVE_POWERFLOW_V6_20260506_RG_GUARD.md") (Join-Path $CurrentDir "ROADMAP_ACTIVE.md") -Force
Copy-Item (Join-Path $SourceFolder "LEXIQUE_UPDATE_QUEUE_POWERFLOW_V6_20260506_RG_GUARD.md") (Join-Path $CurrentDir "LEXIQUE_UPDATE_QUEUE.md") -Force

Copy-Item (Join-Path $SourceFolder "CHECKPOINT_LATEST_POWERFLOW_V6_20260506_RG_GUARD.md") (Join-Path $CheckpointDir "CHECKPOINT_RELATIONAL_GRAVITY_GUARD_20260506.md") -Force
Copy-Item (Join-Path $SourceFolder "RAPPORT_ARCHITECTE_RELATIONAL_GRAVITY_GUARD_20260506.md") (Join-Path $ReportsDir "RAPPORT_ARCHITECTE_RELATIONAL_GRAVITY_GUARD_20260506.md") -Force
Copy-Item (Join-Path $SourceFolder "LEXIQUE_UPDATE_QUEUE_POWERFLOW_V6_20260506_RG_GUARD.md") (Join-Path $LexiqueDir "LEXIQUE_UPDATE_QUEUE_RELATIONAL_GRAVITY_GUARD_20260506.md") -Force

Write-Host "DONE - PowerFlow workspace current state updated."
Write-Host "Current:"
Write-Host "  $(Join-Path $CurrentDir 'CURRENT_STATE.md')"
Write-Host "  $(Join-Path $CurrentDir 'CHECKPOINT_LATEST.md')"
Write-Host "  $(Join-Path $CurrentDir 'ROADMAP_ACTIVE.md')"
Write-Host "  $(Join-Path $CurrentDir 'LEXIQUE_UPDATE_QUEUE.md')"
Write-Host "Checkpoint:"
Write-Host "  $(Join-Path $CheckpointDir 'CHECKPOINT_RELATIONAL_GRAVITY_GUARD_20260506.md')"

if ($OpenExplorer) {
    explorer.exe $WorkspaceRoot
}
