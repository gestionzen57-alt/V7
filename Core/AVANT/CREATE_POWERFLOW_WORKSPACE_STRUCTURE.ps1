<# 
CREATE_POWERFLOW_WORKSPACE_STRUCTURE.ps1

Purpose:
Create a clean PowerFlow workspace structure next to Core,
without moving, deleting, or modifying runtime files.

Default target:
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\PowerFlow_Workspace

Usage:
powershell -ExecutionPolicy Bypass -File .\CREATE_POWERFLOW_WORKSPACE_STRUCTURE.ps1

Optional:
powershell -ExecutionPolicy Bypass -File .\CREATE_POWERFLOW_WORKSPACE_STRUCTURE.ps1 -OpenExplorer
powershell -ExecutionPolicy Bypass -File .\CREATE_POWERFLOW_WORKSPACE_STRUCTURE.ps1 -WorkspaceRoot "D:\PowerFlow_Workspace"

Safe:
- Does not move Core files.
- Does not modify powerflow.db.
- Does not delete anything.
- Can be run multiple times.
#>

param(
    [string]$CorePath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core",
    [string]$WorkspaceRoot = "",
    [switch]$NoStarterFiles,
    [switch]$OpenExplorer
)

$ErrorActionPreference = "Stop"

function New-Folder {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "[CREATED] $Path"
    } else {
        Write-Host "[OK]      $Path"
    }
}

function Write-TextFileIfMissing {
    param(
        [string]$Path,
        [string]$Content
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        $parent = Split-Path -Parent $Path
        if (-not (Test-Path -LiteralPath $parent)) {
            New-Folder -Path $parent
        }
        Set-Content -Path $Path -Value $Content -Encoding UTF8
        Write-Host "[FILE]    $Path"
    } else {
        Write-Host "[KEEP]    $Path"
    }
}

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    if (Test-Path -LiteralPath $CorePath) {
        $projectRoot = Split-Path -Parent $CorePath
        $WorkspaceRoot = Join-Path $projectRoot "PowerFlow_Workspace"
    } else {
        $WorkspaceRoot = Join-Path (Get-Location) "PowerFlow_Workspace"
    }
}

Write-Host ""
Write-Host "==============================================="
Write-Host " POWERFLOW WORKSPACE STRUCTURE CREATOR"
Write-Host "==============================================="
Write-Host "CorePath      : $CorePath"
Write-Host "WorkspaceRoot : $WorkspaceRoot"
Write-Host ""

$folders = @(
    "00_CURRENT",
    "01_INBOX_TO_CLASSIFY",
    "01_INBOX_TO_CLASSIFY\FROM_GPT_MAIN",
    "01_INBOX_TO_CLASSIFY\FROM_GPT_CODE",
    "01_INBOX_TO_CLASSIFY\FROM_CLAUDE",
    "01_INBOX_TO_CLASSIFY\FROM_PERPLEXITY",
    "01_INBOX_TO_CLASSIFY\FROM_GEMINI_AUDIO",
    "01_INBOX_TO_CLASSIFY\FROM_TRADER",

    "02_DOCS_ACTIVE",
    "02_DOCS_ACTIVE\DOCTRINE",
    "02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE",
    "02_DOCS_ACTIVE\MANIFESTE",
    "02_DOCS_ACTIVE\ARCHITECTURE",
    "02_DOCS_ACTIVE\IA_COLLABORATION",

    "03_REPORTS",
    "03_REPORTS\2026",
    "03_REPORTS\2026\2026-05",
    "03_REPORTS\2026\2026-05\2026-05-05",

    "04_CHECKPOINTS",
    "04_CHECKPOINTS\2026",
    "04_CHECKPOINTS\2026\2026-05",
    "04_CHECKPOINTS\2026\2026-05\2026-05-05",

    "05_MISSIONS",
    "05_MISSIONS\MISSION_QUEUE",
    "05_MISSIONS\MISSION_ACTIVE",
    "05_MISSIONS\MISSION_DONE",
    "05_MISSIONS\MISSION_ABORTED",

    "06_LABS",
    "06_LABS\VISION_NOTES",
    "06_LABS\CAPTURES",
    "06_LABS\AUDIO_NOTES",
    "06_LABS\SCENES_REELLES",
    "06_LABS\SIGNATURES_A_TESTER",

    "07_SPECS",
    "07_SPECS\SPECS_ACTIVE",
    "07_SPECS\SPECS_DRAFT",
    "07_SPECS\SPECS_DONE",

    "08_PATCHES",
    "08_PATCHES\PATCH_QUEUE",
    "08_PATCHES\PATCH_ACTIVE",
    "08_PATCHES\PATCH_DONE",
    "08_PATCHES\PATCH_REJECTED",

    "09_CORE_MAP",
    "09_CORE_MAP\CORE_INVENTORY",
    "09_CORE_MAP\CORE_CLEANUP",
    "09_CORE_MAP\MODULE_REGISTRY",
    "09_CORE_MAP\DEPENDENCIES",

    "10_OUTPUTS_LIVE",
    "10_OUTPUTS_LIVE\AGENTIC_STATE",
    "10_OUTPUTS_LIVE\COCKPIT_STATE",
    "10_OUTPUTS_LIVE\TEMPORAL_NODE_STATE",
    "10_OUTPUTS_LIVE\TELEGRAM_DRYRUN",
    "10_OUTPUTS_LIVE\DB_VISION",
    "10_OUTPUTS_LIVE\FRESHNESS",
    "10_OUTPUTS_LIVE\FORCE_ACCELERATION",

    "90_LEGACY",
    "90_LEGACY\DOCS_LEGACY",
    "90_LEGACY\REPORTS_LEGACY",
    "90_LEGACY\OLD_README",
    "90_LEGACY\OLD_WORKFLOWS",

    "99_ARCHIVE",
    "99_ARCHIVE\BACKUPS",
    "99_ARCHIVE\OLD_PATCHES",
    "99_ARCHIVE\OLD_REPORTS",
    "99_ARCHIVE\OLD_EXPORTS"
)

