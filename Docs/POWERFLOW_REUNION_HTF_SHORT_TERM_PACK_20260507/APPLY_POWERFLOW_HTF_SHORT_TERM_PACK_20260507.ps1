<#
APPLY_POWERFLOW_HTF_SHORT_TERM_PACK_20260507.ps1

But :
Intégrer le pack HTF / court terme PowerFlow dans PowerFlow_Workspace.

Pack attendu :
POWERFLOW_REUNION_HTF_SHORT_TERM_PACK_20260507

Usage recommandé depuis :
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT

Commande :
powershell -ExecutionPolicy Bypass -File .\POWERFLOW_REUNION_HTF_SHORT_TERM_PACK_20260507\APPLY_POWERFLOW_HTF_SHORT_TERM_PACK_20260507.ps1 -SourceFolder .\POWERFLOW_REUNION_HTF_SHORT_TERM_PACK_20260507 -OpenExplorer

Safe :
- ne touche pas Core
- ne touche pas powerflow.db
- ne touche pas capture_bridge.py
- ne modifie aucun .py
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
    param(
        [string]$Source,
        [string]$Dest
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Host "[MISSING] $Source"
        return
    }

    Ensure-Folder -Path (Split-Path -Parent $Dest)
    Copy-Item -LiteralPath $Source -Destination $Dest -Force
    Write-Host "[COPY] $Source -> $Dest"
}

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Content
    )

    Ensure-Folder -Path (Split-Path -Parent $Path)
    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
    Write-Host "[FILE] $Path"
}

$src = Resolve-Path -LiteralPath $SourceFolder

$currentDir    = Join-Path $WorkspaceRoot "00_CURRENT"
$lexiqueDir    = Join-Path $WorkspaceRoot "02_DOCS_ACTIVE\LEXIQUE_GRAMMAIRE"
$doctrineDir   = Join-Path $WorkspaceRoot "02_DOCS_ACTIVE\DOCTRINE"
$reportDir     = Join-Path $WorkspaceRoot "03_REPORTS\2026\2026-05\2026-05-07"
$checkpointDir = Join-Path $WorkspaceRoot "04_CHECKPOINTS\2026\2026-05\2026-05-07"
$missionDir    = Join-Path $WorkspaceRoot "05_MISSIONS\MISSION_ACTIVE"
$specDir       = Join-Path $WorkspaceRoot "07_SPECS\SPECS_ACTIVE"

Ensure-Folder -Path $currentDir
Ensure-Folder -Path $lexiqueDir
Ensure-Folder -Path $doctrineDir
Ensure-Folder -Path $reportDir
Ensure-Folder -Path $checkpointDir
Ensure-Folder -Path $missionDir
Ensure-Folder -Path $specDir

Write-Host ""
Write-Host "==============================================="
Write-Host " POWERFLOW HTF SHORT TERM PACK INTEGRATION"
Write-Host "==============================================="
Write-Host "WorkspaceRoot : $WorkspaceRoot"
Write-Host "SourceFolder  : $src"
Write-Host ""

# Source filenames
$reportFile     = Join-Path $src "RAPPORT_REUNION_POWERFLOW_HTF_SHORT_TERM_20260507.md"
$lexiqueFile    = Join-Path $src "PATCH_LEXIQUE_HTF_SHORT_TERM_POWERFLOW_20260507.md"
$checkpointFile = Join-Path $src "CHECKPOINT_CORRECTION_HTF_POWERFLOW_20260507.md"
$missionFile    = Join-Path $src "MISSION_HTF_CONTEXT_STACK_V01_SPEC_20260507.md"

# Main copies
Copy-Required -Source $reportFile     -Dest (Join-Path $reportDir "RAPPORT_REUNION_POWERFLOW_HTF_SHORT_TERM_20260507.md")
Copy-Required -Source $lexiqueFile    -Dest (Join-Path $lexiqueDir "PATCH_LEXIQUE_HTF_SHORT_TERM_POWERFLOW_20260507.md")
Copy-Required -Source $checkpointFile -Dest (Join-Path $checkpointDir "CHECKPOINT_CORRECTION_HTF_POWERFLOW_20260507.md")
Copy-Required -Source $missionFile    -Dest (Join-Path $missionDir "MISSION_HTF_CONTEXT_STACK_V01_SPEC_20260507.md")
Copy-Required -Source $missionFile    -Dest (Join-Path $specDir "SPEC_HTF_CONTEXT_STACK_V01_20260507.md")

# Also place doctrine addendum in active doctrine
Copy-Required -Source $checkpointFile -Dest (Join-Path $doctrineDir "DOCTRINE_ADDENDUM_HTF_SHORT_TERM_POWERFLOW_20260507.md")

