param(
    [ValidateSet("enable", "disable", "status")]
    [string]$Action = "status",
    [string]$TaskName = "PowerFlow_V72_MultiSymbol_Scheduler",
    [string]$CorePath = ".",
    [string]$PythonPath = "python"
)

$ErrorActionPreference = "Stop"
$CoreFull = (Resolve-Path $CorePath).Path
$LogDir = Join-Path $CoreFull "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$TaskLog = Join-Path $LogDir "task_scheduler.log"
$Scheduler = Join-Path $CoreFull "scheduler_powerflow.py"

if ($Action -eq "enable") {
    if (-not (Test-Path $Scheduler)) { throw "scheduler_powerflow.py introuvable: $Scheduler" }
    $Command = "cd /d `"$CoreFull`" && $PythonPath scheduler_powerflow.py >> `"$TaskLog`" 2>&1"
    schtasks /Create /TN $TaskName /SC MINUTE /MO 5 /TR "cmd.exe /c $Command" /F | Out-Host
    schtasks /Change /TN $TaskName /ENABLE | Out-Host
    Write-Host "PASS enable: $TaskName"
    Write-Host "Log: $TaskLog"
    exit 0
}

if ($Action -eq "disable") {
    schtasks /Change /TN $TaskName /DISABLE | Out-Host
    Write-Host "PASS disable: $TaskName"
    exit 0
}

schtasks /Query /TN $TaskName /V /FO LIST | Out-Host
