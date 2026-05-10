param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "",

    [switch]$IncludeDeletes,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"

function Step($msg) {
    Write-Host ""
    Write-Host "=== $msg ===" -ForegroundColor Cyan
}

function IsProtected($path) {
    $p = $path -replace "\\", "/"

    $protected = @(
        "powerflow.db",
        "Core/powerflow.db",
        "capture_bridge.py",
        "Core/capture_bridge.py",
        "Core/pf_temporal_node_state.py",
        "Core/pf_relational_gravity_bridge.py",
        "Core/cockpit_agentic_state_v01_orchestral.py"
    )

    foreach ($x in $protected) {
        if ($p -ieq $x) { return $true }
    }

    return $false
}

function IsRuntime($path) {
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
    if ($p -like "desktop.ini") { return $true }
    if ($p -like "*/desktop.ini") { return $true }

    return $false
}

Step "PowerFlow close session V3"

$repo = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Pas dans un repository Git."
}

Set-Location $repo
Write-Host "Repo: $repo"

Step "Nettoyage desktop.ini dans .git"

Get-ChildItem ".git" -Filter "desktop.ini" -Recurse -Force -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

Step "Reset zone staged"

git reset --quiet

Step "Mise a jour .gitignore"

if (!(Test-Path ".gitignore")) {
    New-Item ".gitignore" -ItemType File | Out-Null
}

$ignoreLines = @(
    "# PowerFlow runtime outputs",
    "output/",
    "Core/output/",
    "Core/reports/",
    "Core/0.85",
    "*.pkl",
    "__pycache__/",
    "*.pyc",
    ".venv/",
    "venv/",
    "desktop.ini"
)

$gitignoreRaw = Get-Content ".gitignore" -Raw

foreach ($line in $ignoreLines) {
    $escaped = [regex]::Escape($line)
    if ($gitignoreRaw -notmatch "(?m)^$escaped$") {
        Add-Content ".gitignore" $line
    }
}

Step "Restauration des suppressions accidentelles"

if (-not $IncludeDeletes) {
    $deletedFiles = git ls-files --deleted

    foreach ($d in $deletedFiles) {
        if ([string]::IsNullOrWhiteSpace($d)) { continue }

        if (IsProtected $d) {
            Write-Host "Protege, restaure: $d" -ForegroundColor Yellow
            git restore -- "$d"
            continue
        }

        Write-Host "Restaure: $d" -ForegroundColor Yellow
        git restore -- "$d"
    }
} else {
    Write-Host "Mode IncludeDeletes actif: les suppressions seront autorisees." -ForegroundColor Red
}

Step "Fetch origin"

git fetch --prune origin
if ($LASTEXITCODE -ne 0) {
    Write-Host "Fetch warning: on continue, mais verifier le remote ensuite." -ForegroundColor Yellow
}

Step "Detection fichiers propres"

$statusLines = git status --porcelain=v1 -uall
$filesToAdd = New-Object System.Collections.Generic.List[string]

foreach ($line in $statusLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }

    $xy = $line.Substring(0,2)
    $path = $line.Substring(3)

    if ($path -match " -> ") {
        $path = ($path -split " -> ")[-1]
    }

    $isDeleted = $xy.Contains("D")

    if (IsProtected $path) {
        Write-Host "Skip protege: $path" -ForegroundColor Yellow
        continue
    }

    if (IsRuntime $path) {
        Write-Host "Skip runtime: $path" -ForegroundColor DarkYellow
        continue
    }

    if ($isDeleted -and -not $IncludeDeletes) {
        Write-Host "Skip deletion: $path" -ForegroundColor Yellow
        continue
    }

    $filesToAdd.Add($path)
}

Step "py_compile Core/*.py modifies"

$pyFiles = $filesToAdd |
    Where-Object { $_ -like "Core/*.py" -and (Test-Path $_) } |
    Sort-Object -Unique

foreach ($py in $pyFiles) {
    Write-Host "Compile: $py"
    python -m py_compile $py

    if ($LASTEXITCODE -ne 0) {
        throw "py_compile failed: $py"
    }
}

Step "Staging"

$uniqueFiles = $filesToAdd | Sort-Object -Unique

if ($uniqueFiles.Count -eq 0) {
    Write-Host "Rien a ajouter."
} else {
    foreach ($f in $uniqueFiles) {
        Write-Host "Add: $f"
        git add -- "$f"
    }
}

Step "Etat staged"

git status --short

git diff --cached --quiet
$hasStaged = $LASTEXITCODE -ne 0

if (-not $hasStaged) {
    Write-Host ""
    Write-Host "Rien a committer." -ForegroundColor Green

    Step "Etat final"
    git status
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "Session: PowerFlow sync $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

Step "Commit"

git commit -m "$Message"
if ($LASTEXITCODE -ne 0) {
    throw "Commit failed."
}

if (-not $NoPush) {
    Step "Push"

    git push origin main
    if ($LASTEXITCODE -ne 0) {
        throw "Push failed."
    }
} else {
    Write-Host "Push ignore car -NoPush actif."
}

Step "Etat final"

git status
