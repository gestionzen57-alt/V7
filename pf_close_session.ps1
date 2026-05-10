param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "",

    [switch]$IncludeDeletes,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "=== $msg ===" -ForegroundColor Cyan
}

function Is-ProtectedPath($path) {
    $p = $path -replace "\\", "/"

    $protected = @(
        "powerflow.db",
        "Core/powerflow.db",
        "Core/capture_bridge.py",
        "capture_bridge.py",
        "Core/pf_temporal_node_state.py",
        "Core/pf_relational_gravity_bridge.py",
        "Core/cockpit_agentic_state_v01_orchestral.py"
    )

    foreach ($item in $protected) {
        if ($p -ieq $item) { return $true }
    }

    return $false
}

function Is-IgnoredRuntimePath($path) {
    $p = $path -replace "\\", "/"

    if ($p -like "output/*") { return $true }
    if ($p -like "Core/output/*") { return $true }
    if ($p -like "Core/reports/*") { return $true }
    if ($p -eq "Core/0.85") { return $true }
    if ($p -like "*.pkl") { return $true }
    if ($p -like "__pycache__/*") { return $true }
    if ($p -like "*/__pycache__/*") { return $true }
    if ($p -like "*.pyc") { return $true }
    if ($p -like ".venv/*") { return $true }
    if ($p -like "venv/*") { return $true }

    return $false
}

Write-Step "PowerFlow session close"

$repo = git rev-parse --show-toplevel
Set-Location $repo
Write-Host "Repo: $repo"

Write-Step "Mise a jour .gitignore runtime"

$gitignoreAdd = @"

# PowerFlow runtime outputs
output/
Core/output/
Core/reports/
Core/0.85
*.pkl
__pycache__/
*.pyc
.venv/
venv/
"@

if (!(Test-Path ".gitignore")) {
    New-Item ".gitignore" -ItemType File | Out-Null
}

$currentGitignore = Get-Content ".gitignore" -Raw
if ($currentGitignore -notmatch "PowerFlow runtime outputs") {
    Add-Content ".gitignore" $gitignoreAdd
    Write-Host ".gitignore mis a jour"
} else {
    Write-Host ".gitignore deja OK"
}

Write-Step "Verification Git remote"
git fetch origin

Write-Step "Detection des fichiers modifies"

$statusLines = git status --porcelain=v1 -uall
$filesToAdd = New-Object System.Collections.Generic.List[string]
$deletedSkipped = New-Object System.Collections.Generic.List[string]
$protectedSkipped = New-Object System.Collections.Generic.List[string]
$runtimeSkipped = New-Object System.Collections.Generic.List[string]

foreach ($line in $statusLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }

    $xy = $line.Substring(0,2)
    $path = $line.Substring(3)

    if ($path -match " -> ") {
        $path = ($path -split " -> ")[-1]
    }

    $isDeleted = $xy.Contains("D")

    if (Is-ProtectedPath $path) {
        $protectedSkipped.Add($path)
        continue
    }

    if (Is-IgnoredRuntimePath $path) {
        $runtimeSkipped.Add($path)
        continue
    }

    if ($isDeleted -and -not $IncludeDeletes) {
        $deletedSkipped.Add($path)
        continue
    }

    $filesToAdd.Add($path)
}

if ($protectedSkipped.Count -gt 0) {
    Write-Host ""
    Write-Host "Proteges non stages:" -ForegroundColor Yellow
    $protectedSkipped | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" }
}

if ($runtimeSkipped.Count -gt 0) {
    Write-Host ""
    Write-Host "Runtime ignores non stages:" -ForegroundColor DarkYellow
    $runtimeSkipped | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" }
}

if ($deletedSkipped.Count -gt 0) {
    Write-Host ""
    Write-Host "Suppressions non stagees. Normal. Pour les inclure: -IncludeDeletes" -ForegroundColor Yellow
    $deletedSkipped | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" }
}

Write-Step "py_compile sur fichiers Python Core modifies"

$pyFiles = $filesToAdd |
    Where-Object { $_ -like "Core/*.py" -and (Test-Path $_) } |
    Sort-Object -Unique

foreach ($py in $pyFiles) {
    Write-Host "Compile: $py"
    python -m py_compile $py
}

Write-Step "Staging propre"

if ($filesToAdd.Count -eq 0) {
    Write-Host "Aucun fichier propre a ajouter."
} else {
    foreach ($file in ($filesToAdd | Sort-Object -Unique)) {
        Write-Host "Add: $file"
        git add -- "$file"
    }
}

Write-Step "Diff staged"

git status --short

git diff --cached --quiet
$hasStaged = $LASTEXITCODE -ne 0

if (-not $hasStaged) {
    Write-Host ""
    Write-Host "Aucun changement stage. Rien a committer." -ForegroundColor Green
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "Session: PowerFlow sync $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

Write-Step "Commit"
git commit -m "$Message"

if (-not $NoPush) {
    Write-Step "Push"
    git push origin main
} else {
    Write-Host "Push ignore car -NoPush actif"
}

Write-Step "Etat final"
git status
