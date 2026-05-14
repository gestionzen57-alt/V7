param(
    [string]$RepoPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT",
    [string]$Symbol = "GBPUSD",
    [ValidateSet("off", "dry-run", "send")]
    [string]$TelegramMode = "send",
    [switch]$ForceAlert,
    [switch]$RunCoreScheduler
)

$ErrorActionPreference = "Stop"

Set-Location $RepoPath

# PowerFlow V7.6.5 operational scope: GBPUSD only.
$ActiveSymbol = "GBPUSD"
if ($Symbol -and $Symbol.Trim().ToUpperInvariant() -ne "GBPUSD") {
    Write-Warning "PowerFlow V7.6.5 operational scope is GBPUSD only. Requested '$Symbol' ignored."
}

$env:POWERFLOW_SYMBOL = $ActiveSymbol
$env:POWERFLOW_SYMBOLS = $ActiveSymbol

Write-Host "[PowerFlow V7.6.5] Operational symbol scope: $ActiveSymbol" -ForegroundColor Cyan

if ($RunCoreScheduler) {
    Write-Host "=== RUN CORE SCHEDULER GBPUSD ONLY ===" -ForegroundColor Cyan
    python "Core\scheduler_powerflow_turbo_wrapper.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Core scheduler failed with exit code $LASTEXITCODE"
    }
}

Write-Host "=== RUN V7.6 TELEGRAM CYCLE TAIL ===" -ForegroundColor Cyan

$argsList = @(
    "patch\pf_v76_telegram_cycle_once.py",
    "--symbol", $ActiveSymbol,
    "--telegram-mode", $TelegramMode
)

if ($ForceAlert) {
    $argsList += "--force-alert"
}

python @argsList

if ($LASTEXITCODE -ne 0) {
    throw "V7.6 Telegram cycle failed with exit code $LASTEXITCODE"
}

