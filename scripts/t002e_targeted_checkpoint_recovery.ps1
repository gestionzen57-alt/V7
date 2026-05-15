param(
    [string]$RepoPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002E-CHK] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "Targeted checkpoint for T002-E without touching other workspace files"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$checkpointDir = Join-Path $RepoPath "Docs\Checkpoints"
if (!(Test-Path $checkpointDir)) {
    New-Item -ItemType Directory -Path $checkpointDir -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_E_TICK_SURFACE_TARGETED.md"

$lastCommits = git log --oneline -7
$t002Status = git status --short -- `
    "Docs/Contracts/T002_ENGINE_TICK_SURFACE_CONTRACT.json" `
    "Docs/Audits" `
    "tests/test_t002_engine_tick_surface_contract.py" `
    "scripts/t002_tick_surface_vs_v6_core.ps1"

$content = @()
$content += "# CHECKPOINT - T002-E tick surface vs detached V6 core"
$content += ""
$content += "Date: $(Get-Date -Format o)"
$content += "Focus: T002-E tick surface vs detached V6 core"
$content += ""
$content += "## Result"
$content += ""
$content += "- T002-E audit commit was already pushed."
$content += "- Latest relevant commit should include: audit(t002): compare legacy tick surface with detached v6 core."
$content += "- Runtime was not modified."
$content += "- Dashboard workspace files were intentionally left untouched."
$content += ""
$content += "## Technical findings"
$content += ""
$content += "- Covered by detached core now: symbol, timestamp."
$content += "- Not yet covered: dev_a, dev_b, gap, spread, timeframe, val_a, val_b."
$content += "- T002 tests passed during the run: 14 passed."
$content += ""
$content += "## Files produced by T002-E"
$content += ""
$content += "- Docs/Contracts/T002_ENGINE_TICK_SURFACE_CONTRACT.json"
$content += "- Docs/Audits/T002_ENGINE_TICK_SURFACE_VS_V6_CORE_*.md"
$content += "- tests/test_t002_engine_tick_surface_contract.py if present from prior run"
$content += "- scripts/t002_tick_surface_vs_v6_core.ps1 if present from prior run"
$content += ""
$content += "## Why targeted checkpoint"
$content += ""
$content += "The standard auto_checkpoint_claude.ps1 hit a Git warning from Dashboard files modified by another workspace."
$content += "This checkpoint is targeted and avoids staging or modifying those files."
$content += ""
$content += "## Current git log"
$content += ""
$content += '```text'
$content += $lastCommits
$content += '```'
$content += ""
$content += "## T002-specific status"
$content += ""
$content += '```text'
if ($t002Status) {
    $content += $t002Status
} else {
    $content += "No unstaged T002-specific files detected."
}
$content += '```'
$content += ""
$content += "## Next step"
$content += ""
$content += "Do not wire pf_engine_v6_core.py into runtime yet."
$content += "Next safe step: add explicit support in pf_engine_v6_core.py for legacy tick fields only after tests: dev_a, dev_b, val_a, val_b, gap, timeframe, spread."
$content += ""

Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8
Ok "Checkpoint written: $checkpointPath"

Log "Targeted staging checkpoint only"
git add -- $checkpointPath
if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

$staged = git diff --cached --name-only
if (-not $staged) {
    Warn "Nothing staged. Exiting."
    exit 0
}

Log "Staged files:"
$staged | ForEach-Object { Write-Host "  $_" }

git commit -m "[CHECKPOINT] Targeted checkpoint: T002-E tick surface vs detached V6 core"
if ($LASTEXITCODE -ne 0) { throw "checkpoint commit failed" }

git pull origin main
if ($LASTEXITCODE -ne 0) { throw "git pull failed" }

git push origin main
if ($LASTEXITCODE -ne 0) { throw "git push failed" }

Ok "Targeted checkpoint committed and pushed"
Log "Final status"
git status --short
git log --oneline -5
