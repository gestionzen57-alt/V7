# run_p0_final_auto.ps1
# PowerFlow V7.2 - P0 final automated runner
# Usage from Core:
#   .\run_p0_final_auto.ps1 -Symbol GBPUSD
#   .\run_p0_final_auto.ps1 -Symbol GBPUSD -Git

param(
    [string]$Db = ".\powerflow.db",
    [string]$Symbol = "GBPUSD",
    [string]$Since = "",
    [string]$End = "",
    [switch]$Git,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (!(Test-Path $Db)) { throw "DB not found: $Db" }
if (!(Test-Path ".\p0_final_validator.py")) { throw "Missing p0_final_validator.py in Core." }
if (!(Test-Path ".\run_powerflow_cycle_once.py")) { throw "Missing run_powerflow_cycle_once.py" }

New-Item -ItemType Directory -Force -Path ".\output" | Out-Null

if ($Since -eq "" -or $End -eq "") {
    $windowJson = python -c @"
import sqlite3, json
from datetime import datetime, timedelta

db = r'''$Db'''
symbol = r'''$Symbol'''
con = sqlite3.connect(db)
cur = con.cursor()
row = cur.execute('''
SELECT MAX(created_at)
FROM force_snapshots
WHERE symbol=?
  AND timeframe IN (1,5,15)
''', (symbol,)).fetchone()
latest = row[0]
if not latest:
    raise SystemExit('No latest timestamp found for symbol/tfs')
dt = datetime.fromisoformat(latest.replace('Z', '+00:00'))
if dt.tzinfo is not None:
    dt = dt.replace(tzinfo=None)
since = dt - timedelta(minutes=120)
end = dt + timedelta(minutes=15)
print(json.dumps({
    'latest': latest,
    'since': since.replace(microsecond=0).isoformat(),
    'end': end.replace(microsecond=0).isoformat()
}))
"@
    $window = $windowJson | ConvertFrom-Json
    if ($Since -eq "") { $Since = $window.since }
    if ($End -eq "") { $End = $window.end }
    Write-Host "Auto window from DB:" -ForegroundColor Cyan
    Write-Host "  latest=$($window.latest)"
    Write-Host "  since =$Since"
    Write-Host "  end   =$End"
}

$env:POWERFLOW_CYCLE_SINCE = $Since
$env:POWERFLOW_CYCLE_END = $End

Write-Host "`n[1/3] Running PowerFlow cycle..." -ForegroundColor Cyan
python .\run_powerflow_cycle_once.py `
  --db $Db `
  --symbol $Symbol `
  --pretty `
  --output .\output\cycle_report.json

Write-Host "`n[2/3] Running P0 final validator..." -ForegroundColor Cyan
python .\p0_final_validator.py `
  --db $Db `
  --symbol $Symbol `
  --since $Since `
  --cycle-report .\output\cycle_report.json `
  --output-md .\output\P0_FINAL_DECISION.md `
  --output-json .\output\P0_FINAL_DECISION.json

$statusObj = Get-Content .\output\P0_FINAL_DECISION.json -Raw | ConvertFrom-Json
$status = $statusObj.global_status

Write-Host "`n[3/3] P0 status: $status" -ForegroundColor Green
Write-Host "Report: .\output\P0_FINAL_DECISION.md"

if ($Git) {
    Write-Host "`nGit enabled." -ForegroundColor Cyan
    git add .\run_powerflow_cycle_once.py .\p0_final_validator.py .\run_p0_final_auto.ps1 .\output\P0_FINAL_DECISION.md .\output\P0_FINAL_DECISION.json .\output\cycle_report.json
    if ($status -eq "PASS_STRICT") {
        $msg = "P0: strict market-open validation PASS"
    } elseif ($status -eq "PASS_CORE_PARTIAL_STRICT") {
        $msg = "P0: core perception PASS, strict pending data window"
    } else {
        $msg = "P0: validation partial, review required"
    }
    git commit -m $msg
    if (-not $NoPush) { git push origin main } else { Write-Host "Push skipped because -NoPush was set." }
}
