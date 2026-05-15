param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[STATE] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow current state update for Claude v2"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -10

# Clean previous failed temp if present
Remove-Item ".\.t004o_requalify_after_usd_cohort.py" -Force -ErrorAction SilentlyContinue

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before current-state commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$docsDir = Join-Path $RepoPath "Docs"
$currentDir = Join-Path $docsDir "CurrentState"
$checkpointDir = Join-Path $docsDir "Checkpoints"

if (!(Test-Path $docsDir)) { New-Item -ItemType Directory -Path $docsDir -Force | Out-Null }
if (!(Test-Path $currentDir)) { New-Item -ItemType Directory -Path $currentDir -Force | Out-Null }
if (!(Test-Path $checkpointDir)) { New-Item -ItemType Directory -Path $checkpointDir -Force | Out-Null }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$nowIso = Get-Date -Format o

$currentStatePath = Join-Path $docsDir "CURRENT_STATE.md"
$snapshotPath = Join-Path $currentDir "CURRENT_STATE_${stamp}_T004_REQUALIFIED.md"
$claudePath = Join-Path $docsDir "CLAUDE.md"

$head = git log -1 --oneline
$recent = @(git log --oneline -12)

$stateLines = New-Object System.Collections.Generic.List[string]
$stateLines.Add("# CURRENT STATE - PowerFlow V7.6.7")
$stateLines.Add("")
$stateLines.Add("Date: $nowIso")
$stateLines.Add("Head: $head")
$stateLines.Add("")
$stateLines.Add("## Immediate context")
$stateLines.Add("")
$stateLines.Add("The workspace is clean before this update. T004 has been diagnosed, closed, then requalified after a broader USD cohort test.")
$stateLines.Add("")
$stateLines.Add("## T004 final/requalified state")
$stateLines.Add("")
$stateLines.Add("T004 began as a USDJPY thin-data investigation.")
$stateLines.Add("")
$stateLines.Add("Initial evidence showed:")
$stateLines.Add("- Core/powerflow.db is the active populated DB.")
$stateLines.Add("- USDJPY existed historically but was thin relative to GBPUSD.")
$stateLines.Add("- During earlier active insertion windows, GBPUSD advanced while USDJPY did not.")
$stateLines.Add("- Initial final diagnosis was capture/routing/source-feed side, not engine/scoring/dashboard.")
$stateLines.Add("")
$stateLines.Add("Later operator added/activated more EAs:")
$stateLines.Add("- USD-base cohort: USDJPY, USDCAD, USDCHF.")
$stateLines.Add("- USD-quote cohort: GBPUSD, EURUSD, AUDUSD.")
$stateLines.Add("")
$stateLines.Add("T004-N expanded cohort result:")
$stateLines.Add("- USDJPY advanced.")
$stateLines.Add("- USDCAD advanced.")
$stateLines.Add("- USDCHF advanced.")
$stateLines.Add("- GBPUSD advanced.")
$stateLines.Add("- EURUSD advanced.")
$stateLines.Add("- AUDUSD advanced.")
$stateLines.Add("")
$stateLines.Add("Therefore the hypothesis of a global USD-base blockage is invalidated.")
$stateLines.Add("")
$stateLines.Add("Current T004 interpretation:")
$stateLines.Add("- Global USD-base capture blockage: invalidated.")
$stateLines.Add("- Probable cause: feed / EA / capture intermittent or initial setup incomplete during the first windows.")
$stateLines.Add("- Engine change required: no.")
$stateLines.Add("- Scoring change required: no.")
$stateLines.Add("- Dashboard change required: no.")
$stateLines.Add("- DB schema/path change required: no.")
$stateLines.Add("")
$stateLines.Add("Current dispatch status for T004:")
$stateLines.Add("- DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT")
$stateLines.Add("")
$stateLines.Add("Important T004 evidence files:")
$stateLines.Add("- Docs/Contracts/T004_FINAL_DIAGNOSIS.json")
$stateLines.Add("- Docs/Contracts/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json")
$stateLines.Add("- Docs/Contracts/T004_USD_BASE_POLARITY_COHORT.json")
$stateLines.Add("- Docs/Reports/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT_*.md")
$stateLines.Add("")
$stateLines.Add("## Revalidation commands for later")
$stateLines.Add("")
$stateLines.Add("When EAs and feed are active, rerun:")
$stateLines.Add("")
$stateLines.Add("```powershell")
$stateLines.Add(".\scripts\t004_usd_base_polarity_cohort.ps1 ``")
$stateLines.Add('  -UsdBaseSymbols @("USDJPY","USDCAD","USDCHF") ``')
$stateLines.Add('  -UsdQuoteSymbols @("GBPUSD","EURUSD","AUDUSD") ``')
$stateLines.Add("  -WatchSeconds 180 ``")
$stateLines.Add("  -IntervalSeconds 10")
$stateLines.Add("```")
$stateLines.Add("")
$stateLines.Add("Then:")
$stateLines.Add("")
$stateLines.Add("```powershell")
$stateLines.Add(".\scripts\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10")
$stateLines.Add("```")
$stateLines.Add("")
$stateLines.Add("## Current operating rule")
$stateLines.Add("")
$stateLines.Add("Do not patch Core/engine.py, pf_engine_v6_core.py, scoring, dashboard, or SQLite for T004.")
$stateLines.Add("")
$stateLines.Add("If capture intermittence recurs, add/inspect capture-health instrumentation per symbol before changing PowerFlow perception logic.")
$stateLines.Add("")
$stateLines.Add("## Recent git log")
$stateLines.Add("")
$stateLines.Add("```text")
foreach ($line in $recent) { $stateLines.Add($line) }
$stateLines.Add("```")
$stateLines.Add("")
$stateLines.Add("## Next logical step")
$stateLines.Add("")
$stateLines.Add("Read Docs/DISPATCH_STATUS.json and continue with the next active task. Likely areas from recent history:")
$stateLines.Add("- Scheduler / turbo / overlap continuation work.")
$stateLines.Add("- T002 detached V6 core path if still active.")
$stateLines.Add("- Multi-symbol validation now that EA coverage has expanded.")

