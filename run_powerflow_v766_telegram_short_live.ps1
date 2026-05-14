param(
    [ValidateSet("dry-run", "send")][string]$TelegramMode = "dry-run",
    [string]$Symbol = "GBPUSD"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Keep long V7.6 format available for debug/calibration, but avoid sending it here.
if (Test-Path ".\run_powerflow_v76_telegram_cycle.ps1") {
    powershell -ExecutionPolicy Bypass -File ".\run_powerflow_v76_telegram_cycle.ps1" -TelegramMode dry-run | Out-Host
}

python ".\patch\pf_telegram_short_live_v766.py" --symbol $Symbol --mode $TelegramMode
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