New-Folder -Path $WorkspaceRoot

foreach ($folder in $folders) {
    New-Folder -Path (Join-Path $WorkspaceRoot $folder)
}

if (-not $NoStarterFiles) {
    $currentState = @"
# CURRENT_STATE.md

Status: ACTIVE SHORT TRUTH
Updated: 2026-05-05

PowerFlow = extension algorithmique de perception du trader.
Trader = centre vivant.
IA = partenaires specialises, pas autorites.
Documents = traces, pas lois.
M1 = microfilm scalping.
Temporal Nodes = centraux et alertables progressivement.

Current P0:
1. Stabiliser capture multi-timeframe.
2. Garder M1 / M5 / M15 / M30 / H1 live et coherents.
3. Auditer Temporal Nodes.
4. Produire / maintenir output/temporal_node_state.json.
5. Ajouter Telegram Node Mode.
6. Integrer LAB LIVE 005 dans lexique et roadmap.

Rule:
PowerFlow doit reduire la charge mentale du trader.
"@

    $checkpointLatest = @"
# CHECKPOINT_LATEST.md

Status: PLACEHOLDER
Updated: 2026-05-05

Dernier point connu:
LAB LIVE 005 termine.
Node V0.6 valide.
Node V0.7 necessaire.
P0 = stabiliser capture multi-timeframe.
P1 = force / speed / angle / acceleration / first_detachment.
P2 = Temporal Node V0.7 enrichi.

Next action:
Classer les rapports LAB LIVE 005 dans 03_REPORTS et 04_CHECKPOINTS.
"@

    $roadmapActive = @"
# ROADMAP_ACTIVE.md

P0:
- Stabiliser capture M1 / M5 / M15 / M30 / H1.
- check_tf_counts.py avant Lab.
- Temporal Node State read-only.
- Telegram Node Mode.

P1:
- pf_force_acceleration_probe.py
- angle_cluster
- tight_gravity_cluster
- first_detachment
- relative_freshness
- price_break_context

P2:
- Temporal Node V0.7
- next_watch enrichi
- capture_quality
- direction_conflict
"@

    $nextAction = @"
# NEXT_ACTION.md

1. Copier les 3 rapports LAB LIVE 005 dans:
   01_INBOX_TO_CLASSIFY\FROM_GPT_CODE

2. Puis classer:
   REPORT -> 03_REPORTS\2026\2026-05\2026-05-05
   CHECKPOINT -> 04_CHECKPOINTS\2026\2026-05\2026-05-05
   LEXIQUE -> 02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE

3. Mettre a jour:
   00_CURRENT\CURRENT_STATE.md
   00_CURRENT\CHECKPOINT_LATEST.md
   00_CURRENT\ROADMAP_ACTIVE.md
"@

    $inboxInstructions = @"
# INBOX RULES

Drop fast. Class later.

Filename format:
YYYYMMDD_HHMM__TYPE__SOURCE__TOPIC__STATUS.md

TYPE:
REPORT / CHECKPOINT / MISSION / AUDIT / SPEC / PATCH / LAB / VISION_NOTE / DECISION / ROADMAP / CURRENT_STATE

SOURCE:
GPT_MAIN / GPT_CODE / CLAUDE / PERPLEXITY / GEMINI / TRADER / SYSTEM

STATUS:
DRAFT / ACTIVE / DONE / SUPERSEDED / LEGACY / REJECTED

Rule:
Report goes to REPORTS.
Decision goes to CHECKPOINTS.
Current truth goes to CURRENT.
Live idea goes to LABS.
Mission goes to MISSIONS.
Technical brick goes to SPECS.
"@

    Write-TextFileIfMissing -Path (Join-Path $WorkspaceRoot "00_CURRENT\CURRENT_STATE.md") -Content $currentState
    Write-TextFileIfMissing -Path (Join-Path $WorkspaceRoot "00_CURRENT\CHECKPOINT_LATEST.md") -Content $checkpointLatest
    Write-TextFileIfMissing -Path (Join-Path $WorkspaceRoot "00_CURRENT\ROADMAP_ACTIVE.md") -Content $roadmapActive
    Write-TextFileIfMissing -Path (Join-Path $WorkspaceRoot "00_CURRENT\NEXT_ACTION.md") -Content $nextAction
    Write-TextFileIfMissing -Path (Join-Path $WorkspaceRoot "01_INBOX_TO_CLASSIFY\_INBOX_RULES.md") -Content $inboxInstructions
}

Write-Host ""
Write-Host "==============================================="
Write-Host " DONE"
Write-Host "==============================================="
Write-Host "Workspace created / checked:"
Write-Host $WorkspaceRoot
Write-Host ""
Write-Host "Suggested next copy targets:"
Write-Host "REPORT     -> 03_REPORTS\2026\2026-05\2026-05-05"
Write-Host "CHECKPOINT -> 04_CHECKPOINTS\2026\2026-05\2026-05-05"
Write-Host "LEXIQUE    -> 02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE"
Write-Host ""

if ($OpenExplorer) {
    Start-Process explorer.exe $WorkspaceRoot
}