Set-Content -Path $currentStatePath -Value $stateLines -Encoding UTF8
Set-Content -Path $snapshotPath -Value $stateLines -Encoding UTF8
Ok "Wrote Docs/CURRENT_STATE.md"
Ok "Wrote $snapshotPath"

if (!(Test-Path $claudePath)) {
    Warn "Docs/CLAUDE.md not found. Creating it."
    Set-Content -Path $claudePath -Value "# CLAUDE" -Encoding UTF8
}

$claude = Get-Content $claudePath -Raw -Encoding UTF8
$blockStart = "<!-- POWERFLOW_CURRENT_STATE_START -->"
$blockEnd = "<!-- POWERFLOW_CURRENT_STATE_END -->"
$snapshotName = Split-Path $snapshotPath -Leaf

$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add($blockStart)
$summaryLines.Add("## Current State - updated $nowIso")
$summaryLines.Add("")
$summaryLines.Add("- Workspace current-state update for Claude.")
$summaryLines.Add("- T004 is requalified after expanded USD cohort.")
$summaryLines.Add("- Global USD-base blockage is invalidated.")
$summaryLines.Add("- Probable cause for initial USDJPY thin data: feed / EA / capture intermittent or initial setup incomplete.")
$summaryLines.Add("- Current T004 dispatch status: DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT.")
$summaryLines.Add("- No engine/scoring/dashboard/DB patch is justified for T004.")
$summaryLines.Add("- Canonical current state file: Docs/CURRENT_STATE.md.")
$summaryLines.Add("- Latest snapshot: Docs/CurrentState/$snapshotName.")
$summaryLines.Add("")
$summaryLines.Add($blockEnd)

$summaryBlock = $summaryLines -join "`n"
$pattern = [regex]::Escape($blockStart) + "(?s).*?" + [regex]::Escape($blockEnd)

if ($claude -match [regex]::Escape($blockStart)) {
    $claude = [regex]::Replace($claude, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $summaryBlock })
} else {
    $claude = $summaryBlock + "`n`n" + $claude
}

Set-Content -Path $claudePath -Value $claude -Encoding UTF8
Ok "Updated Docs/CLAUDE.md current-state block"

$checkpointPath = $null
if (-not $SkipCheckpoint) {
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_CURRENT_STATE_FOR_CLAUDE.md"

    $checkpointLines = New-Object System.Collections.Generic.List[string]
    $checkpointLines.Add("# CHECKPOINT - Current state for Claude")
    $checkpointLines.Add("")
    $checkpointLines.Add("Date: $nowIso")
    $checkpointLines.Add("Focus: Update current state after T004 requalification")
    $checkpointLines.Add("")
    $checkpointLines.Add("## Result")
    $checkpointLines.Add("")
    $checkpointLines.Add("- Docs/CURRENT_STATE.md updated.")
    $checkpointLines.Add("- Docs/CLAUDE.md current-state block updated.")
    $checkpointLines.Add("- T004-O requalification recorded as the current source of truth.")
    $checkpointLines.Add("- Runtime unchanged.")
    $checkpointLines.Add("- Dashboard runtime state restored before commit if needed.")
    $checkpointLines.Add("")
    $checkpointLines.Add("## Current T004 reading")
    $checkpointLines.Add("")
    $checkpointLines.Add("- Global USD-base blockage invalidated.")
    $checkpointLines.Add("- Probable cause: feed / EA / capture intermittent or initial setup incomplete.")
    $checkpointLines.Add("- No engine/scoring/dashboard/DB patch required.")
    $checkpointLines.Add("")
    $checkpointLines.Add("## Recent git log")
    $checkpointLines.Add("")
    $checkpointLines.Add("```text")
    foreach ($line in $recent) { $checkpointLines.Add($line) }
    $checkpointLines.Add("```")

    Set-Content -Path $checkpointPath -Value $checkpointLines -Encoding UTF8
    Ok "Wrote $checkpointPath"
}

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/CURRENT_STATE.md",
    "Docs/CLAUDE.md",
    "scripts/update_current_state_for_claude.ps1"
)

if (Test-Path $snapshotPath) { $pathsToAdd += $snapshotPath }
if (-not $SkipCheckpoint -and $null -ne $checkpointPath -and (Test-Path $checkpointPath)) { $pathsToAdd += $checkpointPath }

Log "Targeted staging only current-state files"
foreach ($p in $pathsToAdd) {
    if (Test-Path $p) {
        git add -- $p
        if ($LASTEXITCODE -ne 0) { throw "git add failed for $p" }
    } else {
        Warn "Path not found for staging: $p"
    }
}

$staged = git diff --cached --name-only
if (-not $staged) {
    Warn "No staged current-state changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "docs: update current state for Claude after T004 requalification"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }

    git pull origin main
    if ($LASTEXITCODE -ne 0) { throw "git pull failed" }

    git push origin main
    if ($LASTEXITCODE -ne 0) { throw "git push failed" }
}

Ok "Current state update complete"
Log "Final status"
git status --short
git log --oneline -10
