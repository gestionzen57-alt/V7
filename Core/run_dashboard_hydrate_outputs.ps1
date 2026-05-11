param(
    [string]$CorePath = ".",
    [string]$Symbol = "GBPUSD",
    [string]$Since = "2026-05-11T01:15:00",
    [string]$Tfs = "1,5,15",
    [switch]$Serve,
    [switch]$StopOnError
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Core = Resolve-Path $CorePath
Set-Location $Core

if (!(Test-Path ".\output")) { New-Item -ItemType Directory -Path ".\output" | Out-Null }
if (!(Test-Path ".\logs")) { New-Item -ItemType Directory -Path ".\logs" | Out-Null }

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$logPath = ".\logs\dashboard_hydration_$stamp.log"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Append-LogRaw {
    param([string]$Text)
    $max = 8
    for ($i = 1; $i -le $max; $i++) {
        try {
            [System.IO.File]::AppendAllText((Join-Path (Resolve-Path ".") $logPath.TrimStart(".\")), $Text, $utf8NoBom)
            return
        } catch {
            if ($i -eq $max) { throw }
            Start-Sleep -Milliseconds (80 * $i)
        }
    }
}

function Write-Log {
    param([string]$Message)
    $line = "[" + (Get-Date).ToUniversalTime().ToString("HH:mm:ss") + " UTC] " + $Message
    Write-Host $line
    Append-LogRaw ($line + [Environment]::NewLine)
}

function Run-Step {
    param(
        [string]$Name,
        [string]$File,
        [string[]]$ArgsList
    )

    if (!(Test-Path ".\$File")) {
        Write-Log "SKIP $Name - missing runner $File"
        return
    }

    Write-Log "RUN $Name - python $File $($ArgsList -join ' ')"

    $output = @()
    $exitCode = 0

    try {
        $output = & python ".\$File" @ArgsList 2>&1
        $exitCode = $LASTEXITCODE
    } catch {
        $exitCode = 1
        $output = @($_.Exception.Message)
    }

    if ($output) {
        $buf = New-Object System.Text.StringBuilder
        foreach ($line in $output) {
            [void]$buf.Append("    ")
            [void]$buf.Append([string]$line)
            [void]$buf.Append([Environment]::NewLine)
        }
        Append-LogRaw $buf.ToString()
    }

    if ($exitCode -ne 0) {
        Write-Log "WARN $Name - exit code $exitCode"
        if ($StopOnError) { throw "$Name failed" }
    } else {
        Write-Log "OK $Name"
    }
}

function Normalize-AlertQueue {
    $queuePaths = @(
        ".\behavioral_alert_queue.json",
        ".\output\behavioral_alert_queue.json"
    )

    foreach ($queuePath in $queuePaths) {
        $existingAlerts = @()

        if (Test-Path $queuePath) {
            try {
                $rawQueue = Get-Content $queuePath -Raw | ConvertFrom-Json

                if ($rawQueue -is [System.Array]) {
                    $existingAlerts = @($rawQueue)
                }
                elseif ($rawQueue.PSObject.Properties.Name -contains "behavioral_alert_queue") {
                    $existingAlerts = @($rawQueue.behavioral_alert_queue)
                }
                elseif ($rawQueue.PSObject.Properties.Name -contains "alerts") {
                    $existingAlerts = @($rawQueue.alerts)
                }
                elseif ($rawQueue.PSObject.Properties.Name -contains "items") {
                    $existingAlerts = @($rawQueue.items)
                }
                elseif ($rawQueue.PSObject.Properties.Name -contains "queue") {
                    $existingAlerts = @($rawQueue.queue)
                }
            } catch {
                $existingAlerts = @()
            }
        }

        $fixedQueue = @{
            timestamp_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
            source = "run_dashboard_hydrate_outputs_queue_normalizer"
            behavioral_alert_queue = $existingAlerts
            alerts = $existingAlerts
            items = $existingAlerts
            queue = $existingAlerts
            technical_risks = @()
        } | ConvertTo-Json -Depth 50

        $fullQueuePath = Join-Path (Resolve-Path ".") $queuePath.TrimStart(".\")
        [System.IO.File]::WriteAllText($fullQueuePath, $fixedQueue, $utf8NoBom)
        Write-Log "OK alert queue normalized: $queuePath"
    }
}

Write-Log "PowerFlow Dashboard Hydrate Outputs CANONICAL"
Write-Log "CorePath=$Core Symbol=$Symbol Since=$Since TFs=$Tfs"

Run-Step "B1 Legacy Regime" "run_regime_engine_once.py" @("--db", "powerflow.db", "--pretty")
Run-Step "B1 HMM Regime" "run_hmm_regime_once.py" @("--db", "powerflow.db", "--pretty")

$endUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")
Run-Step "B3 Force Kinematics" "run_force_kinematics_once.py" @(
    "--db", "powerflow.db",
    "--symbol", $Symbol,
    "--start", $Since,
    "--end", $endUtc,
    "--timeframes", $Tfs,
    "--out", "output\force_kinematics_state.json",
    "--json"
)

Run-Step "P1 Currency Energy" "run_currency_energy_probe_once.py" @("--db", "powerflow.db", "--symbol", $Symbol, "--pretty")
Run-Step "B4 Temporal Density" "run_temporal_density_once.py" @("--db", "powerflow.db", "--tfs", $Tfs, "--summary", "--pretty")
Run-Step "B4 Wavelet Density" "run_wavelet_density_once.py" @("--db", "powerflow.db", "--symbol", $Symbol)
Run-Step "B5 Spearman Gravity" "run_spearman_gravity_once.py" @("--db", "powerflow.db", "--tfs", $Tfs, "--summary", "--pretty")
Run-Step "B7 Fractal Resonance" "run_fractal_resonance_once.py" @("--db", "powerflow.db", "--symbol", $Symbol)
Run-Step "B7 Volatility Texture" "run_volatility_texture_once.py" @("--db", "powerflow.db", "--symbol", $Symbol)
Run-Step "B2 Cascade" "run_cascade_engine_once.py" @("--pretty")

Normalize-AlertQueue

Run-Step "Guard Entropy" "run_alert_entropy_once.py" @("--pretty")
Run-Step "Session Overlay" "run_session_overlay_once.py" @("--pretty")
Run-Step "Data Quality LTF" "run_data_quality_guard_once.py" @("--db", "powerflow.db", "--since", $Since, "--tfs", $Tfs, "--pretty", "--output", "output\data_quality_report.json")
Run-Step "B6 Memory" "run_memory_query_once.py" @("--queue", "output\behavioral_alert_queue.json", "--limit", "50")
Run-Step "P2 Behavioral Mapper" "run_behavioral_alert_mapper_once.py" @("--temporal", "output\temporal_density_state.json")

Normalize-AlertQueue

Run-Step "Temporal Node State" "run_temporal_node_state_once.py" @("--db", "powerflow.db", "--symbol", $Symbol, "--recent-minutes", "60", "--timeframes", "1,5,15,30,60", "--pretty")

$placeholder = @{
    _powerflow_contract = "V7.2_DASHBOARD_AGGREGATE_PLACEHOLDER"
    status = "MISSING"
    freshness = "MISSING"
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    data_age_seconds = 0
    source = "dashboard_hydrate_canonical"
    payload = @{
        dashboard = "placeholder"
        note = "Runtime data comes from dashboard_surface, cycle_report, P0 decision and node outputs."
    }
    technical_risks = @("DASHBOARD_AGGREGATE_PLACEHOLDER_ONLY")
}
$dashboardDataPath = Join-Path (Resolve-Path ".\output") "dashboard_data_v7.2.json"
$json = $placeholder | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($dashboardDataPath, $json, $utf8NoBom)
Write-Log "OK dashboard_data_v7.2.json placeholder refreshed UTF8 no BOM"

if (Test-Path ".\run_dashboard_live_stack.ps1") {
    Write-Log "RUN Dashboard stack Normalize Validate Doctor"
    try {
        & powershell -ExecutionPolicy Bypass -File ".\run_dashboard_live_stack.ps1" -Root . -Html ".\dashboard_live_v7.2_final.html" -Normalize -Validate -Doctor
        Write-Log "OK Dashboard stack"
    } catch {
        Write-Log "WARN Dashboard stack failed - $($_.Exception.Message)"
        if ($StopOnError) { throw }
    }
} else {
    Write-Log "WARN run_dashboard_live_stack.ps1 missing"
}

Write-Log "Hydration log written to $logPath"

if ($Serve) {
    Write-Log "SERVE Dashboard"
    & powershell -ExecutionPolicy Bypass -File ".\run_dashboard_live_stack.ps1" -Root . -Html ".\dashboard_live_v7.2_final.html" -Serve
}
