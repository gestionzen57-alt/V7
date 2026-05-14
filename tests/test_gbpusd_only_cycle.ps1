param(
    [string]$RepoRoot = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $RepoRoot

$logDir = Join-Path $RepoRoot "output"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "test_gbpusd_only_cycle.log"

.\run_powerflow_v76_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode dry-run *> $log

Write-Host "--- GBPUSD ONLY CYCLE TEST ---"
Write-Host "Log: $log"

$txt = Get-Content $log -Raw

if ($txt -notmatch "GBPUSD") {
    throw "FAIL: GBPUSD non detecte dans le cycle."
}

if ($txt -match "EURUSD|USDJPY") {
    throw "FAIL: symbole hors scope detecte: EURUSD ou USDJPY."
}

Write-Host "PASS: cycle dry-run limite a GBPUSD uniquement."

