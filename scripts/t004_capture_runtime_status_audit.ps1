param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$DbPath = "Core/powerflow.db",
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-H] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-H capture runtime status audit"
Log "RepoPath = $RepoPath"
Log "DbPath = $DbPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-H commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$auditDir = Join-Path $RepoPath "Docs\Audits"
if (!(Test-Path $auditDir)) {
    New-Item -ItemType Directory -Path $auditDir -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$processSnapshotPath = Join-Path $auditDir "T004_CAPTURE_RUNTIME_PROCESS_SNAPSHOT_$stamp.json"
$networkSnapshotPath = Join-Path $auditDir "T004_CAPTURE_RUNTIME_NETWORK_SNAPSHOT_$stamp.json"

Log "Capturing process snapshot"
$processRows = @()
try {
    $processRows = @(Get-CimInstance Win32_Process | Where-Object {
        $cl = [string]$_.CommandLine
        $nm = [string]$_.Name
        ($cl -match "PowerFlow|powerflow|capture|bridge|scheduler|python|telegram|terminal|MetaTrader|MT4|MT5") -or
        ($nm -match "python|powershell|pwsh|terminal|terminal64|MetaTrader")
    } | Select-Object ProcessId, Name, CommandLine, CreationDate)
} catch {
    Warn "Process snapshot failed: $($_.Exception.Message)"
    $processRows = @()
}
$processRows | ConvertTo-Json -Depth 5 | Set-Content -Path $processSnapshotPath -Encoding UTF8

Log "Capturing network snapshot"
$networkRows = @()
try {
    $networkRows = @(Get-NetTCPConnection -ErrorAction Stop | Where-Object {
        $_.State -in @("Listen", "Established")
    } | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess)
} catch {
    Warn "Get-NetTCPConnection failed: $($_.Exception.Message)"
    $networkRows = @()
}
$networkRows | ConvertTo-Json -Depth 5 | Set-Content -Path $networkSnapshotPath -Encoding UTF8

$pythonAudit = Join-Path $RepoPath ".t004h_capture_runtime_status.py"
$dbPathJson = ($DbPath | ConvertTo-Json -Compress)
$processSnapshotJson = ($processSnapshotPath | ConvertTo-Json -Compress)
$networkSnapshotJson = ($networkSnapshotPath | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3

DB_PATH_ARG = $dbPathJson
PROCESS_SNAPSHOT = Path($processSnapshotJson)
NETWORK_SNAPSHOT = Path($networkSnapshotJson)

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
plan_dir = repo / "Docs" / "Plans"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
plan_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path)

def load_json_any(path: Path):
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    if data is None:
        return []
    if isinstance(data, list):
        return data
    return [data]

def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

db_path = Path(DB_PATH_ARG)
if not db_path.is_absolute():
    db_path = repo / db_path

process_rows = load_json_any(PROCESS_SNAPSHOT)
network_rows = load_json_any(NETWORK_SNAPSHOT)

# Process classification.
capture_keywords = ["capture_bridge", "capture", "bridge"]
scheduler_keywords = ["scheduler_powerflow", "run_powerflow", "telegram", "cycle"]
python_keywords = ["python.exe", "python", "py.exe"]

capture_processes = []
scheduler_processes = []
python_processes = []

for row in process_rows:
    text = ((row.get("Name") or "") + " " + (row.get("CommandLine") or "")).lower()
    if any(k in text for k in capture_keywords):
        capture_processes.append(row)
    if any(k in text for k in scheduler_keywords):
        scheduler_processes.append(row)
    if any(k in text for k in python_keywords):
        python_processes.append(row)

# DB status and latest timestamps.
db_status = {
    "path": rel(db_path),
    "exists": db_path.exists(),
    "size_bytes": db_path.stat().st_size if db_path.exists() else None,
    "modified_at": dt.datetime.fromtimestamp(db_path.stat().st_mtime, tz=dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z") if db_path.exists() else None,
    "tables": [],
    "total_rows": None,
    "error": None,
}

time_candidates = ["created_at", "timestamp", "time", "logged_at", "detected_at", "source_created_at", "bar_time", "ts", "datetime"]
symbol_candidates = ["symbol", "pair", "instrument"]

if db_path.exists():
    try:
        uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        try:
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            total = 0
            for table in tables:
                info = con.execute("PRAGMA table_info(" + quote_ident(table) + ")").fetchall()
                columns = [row[1] for row in info]
                lower = {c.lower(): c for c in columns}
                symbol_col = next((lower[c] for c in symbol_candidates if c in lower), None)
                time_col = next((lower[c] for c in time_candidates if c in lower), None)
                row_count = con.execute("SELECT COUNT(*) AS n FROM " + quote_ident(table)).fetchone()["n"]
                total += row_count if isinstance(row_count, int) else 0
                max_time = None
                if time_col and row_count:
                    try:
                        max_time = con.execute("SELECT MAX(" + quote_ident(time_col) + ") AS max_t FROM " + quote_ident(table)).fetchone()["max_t"]
                    except Exception:
                        max_time = None
                db_status["tables"].append({
                    "table": table,
                    "row_count": row_count,
                    "symbol_col": symbol_col,
                    "time_col": time_col,
                    "max_time": max_time,
                })
            db_status["total_rows"] = total
        finally:
            con.close()
    except Exception as exc:
        db_status["error"] = str(exc)

# Latest logs.
log_roots = [repo / "logs", repo / "Core" / "logs"]
latest_logs = []
for root in log_roots:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".log", ".txt", ".json", ".md"}:
            continue
        try:
            stat = path.stat()
        except Exception:
            continue
        latest_logs.append({
            "path": rel(path),
            "size_bytes": stat.st_size,
            "modified_at": dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        })
latest_logs.sort(key=lambda x: x["modified_at"], reverse=True)

# Launch scripts and likely entrypoints.
entry_patterns = ["capture_bridge", "scheduler_powerflow", "run_powerflow", "start_bridge", "on_tick", "powerflow.db", "Core/powerflow.db"]
entry_files = []
for root in [repo / "Core", repo / "scripts"]:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".ps1", ".bat", ".cmd", ".md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            if any(p.lower() in line.lower() for p in entry_patterns):
                hits.append({"line": i, "text": line.strip()[:260]})
        if hits:
            entry_files.append({"file": rel(path), "hits": hits[:80]})

# Status classification.
db_recent = False
if db_status.get("modified_at"):
    try:
        mod = dt.datetime.fromisoformat(db_status["modified_at"].replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - mod).total_seconds()
        db_status["modified_age_seconds"] = age
        db_recent = age < 600
    except Exception:
        db_status["modified_age_seconds"] = None

if not db_path.exists():
    status = "ACTIVE_DB_NOT_FOUND"
elif capture_processes:
    if db_recent:
        status = "CAPTURE_PROCESS_DETECTED_DB_RECENT"
    else:
        status = "CAPTURE_PROCESS_DETECTED_DB_STALE"
elif scheduler_processes:
    if db_recent:
        status = "SCHEDULER_PROCESS_DETECTED_DB_RECENT"
    else:
        status = "SCHEDULER_PROCESS_DETECTED_DB_STALE"
elif python_processes:
    if db_recent:
        status = "PYTHON_PROCESS_DETECTED_DB_RECENT"
    else:
        status = "PYTHON_PROCESS_DETECTED_DB_STALE"
else:
    if db_recent:
        status = "NO_CAPTURE_PROCESS_DETECTED_BUT_DB_RECENT"
    else:
        status = "NO_CAPTURE_PROCESS_DETECTED_DB_STALE"

recommendations = []
if status == "NO_CAPTURE_PROCESS_DETECTED_DB_STALE":
    recommendations.append("No capture-like process detected and DB is stale. Start or verify live capture before rerunning T004-G.")
elif status == "CAPTURE_PROCESS_DETECTED_DB_STALE":
    recommendations.append("Capture-like process detected but DB is stale. Inspect whether process writes to another DB or insertion is blocked.")
elif status == "CAPTURE_PROCESS_DETECTED_DB_RECENT":
    recommendations.append("Capture-like process and recent DB modification detected. Rerun T004-G with a longer window or inspect per-table insert path.")
elif status == "NO_CAPTURE_PROCESS_DETECTED_BUT_DB_RECENT":
    recommendations.append("DB changed recently without capture process visible in snapshot. Check scheduler/other writer process or short-lived capture.")
elif status.startswith("SCHEDULER_PROCESS"):
    recommendations.append("Scheduler process detected. Confirm whether scheduler also owns capture insertion or only reads DB.")
else:
    recommendations.append("Inspect process snapshot and DB timestamp before changing capture or engine code.")

recommendations.append("Do not change engine/scoring logic. This is live capture health and process supervision.")

contract = {
    "contract": "POWERFLOW_T004_CAPTURE_RUNTIME_STATUS",
    "created_at": now,
    "db_path": rel(db_path),
    "status": status,
    "process_snapshot": rel(PROCESS_SNAPSHOT),
    "network_snapshot": rel(NETWORK_SNAPSHOT),
    "capture_processes": capture_processes,
    "scheduler_processes": scheduler_processes,
    "python_processes": python_processes[:30],
    "network_rows_sample": network_rows[:80],
    "db_status": db_status,
    "latest_logs": latest_logs[:40],
    "entry_files": entry_files[:120],
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_CAPTURE_RUNTIME_STATUS.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_CAPTURE_RUNTIME_STATUS_CHECKLIST_" + stamp + ".md")
md = []
md.append("# T004-H Capture Runtime Status Checklist")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Verdict")
md.append("")
md.append("- Status: " + status)
md.append("- DB: " + rel(db_path))
md.append("- DB modified_at: " + str(db_status.get("modified_at")))
md.append("- DB modified_age_seconds: " + str(db_status.get("modified_age_seconds")))
md.append("- Capture processes detected: " + str(len(capture_processes)))
md.append("- Scheduler processes detected: " + str(len(scheduler_processes)))
md.append("- Python processes detected: " + str(len(python_processes)))
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## DB tables")
md.append("")
for t in db_status.get("tables", []):
    md.append("- " + t["table"] + " | rows=" + str(t.get("row_count")) + " | symbol_col=" + str(t.get("symbol_col")) + " | time_col=" + str(t.get("time_col")) + " | max_time=" + str(t.get("max_time")))
md.append("")
md.append("## Capture-like processes")
md.append("")
if capture_processes:
    for p in capture_processes:
        md.append("- PID " + str(p.get("ProcessId")) + " | " + str(p.get("Name")) + " | " + str(p.get("CommandLine")))
else:
    md.append("- none")
md.append("")
md.append("## Scheduler-like processes")
md.append("")
if scheduler_processes:
    for p in scheduler_processes:
        md.append("- PID " + str(p.get("ProcessId")) + " | " + str(p.get("Name")) + " | " + str(p.get("CommandLine")))
else:
    md.append("- none")
md.append("")
md.append("## Latest logs")
md.append("")
if latest_logs:
    for item in latest_logs[:20]:
        md.append("- " + item["path"] + " | modified=" + item["modified_at"] + " | size=" + str(item["size_bytes"]))
else:
    md.append("- none")
md.append("")
md.append("## Entry files")
md.append("")
for item in entry_files[:60]:
    md.append("### " + item["file"])
    for hit in item["hits"][:20]:
        md.append("- line " + str(hit["line"]) + " | " + hit["text"])
    md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not patch engine/scoring modules until live capture activity is confirmed.")
md.append("")
md.append("## Next action")
md.append("")
md.append("If capture is inactive/stale, start the intended capture stack and rerun T004-G. If capture is active but DB stale, audit insertion target/path.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_capture_runtime_status_contract.py"
test_lines = [
    "from __future__ import annotations",
    "",
    "import json",
    "from pathlib import Path",
    "",
    "",
    "def _repo() -> Path:",
    "    return Path(__file__).resolve().parents[1]",
    "",
    "",
    "def test_t004_capture_runtime_status_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_RUNTIME_STATUS.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_CAPTURE_RUNTIME_STATUS"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert isinstance(data["recommendations"], list)',
    '    assert isinstance(data["db_status"], dict)',
    "",
    "",
    "def test_t004_capture_runtime_status_known():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_RUNTIME_STATUS.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {',
    '        "ACTIVE_DB_NOT_FOUND",',
    '        "CAPTURE_PROCESS_DETECTED_DB_RECENT",',
    '        "CAPTURE_PROCESS_DETECTED_DB_STALE",',
    '        "SCHEDULER_PROCESS_DETECTED_DB_RECENT",',
    '        "SCHEDULER_PROCESS_DETECTED_DB_STALE",',
    '        "PYTHON_PROCESS_DETECTED_DB_RECENT",',
    '        "PYTHON_PROCESS_DETECTED_DB_STALE",',
    '        "NO_CAPTURE_PROCESS_DETECTED_BUT_DB_RECENT",',
    '        "NO_CAPTURE_PROCESS_DETECTED_DB_STALE",',
    '    }',
    '    assert data["status"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "db_path": rel(db_path),
    "capture_process_count": len(capture_processes),
    "scheduler_process_count": len(scheduler_processes),
    "python_process_count": len(python_processes),
    "db_modified_at": db_status.get("modified_at"),
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running capture runtime status audit"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-H capture runtime status audit failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usdjpy_thin_data_diagnostic_contract.py `
    tests/test_t004_capture_db_path_audit_contract.py `
    tests/test_t004_active_db_decision_contract.py `
    tests/test_t004_active_db_symbol_density_contract.py `
    tests/test_t004_usdjpy_thin_root_cause_contract.py `
    tests/test_t004_capture_symbol_routing_audit_contract.py `
    tests/test_t004_live_capture_health_counter_contract.py `
    tests/test_t004_capture_runtime_status_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-H tests failed"
}
Ok "T004-H tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_CAPTURE_RUNTIME_STATUS.json",
    "tests/test_t004_capture_runtime_status_contract.py",
    "scripts/t004_capture_runtime_status_audit.ps1",
    $processSnapshotPath,
    $networkSnapshotPath
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_CAPTURE_RUNTIME_STATUS_CHECKLIST_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-H files"
foreach ($p in $pathsToAdd) {
    if (Test-Path $p) {
        git add -- $p
        if ($LASTEXITCODE -ne 0) { throw "git add failed for $p" }
    } else {
        Warn "Path not found for staging: $p"
    }
}

$staged = git diff --cached --name-only
if (-not $staged) {
    Warn "No staged T004-H changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): inspect live capture runtime status"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }

    git pull origin main
    if ($LASTEXITCODE -ne 0) { throw "git pull failed" }

    git push origin main
    if ($LASTEXITCODE -ne 0) { throw "git push failed" }
}

if (-not $SkipCheckpoint) {
    $checkpointDir = Join-Path $RepoPath "Docs\Checkpoints"
    if (!(Test-Path $checkpointDir)) {
        New-Item -ItemType Directory -Path $checkpointDir -Force | Out-Null
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_H_CAPTURE_RUNTIME_STATUS.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-H capture runtime status"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-H capture runtime status audit"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Capture runtime status audit created."
    $content += "- Runtime unchanged."
    $content += "- DB read-only."
    $content += "- Dashboard workspace files intentionally left untouched."
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""
    $content += "## Next step"
    $content += ""
    $content += "Use runtime status to decide whether to start capture, audit insertion target, or rerun T004-G with active feed."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-H capture runtime status"
        if ($LASTEXITCODE -ne 0) { throw "checkpoint commit failed" }
        git pull origin main
        if ($LASTEXITCODE -ne 0) { throw "git pull checkpoint failed" }
        git push origin main
        if ($LASTEXITCODE -ne 0) { throw "git push checkpoint failed" }
        Ok "Targeted checkpoint committed and pushed"
    } else {
        Warn "No checkpoint changes staged"
    }
} else {
    Warn "Checkpoint skipped by flag"
}

Ok "T004-H capture runtime status audit complete"
Log "Final status"
git status --short
git log --oneline -7
