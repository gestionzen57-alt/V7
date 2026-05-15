# ============================================================================
# AUTO_GIT_SYNC.ps1 — PowerFlow V7.6.7
# Git synchronisation automatique avec commit intelligent
# ENCODING: ASCII-safe (no emojis, no accents)
# ============================================================================
# Usage:
#   .\auto_git_sync.ps1                  # Sync normal
#   .\auto_git_sync.ps1 -Force           # Force push
#   .\auto_git_sync.ps1 -Message "fix"   # Custom message
# ============================================================================

param(
    [string]$Message = "",
    [switch]$Force = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$RepoPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"
$LogFile = "$RepoPath\git\sync.log"
$GitIgnorePath = "$RepoPath\.gitignore"

# Create log directory
if (!(Test-Path "$RepoPath\git")) {
    New-Item -ItemType Directory -Path "$RepoPath\git" -Force | Out-Null
}

function Write-Log {
    param([string]$msg, [string]$level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$level] $msg"
    Add-Content -Path $LogFile -Value $logLine
    if ($Verbose) { Write-Host $logLine }
}

function Get-SmartCommitMessage {
    # Auto-detect change types and generate intelligent message
    $status = git -C $RepoPath status --short
    
    $hasCore = $status | Select-String "core/"
    $hasDocs = $status | Select-String "docs/"
    $hasPatch = $status | Select-String "patch/"
    $hasTests = $status | Select-String "tests/"
    
    $modifiedFiles = ($status | Measure-Object).Count
    
    if ($hasCore -and $hasPatch) {
        return "[PATCH] Core engine patches and documentation ($modifiedFiles files)"
    } elseif ($hasCore) {
        return "[CORE] PowerFlow engine updates ($modifiedFiles files)"
    } elseif ($hasDocs) {
        return "[DOCS] Documentation sync ($modifiedFiles files)"
    } elseif ($hasPatch) {
        return "[FIX] Runtime patches ($modifiedFiles files)"
    } elseif ($hasTests) {
        return "[TEST] Test suite updates ($modifiedFiles files)"
    } else {
        return "[AUTO] Session sync ($modifiedFiles files)"
    }
}

function Update-GitIgnore {
    # Ensure .gitignore has correct exclusions
    $ignoreRules = @(
        "# PowerFlow auto-generated",
        "*.db-shm",
        "*.db-wal",
        "powerflow.db",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        "logs/*.log",
        "output/*.json",
        "git/sync.log",
        "*_backup_*/",
        "GPT*_BACKUP_*/",
        "desktop.ini"
    )
    
    if (!(Test-Path $GitIgnorePath)) {
        Write-Log "Creating initial .gitignore" "INFO"
        Set-Content -Path $GitIgnorePath -Value ($ignoreRules -join "`n") -Encoding ASCII
    } else {
        $current = Get-Content $GitIgnorePath -Raw
        $needsUpdate = $false
        foreach ($rule in $ignoreRules) {
            if ($current -notmatch [regex]::Escape($rule)) {
                Add-Content -Path $GitIgnorePath -Value $rule -Encoding ASCII
                $needsUpdate = $true
            }
        }
        if ($needsUpdate) {
            Write-Log ".gitignore updated" "INFO"
        }
    }
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Log "========== GIT SYNC START ==========" "INFO"
Write-Host "[INFO] PowerFlow Git Auto-Sync V7.6.7" -ForegroundColor Cyan

# Verify Git repo exists
if (!(Test-Path "$RepoPath\.git")) {
    Write-Log "ERROR: No Git repo in $RepoPath" "ERROR"
    Write-Host "[ERROR] No Git repository found" -ForegroundColor Red
    exit 1
}

# Update .gitignore
Update-GitIgnore

# Change to repo
Set-Location $RepoPath

# Check status
Write-Host "[INFO] Checking for changes..." -ForegroundColor Yellow
$gitStatus = git status --porcelain

if (!$gitStatus -and !$Force) {
    Write-Log "No changes detected" "INFO"
    Write-Host "[OK] No changes to sync" -ForegroundColor Green
    exit 0
}

# Count files
$modifiedCount = ($gitStatus | Measure-Object).Count
Write-Host "[INFO] $modifiedCount file(s) modified" -ForegroundColor Cyan

# Show if verbose
if ($Verbose) {
    Write-Host "`nModified files:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
}

# Stage all
Write-Host "[INFO] Staging files..." -ForegroundColor Yellow
git add -A
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: git add failed" "ERROR"
    Write-Host "[ERROR] Staging failed" -ForegroundColor Red
    exit 1
}

# Generate message
if ($Message -eq "") {
    $commitMsg = Get-SmartCommitMessage
} else {
    $commitMsg = $Message
}

Write-Host "[INFO] Message: $commitMsg" -ForegroundColor Cyan

# Commit
Write-Host "[INFO] Committing..." -ForegroundColor Yellow
git commit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: git commit failed: $commitMsg" "ERROR"
    Write-Host "[ERROR] Commit failed" -ForegroundColor Red
    exit 1
}

Write-Log "Commit success: $commitMsg" "INFO"

# Pull before push
Write-Host "[INFO] Pulling latest changes..." -ForegroundColor Yellow
git pull origin main --rebase
if ($LASTEXITCODE -ne 0) {
    Write-Log "WARNING: Potential conflict during pull" "WARN"
    Write-Host "[WARN] Conflict detected - manual resolution needed" -ForegroundColor Yellow
    Write-Host "Run manually: git pull origin main --rebase" -ForegroundColor Yellow
    exit 1
}

# Push
Write-Host "[INFO] Pushing to GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: git push failed" "ERROR"
    Write-Host "[ERROR] Push failed" -ForegroundColor Red
    exit 1
}

Write-Log "Push success to origin/main" "INFO"

# Summary
$lastCommit = git log -1 --oneline
Write-Host "`n[OK] SYNC COMPLETE" -ForegroundColor Green
Write-Host "[INFO] Last commit: $lastCommit" -ForegroundColor Cyan
Write-Log "========== GIT SYNC END ==========" "INFO"

exit 0
