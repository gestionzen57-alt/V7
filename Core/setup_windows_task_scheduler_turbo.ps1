param(
    [string]$Action = "status",
    [string]$CorePath = ".",
    [string]$TaskName = "PowerFlow_V72_MultiSymbol_Scheduler",
    [string]$Symbols = ""
)

$ErrorActionPreference = "Stop"
$CorePath = (Resolve-Path $CorePath).Path
$LogPath = Join-Path $CorePath "logs\task_scheduler.log"

if (-not (Test-Path (Join-Path $CorePath "logs"))) {
    New-Item -ItemType Directory -Path (Join-Path $CorePath "logs") | Out-Null
}

$SymbolsArg = ""
if ($Symbols -ne "") {
    $SymbolsArg = " --symbols $Symbols"
}

$TaskRun = "cmd.exe /c cd /d $CorePath && python scheduler_powerflow_turbo_wrapper.py$SymbolsArg >> $LogPath 2>&1"

if ($Action -eq "enable" -or $Action -eq "update") {
    schtasks /Change /TN $TaskName /TR $TaskRun
    if ($LASTEXITCODE -ne 0) {
        schtasks /Create /TN $TaskName /SC MINUTE /MO 5 /TR $TaskRun /F
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create or update scheduled task"
        }
    }
    schtasks /Change /TN $TaskName /ENABLE
    Write-Host "PASS enable/update turbo: $TaskName" -ForegroundColor Green
    Write-Host "Action: $TaskRun"
    exit 0
}

if ($Action -eq "disable") {
    schtasks /Change /TN $TaskName /DISABLE
    Write-Host "PASS disable: $TaskName" -ForegroundColor Yellow
    exit 0
}

if ($Action -eq "run") {
    schtasks /Run /TN $TaskName
    Write-Host "PASS run requested: $TaskName" -ForegroundColor Green
    exit 0
}

if ($Action -eq "status") {
    schtasks /Query /TN $TaskName /V /FO LIST
    exit $LASTEXITCODE
}

throw "Unknown Action. Use: enable, update, disable, run, status"
