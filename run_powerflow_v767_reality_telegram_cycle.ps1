# PowerFlow V7.6.7 - Reality Board Telegram primary wrapper
# PF_V767_HASHTABLE_SPLAT_FIX_V2
param(
    [ValidateSet("dry-run", "live", "candidate-only")]
    [string]$TelegramMode = "dry-run",

    [switch]$RunCoreScheduler,

    [string]$Symbol = "GBPUSD",

    [switch]$Force
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== PowerFlow V7.6.7 Reality Telegram Cycle ==="
Write-Host ("Repo: " + $repo)
Write-Host ("Symbol: " + $Symbol)
Write-Host ("Reality Telegram mode: " + $TelegramMode)
Write-Host "Legacy V7.6 Telegram mode: dry-run/debug"

Push-Location $repo
try {
    # Hashtable splatting is mandatory here.
    # Array splatting can pass "-RunCoreScheduler" as positional RepoPath in the legacy script.
    $legacyParams = @{
        TelegramMode = "dry-run"
    }
    if ($RunCoreScheduler) {
        $legacyParams["RunCoreScheduler"] = $true
    }

    & ".\run_powerflow_v76_telegram_cycle.ps1" @legacyParams
    if ($LASTEXITCODE -ne 0) {
        throw ("Legacy V7.6 cycle failed with exit code " + $LASTEXITCODE)
    }

    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        throw "python introuvable dans le PATH"
    }

    $env:PYTHONIOENCODING = "utf-8"

    $rbArgs = @("patch\pf_telegram_reality_board_v767.py", "--symbol", $Symbol, "--mode", $TelegramMode)
    if ($Force) {
        $rbArgs += "--force"
    }

    & $py.Source @rbArgs
    if ($LASTEXITCODE -ne 0) {
        throw ("Reality Board Telegram failed with exit code " + $LASTEXITCODE)
    }

    Write-Host "OK - Reality Board Telegram cycle complete."
}
finally {
    Pop-Location
}
