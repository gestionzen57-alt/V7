param(
    [string]$Symbol = "GBPUSD",
    [string]$Db = "powerflow.db",
    [switch]$Loop,
    [switch]$Git,
    [switch]$NoDashboardRefresh,
    [int]$IntervalMinutes = 60
)

$ErrorActionPreference = "Continue"

$CoreDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $CoreDir
$OutputDir = Join-Path $CoreDir "output"
$LogsDir = Join-Path $CoreDir "logs"
$StateFile = Join-Path $OutputDir "p0_workflow_last_state.json"
$ConfigFile = Join-Path $CoreDir "p0_scheduler_config.json"

New-Item -ItemType Directory -Force $OutputDir | Out-Null
New-Item -ItemType Directory -Force $LogsDir | Out-Null

function UtcNow {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function UtcLogTime {
    return (Get-Date).ToUniversalTime().ToString("HH:mm:ss")
}

function Write-P0Log {
    param([string]$Message)

    $line = "[$(UtcLogTime) UTC] $Message"
    Write-Host $line

    $logPath = Join-Path $LogsDir ("p0_run_{0}.log" -f (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd"))
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

function Read-JsonFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-DbHealth {
    param(
        [string]$DbPath,
        [string]$Symbol
    )

    $py = @"
import sqlite3, json, os
from datetime import datetime, timezone

db = r"$DbPath"
symbol = "$Symbol"

result = {
    "exists": os.path.exists(db),
    "status": "RED",
    "rows_recent_anchor": 0,
    "last_created_at": None,
    "latest_tf_rows": {},
    "technical_risks": []
}

if not result["exists"]:
    result["technical_risks"].append("DB_MISSING")
    print(json.dumps(result))
    raise SystemExit(0)

try:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(force_snapshots)")]

    if "created_at" not in cols:
        result["technical_risks"].append("CREATED_AT_MISSING")
        print(json.dumps(result))
        raise SystemExit(0)

    last = conn.execute("""
        SELECT MAX(created_at)
        FROM force_snapshots
        WHERE symbol = ?
    """, (symbol,)).fetchone()[0]

    result["last_created_at"] = last

    if not last:
        result["technical_risks"].append("NO_ROWS_FOR_SYMBOL")
        print(json.dumps(result))
        raise SystemExit(0)

    # Anchor relative to DB's own latest timestamp, not Windows clock.
    rows = conn.execute("""
        SELECT timeframe, COUNT(*), MAX(created_at)
        FROM force_snapshots
        WHERE symbol = ?
          AND created_at >= datetime(?, '-15 minutes')
        GROUP BY timeframe
        ORDER BY timeframe
    """, (symbol, last)).fetchall()

    latest_tf_rows = {}
    total = 0
    for tf, n, mx in rows:
        latest_tf_rows[str(tf)] = {"rows": int(n), "last": mx}
        total += int(n)

    result["rows_recent_anchor"] = total
    result["latest_tf_rows"] = latest_tf_rows

    # P0 health logic:
    # GREEN if any live LTF is updating near DB latest.
    # YELLOW if DB exists but symbol has weak recent rows.
    # RED only if no data.
    if total >= 3:
        result["status"] = "GREEN"
    elif total > 0:
        result["status"] = "YELLOW"
        result["technical_risks"].append("LOW_RECENT_ROWS")
    else:
        result["status"] = "YELLOW"
        result["technical_risks"].append("NO_RECENT_ROWS_RELATIVE_TO_DB_ANCHOR")

    conn.close()

except Exception as e:
    result["status"] = "RED"
    result["technical_risks"].append("DB_HEALTH_EXCEPTION:" + type(e).__name__ + ":" + str(e))

print(json.dumps(result, ensure_ascii=False))
"@

    try {
        $raw = $py | python -
        return $raw | ConvertFrom-Json
    }
    catch {
        return [pscustomobject]@{
            exists = $false
            status = "RED"
            rows_recent_anchor = 0
            last_created_at = $null
            latest_tf_rows = @{}
            technical_risks = @("DB_HEALTH_SCRIPT_FAIL")
        }
    }
}

function Get-BridgeHealth {
    $procs = Get-CimInstance Win32_Process |
        Where-Object {
            ($_.CommandLine -match "capture_bridge\.py") -or
            ($_.CommandLine -match "python.*55555") -or
            ($_.CommandLine -match "Bridge TCP PowerFlow")
        }

    if ($procs) {
        return "GREEN"
    }

    # Bridge may be running in another terminal with commandline not visible.
    # Do not fail P0 only on process detection.
    return "YELLOW"
}

function Extract-P0Status {
    param([object]$Decision)

    if ($null -eq $Decision) {
        return "UNKNOWN"
    }

    $candidateFields = @(
        "final_status",
        "p0_status",
        "status",
        "verdict",
        "decision",
        "global_status",
        "p0_verdict",
        "result"
    )

    foreach ($f in $candidateFields) {
        if ($Decision.PSObject.Properties.Name -contains $f) {
            $v = [string]$Decision.$f
            if ($v -and $v.Trim().Length -gt 0) {
                return $v.Trim()
            }
        }
    }

    # Nested common structures
    foreach ($f in @("summary", "p0", "final_decision", "decision_summary")) {
        if ($Decision.PSObject.Properties.Name -contains $f) {
            $nested = $Decision.$f
            foreach ($nf in $candidateFields) {
                if ($nested -and ($nested.PSObject.Properties.Name -contains $nf)) {
                    $v = [string]$nested.$nf
                    if ($v -and $v.Trim().Length -gt 0) {
                        return $v.Trim()
                    }
                }
            }
        }
    }

    # Fallback: parse markdown report if present
    $md = Join-Path $OutputDir "P0_FINAL_DECISION.md"
    if (Test-Path $md) {
        $text = Get-Content $md -Raw -Encoding UTF8
        if ($text -match "PASS_CORE_PARTIAL_STRICT") { return "PASS_CORE_PARTIAL_STRICT" }
        if ($text -match "PASS_STRICT") { return "PASS_STRICT" }
        if ($text -match "PENDING_DATA_WINDOW") { return "PENDING_DATA_WINDOW" }
        if ($text -match "PASS_CORE") { return "PASS_CORE" }
        if ($text -match "FAIL") { return "FAIL" }
    }

    return "UNKNOWN"
}

function Extract-PendingPercent {
    param([object]$Decision)

    if ($null -eq $Decision) {
        return $null
    }

    $names = $Decision.PSObject.Properties.Name

    foreach ($f in @("pending_percent", "data_window_percent", "strict_progress_percent", "window_progress_percent")) {
        if ($names -contains $f) {
            return $Decision.$f
        }
    }

    foreach ($f in @("summary", "p0", "strict", "market_open", "data_window")) {
        if ($names -contains $f) {
            $nested = $Decision.$f
            if ($nested) {
                foreach ($nf in @("pending_percent", "data_window_percent", "strict_progress_percent", "window_progress_percent")) {
                    if ($nested.PSObject.Properties.Name -contains $nf) {
                        return $nested.$nf
                    }
                }
            }
        }
    }

    return $null
}

function Run-P0Once {
    $dbHealth = Get-DbHealth -DbPath $Db -Symbol $Symbol
    $bridgeHealth = Get-BridgeHealth

    $healthStatus = "GREEN"
    if ($dbHealth.status -eq "RED") {
        $healthStatus = "RED"
    }
    elseif ($dbHealth.status -eq "YELLOW" -or $bridgeHealth -eq "YELLOW") {
        $healthStatus = "YELLOW"
    }

    Write-P0Log "HEALTH: $healthStatus | DB=$($dbHealth.status) rows=$($dbHealth.rows_recent_anchor) last=$($dbHealth.last_created_at) | Bridge=$bridgeHealth"

    $autoScript = Join-Path $CoreDir "run_p0_final_auto.ps1"
    if (-not (Test-Path $autoScript)) {
        Write-P0Log "STATUS: FAIL | run_p0_final_auto.ps1 missing"
        return "FAIL"
    }

    Unblock-File $autoScript -ErrorAction SilentlyContinue

    Push-Location $CoreDir
    try {
        if ($Git) {
            & $autoScript -Symbol $Symbol -Git
        }
        else {
            & $autoScript -Symbol $Symbol
        }
    }
    finally {
        Pop-Location
    }

    $decisionPath = Join-Path $OutputDir "P0_FINAL_DECISION.json"
    $decision = Read-JsonFile $decisionPath
    $status = Extract-P0Status -Decision $decision
    $pct = Extract-PendingPercent -Decision $decision

    $previous = Read-JsonFile $StateFile
    $previousStatus = $null
    if ($previous -and ($previous.PSObject.Properties.Name -contains "status")) {
        $previousStatus = [string]$previous.status
    }

    if ($pct -ne $null -and "$pct" -ne "") {
        Write-P0Log "STATUS: $status | pending_window=$pct%"
    }
    else {
        Write-P0Log "STATUS: $status"
    }

    if ($previousStatus -and $previousStatus -ne $status) {
        Write-P0Log "STATE_CHANGE: $previousStatus -> $status"
    }

    $state = [ordered]@{
        generated_at_utc = UtcNow
        symbol = $Symbol
        status = $status
        previous_status = $previousStatus
        pending_percent = $pct
        db_health = $dbHealth
        bridge_health = $bridgeHealth
    }

    $state | ConvertTo-Json -Depth 8 | Set-Content $StateFile -Encoding UTF8

    if (-not $NoDashboardRefresh) {
        $cycleReportCore = Join-Path $OutputDir "cycle_report.json"
        $cycleReportRoot = Join-Path $ProjectRoot "output\cycle_report.json"

        if (Test-Path $cycleReportCore) {
            Copy-Item $cycleReportCore $cycleReportRoot -Force -ErrorAction SilentlyContinue
            Write-P0Log "DASHBOARD_REFRESH: copied Core/output/cycle_report.json"
        }
        elseif (Test-Path $cycleReportRoot) {
            Write-P0Log "DASHBOARD_REFRESH: root cycle_report already present"
        }
        else {
            Write-P0Log "DASHBOARD_REFRESH: no cycle_report found"
        }
    }

    return $status
}

# Create default config if missing
if (-not (Test-Path $ConfigFile)) {
    [ordered]@{
        enabled = $true
        interval_minutes = $IntervalMinutes
        auto_push_git = $false
        alert_on_status_change = $true
        log_directory = "logs/"
        symbol = $Symbol
    } | ConvertTo-Json -Depth 4 | Set-Content $ConfigFile -Encoding UTF8
}

if ($Loop) {
    Write-P0Log "LOOP_START: interval=${IntervalMinutes}min symbol=$Symbol"
    while ($true) {
        Run-P0Once | Out-Null
        Write-P0Log "NEXT_RUN: in ${IntervalMinutes}min"
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    }
}
else {
    Run-P0Once | Out-Null
}
