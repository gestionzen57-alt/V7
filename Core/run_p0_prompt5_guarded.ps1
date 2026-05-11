param(
    [string]$Symbol = "GBPUSD",
    [int]$WaitMinutes = 35
)

$ErrorActionPreference = "Continue"

function Log($m) {
    $ts = (Get-Date).ToUniversalTime().ToString("HH:mm:ss")
    Write-Host "[$ts UTC] $m"
}

Log "CHECK_M1_HEARTBEAT"

python .\p0_m1_heartbeat.py
$rc = $LASTEXITCODE

if ($rc -ne 0) {
    Log "M1_BLOCKER_DETECTED"
    Log "ACTION_REQUIRED: vérifier MT4 / EA GBPUSD M1. Le bridge tourne mais M1 est stale."
    Log "REPORT=output\m1_heartbeat_GBPUSD.json"
    exit 2
}

Log "M1_OK_OR_YELLOW"

Log "RUN_PROMPT5"
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_p0_prompt5_auto.ps1 -Symbol $Symbol -Pretty
$promptRc = $LASTEXITCODE

Log "PROMPT5_DONE rc=$promptRc"

if ($promptRc -ne 0) {
    Log "IF_BLOCKING_TF1: relancer EA M1 puis attendre $WaitMinutes minutes"
}

exit $promptRc
