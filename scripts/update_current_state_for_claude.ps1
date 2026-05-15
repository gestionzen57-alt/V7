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

Log "PowerFlow current state update for Claude v3 safe"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -10

# Clean failed residue
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

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# CURRENT STATE - PowerFlow V7.6.7')
$lines.Add('')
$lines.Add("Date: $nowIso")
$lines.Add("Head: $head")
$lines.Add('')
$lines.Add('## Immediate context')
$lines.Add('')
$lines.Add('Workspace state update for Claude after T004 requalification.')
$lines.Add('')
$lines.Add('## T004 final/requalified state')
$lines.Add('')
$lines.Add('T004 began as a USDJPY thin-data investigation.')
$lines.Add('')
$lines.Add('Initial evidence showed:')
$lines.Add('- Core/powerflow.db is the active populated DB.')
$lines.Add('- USDJPY existed historically but was thin relative to GBPUSD.')
$lines.Add('- During earlier active insertion windows, GBPUSD advanced while USDJPY did not.')
$lines.Add('- Initial diagnosis was capture/routing/source-feed side, not engine/scoring/dashboard.')
$lines.Add('')
$lines.Add('Later operator added/activated more EAs:')
$lines.Add('- USD-base cohort: USDJPY, USDCAD, USDCHF.')
$lines.Add('- USD-quote cohort: GBPUSD, EURUSD, AUDUSD.')
$lines.Add('')
$lines.Add('T004-N expanded cohort result:')
$lines.Add('- USDJPY advanced.')
$lines.Add('- USDCAD advanced.')
$lines.Add('- USDCHF advanced.')
$lines.Add('- GBPUSD advanced.')
$lines.Add('- EURUSD advanced.')
$lines.Add('- AUDUSD advanced.')
$lines.Add('')
$lines.Add('Therefore the hypothesis of a global USD-base blockage is invalidated.')
$lines.Add('')
$lines.Add('Current T004 interpretation:')
$lines.Add('- Global USD-base capture blockage: invalidated.')
$lines.Add('- Probable cause: feed / EA / capture intermittent or initial setup incomplete during the first windows.')
$lines.Add('- Engine change required: no.')
$lines.Add('- Scoring change required: no.')
$lines.Add('- Dashboard change required: no.')
$lines.Add('- DB schema/path change required: no.')
$lines.Add('')
$lines.Add('Current dispatch status for T004:')
$lines.Add('- DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT')
$lines.Add('')
$lines.Add('Important T004 evidence files:')
$lines.Add('- Docs/Contracts/T004_FINAL_DIAGNOSIS.json')
$lines.Add('- Docs/Contracts/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json')
$lines.Add('- Docs/Contracts/T004_USD_BASE_POLARITY_COHORT.json')
$lines.Add('- Docs/Reports/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT_*.md')
$lines.Add('')
$lines.Add('## Revalidation commands for later')
$lines.Add('')
$lines.Add('Command 1:')
$lines.Add('.\scripts\t004_usd_base_polarity_cohort.ps1 -UsdBaseSymbols @("USDJPY","USDCAD","USDCHF") -UsdQuoteSymbols @("GBPUSD","EURUSD","AUDUSD") -WatchSeconds 180 -IntervalSeconds 10')
$lines.Add('')
$lines.Add('Command 2:')
$lines.Add('.\scripts\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10')
$lines.Add('')
$lines.Add('## Current operating rule')
$lines.Add('')
$lines.Add('Do not patch Core/engine.py, pf_engine_v6_core.py, scoring, dashboard, or SQLite for T004.')
$lines.Add('')
$lines.Add('If capture intermittence recurs, add or inspect capture-health instrumentation per symbol before changing PowerFlow perception logic.')
$lines.Add('')
$lines.Add('## Recent git log')
$lines.Add('')
foreach ($line in $recent) { $lines.Add("- $line") }
$lines.Add('')
$lines.Add('## Next logical step')
$lines.Add('')
$lines.Add('Read Docs/DISPATCH_STATUS.json and continue with the next active task.')
$lines.Add('Likely areas from recent history:')
$lines.Add('- Scheduler / turbo / overlap continuation work.')
$lines.Add('- T002 detached V6 core path if still active.')
$lines.Add('- Multi-symbol validation now that EA coverage has expanded.')

Set-Content -Path $currentStatePath -Value $lines -Encoding UTF8
Set-Content -Path $snapshotPath -Value $lines -Encoding UTF8
Ok "Wrote Docs/CURRENT_STATE.md"
Ok "Wrote $snapshotPath"

