param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$NoGit,
    [switch]$NoCheckpoint,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-Location $RepoPath

function Info($msg) { Write-Host ("[T002-DISCOVERY] " + $msg) -ForegroundColor Cyan }
function Ok($msg) { Write-Host ("[OK] " + $msg) -ForegroundColor Green }
function Warn($msg) { Write-Host ("[WARN] " + $msg) -ForegroundColor Yellow }
function Fail($msg) { Write-Host ("[FAIL] " + $msg) -ForegroundColor Red; exit 1 }

function RelPath([string]$FullName) {
    $root = (Resolve-Path $RepoPath).Path
    $path = (Resolve-Path $FullName).Path
    if ($path.StartsWith($root)) {
        return $path.Substring($root.Length).TrimStart('\','/')
    }
    return $path
}

function IsIgnoredPath([string]$FullName) {
    $p = $FullName -replace '\\','/'
    if ($p -match '/\.git/') { return $true }
    if ($p -match '/Archive/') { return $true }
    if ($p -match '/archive/') { return $true }
    if ($p -match '/backups?/') { return $true }
    if ($p -match '/_backup') { return $true }
    if ($p -match '/venv/') { return $true }
    if ($p -match '/\.venv/') { return $true }
    if ($p -match '/__pycache__/') { return $true }
    return $false
}

Info "PowerFlow V7.6.7 T002 engine target discovery"
Info ("RepoPath = " + $RepoPath)

if (-not (Test-Path ".git")) {
    Fail "Not a git repository. Run from the PowerFlow repo root."
}

Info "Git preflight"
git status --short
git branch --show-current
git log --oneline -5

if (-not $SkipRestoreDashboardData) {
    $dash = Join-Path $RepoPath "Core/dashboard_data.json"
    if (Test-Path $dash) {
        $dashStatus = git status --short -- "Core/dashboard_data.json"
        if ($dashStatus) {
            Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before audit commit."
            git restore -- "Core/dashboard_data.json"
            Ok "Restored Core/dashboard_data.json"
        }
    }
}

Info "Collecting active Python files"
$allPy = Get-ChildItem -Path $RepoPath -Recurse -File -Filter "*.py" | Where-Object { -not (IsIgnoredPath $_.FullName) }
Ok (("Active Python files scanned: " + $allPy.Count))

$pfEngine = @($allPy | Where-Object { $_.Name -eq "pf_engine.py" })
$enginePy = @($allPy | Where-Object { $_.Name -eq "engine.py" })
$engineLike = @($allPy | Where-Object {
    $_.Name -match "engine" -or
    $_.Name -match "orchestrator" -or
    $_.Name -match "scheduler" -or
    $_.Name -match "cycle"
}) | Sort-Object FullName

$mainTarget = $null
if ($pfEngine.Count -gt 0) {
    $mainTarget = $pfEngine[0]
} elseif (Test-Path (Join-Path $RepoPath "Core/engine.py")) {
    $mainTarget = Get-Item (Join-Path $RepoPath "Core/engine.py")
} elseif ($enginePy.Count -gt 0) {
    $mainTarget = $enginePy[0]
}

Info "Scanning references"
$patterns = @(
    "pf_engine",
    "from engine import",
    "import engine",
    "Core.engine",
    "engine.py",
    "pf_engine_orchestrator",
    "pf_cycle_orchestrator",
    "scheduler_powerflow",
    "scheduler_powerflow_turbo_wrapper",
    "run_powerflow_live_stack_once",
    "run_powerflow_cycle_once"
)

$hits = New-Object System.Collections.Generic.List[object]
foreach ($file in $allPy) {
    foreach ($pattern in $patterns) {
        try {
            $matches = Select-String -Path $file.FullName -Pattern $pattern -SimpleMatch -ErrorAction Stop
            foreach ($m in $matches) {
                $hits.Add([pscustomobject]@{
                    File = (RelPath $file.FullName)
                    Line = $m.LineNumber
                    Pattern = $pattern
                    Text = $m.Line.Trim()
                }) | Out-Null
            }
        } catch {
            Warn ("Could not scan " + (RelPath $file.FullName) + " for pattern " + $pattern)
        }
    }
}

Info "Running syntax checks on discovered target candidates"
$syntaxTargets = New-Object System.Collections.Generic.List[string]
if ($mainTarget) { $syntaxTargets.Add($mainTarget.FullName) | Out-Null }
foreach ($name in @(
    "Core/pf_engine_orchestrator.py",
    "Core/pf_cycle_orchestrator.py",
    "Core/scheduler_powerflow.py",
    "Core/scheduler_powerflow_turbo_wrapper.py",
    "Core/run_powerflow_live_stack_once.py",
    "Core/run_powerflow_cycle_once.py"
)) {
    $p = Join-Path $RepoPath $name
    if (Test-Path $p) { $syntaxTargets.Add((Resolve-Path $p).Path) | Out-Null }
}
$syntaxTargets = @($syntaxTargets | Select-Object -Unique)
foreach ($target in $syntaxTargets) {
    Info ("py_compile " + (RelPath $target))
    python -m py_compile $target
}
Ok "Syntax checks completed"

$auditsDir = Join-Path $RepoPath "Docs/Audits"
New-Item -ItemType Directory -Path $auditsDir -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = Join-Path $auditsDir ("T002_ENGINE_TARGET_DISCOVERY_" + $stamp + ".md")

$report = New-Object System.Collections.Generic.List[string]
$report.Add("# T002 Engine Target Discovery") | Out-Null
$report.Add("") | Out-Null
$report.Add("Date: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")) | Out-Null
$report.Add("Repo: " + $RepoPath) | Out-Null
$report.Add("") | Out-Null
$report.Add("## Executive finding") | Out-Null
$report.Add("") | Out-Null

