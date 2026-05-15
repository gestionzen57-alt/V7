param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$DbPath = "Core/powerflow.db",
    [string]$ThinSymbol = "USDJPY",
    [string[]]$ReferenceSymbols = @("GBPUSD", "EURUSD"),
    [int]$DurationSeconds = 30,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-G] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

if ($DurationSeconds -lt 5) {
    throw "DurationSeconds must be >= 5"
}

Log "PowerFlow V7.6.7 T004-G live capture health counter"
Log "RepoPath = $RepoPath"
Log "DbPath = $DbPath"
Log "ThinSymbol = $ThinSymbol"
Log "ReferenceSymbols = $($ReferenceSymbols -join ',')"
Log "DurationSeconds = $DurationSeconds"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-G commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004g_live_capture_health_counter.py"
$thinSymbolJson = ($ThinSymbol | ConvertTo-Json -Compress)
$refsJson = ($ReferenceSymbols | ConvertTo-Json -Compress)
$dbPathJson = ($DbPath | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3
import time

THIN_SYMBOL = $thinSymbolJson
REFERENCE_SYMBOLS = $refsJson
ALL_SYMBOLS = [THIN_SYMBOL] + list(REFERENCE_SYMBOLS)
DB_PATH_ARG = $dbPathJson
DURATION_SECONDS = int($DurationSeconds)

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
plan_dir = repo / "Docs" / "Plans"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
plan_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

db_path = Path(DB_PATH_ARG)
if not db_path.is_absolute():
    db_path = repo / db_path

now_start = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

symbol_candidates = ["symbol", "pair", "instrument"]
time_candidates = [
    "created_at", "timestamp", "time", "logged_at", "detected_at",
    "source_created_at", "bar_time", "ts", "datetime"
]

def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path)

def read_counts() -> dict:
    snapshot = {
        "taken_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_exists": db_path.exists(),
        "tables": [],
        "symbol_totals": {sym: 0 for sym in ALL_SYMBOLS},
        "error": None,
    }

    if not db_path.exists():
        snapshot["error"] = "DB_NOT_FOUND"
        return snapshot

    uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        try:
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            for table in tables:
                try:
                    info = con.execute("PRAGMA table_info(" + quote_ident(table) + ")").fetchall()
                    columns = [row[1] for row in info]
                    lower = {c.lower(): c for c in columns}
                    symbol_col = next((lower[c] for c in symbol_candidates if c in lower), None)
                    time_col = next((lower[c] for c in time_candidates if c in lower), None)

                    row_count = con.execute("SELECT COUNT(*) AS n FROM " + quote_ident(table)).fetchone()["n"]

                    entry = {
                        "table": table,
                        "row_count": row_count,
                        "symbol_col": symbol_col,
                        "time_col": time_col,
                        "per_symbol": {},
                    }

                    if symbol_col:
                        for sym in ALL_SYMBOLS:
                            if time_col:
                                sql = (
                                    "SELECT COUNT(*) AS n, MAX(" + quote_ident(time_col) + ") AS max_t "
                                    "FROM " + quote_ident(table)
                                    + " WHERE " + quote_ident(symbol_col) + " = ?"
                                )
                                row = con.execute(sql, (sym,)).fetchone()
                                result = {"count": row["n"], "max_time": row["max_t"]}
                            else:
                                sql = (
                                    "SELECT COUNT(*) AS n FROM " + quote_ident(table)
                                    + " WHERE " + quote_ident(symbol_col) + " = ?"
                                )
                                row = con.execute(sql, (sym,)).fetchone()
                                result = {"count": row["n"], "max_time": None}

                            entry["per_symbol"][sym] = result
                            snapshot["symbol_totals"][sym] += result["count"]

                    snapshot["tables"].append(entry)
                except sqlite3.Error as exc:
                    snapshot["tables"].append({
                        "table": table,
                        "error": str(exc),
                        "per_symbol": {},
                    })
        finally:
            con.close()
    except Exception as exc:
        snapshot["error"] = str(exc)

    return snapshot

before = read_counts()
time.sleep(DURATION_SECONDS)
after = read_counts()

deltas = {sym: (after["symbol_totals"].get(sym, 0) - before["symbol_totals"].get(sym, 0)) for sym in ALL_SYMBOLS}

table_deltas = []
before_by_table = {t.get("table"): t for t in before.get("tables", [])}
after_by_table = {t.get("table"): t for t in after.get("tables", [])}
for table, after_table in after_by_table.items():
    before_table = before_by_table.get(table, {})
    item = {
        "table": table,
        "per_symbol_delta": {},
    }
    for sym in ALL_SYMBOLS:
        b = before_table.get("per_symbol", {}).get(sym, {}).get("count", 0)
        a = after_table.get("per_symbol", {}).get(sym, {}).get("count", 0)
        item["per_symbol_delta"][sym] = a - b
    table_deltas.append(item)

thin_delta = deltas.get(THIN_SYMBOL, 0)
ref_deltas = {sym: deltas.get(sym, 0) for sym in REFERENCE_SYMBOLS}
ref_positive = {sym: delta for sym, delta in ref_deltas.items() if delta > 0}

if before.get("error") or after.get("error"):
    status = "DB_READ_ERROR"
elif all(delta == 0 for delta in deltas.values()):
    status = "NO_LIVE_DELTA_CAPTURE_INACTIVE_OR_IDLE"
elif thin_delta == 0 and ref_positive:
    status = "THIN_SYMBOL_NO_DELTA_REFERENCES_ACTIVE"
