param(
    [string]$RepoPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT",
    [switch]$SkipRestoreDashboardData,
    [switch]$NoCheckpoint,
    [switch]$NoGit
)

$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "[NEXT] $msg" -ForegroundColor Cyan }
function Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

Info "PowerFlow V7.6.7 continuation: post-T003 cleanup + T002 audit"
Info "RepoPath = $RepoPath"

if (-not (Test-Path $RepoPath)) {
    Fail "RepoPath not found: $RepoPath"
}

Set-Location $RepoPath

if (-not (Test-Path ".git")) {
    Fail "Not a git repository: $RepoPath"
}

Info "Git preflight"
git status --short
git branch --show-current
git log --oneline -5

# 1. Clean known runtime residue from T003 session.
if (-not $SkipRestoreDashboardData) {
    $dash = "Core\dashboard_data.json"
    $statusLine = git status --short -- $dash
    if ($statusLine) {
        Warn "$dash is modified. Restoring it because it is runtime dashboard state, not T003 code."
        git restore -- $dash
        Ok "Restored $dash"
    } else {
        Ok "$dash is clean"
    }
} else {
    Warn "SkipRestoreDashboardData set. Leaving Core\dashboard_data.json as-is."
}

# 2. Verify T003 commit presence.
Info "Verifying T003 commits"
$t003Commit = git log --oneline -20 | Select-String -Pattern "T003 hotfix pf_normalizer"
$checkpointCommit = git log --oneline -20 | Select-String -Pattern "T003 pf_normalizer signature hotfix"
if ($t003Commit) { Ok "T003 core commit found: $($t003Commit.Line)" } else { Warn "T003 core commit not found in last 20 commits" }
if ($checkpointCommit) { Ok "T003 checkpoint commit found: $($checkpointCommit.Line)" } else { Warn "T003 checkpoint commit not found in last 20 commits" }

# 3. Build T002 audit report without modifying pf_engine.py.
$reportDir = Join-Path $RepoPath "Docs\Audits"
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = Join-Path $reportDir "T002_PF_ENGINE_USAGE_AUDIT_$timestamp.md"

$coreDir = Join-Path $RepoPath "Core"
$pfEngine = Join-Path $coreDir "pf_engine.py"

if (-not (Test-Path $pfEngine)) {
    Warn "Core\pf_engine.py not found. Trying global search."
    $pfEngineCandidates = Get-ChildItem -Path $RepoPath -Recurse -Filter "pf_engine.py" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "\\Archive\\" -and $_.FullName -notmatch "\\backups?\\" }
    if ($pfEngineCandidates.Count -gt 0) {
        $pfEngine = $pfEngineCandidates[0].FullName
        Ok "Found pf_engine.py at $pfEngine"
    } else {
        Fail "pf_engine.py not found outside archives/backups"
    }
}

Info "Auditing call-sites for pf_engine.py"

$patterns = @(
    "import pf_engine",
    "from pf_engine import",
    "pf_engine\.",
    "run_engine",
    "PowerFlowEngine",
    "engine\.py",
    "pf_engine"
)

$codeFiles = Get-ChildItem -Path $RepoPath -Recurse -Include *.py,*.ps1,*.json,*.md -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch "\\.git\\" -and
        $_.FullName -notmatch "\\Archive\\" -and
        $_.FullName -notmatch "\\backups?\\" -and
        $_.FullName -notmatch "\\__pycache__\\"
    }

$hits = @()
foreach ($file in $codeFiles) {
    foreach ($pattern in $patterns) {
        $matches = Select-String -Path $file.FullName -Pattern $pattern -ErrorAction SilentlyContinue
        foreach ($m in $matches) {
            $rel = Resolve-Path -Path $m.Path -Relative
            $hits += [PSCustomObject]@{
                File = $rel
                Line = $m.LineNumber
                Pattern = $pattern
                Text = $m.Line.Trim()
            }
        }
    }
}

# 4. Static summary of pf_engine.py.
Info "Inspecting pf_engine.py structure"
$engineContent = Get-Content $pfEngine -Raw
$engineLines = ($engineContent -split "`r?`n").Count

$functionHits = Select-String -Path $pfEngine -Pattern "^\s*def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(" -ErrorAction SilentlyContinue
$classHits = Select-String -Path $pfEngine -Pattern "^\s*class\s+[A-Za-z_][A-Za-z0-9_]*" -ErrorAction SilentlyContinue
$importHits = Select-String -Path $pfEngine -Pattern "^\s*(import|from)\s+" -ErrorAction SilentlyContinue

$functions = @()
foreach ($f in $functionHits) { $functions += "$($f.LineNumber): $($f.Line.Trim())" }

$classes = @()
foreach ($c in $classHits) { $classes += "$($c.LineNumber): $($c.Line.Trim())" }

$imports = @()
foreach ($i in $importHits) { $imports += "$($i.LineNumber): $($i.Line.Trim())" }

# 5. Find likely dangerous dependencies.
$dangerPatterns = @(
    "cockpit_",
    "dashboard_",
    "telegram_",
    "sqlite3\.connect",
    "INSERT INTO",
    "UPDATE ",
    "DELETE FROM",
    "powerflow\.db"
)
$dangerHits = @()
foreach ($pattern in $dangerPatterns) {
    $matches = Select-String -Path $pfEngine -Pattern $pattern -ErrorAction SilentlyContinue
    foreach ($m in $matches) {
        $dangerHits += [PSCustomObject]@{
            Line = $m.LineNumber
            Pattern = $pattern
            Text = $m.Line.Trim()
        }
    }
}

