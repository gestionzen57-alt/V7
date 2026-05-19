# auto_claude_session_close_b9.ps1
# Fin de session Claude - mise a jour automatique etat B9

$CORE = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
$DOWNLOADS = "C:\Users\User\Downloads"
$DATE = Get-Date -Format "yyyy-MM-dd HH:mm"

Set-Location $CORE

Write-Host "=== AUTO CLOSE SESSION B9 ===" -ForegroundColor Cyan

# 1. Run tests - capture resultat
Write-Host "Running tests..." -ForegroundColor Yellow
$testOutput = python -m pytest tests\ --tb=no -q 2>&1
$testSummary = $testOutput | Select-String "passed|failed|error" | Select-Object -Last 1
if (-not $testSummary) { $testSummary = "No pytest summary captured" }

# 2. Git status
$gitStatus = git status --short
$gitHead = git rev-parse --short HEAD
$gitBranch = git branch --show-current

# 3. Mettre a jour CLAUDE_MASTER_B9 (section etat)
$masterFile = "$CORE\Docs\CLAUDE_MASTER_B9.md"
if (Test-Path $masterFile) {
    (Get-Content $masterFile) -replace "Git HEAD : .*", "Git HEAD : $gitHead ($gitBranch)" | Set-Content $masterFile
    (Get-Content $masterFile) -replace "Derniere session Claude : .*", "Derniere session Claude : $DATE" | Set-Content $masterFile
} else {
    Write-Host "WARN: CLAUDE_MASTER_B9.md introuvable: $masterFile" -ForegroundColor Yellow
}

# 4. Git add + commit + push
if (Test-Path $masterFile) {
    git add Docs\CLAUDE_MASTER_B9.md
    git commit -m "chore(session): auto-close B9 $DATE [$testSummary]"
    git push origin $gitBranch
}

Write-Host "=== SESSION FERMEE ===" -ForegroundColor Green
Write-Host "Branche : $gitBranch" -ForegroundColor White
Write-Host "Commit  : $(git rev-parse --short HEAD)" -ForegroundColor White
Write-Host "Tests   : $testSummary" -ForegroundColor White
Write-Host ""
Write-Host "Copie message pour prochain Claude :" -ForegroundColor Cyan
Write-Host "PowerFlow V7.6.7 B9 - Reprise session" -ForegroundColor Yellow
Write-Host "Branche active : $gitBranch" -ForegroundColor Yellow
Write-Host "Dernier commit : $(git rev-parse --short HEAD)" -ForegroundColor Yellow
Write-Host "Tests : $testSummary" -ForegroundColor Yellow
Write-Host "Lire : Docs\CLAUDE_MASTER_B9.md" -ForegroundColor Yellow