elif ref_positive:
    ref_avg = sum(ref_positive.values()) / len(ref_positive)
    if thin_delta < 0.25 * ref_avg:
        status = "THIN_SYMBOL_DELTA_UNDER_25_PERCENT_REF_AVG"
    elif thin_delta < 0.75 * ref_avg:
        status = "THIN_SYMBOL_DELTA_MODERATELY_THIN"
    else:
        status = "THIN_SYMBOL_DELTA_HEALTHY"
else:
    status = "THIN_SYMBOL_DELTA_PRESENT_REFERENCES_IDLE"

recommendations = []
if status == "NO_LIVE_DELTA_CAPTURE_INACTIVE_OR_IDLE":
    recommendations.append("No symbol row deltas during the window. Capture may be stopped, market/feed idle, or DB writes are not active.")
elif status == "THIN_SYMBOL_NO_DELTA_REFERENCES_ACTIVE":
    recommendations.append("References advanced but USDJPY did not. Inspect USDJPY source stream, broker suffix, Market Watch, or allowlist.")
elif status == "THIN_SYMBOL_DELTA_UNDER_25_PERCENT_REF_AVG":
    recommendations.append("USDJPY advanced but remains materially under reference cadence. Capture health counter confirms live relative sparsity.")
elif status == "THIN_SYMBOL_DELTA_MODERATELY_THIN":
    recommendations.append("USDJPY live cadence is lower than references, but not fully absent. Monitor longer or inspect feed cadence.")
elif status == "THIN_SYMBOL_DELTA_HEALTHY":
    recommendations.append("USDJPY live cadence looks healthy in this short window. Historical thinness may be session/time-window specific.")
else:
    recommendations.append("USDJPY moved but references did not; rerun during active market or with a longer window.")

recommendations.append("Do not change engine/scoring logic based on this check alone; this is capture health evidence.")

contract = {
    "contract": "POWERFLOW_T004_LIVE_CAPTURE_HEALTH_COUNTER",
    "created_at": now_start.isoformat().replace("+00:00", "Z"),
    "duration_seconds": DURATION_SECONDS,
    "db_path": rel(db_path),
    "thin_symbol": THIN_SYMBOL,
    "reference_symbols": REFERENCE_SYMBOLS,
    "status": status,
    "before": before,
    "after": after,
    "deltas": deltas,
    "table_deltas": table_deltas,
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_LIVE_CAPTURE_HEALTH_COUNTER.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_LIVE_CAPTURE_HEALTH_COUNTER_RESULT_" + stamp + ".md")
md = []
md.append("# T004-G Live Capture Health Counter")
md.append("")
md.append("Date: " + now_start.isoformat().replace("+00:00", "Z"))
md.append("")
md.append("## Result")
md.append("")
md.append("- DB: " + rel(db_path))
md.append("- Duration seconds: " + str(DURATION_SECONDS))
md.append("- Status: " + status)
md.append("")
md.append("## Symbol deltas")
md.append("")
for sym in ALL_SYMBOLS:
    md.append("- " + sym + ": " + str(deltas.get(sym, 0)))
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Table deltas")
md.append("")
if table_deltas:
    for table in table_deltas:
        md.append("### " + table["table"])
        md.append("")
        for sym, delta in table["per_symbol_delta"].items():
            md.append("- " + sym + ": " + str(delta))
        md.append("")
else:
    md.append("- none")
md.append("")
md.append("## Runtime behavior")
md.append("")
md.append("- DB opened read-only twice.")
md.append("- No runtime wiring.")
md.append("- No dashboard files touched.")
md.append("- This script only compares before/after counts.")
md.append("")
md.append("## Next action")
md.append("")
md.append("If references move and USDJPY does not, fix source/routing/allowlist before engine changes.")
md.append("If no symbols move, rerun while capture/market feed is active.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_live_capture_health_counter_contract.py"
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
    "def test_t004_live_capture_health_counter_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_LIVE_CAPTURE_HEALTH_COUNTER.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_LIVE_CAPTURE_HEALTH_COUNTER"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert data["thin_symbol"] == "USDJPY"',
    '    assert isinstance(data["deltas"], dict)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_live_capture_health_counter_status_known():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_LIVE_CAPTURE_HEALTH_COUNTER.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {',
    '        "DB_READ_ERROR",',
    '        "NO_LIVE_DELTA_CAPTURE_INACTIVE_OR_IDLE",',
    '        "THIN_SYMBOL_NO_DELTA_REFERENCES_ACTIVE",',
    '        "THIN_SYMBOL_DELTA_UNDER_25_PERCENT_REF_AVG",',
    '        "THIN_SYMBOL_DELTA_MODERATELY_THIN",',
    '        "THIN_SYMBOL_DELTA_HEALTHY",',
    '        "THIN_SYMBOL_DELTA_PRESENT_REFERENCES_IDLE",',
    '    }',
    '    assert data["status"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "duration_seconds": DURATION_SECONDS,
    "db_path": rel(db_path),
    "deltas": deltas,
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running live capture health counter"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-G live capture health counter failed"
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
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-G tests failed"
}
Ok "T004-G tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_LIVE_CAPTURE_HEALTH_COUNTER.json",
    "tests/test_t004_live_capture_health_counter_contract.py",
    "scripts/t004_live_capture_health_counter.ps1"
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_LIVE_CAPTURE_HEALTH_COUNTER_RESULT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-G files"
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
    Warn "No staged T004-G changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): add live capture health counter for USDJPY"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_G_LIVE_CAPTURE_HEALTH_COUNTER.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-G live capture health counter"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-G live capture health counter"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Live capture health counter created and executed."
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
    $content += "Use the health counter status to decide whether to fix source routing or rerun during active feed."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-G live capture health counter"
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

Ok "T004-G live capture health counter complete"
Log "Final status"
git status --short
git log --oneline -7