if ($pfEngine.Count -eq 0) {
    $report.Add("- Active pf_engine.py: NOT FOUND outside archives/backups.") | Out-Null
} else {
    $report.Add("- Active pf_engine.py: FOUND.") | Out-Null
    foreach ($f in $pfEngine) { $report.Add("  - " + (RelPath $f.FullName)) | Out-Null }
}

if ($enginePy.Count -eq 0) {
    $report.Add("- Active engine.py: NOT FOUND outside archives/backups.") | Out-Null
} else {
    $report.Add("- Active engine.py candidates:") | Out-Null
    foreach ($f in $enginePy) { $report.Add("  - " + (RelPath $f.FullName)) | Out-Null }
}

if ($mainTarget) {
    $report.Add("- Candidate T002 target: " + (RelPath $mainTarget.FullName)) | Out-Null
} else {
    $report.Add("- Candidate T002 target: NONE DISCOVERED") | Out-Null
}

$report.Add("") | Out-Null
$report.Add("## Engine-like active files") | Out-Null
$report.Add("") | Out-Null
if ($engineLike.Count -eq 0) {
    $report.Add("- None") | Out-Null
} else {
    foreach ($f in $engineLike) { $report.Add("- " + (RelPath $f.FullName)) | Out-Null }
}

$report.Add("") | Out-Null
$report.Add("## Reference scan") | Out-Null
$report.Add("") | Out-Null
if ($hits.Count -eq 0) {
    $report.Add("- No references found for target patterns.") | Out-Null
} else {
    foreach ($h in ($hits | Sort-Object File, Line, Pattern)) {
        $line = "- " + $h.File + ":" + $h.Line + " | pattern " + $h.Pattern + " | " + $h.Text
        $report.Add($line) | Out-Null
    }
}

$report.Add("") | Out-Null
$report.Add("## Syntax checks") | Out-Null
$report.Add("") | Out-Null
if ($syntaxTargets.Count -eq 0) {
    $report.Add("- No syntax targets discovered.") | Out-Null
} else {
    foreach ($t in $syntaxTargets) { $report.Add("- PASS py_compile " + (RelPath $t)) | Out-Null }
}

$report.Add("") | Out-Null
$report.Add("## Recommendation") | Out-Null
$report.Add("") | Out-Null
if ($pfEngine.Count -eq 0 -and $mainTarget -and $mainTarget.Name -eq "engine.py") {
    $report.Add("- T002 is probably misnamed: dispatch says pf_engine.py, but active target appears to be " + (RelPath $mainTarget.FullName) + ".") | Out-Null
    $report.Add("- Do not refactor blindly. First convert T002 from 'pf_engine.py refactor' to 'engine target audit / extraction plan'.") | Out-Null
    $report.Add("- Next action: inspect callable surfaces and runtime entrypoints before changing behavior.") | Out-Null
} elseif ($pfEngine.Count -gt 0) {
    $report.Add("- T002 target exists. Next action: audit imports/call-sites and split refactor into safe adapter plus implementation modules.") | Out-Null
} else {
    $report.Add("- No safe target discovered. Update DISPATCH_STATUS before any code change.") | Out-Null
}

$report.Add("") | Out-Null
$report.Add("## PowerFlow rule") | Out-Null
$report.Add("") | Out-Null
$report.Add("No runtime refactor before confirming the actual entrypoint and active call graph.") | Out-Null

$report | Set-Content -Path $reportPath -Encoding UTF8
Ok ("Report written: " + (RelPath $reportPath))

Info "Git diff summary"
git diff --stat

if (-not $NoGit) {
    $sync = Join-Path $RepoPath "scripts/auto_git_sync.ps1"
    if (Test-Path $sync) {
        Info "Syncing audit via auto_git_sync"
        & $sync -Message "audit(t002): discover actual engine legacy target"
    } else {
        Warn "auto_git_sync.ps1 not found. Manual commit needed."
    }
}

if (-not $NoCheckpoint) {
    $checkpoint = Join-Path $RepoPath "scripts/auto_checkpoint_claude.ps1"
    if (Test-Path $checkpoint) {
        Info "Creating checkpoint"
        & $checkpoint -Focus "T002 engine target discovery"
    } else {
        Warn "auto_checkpoint_claude.ps1 not found. Manual checkpoint needed."
    }
}

Ok "T002 target discovery complete"
