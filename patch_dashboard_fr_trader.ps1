param(
    [string]$RepoPath = ".",
    [string]$DashboardFile = ""
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path $RepoPath
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceJs = Join-Path $scriptDir "dashboard_fr_trader_labels.js"
$targetJs = Join-Path $root "dashboard_fr_trader_labels.js"

if (-not (Test-Path $sourceJs)) {
    throw "dashboard_fr_trader_labels.js introuvable a cote du script patch."
}

Copy-Item $sourceJs $targetJs -Force
Write-Host "[OK] Copie: dashboard_fr_trader_labels.js"

$candidates = @()
if ($DashboardFile -ne "") {
    $candidates += (Join-Path $root $DashboardFile)
} else {
    $candidates += (Join-Path $root "dashboard_v74.html")
    $candidates += (Join-Path $root "dashboard_powerflow_v74.html")
    $candidates += (Join-Path $root "dashboard_live.html")
}

$existing = $candidates | Where-Object { Test-Path $_ }
if ($existing.Count -eq 0) {
    throw "Aucun dashboard HTML trouve. Precise -DashboardFile .\dashboard_v74.html"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$scriptTag = '<script src="dashboard_fr_trader_labels.js"></script>'

foreach ($file in $existing) {
    $html = Get-Content $file -Raw -Encoding UTF8
    if ($html -match "dashboard_fr_trader_labels\.js") {
        Write-Host "[SKIP] Deja injecte: $file"
        continue
    }

    $backup = "$file.bak_fr_trader_$stamp"
    Copy-Item $file $backup -Force

    if ($html -match "</body>") {
        $html = $html -replace "</body>", "  $scriptTag`r`n</body>"
    } else {
        $html = $html + "`r`n$scriptTag`r`n"
    }

    Set-Content $file $html -Encoding UTF8
    Write-Host "[OK] Injection FR trader: $file"
    Write-Host "[OK] Backup: $backup"
}

Write-Host ""
Write-Host "Validation rapide:"
Write-Host "  1. Relancer/rafraichir le dashboard avec Ctrl+F5"
Write-Host "  2. Verifier: HIGH_ZONE_REJECTION -> Rejet de zone haute"
Write-Host "  3. Verifier: PAIR_UP / PAIR_DOWN ne sont plus affiches bruts"
Write-Host "  4. Lancer si disponible: python dashboard_v74_contract_check.py"
