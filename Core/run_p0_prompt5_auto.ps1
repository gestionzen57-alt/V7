param(
    [string]$Symbol = "GBPUSD",
    [string]$Db = "powerflow.db",
    [switch]$Git,
    [switch]$NoWorkflow,
    [switch]$Pretty
)

$ErrorActionPreference = "Continue"

$CoreDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputDir = Join-Path $CoreDir "output"
New-Item -ItemType Directory -Force $OutputDir | Out-Null

function Log($m) {
    $ts = (Get-Date).ToUniversalTime().ToString("HH:mm:ss")
    Write-Host "[$ts UTC] $m"
}

Push-Location $CoreDir

try {
    Log "PROMPT5_START symbol=$Symbol db=$Db"

    if (-not $NoWorkflow) {
        Log "RUN_P0_FULL_WORKFLOW"
        if ($Git) {
            powershell -NoProfile -ExecutionPolicy Bypass -File .\run_p0_full_workflow.ps1 -Symbol $Symbol -Git
        }
        else {
            powershell -NoProfile -ExecutionPolicy Bypass -File .\run_p0_full_workflow.ps1 -Symbol $Symbol
        }
    }

    Log "RUN_DATA_WINDOW_DOCTOR"
    powershell -NoProfile -ExecutionPolicy Bypass -File .\run_data_window_doctor.ps1 -Symbol $Symbol -Db $Db -Pretty

    $doctorJson = Join-Path $OutputDir "data_window_doctor_$Symbol.json"

    if (-not (Test-Path $doctorJson)) {
        Log "PROMPT5_STATUS=DATA_WINDOW_FAIL reason=doctor_json_missing"
        exit 2
    }

    $d = Get-Content $doctorJson -Raw -Encoding UTF8 | ConvertFrom-Json

    Log "PROMPT5_STATUS=$($d.verdict)"
    Log "LTF_PASS=$($d.summary.ltf_pass) STRICT_PASS=$($d.summary.strict_pass) BLOCKING=$($d.summary.blocking_tfs -join ',')"
    Log "REPORT_JSON=$doctorJson"
    Log "REPORT_MD=$(Join-Path $OutputDir "data_window_doctor_$Symbol.md")"

    if ($d.verdict -eq "DATA_WINDOW_FAIL") {
        exit 2
    }

    exit 0
}
finally {
    Pop-Location
}
