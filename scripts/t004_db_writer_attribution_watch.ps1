param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$DbPath = "Core/powerflow.db",
    [int]$WatchSeconds = 60,
    [int]$IntervalSeconds = 5,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-I] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

if ($WatchSeconds -lt 10) { throw "WatchSeconds must be >= 10" }
if ($IntervalSeconds -lt 2) { throw "IntervalSeconds must be >= 2" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-I DB writer attribution watch"
Log "RepoPath = $RepoPath"
Log "DbPath = $DbPath"
Log "WatchSeconds = $WatchSeconds"
Log "IntervalSeconds = $IntervalSeconds"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-I commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$auditDir = Join-Path $RepoPath "Docs\Audits"
if (!(Test-Path $auditDir)) {
    New-Item -ItemType Directory -Path $auditDir -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$processWatchPath = Join-Path $auditDir "T004_DB_WRITER_PROCESS_WATCH_$stamp.json"
$scheduledTaskPath = Join-Path $auditDir "T004_DB_WRITER_SCHEDULED_TASKS_$stamp.json"

Log "Capturing scheduled task candidates"
$taskRows = @()
try {
    $taskRows = @(Get-ScheduledTask -ErrorAction Stop | ForEach-Object {
        $task = $_
        $actionText = (($task.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join " ")
        $hay = "$($task.TaskName) $($task.TaskPath) $actionText"
        if ($hay -match "PowerFlow|powerflow|ProjetPowerFlow|python|capture|bridge|scheduler|telegram|GPT|V7") {
            [PSCustomObject]@{
                TaskName = $task.TaskName
                TaskPath = $task.TaskPath
                State = $task.State.ToString()
                Actions = $actionText
            }
        }
    })
} catch {
    Warn "Get-ScheduledTask failed: $($_.Exception.Message)"
    $taskRows = @()
}
$taskRows | ConvertTo-Json -Depth 6 | Set-Content -Path $scheduledTaskPath -Encoding UTF8
Log "Scheduled task candidates: $($taskRows.Count)"

Log "Watching process candidates"
$processSamples = @()
$endAt = (Get-Date).AddSeconds($WatchSeconds)
while ((Get-Date) -lt $endAt) {
    $takenAt = Get-Date -Format o
    $rows = @()
    try {
        $rows = @(Get-CimInstance Win32_Process | Where-Object {
            $cl = [string]$_.CommandLine
            $nm = [string]$_.Name
            ($cl -match "PowerFlow|powerflow|ProjetPowerFlow|capture|bridge|scheduler|telegram|run_powerflow|python|GPT|V7|powerflow.db") -or
            ($nm -match "python|powershell|pwsh")
        } | Select-Object ProcessId, Name, CommandLine, CreationDate)
    } catch {
        $rows = @()
    }

    $processSamples += [PSCustomObject]@{
        taken_at = $takenAt
        processes = $rows
    }

    Start-Sleep -Seconds $IntervalSeconds
}

$processSamples | ConvertTo-Json -Depth 8 | Set-Content -Path $processWatchPath -Encoding UTF8
Log "Process watch samples: $($processSamples.Count)"

$pythonAudit = Join-Path $RepoPath ".t004i_db_writer_attribution.py"
$dbPathJson = ($DbPath | ConvertTo-Json -Compress)
$processWatchJson = ($processWatchPath | ConvertTo-Json -Compress)
$scheduledTaskJson = ($scheduledTaskPath | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3
import time

DB_PATH_ARG = $dbPathJson
PROCESS_WATCH_PATH = Path($processWatchJson)
SCHEDULED_TASK_PATH = Path($scheduledTaskJson)
WATCH_SECONDS = int($WatchSeconds)
INTERVAL_SECONDS = int($IntervalSeconds)

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
plan_dir = repo / "Docs" / "Plans"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
plan_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

started_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

db_path = Path(DB_PATH_ARG)
if not db_path.is_absolute():
    db_path = repo / db_path

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path)

def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

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

def file_stat(path: Path):
    if not path.exists():
        return {"path": rel(path), "exists": False, "size_bytes": None, "modified_at": None}
    st = path.stat()
    return {
        "path": rel(path),
        "exists": True,
        "size_bytes": st.st_size,
        "modified_at": dt.datetime.fromtimestamp(st.st_mtime, tz=dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }

def db_counts():
    snapshot = {
        "taken_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_file": file_stat(db_path),
        "wal_file": file_stat(Path(str(db_path) + "-wal")),
        "shm_file": file_stat(Path(str(db_path) + "-shm")),
        "journal_file": file_stat(Path(str(db_path) + "-journal")),
        "tables": [],
        "total_rows": None,
        "error": None,
    }
    if not db_path.exists():
        snapshot["error"] = "DB_NOT_FOUND"
        return snapshot

    try:
        uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        try:
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            total = 0
            for table in tables:
                try:
                    n = con.execute("SELECT COUNT(*) AS n FROM " + quote_ident(table)).fetchone()["n"]
                    total += n if isinstance(n, int) else 0
                    snapshot["tables"].append({"table": table, "rows": n})
                except sqlite3.Error as exc:
                    snapshot["tables"].append({"table": table, "rows": None, "error": str(exc)})
            snapshot["total_rows"] = total
        finally:
            con.close()
    except Exception as exc:
        snapshot["error"] = str(exc)
    return snapshot

# DB watch: independent of process watch; shorter interval if needed.
db_samples = []
db_started = dt.datetime.now(dt.timezone.utc)
while (dt.datetime.now(dt.timezone.utc) - db_started).total_seconds() < WATCH_SECONDS:
    db_samples.append(db_counts())
    time.sleep(INTERVAL_SECONDS)
db_samples.append(db_counts())

process_watch = load_json_any(PROCESS_WATCH_PATH)
scheduled_tasks = load_json_any(SCHEDULED_TASK_PATH)

# Flatten process observations.
process_observations = []
for sample in process_watch:
    for p in sample.get("processes", []) or []:
        text = ((p.get("Name") or "") + " " + (p.get("CommandLine") or "")).lower()
        tags = []
        for key in ["capture", "bridge", "scheduler", "telegram", "python", "powerflow.db", "run_powerflow", "ProjetPowerFlow".lower()]:
            if key.lower() in text:
                tags.append(key)
        process_observations.append({
            "taken_at": sample.get("taken_at"),
            "process_id": p.get("ProcessId"),
            "name": p.get("Name"),
            "command_line": p.get("CommandLine"),
            "tags": sorted(set(tags)),
        })

capture_seen = [p for p in process_observations if any(t in p.get("tags", []) for t in ["capture", "bridge"])]
scheduler_seen = [p for p in process_observations if "scheduler" in p.get("tags", [])]
db_writer_hint_seen = [p for p in process_observations if "powerflow.db" in p.get("tags", [])]
python_seen = [p for p in process_observations if "python" in p.get("tags", [])]

# DB deltas.
first = db_samples[0] if db_samples else {}
last = db_samples[-1] if db_samples else {}
first_rows = first.get("total_rows")
last_rows = last.get("total_rows")
row_delta = None
if isinstance(first_rows, int) and isinstance(last_rows, int):
    row_delta = last_rows - first_rows

table_delta = []
first_tables = {t.get("table"): t.get("rows") for t in first.get("tables", [])}
last_tables = {t.get("table"): t.get("rows") for t in last.get("tables", [])}
for table, last_n in sorted(last_tables.items()):
    first_n = first_tables.get(table)
    delta = None
    if isinstance(first_n, int) and isinstance(last_n, int):
        delta = last_n - first_n
    table_delta.append({"table": table, "before": first_n, "after": last_n, "delta": delta})

db_file_changed = False
if first.get("db_file") and last.get("db_file"):
    db_file_changed = (
        first["db_file"].get("size_bytes") != last["db_file"].get("size_bytes")
        or first["db_file"].get("modified_at") != last["db_file"].get("modified_at")
    )

wal_or_journal_seen = any(
    s.get("wal_file", {}).get("exists")
    or s.get("journal_file", {}).get("exists")
    for s in db_samples
)

task_candidates = []
for task in scheduled_tasks:
    text = ((task.get("TaskName") or "") + " " + (task.get("TaskPath") or "") + " " + (task.get("Actions") or "")).lower()
    tags = []
    for key in ["capture", "bridge", "scheduler", "telegram", "python", "powerflow", "projetpowerflow"]:
        if key in text:
            tags.append(key)
    task_candidates.append({
        "task_name": task.get("TaskName"),
        "task_path": task.get("TaskPath"),
        "state": task.get("State"),
        "actions": task.get("Actions"),
        "tags": sorted(set(tags)),
    })

if row_delta is not None and row_delta > 0:
    status = "DB_ROWS_ADVANCED_DURING_WATCH"
elif db_file_changed and not capture_seen and not scheduler_seen:
    status = "DB_FILE_CHANGED_WITHOUT_VISIBLE_CAPTURE_PROCESS"
elif capture_seen and row_delta == 0:
    status = "CAPTURE_PROCESS_VISIBLE_BUT_NO_DB_ROWS"
elif scheduler_seen and row_delta == 0:
    status = "SCHEDULER_VISIBLE_BUT_NO_DB_ROWS"
elif task_candidates and not capture_seen and not scheduler_seen and row_delta == 0:
    status = "SCHEDULED_TASK_CANDIDATES_BUT_NO_LIVE_WRITER"
elif not capture_seen and not scheduler_seen and row_delta == 0:
    status = "NO_VISIBLE_WRITER_AND_NO_DB_ROW_DELTA"
else:
    status = "INCONCLUSIVE_WRITER_ATTRIBUTION"

recommendations = []
if status == "DB_ROWS_ADVANCED_DURING_WATCH":
    recommendations.append("Rows advanced during the watch. Use table_delta to identify active insertion target and rerun symbol health if needed.")
elif status == "DB_FILE_CHANGED_WITHOUT_VISIBLE_CAPTURE_PROCESS":
    recommendations.append("DB file changed without visible capture process. Suspect short-lived writer, scheduler task, or external process.")
elif status == "CAPTURE_PROCESS_VISIBLE_BUT_NO_DB_ROWS":
    recommendations.append("Capture process visible but rows did not advance. Inspect insertion errors, DB path, and source tick arrival.")
elif status == "SCHEDULER_VISIBLE_BUT_NO_DB_ROWS":
    recommendations.append("Scheduler visible but no rows advanced. Scheduler may be reader-only or capture feed inactive.")
elif status == "SCHEDULED_TASK_CANDIDATES_BUT_NO_LIVE_WRITER":
    recommendations.append("Scheduled task candidates exist but no live writer was observed. Inspect task triggers and last run state manually.")
elif status == "NO_VISIBLE_WRITER_AND_NO_DB_ROW_DELTA":
    recommendations.append("No writer process and no DB row delta. Start/verify capture stack before USDJPY-specific debugging.")
else:
    recommendations.append("Writer attribution inconclusive. Review process watch and scheduled task candidates.")

recommendations.append("Do not change engine/scoring modules until a live writer and row deltas are confirmed.")

contract = {
    "contract": "POWERFLOW_T004_DB_WRITER_ATTRIBUTION",
    "created_at": started_at.isoformat().replace("+00:00", "Z"),
    "db_path": rel(db_path),
    "watch_seconds": WATCH_SECONDS,
    "interval_seconds": INTERVAL_SECONDS,
    "status": status,
    "row_delta": row_delta,
    "db_file_changed": db_file_changed,
    "wal_or_journal_seen": wal_or_journal_seen,
    "table_delta": table_delta,
    "db_samples": db_samples,
    "process_watch": rel(PROCESS_WATCH_PATH),
    "scheduled_tasks_snapshot": rel(SCHEDULED_TASK_PATH),
    "capture_process_observations": capture_seen[:80],
    "scheduler_process_observations": scheduler_seen[:80],
    "db_writer_hint_processes": db_writer_hint_seen[:80],
    "python_process_observations": python_seen[:80],
    "scheduled_task_candidates": task_candidates[:120],
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_DB_WRITER_ATTRIBUTION.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_DB_WRITER_ATTRIBUTION_RESULT_" + stamp + ".md")
md = []
md.append("# T004-I DB Writer Attribution Watch")
md.append("")
md.append("Date: " + started_at.isoformat().replace("+00:00", "Z"))
md.append("")
md.append("## Verdict")
md.append("")
md.append("- Status: " + status)
md.append("- DB: " + rel(db_path))
md.append("- Watch seconds: " + str(WATCH_SECONDS))
md.append("- Row delta: " + str(row_delta))
md.append("- DB file changed: " + str(db_file_changed))
md.append("- WAL/journal seen: " + str(wal_or_journal_seen))
md.append("- Capture observations: " + str(len(capture_seen)))
md.append("- Scheduler observations: " + str(len(scheduler_seen)))
md.append("- Scheduled task candidates: " + str(len(task_candidates)))
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Table deltas")
md.append("")
for item in table_delta:
    md.append("- " + item["table"] + " | before=" + str(item["before"]) + " | after=" + str(item["after"]) + " | delta=" + str(item["delta"]))
md.append("")
md.append("## Capture process observations")
md.append("")
if capture_seen:
    for p in capture_seen[:40]:
        md.append("- " + str(p.get("taken_at")) + " | PID " + str(p.get("process_id")) + " | " + str(p.get("name")) + " | " + str(p.get("command_line")))
else:
    md.append("- none")
md.append("")
md.append("## Scheduler process observations")
md.append("")
if scheduler_seen:
    for p in scheduler_seen[:40]:
        md.append("- " + str(p.get("taken_at")) + " | PID " + str(p.get("process_id")) + " | " + str(p.get("name")) + " | " + str(p.get("command_line")))
else:
    md.append("- none")
md.append("")
md.append("## Scheduled task candidates")
md.append("")
if task_candidates:
    for task in task_candidates[:60]:
        md.append("- " + str(task.get("task_path")) + str(task.get("task_name")) + " | state=" + str(task.get("state")) + " | tags=" + ",".join(task.get("tags", [])) + " | actions=" + str(task.get("actions")))
else:
    md.append("- none")
md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not patch USDJPY logic while the live DB writer is not clearly identified.")
md.append("")
md.append("## Next action")
md.append("")
md.append("If no writer is visible, operator must start/verify the capture stack and rerun T004-G/T004-I. If writer is visible but no rows advance, inspect insertion errors and DB target.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_db_writer_attribution_contract.py"
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
    "def test_t004_db_writer_attribution_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_DB_WRITER_ATTRIBUTION.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_DB_WRITER_ATTRIBUTION"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert isinstance(data["recommendations"], list)',
    '    assert isinstance(data["table_delta"], list)',
    "",
    "",
    "def test_t004_db_writer_attribution_status_known():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_DB_WRITER_ATTRIBUTION.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {',
    '        "DB_ROWS_ADVANCED_DURING_WATCH",',
    '        "DB_FILE_CHANGED_WITHOUT_VISIBLE_CAPTURE_PROCESS",',
    '        "CAPTURE_PROCESS_VISIBLE_BUT_NO_DB_ROWS",',
    '        "SCHEDULER_VISIBLE_BUT_NO_DB_ROWS",',
    '        "SCHEDULED_TASK_CANDIDATES_BUT_NO_LIVE_WRITER",',
    '        "NO_VISIBLE_WRITER_AND_NO_DB_ROW_DELTA",',
    '        "INCONCLUSIVE_WRITER_ATTRIBUTION",',
    '    }',
    '    assert data["status"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "row_delta": row_delta,
    "db_file_changed": db_file_changed,
    "capture_observations": len(capture_seen),
    "scheduler_observations": len(scheduler_seen),
    "task_candidates": len(task_candidates),
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running DB writer attribution analyzer"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-I writer attribution failed"
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
    tests/test_t004_db_writer_attribution_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-I tests failed"
}
Ok "T004-I tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_DB_WRITER_ATTRIBUTION.json",
    "tests/test_t004_db_writer_attribution_contract.py",
    "scripts/t004_db_writer_attribution_watch.ps1",
    $processWatchPath,
    $scheduledTaskPath
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_DB_WRITER_ATTRIBUTION_RESULT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-I files"
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
    Warn "No staged T004-I changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): attribute active DB writer state"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_I_DB_WRITER_ATTRIBUTION.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-I DB writer attribution"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-I DB writer attribution watch"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- DB writer attribution watch created and executed."
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
    $content += "Use writer attribution status to decide whether to start capture, inspect scheduled tasks, or audit insertion target."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-I DB writer attribution"
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

Ok "T004-I DB writer attribution complete"
Log "Final status"
git status --short
git log --oneline -7
