param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$DbPath = "Core/powerflow.db",
    [string]$ThinSymbol = "USDJPY",
    [string[]]$ReferenceSymbols = @("GBPUSD", "EURUSD"),
    [int]$WatchSeconds = 120,
    [int]$IntervalSeconds = 10,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-J] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

if ($WatchSeconds -lt 20) { throw "WatchSeconds must be >= 20" }
if ($IntervalSeconds -lt 2) { throw "IntervalSeconds must be >= 2" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-J active insertion table and symbol delta drilldown"
Log "RepoPath = $RepoPath"
Log "DbPath = $DbPath"
Log "ThinSymbol = $ThinSymbol"
Log "ReferenceSymbols = $($ReferenceSymbols -join ',')"
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
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-J commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004j_active_insertion_symbol_delta.py"
$dbPathJson = ($DbPath | ConvertTo-Json -Compress)
$thinSymbolJson = ($ThinSymbol | ConvertTo-Json -Compress)
$refsJson = ($ReferenceSymbols | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3
import time

DB_PATH_ARG = $dbPathJson
THIN_SYMBOL = $thinSymbolJson
REFERENCE_SYMBOLS = $refsJson
ALL_SYMBOLS = [THIN_SYMBOL] + list(REFERENCE_SYMBOLS)
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

symbol_candidates = ["symbol", "pair", "instrument"]
time_candidates = ["created_at", "timestamp", "time", "logged_at", "detected_at", "source_created_at", "bar_time", "ts", "datetime"]
id_candidates = ["id", "rowid"]

def table_schema(con, table):
    info = con.execute("PRAGMA table_info(" + quote_ident(table) + ")").fetchall()
    columns = [row[1] for row in info]
    lower = {c.lower(): c for c in columns}
    symbol_col = next((lower[c] for c in symbol_candidates if c in lower), None)
    time_col = next((lower[c] for c in time_candidates if c in lower), None)
    id_col = next((lower[c] for c in id_candidates if c in lower), None)
    return columns, symbol_col, time_col, id_col

def recent_rows(con, table, columns, time_col, id_col, limit=5):
    sample_cols = columns[:12]
    select_cols = ", ".join(quote_ident(c) for c in sample_cols)
    order_col = id_col or time_col
    try:
        if order_col:
            sql = "SELECT " + select_cols + " FROM " + quote_ident(table) + " ORDER BY " + quote_ident(order_col) + " DESC LIMIT ?"
        else:
            sql = "SELECT " + select_cols + " FROM " + quote_ident(table) + " LIMIT ?"
        rows = con.execute(sql, (limit,)).fetchall()
        return [{k: row[k] for k in row.keys()} for row in rows]
    except Exception as exc:
        return [{"error": str(exc)}]

def snapshot():
    snap = {
        "taken_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_exists": db_path.exists(),
        "tables": [],
        "symbol_totals": {sym: 0 for sym in ALL_SYMBOLS},
        "total_rows": None,
        "error": None,
    }
    if not db_path.exists():
        snap["error"] = "DB_NOT_FOUND"
        return snap

    try:
        uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        try:
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            total = 0
            for table in tables:
                columns, symbol_col, time_col, id_col = table_schema(con, table)
                try:
                    row_count = con.execute("SELECT COUNT(*) AS n FROM " + quote_ident(table)).fetchone()["n"]
                except Exception:
                    row_count = None
                if isinstance(row_count, int):
                    total += row_count
                entry = {
                    "table": table,
                    "row_count": row_count,
                    "columns": columns,
                    "symbol_col": symbol_col,
                    "time_col": time_col,
                    "id_col": id_col,
                    "per_symbol": {},
                    "max_time": None,
                    "recent_rows": [],
                }
                if row_count and time_col:
                    try:
                        entry["max_time"] = con.execute("SELECT MAX(" + quote_ident(time_col) + ") AS max_t FROM " + quote_ident(table)).fetchone()["max_t"]
                    except Exception:
                        entry["max_time"] = None
                if row_count:
                    entry["recent_rows"] = recent_rows(con, table, columns, time_col, id_col, limit=5)

                if symbol_col:
                    for sym in ALL_SYMBOLS:
                        try:
                            if time_col:
                                sql = (
                                    "SELECT COUNT(*) AS n, MAX(" + quote_ident(time_col) + ") AS max_t "
                                    "FROM " + quote_ident(table) + " WHERE " + quote_ident(symbol_col) + " = ?"
                                )
                                row = con.execute(sql, (sym,)).fetchone()
                                res = {"count": row["n"], "max_time": row["max_t"]}
                            else:
                                sql = "SELECT COUNT(*) AS n FROM " + quote_ident(table) + " WHERE " + quote_ident(symbol_col) + " = ?"
                                row = con.execute(sql, (sym,)).fetchone()
                                res = {"count": row["n"], "max_time": None}
                            entry["per_symbol"][sym] = res
                            snap["symbol_totals"][sym] += res["count"]
                        except Exception as exc:
                            entry["per_symbol"][sym] = {"count": None, "max_time": None, "error": str(exc)}
                snap["tables"].append(entry)
            snap["total_rows"] = total
        finally:
            con.close()
    except Exception as exc:
        snap["error"] = str(exc)
    return snap

samples = []
end_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=WATCH_SECONDS)
while dt.datetime.now(dt.timezone.utc) < end_at:
    samples.append(snapshot())
    time.sleep(INTERVAL_SECONDS)
samples.append(snapshot())

first = samples[0]
last = samples[-1]

table_deltas = []
first_tables = {t["table"]: t for t in first.get("tables", [])}
last_tables = {t["table"]: t for t in last.get("tables", [])}
for table, after_t in sorted(last_tables.items()):
    before_t = first_tables.get(table, {})
    before_rows = before_t.get("row_count")
    after_rows = after_t.get("row_count")
    row_delta = None
    if isinstance(before_rows, int) and isinstance(after_rows, int):
        row_delta = after_rows - before_rows
    per_symbol_delta = {}
    all_syms = set((before_t.get("per_symbol") or {}).keys()) | set((after_t.get("per_symbol") or {}).keys()) | set(ALL_SYMBOLS)
    for sym in sorted(all_syms):
        b = (before_t.get("per_symbol") or {}).get(sym, {}).get("count", 0)
        a = (after_t.get("per_symbol") or {}).get(sym, {}).get("count", 0)
        if isinstance(b, int) and isinstance(a, int):
            per_symbol_delta[sym] = a - b
        else:
            per_symbol_delta[sym] = None
    table_deltas.append({
        "table": table,
        "before_rows": before_rows,
        "after_rows": after_rows,
        "row_delta": row_delta,
        "symbol_col": after_t.get("symbol_col"),
        "time_col": after_t.get("time_col"),
        "id_col": after_t.get("id_col"),
        "max_time_before": before_t.get("max_time"),
        "max_time_after": after_t.get("max_time"),
        "per_symbol_delta": per_symbol_delta,
        "recent_rows_after": after_t.get("recent_rows", []),
    })

active_tables = [t for t in table_deltas if isinstance(t.get("row_delta"), int) and t["row_delta"] > 0]
symbol_deltas = {sym: last.get("symbol_totals", {}).get(sym, 0) - first.get("symbol_totals", {}).get(sym, 0) for sym in ALL_SYMBOLS}

thin_delta = symbol_deltas.get(THIN_SYMBOL, 0)
ref_deltas = {sym: symbol_deltas.get(sym, 0) for sym in REFERENCE_SYMBOLS}
ref_positive = {sym: v for sym, v in ref_deltas.items() if isinstance(v, int) and v > 0}

if not active_tables:
    status = "NO_TABLE_ROW_DELTA"
elif active_tables and all(v == 0 for v in symbol_deltas.values()):
    status = "TABLE_ROWS_ADVANCED_WITHOUT_TRACKED_SYMBOL_DELTA"
elif thin_delta == 0 and ref_positive:
    status = "REFERENCES_ADVANCED_THIN_SYMBOL_ZERO"
elif ref_positive:
    avg_ref = sum(ref_positive.values()) / len(ref_positive)
    if thin_delta < 0.25 * avg_ref:
        status = "THIN_SYMBOL_ADVANCED_BUT_UNDER_25_PERCENT_REF_AVG"
    elif thin_delta < 0.75 * avg_ref:
        status = "THIN_SYMBOL_ADVANCED_MODERATELY_THIN"
    else:
        status = "THIN_SYMBOL_ADVANCED_HEALTHY"
elif thin_delta > 0 and not ref_positive:
    status = "THIN_SYMBOL_ADVANCED_REFERENCES_IDLE"
else:
    status = "TABLE_ROWS_ADVANCED_UNCLASSIFIED_SYMBOLS"

recommendations = []
if status == "NO_TABLE_ROW_DELTA":
    recommendations.append("No table advanced during this watch. Capture/writer is intermittent or inactive in this window.")
elif status == "TABLE_ROWS_ADVANCED_WITHOUT_TRACKED_SYMBOL_DELTA":
    recommendations.append("Rows advanced but not for tracked symbols. Inspect active table recent rows and symbol universe.")
elif status == "REFERENCES_ADVANCED_THIN_SYMBOL_ZERO":
    recommendations.append("References advanced but USDJPY did not. Focus on USDJPY feed/routing/allowlist.")
elif status == "THIN_SYMBOL_ADVANCED_BUT_UNDER_25_PERCENT_REF_AVG":
    recommendations.append("USDJPY advanced but much less than references. Capture confirms live relative sparsity.")
elif status == "THIN_SYMBOL_ADVANCED_MODERATELY_THIN":
    recommendations.append("USDJPY advanced but lower than references. Monitor longer and inspect feed cadence.")
elif status == "THIN_SYMBOL_ADVANCED_HEALTHY":
    recommendations.append("USDJPY live delta is healthy in this window. Historical thinness may be session-dependent.")
elif status == "THIN_SYMBOL_ADVANCED_REFERENCES_IDLE":
    recommendations.append("USDJPY advanced while references did not. Rerun during a broader active window.")
else:
    recommendations.append("Rows advanced but symbol classification is unclear. Inspect active table recent rows.")

recommendations.append("Do not patch engine/scoring logic; use this to target capture/feed checks.")

contract = {
    "contract": "POWERFLOW_T004_ACTIVE_INSERTION_SYMBOL_DELTA",
    "created_at": started_at.isoformat().replace("+00:00", "Z"),
    "db_path": rel(db_path),
    "watch_seconds": WATCH_SECONDS,
    "interval_seconds": INTERVAL_SECONDS,
    "thin_symbol": THIN_SYMBOL,
    "reference_symbols": REFERENCE_SYMBOLS,
    "status": status,
    "symbol_deltas": symbol_deltas,
    "active_tables": active_tables,
    "table_deltas": table_deltas,
    "sample_count": len(samples),
    "samples": samples,
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_ACTIVE_INSERTION_SYMBOL_DELTA.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_ACTIVE_INSERTION_SYMBOL_DELTA_RESULT_" + stamp + ".md")
md = []
md.append("# T004-J Active Insertion Table and Symbol Delta")
md.append("")
md.append("Date: " + started_at.isoformat().replace("+00:00", "Z"))
md.append("")
md.append("## Verdict")
md.append("")
md.append("- Status: " + status)
md.append("- DB: " + rel(db_path))
md.append("- Watch seconds: " + str(WATCH_SECONDS))
md.append("- Sample count: " + str(len(samples)))
md.append("")
md.append("## Symbol deltas")
md.append("")
for sym in ALL_SYMBOLS:
    md.append("- " + sym + ": " + str(symbol_deltas.get(sym)))
md.append("")
md.append("## Active tables")
md.append("")
if active_tables:
    for t in active_tables:
        md.append("- " + t["table"] + " | row_delta=" + str(t.get("row_delta")) + " | symbol_col=" + str(t.get("symbol_col")) + " | time_col=" + str(t.get("time_col")) + " | max_time_before=" + str(t.get("max_time_before")) + " | max_time_after=" + str(t.get("max_time_after")))
        for sym, delta in t.get("per_symbol_delta", {}).items():
            if delta:
                md.append("  - " + sym + ": " + str(delta))
else:
    md.append("- none")
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Table deltas")
md.append("")
for t in table_deltas:
    md.append("### " + t["table"])
    md.append("")
    md.append("- row_delta: " + str(t.get("row_delta")))
    md.append("- symbol_col: " + str(t.get("symbol_col")))
    md.append("- time_col: " + str(t.get("time_col")))
    md.append("- max_time_before: " + str(t.get("max_time_before")))
    md.append("- max_time_after: " + str(t.get("max_time_after")))
    md.append("")
    md.append("symbol deltas:")
    for sym, delta in t.get("per_symbol_delta", {}).items():
        md.append("- " + sym + ": " + str(delta))
    if t.get("recent_rows_after"):
        md.append("")
        md.append("recent rows after:")
        md.append("```json")
        md.append(json.dumps(t["recent_rows_after"][:3], indent=2, ensure_ascii=False, default=str))
        md.append("```")
    md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not change engine/scoring modules. This is an active insertion and symbol routing diagnostic.")
md.append("")
md.append("## Next action")
md.append("")
md.append("If rows advanced without tracked symbol deltas, inspect active table schema and recent rows. If references advanced and USDJPY did not, inspect source feed/allowlist for USDJPY.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_active_insertion_symbol_delta_contract.py"
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
    "def test_t004_active_insertion_symbol_delta_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_INSERTION_SYMBOL_DELTA.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_ACTIVE_INSERTION_SYMBOL_DELTA"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert data["thin_symbol"] == "USDJPY"',
    '    assert isinstance(data["symbol_deltas"], dict)',
    '    assert isinstance(data["table_deltas"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_active_insertion_symbol_delta_status_known():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_INSERTION_SYMBOL_DELTA.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {',
    '        "NO_TABLE_ROW_DELTA",',
    '        "TABLE_ROWS_ADVANCED_WITHOUT_TRACKED_SYMBOL_DELTA",',
    '        "REFERENCES_ADVANCED_THIN_SYMBOL_ZERO",',
    '        "THIN_SYMBOL_ADVANCED_BUT_UNDER_25_PERCENT_REF_AVG",',
    '        "THIN_SYMBOL_ADVANCED_MODERATELY_THIN",',
    '        "THIN_SYMBOL_ADVANCED_HEALTHY",',
    '        "THIN_SYMBOL_ADVANCED_REFERENCES_IDLE",',
    '        "TABLE_ROWS_ADVANCED_UNCLASSIFIED_SYMBOLS",',
    '    }',
    '    assert data["status"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "symbol_deltas": symbol_deltas,
    "active_table_count": len(active_tables),
    "active_tables": [{"table": t["table"], "row_delta": t["row_delta"], "per_symbol_delta": t["per_symbol_delta"]} for t in active_tables],
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running active insertion symbol delta drilldown"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-J active insertion symbol delta failed"
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
    tests/test_t004_active_insertion_symbol_delta_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-J tests failed"
}
Ok "T004-J tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_ACTIVE_INSERTION_SYMBOL_DELTA.json",
    "tests/test_t004_active_insertion_symbol_delta_contract.py",
    "scripts/t004_active_insertion_symbol_delta.ps1"
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_ACTIVE_INSERTION_SYMBOL_DELTA_RESULT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-J files"
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
    Warn "No staged T004-J changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): drill down active insertion symbol deltas"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_J_ACTIVE_INSERTION_SYMBOL_DELTA.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-J active insertion symbol delta"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-J active insertion symbol delta drilldown"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Active insertion table and symbol delta drilldown created and executed."
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
    $content += "Use T004-J status to decide whether to inspect active table schema, source feed, or close T004 as capture-health diagnosed."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-J active insertion symbol delta"
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

Ok "T004-J active insertion symbol delta complete"
Log "Final status"
git status --short
git log --oneline -7
