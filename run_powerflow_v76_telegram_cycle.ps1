param(
    [string]$RepoPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT",
    [string]$Symbol = "GBPUSD",
    [string]$CoreSymbols = "GBPUSD,EURUSD,USDJPY,USDCAD,USDCHF,AUDUSD",
    [ValidateSet("off", "dry-run", "send")]
    [string]$TelegramMode = "dry-run",
    [switch]$ForceAlert,
    [switch]$RunCoreScheduler
)

$ErrorActionPreference = "Stop"

Set-Location $RepoPath

# PowerFlow V7.6.7 trader scope: GBPUSD only.
# Core/B8 scope may be wider for DB/multicurrency analysis.
$ActiveSymbol = "GBPUSD"
if ($Symbol -and $Symbol.Trim().ToUpperInvariant() -ne "GBPUSD") {
    Write-Warning "PowerFlow V7.6.7 trader scope is GBPUSD only. Requested '$Symbol' ignored for Telegram/trader tail."
}

$CoreSymbolScope = $CoreSymbols
if (-not $CoreSymbolScope -or [string]::IsNullOrWhiteSpace($CoreSymbolScope)) {
    $CoreSymbolScope = $ActiveSymbol
}

$env:POWERFLOW_SYMBOL = $ActiveSymbol
$env:POWERFLOW_SYMBOLS = $CoreSymbolScope

Write-Host "[PowerFlow V7.6.7] Trader symbol scope: $ActiveSymbol" -ForegroundColor Cyan
Write-Host "[PowerFlow V7.6.7] Core/B8 symbol scope: $CoreSymbolScope" -ForegroundColor Cyan
if ($RunCoreScheduler) {
    Write-Host "=== RUN CORE SCHEDULER MULTI-SYMBOL FOR B8 / DB ANALYSIS ===" -ForegroundColor Cyan
    python "Core\scheduler_powerflow_turbo_wrapper.py" --symbols "$CoreSymbolScope"
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

# PF_V767_REALITY_BOARD_CYCLE_HOOK_BEGIN
Write-Host ""
Write-Host "=== V7.6.7 REALITY BOARD REFRESH ==="
$pfV767RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pfV767RealityBoardRunner = Join-Path $pfV767RepoRoot "patch\pf_reality_board_state_once.py"

if (Test-Path $pfV767RealityBoardRunner) {
    Push-Location $pfV767RepoRoot
    try {
        $pfV767PythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($pfV767PythonCommand) {
            & $pfV767PythonCommand.Source $pfV767RealityBoardRunner --symbol "GBPUSD"
        } else {
            & python $pfV767RealityBoardRunner --symbol "GBPUSD"
        }

        if ($LASTEXITCODE -ne 0) {
            throw ("Reality Board refresh failed with exit code " + $LASTEXITCODE)
        }
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "Reality Board runner missing; refresh skipped." -ForegroundColor Yellow
}
# PF_V767_REALITY_BOARD_CYCLE_HOOK_END