# 00_CURRENT addendum files
$currentAddendum = @"
# CURRENT_STATE_ADDENDUM — HTF / SHORT TERM POWERFLOW

Date : 2026-05-07
Statut : ADDENDUM DOCTRINAL ACTIF

## Correction centrale

Le trader trade court terme, mais son analyse primaire est HTF :

```text
W / D / H4 / H1
```

Le LTF n'est pas la doctrine complète.
Le LTF sert à détecter l'ignition, le rattrapage ou l'invalidation d'une fenêtre HTF retardée.

## Formule corrigée

```text
W/D donnent le régime et la mémoire.
H4 donne la gravité.
H1 traduit la phase intraday.
M15 ouvre la fenêtre tactique.
M5 mesure le relais.
M1 montre l'ignition et le rattrapage.
```

## Nouvelle priorité stratégique

```text
HTF_CONTEXT_STACK
→ Tactical Window
→ Node / Kinematics
→ Energy Alignment
→ Relational Gravity
→ Behavioral Alerts
→ Trader Decision
```

## Chantier actif

```text
P0 — intégrer cette correction HTF dans le workspace
P1 — P1.2 Relational Gravity Bridge Guard
P2 — audit runtime Kinematics / Currency Energy / Relational Gravity
P3 — spec HTF_CONTEXT_STACK V0.1
P4 — P2 Behavioral Mapper seulement après P1.2 propre
```

## Phrase noyau

```text
Le LTF montre l'étincelle.
Mais le HTF dit pourquoi l'étincelle compte.
```
"@

$latestCheckpoint = @"
# CHECKPOINT_LATEST_ADDENDUM — HTF / SHORT TERM POWERFLOW

Date : 2026-05-07

## Point officiel

Correction majeure :
PowerFlow ne doit pas être recentré uniquement sur M1/M5/M15.

Le besoin réel :
trading court terme + analyse primaire HTF W/D/H4/H1.

## État à retenir

```text
Kinematics = à auditer runtime
Currency Energy = à relancer
Relational Gravity = dans le cockpit
P1.2 Bridge Guard = à corriger
P2 Behavioral Mapper = en attente
HTF_CONTEXT_STACK = prochaine brique structurante à spécifier
```

## Blocage actif

```text
P2 interdit tant que P1.2 Bridge Guard n'est pas corrigé.
```

## Pourquoi

Si RELATIONAL_GRAVITY_MIXED raconte un leader clair, l'alerte devient trompeuse.

## Next action

```text
1. P1.2 Relational Gravity Bridge Guard
2. Audit runtime Kinematics / Energy / Gravity
3. Spec HTF_CONTEXT_STACK V0.1
4. P2 Behavioral Mapper seulement après P1.2 OK
```
"@

$roadmapAddendum = @"
# ROADMAP_ADDENDUM — HTF / SHORT TERM POWERFLOW

Date : 2026-05-07

## Ordre court

```text
P0 — Workspace HTF memory sync
P1 — P1.2 Relational Gravity Bridge Guard
P2 — Runtime audit Kinematics / Energy / Gravity
P3 — HTF_CONTEXT_STACK V0.1 spec
P4 — Behavioral Mapper relational alerts
P5 — Dashboard Sync
P6 — Telegram later
```

## Règle

```text
Ne pas ajouter d'alertes avant de fiabiliser la lecture.
```

## Cible trading

```text
HTF Window + LTF Ignition + Energy Alignment + Relational Gravity + 3 alertes max
```
"@

Write-TextFile -Path (Join-Path $currentDir "CURRENT_STATE_ADDENDUM_HTF_SHORT_TERM_20260507.md") -Content $currentAddendum
Write-TextFile -Path (Join-Path $currentDir "CHECKPOINT_LATEST_ADDENDUM_HTF_SHORT_TERM_20260507.md") -Content $latestCheckpoint
Write-TextFile -Path (Join-Path $currentDir "ROADMAP_ADDENDUM_HTF_SHORT_TERM_20260507.md") -Content $roadmapAddendum

Write-Host ""
Write-Host "==============================================="
Write-Host " DONE"
Write-Host "==============================================="
Write-Host "Copied report      -> $reportDir"
Write-Host "Copied lexique     -> $lexiqueDir"
Write-Host "Copied checkpoint  -> $checkpointDir"
Write-Host "Copied mission     -> $missionDir"
Write-Host "Copied spec        -> $specDir"
Write-Host "Current addendums  -> $currentDir"
Write-Host ""

if ($OpenExplorer) {
    Start-Process -FilePath "explorer.exe" -ArgumentList $currentDir
}