if (!(Test-Path $claudePath)) {
    Warn "Docs/CLAUDE.md not found. Creating it."
    Set-Content -Path $claudePath -Value '# CLAUDE' -Encoding UTF8
}

$claude = Get-Content $claudePath -Raw -Encoding UTF8
$blockStart = '<!-- POWERFLOW_CURRENT_STATE_START -->'
$blockEnd = '<!-- POWERFLOW_CURRENT_STATE_END -->'
$snapshotName = Split-Path $snapshotPath -Leaf

$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add($blockStart)
$summaryLines.Add("## Current State - updated $nowIso")
$summaryLines.Add('')
$summaryLines.Add('- Workspace current-state update for Claude.')
$summaryLines.Add('- T004 is requalified after expanded USD cohort.')
$summaryLines.Add('- Global USD-base blockage is invalidated.')
$summaryLines.Add('- Probable cause for initial USDJPY thin data: feed / EA / capture intermittent or initial setup incomplete.')
$summaryLines.Add('- Current T004 dispatch status: DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT.')
$summaryLines.Add('- No engine/scoring/dashboard/DB patch is justified for T004.')
$summaryLines.Add('- Canonical current state file: Docs/CURRENT_STATE.md.')
$summaryLines.Add("- Latest snapshot: Docs/CurrentState/$snapshotName.")
$summaryLines.Add('')
$summaryLines.Add($blockEnd)

$summaryBlock = $summaryLines -join "`n"
$pattern = [regex]::Escape($blockStart) + '(?s).*?' + [regex]::Escape($blockEnd)

if ($claude -match [regex]::Escape($blockStart)) {
    $claude = [regex]::Replace($claude, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $summaryBlock })
} else {
    $claude = $summaryBlock + "`n`n" + $claude
}

Set-Content -Path $claudePath -Value $claude -Encoding UTF8
Ok 'Updated Docs/CLAUDE.md current-state block'

$checkpointPath = $null
if (-not $SkipCheckpoint) {
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_CURRENT_STATE_FOR_CLAUDE.md"

    $ck = New-Object System.Collections.Generic.List[string]
    $ck.Add('# CHECKPOINT - Current state for Claude')
    $ck.Add('')
    $ck.Add("Date: $nowIso")
    $ck.Add('Focus: Update current state after T004 requalification')
    $ck.Add('')
    $ck.Add('## Result')
    $ck.Add('')
    $ck.Add('- Docs/CURRENT_STATE.md updated.')
    $ck.Add('- Docs/CLAUDE.md current-state block updated.')
    $ck.Add('- T004-O requalification recorded as current source of truth.')
    $ck.Add('- Runtime unchanged.')
    $ck.Add('- Dashboard runtime state restored before commit if needed.')
    $ck.Add('')
    $ck.Add('## Current T004 reading')
    $ck.Add('')
    $ck.Add('- Global USD-base blockage invalidated.')
    $ck.Add('- Probable cause: feed / EA / capture intermittent or initial setup incomplete.')
    $ck.Add('- No engine/scoring/dashboard/DB patch required.')
    $ck.Add('')
    $ck.Add('## Recent git log')
    $ck.Add('')
    foreach ($line in $recent) { $ck.Add("- $line") }

    Set-Content -Path $checkpointPath -Value $ck -Encoding UTF8
    Ok "Wrote $checkpointPath"
}

Log 'Targeted git status before commit'
git status --short

$pathsToAdd = @(
    'Docs/CURRENT_STATE.md',
    'Docs/CLAUDE.md',
    'scripts/update_current_state_for_claude.ps1'
)

if (Test-Path $snapshotPath) { $pathsToAdd += $snapshotPath }
if (-not $SkipCheckpoint -and $null -ne $checkpointPath -and (Test-Path $checkpointPath)) { $pathsToAdd += $checkpointPath }

Log 'Targeted staging only current-state files'
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
    Warn 'No staged current-state changes. Skipping commit.'
} else {
    Log 'Staged files:'
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m 'docs: update current state for Claude after T004 requalification'
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }

    git pull origin main
    if ($LASTEXITCODE -ne 0) { throw 'git pull failed' }

    git push origin main
    if ($LASTEXITCODE -ne 0) { throw 'git push failed' }
}

Ok 'Current state update complete'
Log 'Final status'
git status --short
git log --oneline -10
