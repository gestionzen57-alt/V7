# ============================================================================
# SYNC_LEXIQUE.ps1 — PowerFlow V7.6.7
# Automatic lexique consolidation
# ENCODING: ASCII-safe (no emojis, no accents)
# ============================================================================
# Usage:
#   .\sync_lexique.ps1              # Normal consolidation
#   .\sync_lexique.ps1 -Archive     # Archive old patches
#   .\sync_lexique.ps1 -Verbose     # Verbose mode
# ============================================================================

param(
    [switch]$Archive = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$RepoPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"
$DocsPath = "$RepoPath\Docs"
$CorePath = "$RepoPath\core"
$ArchivePath = "$DocsPath\Archive\Lexique"
$MasterLexiquePath = "$DocsPath\LEXIQUE_MASTER.md"

# Create archive if requested
if ($Archive -and !(Test-Path $ArchivePath)) {
    New-Item -ItemType Directory -Path $ArchivePath -Force | Out-Null
}

function Find-LexiquePatches {
    # Find all LEXIQUE_PATCH_*.md files
    $patches = @()
    
    # In core/
    $patches += Get-ChildItem -Path $CorePath -Filter "LEXIQUE_PATCH_*.md" -File -ErrorAction SilentlyContinue
    
    # In docs/ and subdirs
    $patches += Get-ChildItem -Path $DocsPath -Filter "LEXIQUE_PATCH_*.md" -File -Recurse -ErrorAction SilentlyContinue | 
                Where-Object { $_.FullName -notmatch "Archive" }
    
    return $patches | Sort-Object LastWriteTime
}

function Find-TermeGrammaireFiles {
    # Find TERRAIN_GRAMMAR, LEXIQUE_FR files
    $files = @()
    
    # Docs/
    $files += Get-ChildItem -Path $DocsPath -Filter "*TERRAIN_GRAMMAR*.md" -File -ErrorAction SilentlyContinue
    $files += Get-ChildItem -Path $DocsPath -Filter "*LEXIQUE_FR*.md" -File -ErrorAction SilentlyContinue
    $files += Get-ChildItem -Path $DocsPath -Filter "*LEXIQUE_GRAMMAIRE*.md" -File -ErrorAction SilentlyContinue
    
    # Core/
    $files += Get-ChildItem -Path $CorePath -Filter "*LEXIQUE_GRAMMAIRE*.md" -File -ErrorAction SilentlyContinue
    
    return $files | Sort-Object LastWriteTime -Descending
}

function Extract-TermesFromPatch {
    param([string]$patchPath)
    
    $content = Get-Content $patchPath -Raw -Encoding UTF8
    $termes = @()
    
    # Pattern: ## Terme | **Terme**
    $matches = [regex]::Matches($content, "(?:^|\n)(?:##\s+|###\s+|\*\*)([\w\s\-]+)(?:\*\*)?(?:\n|:)")
    
    foreach ($match in $matches) {
        $terme = $match.Groups[1].Value.Trim()
        if ($terme -and $terme.Length -gt 2) {
            $termes += $terme
        }
    }
    
    return $termes | Select-Object -Unique
}

function Build-MasterLexique {
    param([array]$patches, [array]$grammaireFiles)
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    
    $content = @"
# LEXIQUE MASTER PowerFlow V7.6.7

Last consolidation: $timestamp
Source: Automatic merge of $($patches.Count) patches and $($grammaireFiles.Count) grammar files

---

## PowerFlow Terms - Index

"@

    # Extract all unique terms
    $allTermes = @{}
    
    foreach ($patch in $patches) {
        $termes = Extract-TermesFromPatch -patchPath $patch.FullName
        foreach ($terme in $termes) {
            if (!$allTermes.ContainsKey($terme)) {
                $allTermes[$terme] = $patch.Name
            }
        }
    }
    
    # Add alphabetic index
    $content += "`n### Alphabetic Index`n`n"
    $allTermes.Keys | Sort-Object | ForEach-Object {
        $content += "- **$_** - Source: [$($allTermes[$_])]`n"
    }
    
    # Add main sections
    $content += @"

---

## 1. FLOW PHILOSOPHY

### Core Concepts

Flux vivant (Living Flow)
Market as continuous moving organism, not isolated candles

Tension accumulee (Accumulated Tension)
Potential force compressed in a zone, ready to release

Elastique charge (Overloaded Elastic)
Price zone that accumulated too much pressure, creating return probability

Respiration de zone (Zone Breathing)
Natural oscillation around key level, sign of temporary equilibrium

Pullback absorbe (Absorbed Pullback)
Pullback meeting immediate demand/supply, sign of directional strength

Densite temporelle (Temporal Density)
Concentration of price activity in reduced time window

Leader / Follower
Currency leading movement vs trailing with delay

Force relative (Relative Strength)
Currency behavior comparison vs USD basket

---

## 2. TERRAIN GRAMMAR

### Nodes & Zones

Node temporel (Temporal Node)
Pivot point where multiple forces converge

Zone de repulsion (Repulsion Zone)
Level systematically rejecting price, creating clean bounces

Zone de compression (Compression Zone)
Tight range preceding usually volatile expansion

Convergence
Multiple timeframes/currencies align toward same direction

Cassure (Breakout)
Net crossing of zone with volume/momentum

Relachement (Release)
Sudden liberation of accumulated tension

---

## 3. BEHAVIORAL SIGNATURES

Asymmetries

Asymetrie des micro-oscillations
Visible bias in amplitude or frequency of M1/M5 oscillations

Price lag then catch-up
One currency price delay followed by explosive catch-up

Counter breath
Respiration contrary to major direction, sign of fatigue

Second leg
Second movement wave after consolidation, often more powerful

---

## 4. POWERFLOW EVENTS

Scenes detectable

COALITION_PUSH
Major currencies align pushing USD same direction

TREND_CONTINUATION
Directional flow confirmed over multiple timeframes

ROTATION_BUILDING
Accumulating signals of potential inversion

COMPRESSION_RELEASE
Explosive exit after tight range

ELASTIC_RECOIL
Brutal return after excessive extension

---

## 5. ALERTS & GATES

Alert System

Alert preemptive
Alert triggered before obvious breakout, on early signals

Alert qualified
Alert enriched with HTF/LTF context and relative strength

Gate deduplication
Filter preventing identical alert repetition in loop

Telegram gate
Control Telegram sending with intelligent throttling

---

## 6. TIMEFRAMES & PROFILES

M1 - Microfilm, event birth
M5 - Quick confirmation
M15 - Short-term structure
M30 - Intraday pivot
H1 - Medium gravity
H4 - Major context
D1 - Macro direction

HTF (High TimeFrame) - H4, D1
MTF (Medium TimeFrame) - M30, H1
LTF (Low TimeFrame) - M1, M5, M15

---

## 7. TECHNICAL BRICKS

Core Modules

pf_normalizer.py - Currency normalization vs USD
pf_engine.py - Flow perception engine
pf_temporal_nodes.py - Temporal node detection
pf_zones.py - Key zones identification
pf_coalitions.py - Currency coalition analysis
pf_memory.py - Event memory system
pf_battlefield_map.py - Terrain mapping

Dashboard

dashboard_live.html - Real-time trader interface
dashboard_data_normalizer.py - Display data normalization

Schedulers

scheduler_powerflow.py - Main orchestrator
scheduler_powerflow_turbo_wrapper.py - Turbo runtime wrapper

---

## 8. COLLABORATIVE WORKFLOW

Claude Sonnet 4.5 - Orchestrator, architecture, strategy
GPT-1 Core Engine - Python pf_* modules
GPT-2 Dashboard - HTML/JS interface
GPT-3 Scheduler - Real-time orchestration, Telegram
GPT-4 Field Memory - GBPUSD analysis, film library
GPT Pro - Refactoring, complex issues

---

## 9. SOURCE PATCHES

Consolidated patches in this master:

"@

    # List source patches
    foreach ($patch in $patches) {
        $content += "- [$($patch.Name)] - $($patch.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))`n"
    }
    
    $content += @"

---

## 10. FRENCH LEXICON TRADER

Alerte preemptive - Preemptive alert
Cassure nette - Clean breakout
Compression range - Range compression
Elastique surchage - Overloaded elastic
Force relative - Relative strength
Gravite temporelle - Temporal gravity
Node pivot - Pivot node
Pullback absorbe - Absorbed pullback
Relachement - Release
Respiration zone - Zone breathing
Second leg - Second leg
Tension accumulee - Accumulated tension
Zone de repulsion - Repulsion zone

---

Live lexicon - Auto-updated by sync_lexique.ps1
Do not edit manually - Use patches for additions

"@

    return $content
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Host "[INFO] PowerFlow Lexique Consolidator V7.6.7" -ForegroundColor Cyan

# Find patches
Write-Host "[INFO] Searching for lexique patches..." -ForegroundColor Yellow
$patches = Find-LexiquePatches
Write-Host "[INFO] $($patches.Count) patch(es) found" -ForegroundColor Cyan

if ($Verbose) {
    $patches | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
}

# Find grammar files
Write-Host "[INFO] Searching for grammar files..." -ForegroundColor Yellow
$grammaireFiles = Find-TermeGrammaireFiles
Write-Host "[INFO] $($grammaireFiles.Count) grammar file(s) found" -ForegroundColor Cyan

# Generate master
Write-Host "[INFO] Generating LEXIQUE_MASTER.md..." -ForegroundColor Yellow
$masterContent = Build-MasterLexique -patches $patches -grammaireFiles $grammaireFiles
Set-Content -Path $MasterLexiquePath -Value $masterContent -Encoding ASCII
Write-Host "[OK] LEXIQUE_MASTER.md generated" -ForegroundColor Green

# Archive if requested
if ($Archive) {
    Write-Host "[INFO] Archiving patches..." -ForegroundColor Yellow
    foreach ($patch in $patches) {
        $destPath = Join-Path $ArchivePath $patch.Name
        Copy-Item -Path $patch.FullName -Destination $destPath -Force
        if ($Verbose) {
            Write-Host "  (OK) $($patch.Name) to Archive/" -ForegroundColor Gray
        }
    }
    Write-Host "[OK] $($patches.Count) patch(es) archived" -ForegroundColor Green
}

Write-Host "`n[OK] LEXIQUE CONSOLIDATION COMPLETE" -ForegroundColor Green
Write-Host "[INFO] File: $MasterLexiquePath" -ForegroundColor Cyan

exit 0
