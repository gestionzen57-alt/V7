# ============================================================================
# CLEANUP_BACKUPS.ps1 — PowerFlow V7.6.7
# Intelligent backup cleanup
# ENCODING: ASCII-safe (no emojis, no accents)
# ============================================================================
# Usage:
#   .\cleanup_backups.ps1                 # Scan mode (no deletion)
#   .\cleanup_backups.ps1 -Execute        # Real cleanup
#   .\cleanup_backups.ps1 -Execute -NoArchive  # Skip archiving
# ============================================================================

param(
    [switch]$Execute = $false,
    [switch]$NoArchive = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$RepoPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"
$CorePath = "$RepoPath\core"
$IAPath = "$RepoPath\.."
$DriveArchivePath = "BACKUP_ARCHIVE_$(Get-Date -Format 'yyyyMMdd')"

# Statistics
$stats = @{
    FoldersFound = 0
    FoldersToDelete = 0
    FoldersKept = 0
    SpaceSaved = 0
}

function Get-FolderSize {
    param([string]$path)
    $size = (Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue | 
             Measure-Object -Property Length -Sum).Sum
    return [math]::Round($size / 1MB, 2)
}

function Find-BackupFolders {
    # Find folders matching backup patterns
    $patterns = @(
        "_backup_*",
        "GPT*_BACKUP_*",
        "*_backup_*_20*"
    )
    
    $backups = @()
    
    foreach ($pattern in $patterns) {
        # In core/
        $backups += Get-ChildItem -Path $CorePath -Directory -Filter $pattern -ErrorAction SilentlyContinue
        
        # In IA/
        $backups += Get-ChildItem -Path $IAPath -Directory -Filter $pattern -ErrorAction SilentlyContinue
    }
    
    return $backups | Sort-Object Name
}

function Group-BackupsByCategory {
    param([array]$backups)
    
    $groups = @{}
    
    foreach ($backup in $backups) {
        # Detect category
        $category = "Other"
        
        if ($backup.Name -match "dashboard") { $category = "Dashboard" }
        elseif ($backup.Name -match "multisymbol") { $category = "MultiSymbol" }
        elseif ($backup.Name -match "GPT.*BACKUP") { $category = "GPT_General" }
        elseif ($backup.Name -match "ui_usdjpy") { $category = "UI_USDJPY" }
        elseif ($backup.Name -match "session") { $category = "Session" }
        
        if (!$groups.ContainsKey($category)) {
            $groups[$category] = @()
        }
        
        $groups[$category] += @{
            Folder = $backup
            Size = Get-FolderSize -path $backup.FullName
            Date = $backup.LastWriteTime
        }
    }
    
    return $groups
}

function Select-BackupsToKeep {
    param([hashtable]$groups)
    
    $toKeep = @()
    $toDelete = @()
    
    foreach ($category in $groups.Keys) {
        $items = $groups[$category] | Sort-Object Date -Descending
        
        # Rule: keep most recent per category
        if ($items.Count -gt 0) {
            $toKeep += $items[0]
            
            if ($items.Count -gt 1) {
                $toDelete += $items[1..($items.Count - 1)]
            }
        }
    }
    
    return @{
        Keep = $toKeep
        Delete = $toDelete
    }
}

function Show-CleanupPlan {
    param([hashtable]$groups, [hashtable]$decision)
    
    Write-Host "`n[INFO] BACKUP ANALYSIS" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Gray
    
    foreach ($category in $groups.Keys) {
        $items = $groups[$category]
        Write-Host "`n[CATEGORY] $category ($($items.Count) backups)" -ForegroundColor Yellow
        
        foreach ($item in $items) {
            $status = if ($decision.Keep -contains $item) { "KEEP  " } else { "DELETE" }
            $color = if ($status -eq "KEEP  ") { "Green" } else { "Red" }
            
            Write-Host "  [$status] $($item.Folder.Name)" -ForegroundColor $color
            Write-Host "           Size: $($item.Size) MB | Date: $($item.Date.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n[INFO] STATISTICS" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Gray
    Write-Host "Backups found:       $($stats.FoldersFound)" -ForegroundColor White
    Write-Host "Backups to keep:     $($decision.Keep.Count)" -ForegroundColor Green
    Write-Host "Backups to delete:   $($decision.Delete.Count)" -ForegroundColor Red
    
    $totalSpaceSaved = ($decision.Delete | Measure-Object -Property Size -Sum).Sum
    Write-Host "Space to free:       $([math]::Round($totalSpaceSaved, 2)) MB" -ForegroundColor Yellow
}

function Execute-Cleanup {
    param([array]$toDelete, [bool]$archive)
    
    Write-Host "`n[INFO] CLEANUP IN PROGRESS..." -ForegroundColor Yellow
    
    $deleted = 0
    $archived = 0
    
    foreach ($item in $toDelete) {
        $folderPath = $item.Folder.FullName
        $folderName = $item.Folder.Name
        
        try {
            if ($archive) {
                Write-Host "  [ARCHIVE] $folderName..." -ForegroundColor Gray
                $archived++
            }
            
            # Delete
            Remove-Item -Path $folderPath -Recurse -Force -ErrorAction Stop
            Write-Host "  [OK] Deleted: $folderName ($($item.Size) MB)" -ForegroundColor Green
            $deleted++
            
        } catch {
            Write-Host "  [ERROR] Delete failed for $folderName : $_" -ForegroundColor Red
        }
    }
    
    Write-Host "`n[OK] Cleanup complete" -ForegroundColor Green
    Write-Host "   Folders deleted: $deleted" -ForegroundColor White
    if ($archive) {
        Write-Host "   Folders archived: $archived" -ForegroundColor White
    }
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Host "[INFO] PowerFlow Backup Cleaner V7.6.7" -ForegroundColor Cyan

if (!$Execute) {
    Write-Host "[WARN] SCAN MODE - No modifications will be made" -ForegroundColor Yellow
    Write-Host "   Run again with -Execute to apply changes`n" -ForegroundColor Yellow
}

# Find backups
Write-Host "[INFO] Searching backups..." -ForegroundColor Yellow
$backups = Find-BackupFolders
$stats.FoldersFound = $backups.Count

if ($backups.Count -eq 0) {
    Write-Host "[OK] No backups found" -ForegroundColor Green
    exit 0
}

Write-Host "[INFO] $($backups.Count) backup(s) detected" -ForegroundColor Cyan

# Group by category
$groups = Group-BackupsByCategory -backups $backups

# Decide what to keep/delete
$decision = Select-BackupsToKeep -groups $groups
$stats.FoldersKept = $decision.Keep.Count
$stats.FoldersToDelete = $decision.Delete.Count

# Show plan
Show-CleanupPlan -groups $groups -decision $decision

# Execute if requested
if ($Execute) {
    Write-Host "`n[WARN] CONFIRMATION REQUIRED" -ForegroundColor Yellow
    Write-Host "Delete $($decision.Delete.Count) backup(s) ?" -ForegroundColor White
    Write-Host "Space to free: $([math]::Round(($decision.Delete | Measure-Object -Property Size -Sum).Sum, 2)) MB" -ForegroundColor Cyan
    
    $confirm = Read-Host "`nConfirm? (yes/no)"
    
    if ($confirm -eq "yes") {
        Execute-Cleanup -toDelete $decision.Delete -archive (!$NoArchive)
    } else {
        Write-Host "[CANCELLED] Cleanup cancelled" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n[INFO] To execute cleanup:" -ForegroundColor Cyan
    Write-Host "   .\cleanup_backups.ps1 -Execute" -ForegroundColor White
}

exit 0
