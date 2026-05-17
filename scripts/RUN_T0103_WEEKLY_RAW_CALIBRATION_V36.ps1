param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core",
    [string[]]$SummaryRoot = @("C:\Users\User\Desktop\PF_T009_CLEAN_20260516_175946","C:\Users\User\Downloads"),
    [string]$TickDb = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core\tick_archive.db",
    [string]$OutputRoot = "C:\Users\User\Downloads\_b9_weekly_raw_calibration_v36_outputs",
    [string]$Symbol = "GBPUSD",
    [string]$Broker = "OneFunded Capital Ltd.",
    [int]$BrokerTimeShiftMin = 180,
    [string]$RawSourceMode = "HISTORICAL_RAW",
    [string]$RawDataVisibility = "MT5_RAW_ALIGNED",
    [string]$StartDate = "2026-05-04",
    [string]$EndDate = "2026-05-15"
)

$ErrorActionPreference = "Stop"
Write-Host "T0103 B9 WEEKLY RAW CALIBRATION V3.6" -ForegroundColor Cyan
Set-Location $RepoRoot
if (!(Test-Path ".\run_t009_raw_calibration_once.py")) { throw "Missing run_t009_raw_calibration_once.py" }
if (!(Test-Path ".\tools\make_t0103_weekly_raw_calibration_report.py")) { throw "Missing aggregator" }
if (!(Test-Path $TickDb)) { throw "Missing tick DB: $TickDb" }
New-Item -ItemType Directory -Force $OutputRoot | Out-Null

$all = @()
foreach ($root in $SummaryRoot) {
  if (Test-Path $root) { $all += Get-ChildItem $root -Recurse -Filter "t009_sequence_summary.json" -ErrorAction SilentlyContinue }
}
if ($all.Count -eq 0) { throw "No t009_sequence_summary.json found. Provide -SummaryRoot." }

$start = [datetime]::Parse($StartDate)
$end = [datetime]::Parse($EndDate).AddDays(1)
$selected = @()

foreach ($f in $all) {
  try { $j = Get-Content $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { continue }
  if ($null -eq $j.moments) { continue }
  $ok = $false
  foreach ($m in $j.moments) {
    foreach ($field in @("time_start","time_end")) {
      $v = $m.$field
      if ($null -eq $v) { continue }
      try {
        $dt = [datetime]::Parse([string]$v)
        if ($dt -ge $start -and $dt -lt $end) { $ok = $true }
      } catch {}
    }
  }
  if ($ok) { $selected += $f }
}
if ($selected.Count -eq 0) { throw "Summaries found, but no moment time in target date range." }

Write-Host "Selected summaries: $($selected.Count)" -ForegroundColor Green

$i = 0
foreach ($f in $selected) {
  $i++
  $safe = (($f.Directory.Parent.Name + "_" + $f.Directory.Name) -replace "[^A-Za-z0-9_\-]", "_")
  $out = Join-Path $OutputRoot $safe
  Write-Host ""
  Write-Host "[$i/$($selected.Count)] RUN $safe" -ForegroundColor Cyan
  python .\run_t009_raw_calibration_once.py `
    --summary-json $f.FullName `
    --tick-db $TickDb `
    --output $out `
    --symbol $Symbol `
    --broker $Broker `
    --broker-time-shift-min $BrokerTimeShiftMin `
    --raw-source-mode $RawSourceMode `
    --raw-data-visibility $RawDataVisibility
}

$reportMd = Join-Path $OutputRoot "B9_WEEK_CALIBRATION_RESULTS_20260504_20260515.md"
$reportCsv = Join-Path $OutputRoot "B9_WEEK_CALIBRATION_RESULTS_20260504_20260515.csv"

python .\tools\make_t0103_weekly_raw_calibration_report.py `
  --input-root $OutputRoot `
  --out-md $reportMd `
  --out-csv $reportCsv `
  --symbol $Symbol `
  --broker $Broker `
  --shift-min $BrokerTimeShiftMin

$zip = Join-Path (Split-Path $OutputRoot -Parent) "B9_RAW_CALIBRATION_OUTPUTS_20260504_20260515_V36.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $OutputRoot "*") -DestinationPath $zip -Force
Write-Host "DONE" -ForegroundColor Green
Write-Host "Outputs: $OutputRoot"
Write-Host "ZIP    : $zip"
