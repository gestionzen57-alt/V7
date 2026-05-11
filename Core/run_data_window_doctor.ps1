param(
    [string]$Symbol = "GBPUSD",
    [string]$Db = "powerflow.db",
    [string]$Tfs = "1,5,15,30,60,240",
    [int]$LookbackMinutes = 180,
    [switch]$Pretty
)

$ErrorActionPreference = "Continue"

$CoreDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $CoreDir

try {
    $prettyArg = @()
    if ($Pretty) { $prettyArg = @("--pretty") }

    python .\pf_data_window_doctor.py `
        --db $Db `
        --symbol $Symbol `
        --tfs $Tfs `
        --lookback-minutes $LookbackMinutes `
        --output-json ".\output\data_window_doctor_$Symbol.json" `
        --output-md ".\output\data_window_doctor_$Symbol.md" `
        @prettyArg

    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