# 6. Write report.
$branch = git branch --show-current
$head = git log --oneline -1

$hitLines = if ($hits.Count -gt 0) {
    ($hits | Sort-Object File, Line, Pattern | ForEach-Object {
        ("- `{0}`:{1} - pattern `{2}` - {3}" -f $_.File, $_.Line, $_.Pattern, $_.Text)
    }) -join "`n"
} else {
    "_Aucun appel direct trouve hors archives/backups._"
}

$functionLines = if ($functions.Count -gt 0) { ($functions | ForEach-Object { ("- {0}" -f $_) }) -join "`n" } else { "_Aucune fonction detectee._" }
$classLines = if ($classes.Count -gt 0) { ($classes | ForEach-Object { ("- {0}" -f $_) }) -join "`n" } else { "_Aucune classe detectee._" }
$importLines = if ($imports.Count -gt 0) { ($imports | ForEach-Object { ("- {0}" -f $_) }) -join "`n" } else { "_Aucun import detecte._" }

$dangerLines = if ($dangerHits.Count -gt 0) {
    ($dangerHits | Sort-Object Line, Pattern | ForEach-Object {
        ("- line {0} - pattern `{1}` - {2}" -f $_.Line, $_.Pattern, $_.Text)
    }) -join "`n"
} else {
    "_Aucun pattern critique detecte dans pf_engine.py._"
}

$recommendation = @"
## Verdict technique

T002 ne doit pas encore etre refactore a l'aveugle.

Etape correcte :
1. Identifier les call-sites actifs.
2. Separer code runtime actif vs legacy dormant.
3. Ne modifier aucune sortie dashboard/cockpit pendant l'audit.
4. Preferer un refactor par extraction de fonctions pures, pas une reecriture globale.
5. Ajouter tests de non-regression avant toute suppression.

## Risques techniques

- Risque de casser un chemin scheduler encore actif.
- Risque de dependance implicite cockpit/dashboard si `pf_engine.py` sert encore de facade.
- Risque de refactor trop large si les responsabilites ne sont pas cartographiees.
- Risque de DB write cache si le moteur legacy ecrit encore dans `powerflow.db`.
"@

$report = @"
# T002 - pf_engine.py usage audit

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Branch: $branch
HEAD: $head
Target: $pfEngine

## Contexte

T002 vise le refactor de `pf_engine.py` legacy vers une forme V6 modulaire.

Ce rapport ne modifie pas le moteur. Il cartographie les dependances et les risques avant intervention.

## Resume structurel

- Lines: $engineLines
- Classes detected: $($classes.Count)
- Functions detected: $($functions.Count)
- Imports detected: $($imports.Count)
- External call-site hits: $($hits.Count)
- Critical pattern hits inside engine: $($dangerHits.Count)

## Classes

$classLines

## Functions

$functionLines

## Imports

$importLines

## Call-sites detectes hors archives/backups

$hitLines

## Patterns critiques dans pf_engine.py

$dangerLines

$recommendation

## Next action recommandee

Si les call-sites sont faibles ou inexistants :
- marquer `pf_engine.py` comme legacy facade;
- extraire uniquement les fonctions encore appelees;
- ne pas creer de nouvelle spine lourde.

Si les call-sites sont nombreux :
- creer une matrice `caller -> function -> output`;
- patcher d'abord les tests avant refactor;
- garder wrapper de compatibilite.
"@

Set-Content -Path $reportPath -Value $report -Encoding UTF8
Ok "T002 audit report written: $reportPath"

# 7. Syntax quick checks.
Info "Running targeted syntax checks"
$targets = @(
    "Core\pf_normalizer.py",
    "Core\dashboard_server.py",
    "Core\dashboard_data_normalizer.py",
    "Core\dashboard_v74_contract_check.py"
)
foreach ($t in $targets) {
    if (Test-Path $t) {
        python -m py_compile $t
        Ok "Syntax OK: $t"
    } else {
        Warn "Missing syntax target: $t"
    }
}

# 8. Commit report + cleanup if needed.
Info "Git diff summary"
git diff --stat
git status --short

if (-not $NoGit) {
    if (Test-Path ".\scripts\auto_git_sync.ps1") {
        Info "Syncing with auto_git_sync.ps1"
        .\scripts\auto_git_sync.ps1 -Message "audit(t002): pf_engine usage map after T003"
    } else {
        Warn "auto_git_sync.ps1 not found. Manual git commit required."
    }
} else {
    Warn "NoGit set. Skipping Git sync."
}

# 9. Optional checkpoint.
if (-not $NoCheckpoint) {
    if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
        Info "Creating checkpoint"
        .\scripts\auto_checkpoint_claude.ps1 -Focus "T002 pf_engine usage audit after T003"
    } else {
        Warn "auto_checkpoint_claude.ps1 not found. Manual checkpoint required."
    }
} else {
    Warn "NoCheckpoint set. Skipping checkpoint."
}

Ok "Continuation complete"
Write-Host "[NEXT] Report: $reportPath" -ForegroundColor Cyan
