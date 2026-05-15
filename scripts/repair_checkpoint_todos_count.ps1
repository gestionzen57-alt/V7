param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$Focus = "T002 runtime surface audit checkpoint repair"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info([string]$m) { Write-Host ("[CHK-REPAIR] " + $m) }
function Ok([string]$m) { Write-Host ("[OK] " + $m) }
function Warn([string]$m) { Write-Host ("[WARN] " + $m) }
function Fail([string]$m) { Write-Host ("[FAIL] " + $m); exit 1 }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath
Info "RepoPath = $RepoPath"

$checkpoint = Join-Path $RepoPath "scripts\auto_checkpoint_claude.ps1"
if (-not (Test-Path $checkpoint)) {
    Fail "scripts\auto_checkpoint_claude.ps1 not found"
}

Info "Git preflight"
git status --short
git branch --show-current
git log --oneline -5

# Runtime dashboard state is noisy and should not be part of infra repair commits.
$dash = Join-Path $RepoPath "Core\dashboard_data.json"
if (Test-Path $dash) {
    $dashStatus = git status --short -- "Core/dashboard_data.json"
    if ($dashStatus) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before repair commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = $checkpoint + ".bak_todos_count_" + $stamp
Copy-Item $checkpoint $backup -Force
Ok "Backup created: $backup"

$content = Get-Content $checkpoint -Raw
$patched = $content

# StrictMode fix: PowerShell scalar strings may not expose .Count reliably in this script context.
# Force array wrapping before Count for todos.
$patched = $patched -replace '\$todos\.Count\s+-gt\s+0', '@($todos).Count -gt 0'
$patched = $patched -replace '\$todos\.Count', '@($todos).Count'

# Same defensive fix for common scalar/list variables if present. This is conservative and only affects Count reads.
$patched = $patched -replace '\$modifiedFiles\.Count', '@($modifiedFiles).Count'
$patched = $patched -replace '\$changedFiles\.Count', '@($changedFiles).Count'
$patched = $patched -replace '\$changes\.Count', '@($changes).Count'

if ($patched -eq $content) {
    Warn "No Count patterns were changed. The script may already be patched."
} else {
    Set-Content -Path $checkpoint -Value $patched -Encoding UTF8
    Ok "Patched auto_checkpoint_claude.ps1 Count handling"
}

Info "Checking PowerShell parser"
$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $checkpoint -Raw), [ref]$null)
Ok "Parser check completed"

Info "Running checkpoint again"
& $checkpoint -Focus $Focus
if ($LASTEXITCODE -ne 0) {
    Fail "auto_checkpoint_claude.ps1 returned exit code $LASTEXITCODE"
}

Info "Final git status"
git status --short
git log --oneline -5
Ok "Checkpoint Count repair complete"
