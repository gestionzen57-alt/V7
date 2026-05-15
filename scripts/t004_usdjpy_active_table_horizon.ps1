param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$DbPath = "Core/powerflow.db",
    [string]$ThinSymbol = "USDJPY",
    [string[]]$ReferenceSymbols = @("GBPUSD", "EURUSD"),
    [int]$LimitPerSymbol = 5,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-K] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

if ($LimitPerSymbol -lt 1) { throw "LimitPerSymbol must be >= 1" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-K USDJPY active-table horizon audit"
Log "RepoPath = $RepoPath"
Log "DbPath = $DbPath"
Log "ThinSymbol = $ThinSymbol"
Log "ReferenceSymbols = $($ReferenceSymbols -join ',')"
Log "LimitPerSymbol = $LimitPerSymbol"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-K commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004k_active_table_horizon.py"
$dbPathJson = ($DbPath | ConvertTo-Json -Compress)
$thinSymbolJson = ($ThinSymbol | ConvertTo-Json -Compress)
$refsJson = ($ReferenceSymbols | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3

DB_PATH_ARG = $dbPathJson
THIN_SYMBOL = $thinSymbolJson
REFERENCE_SYMBOLS = $refsJson
ALL_SYMBOLS = [THIN_SYMBOL] + list(REFERENCE_SYMBOLS)
LIMIT_PER_SYMBOL = int($LimitPerSymbol)

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

source_path = contract_dir / "T004_ACTIVE_INSERTION_SYMBOL_DELTA.json"
source = {}
if source_path.exists():
    source = json.loads(source_path.read_text(encoding="utf-8"))

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path)

def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def parse_dt(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    candidates = [
        text,
        text.replace("Z", "+00:00"),
        text.replace(" ", "T"),
        text.split(".")[0],
    ]
    for candidate in candidates:
        try:
            return dt.datetime.fromisoformat(candidate)
        except Exception:
            pass
    return None

def age_seconds(value):
    parsed = parse_dt(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - parsed.astimezone(dt.timezone.utc)).total_seconds()

def table_schema(con, table):
    info = con.execute("PRAGMA table_info(" + quote_ident(table) + ")").fetchall()
    columns = [row[1] for row in info]
    lower = {c.lower(): c for c in columns}
    symbol_col = next((lower[c] for c in ["symbol", "pair", "instrument"] if c in lower), None)
    time_col = next((lower[c] for c in ["created_at", "timestamp", "time", "logged_at", "detected_at", "source_created_at", "bar_time", "ts", "datetime"] if c in lower), None)
    id_col = next((lower[c] for c in ["id", "rowid"] if c in lower), None)
    return columns, symbol_col, time_col, id_col

def select_recent_for_symbol(con, table, columns, symbol_col, time_col, id_col, sym):
    sample_cols = columns[:14]
    select_cols = ", ".join(quote_ident(c) for c in sample_cols)
    order_col = time_col or id_col
    try:
        if order_col:
            sql = (
                "SELECT " + select_cols + " FROM " + quote_ident(table)
                + " WHERE " + quote_ident(symbol_col) + " = ?"
                + " ORDER BY " + quote_ident(order_col) + " DESC LIMIT ?"
            )
        else:
            sql = (
                "SELECT " + select_cols + " FROM " + quote_ident(table)
                + " WHERE " + quote_ident(symbol_col) + " = ? LIMIT ?"
            )
        rows = con.execute(sql, (sym, LIMIT_PER_SYMBOL)).fetchall()
        return [{k: row[k] for k in row.keys()} for row in rows]
    except Exception as exc:
        return [{"error": str(exc)}]

source_active_tables = []
for item in source.get("active_tables", []):
    table = item.get("table")
    if table:
        source_active_tables.append(table)

if not source_active_tables:
    source_active_tables = ["flow_packets", "force_snapshots", "force_snapshots_v2"]

tables = []
suffix_candidates = []
status_votes = []

if not db_path.exists():
    raise SystemExit("DB not found: " + str(db_path))

uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row
try:
    existing_tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for table in source_active_tables:
        if table not in existing_tables:
            tables.append({"table": table, "exists": False, "error": "missing table"})
            continue

        columns, symbol_col, time_col, id_col = table_schema(con, table)
        row_count = con.execute("SELECT COUNT(*) AS n FROM " + quote_ident(table)).fetchone()["n"]
        entry = {
            "table": table,
            "exists": True,
            "row_count": row_count,
            "columns": columns,
            "symbol_col": symbol_col,
            "time_col": time_col,
            "id_col": id_col,
            "top_symbols": [],
            "per_symbol": {},
            "suffix_candidates": [],
            "horizon_status": "NO_SYMBOL_COLUMN",
        }

        if symbol_col:
            # Top symbols.
            try:
                top_rows = con.execute(
                    "SELECT " + quote_ident(symbol_col) + " AS sym, COUNT(*) AS n FROM "
                    + quote_ident(table) + " GROUP BY " + quote_ident(symbol_col)
                    + " ORDER BY n DESC LIMIT 30"
                ).fetchall()
                entry["top_symbols"] = [{"symbol": row["sym"], "count": row["n"]} for row in top_rows]
            except Exception as exc:
                entry["top_symbols_error"] = str(exc)

            # Suffix / near-symbol candidates.
            try:
                near_rows = con.execute(
                    "SELECT " + quote_ident(symbol_col) + " AS sym, COUNT(*) AS n FROM "
                    + quote_ident(table) + " WHERE UPPER(" + quote_ident(symbol_col) + ") LIKE ? "
                    + "GROUP BY " + quote_ident(symbol_col) + " ORDER BY n DESC LIMIT 20",
                    (THIN_SYMBOL.upper() + "%",),
                ).fetchall()
                entry["suffix_candidates"] = [{"symbol": row["sym"], "count": row["n"]} for row in near_rows]
                for row in near_rows:
                    if str(row["sym"]).upper() != THIN_SYMBOL.upper():
                        suffix_candidates.append({"table": table, "symbol": row["sym"], "count": row["n"]})
            except Exception as exc:
                entry["suffix_candidates_error"] = str(exc)

            for sym in ALL_SYMBOLS:
                result = {
                    "count": 0,
                    "max_time": None,
                    "age_seconds": None,
                    "recent_rows": [],
                }
                try:
                    if time_col:
                        sql = (
                            "SELECT COUNT(*) AS n, MAX(" + quote_ident(time_col) + ") AS max_t FROM "
                            + quote_ident(table) + " WHERE " + quote_ident(symbol_col) + " = ?"
                        )
                        row = con.execute(sql, (sym,)).fetchone()
                        result["count"] = row["n"]
                        result["max_time"] = row["max_t"]
                        result["age_seconds"] = age_seconds(row["max_t"])
                    else:
                        sql = "SELECT COUNT(*) AS n FROM " + quote_ident(table) + " WHERE " + quote_ident(symbol_col) + " = ?"
                        row = con.execute(sql, (sym,)).fetchone()
                        result["count"] = row["n"]

                    if result["count"]:
                        result["recent_rows"] = select_recent_for_symbol(con, table, columns, symbol_col, time_col, id_col, sym)
                except Exception as exc:
                    result["error"] = str(exc)

                entry["per_symbol"][sym] = result

            thin = entry["per_symbol"].get(THIN_SYMBOL, {})
            refs = {sym: entry["per_symbol"].get(sym, {}) for sym in REFERENCE_SYMBOLS}
            thin_count = thin.get("count") or 0
            ref_counts = {sym: (data.get("count") or 0) for sym, data in refs.items()}
            ref_nonzero = {sym: c for sym, c in ref_counts.items() if c > 0}

            thin_age = thin.get("age_seconds")
            ref_ages = [data.get("age_seconds") for data in refs.values() if data.get("age_seconds") is not None]
            best_ref_age = min(ref_ages) if ref_ages else None
            entry["thin_latest_gap_seconds_vs_best_ref"] = None
            if thin_age is not None and best_ref_age is not None:
                entry["thin_latest_gap_seconds_vs_best_ref"] = thin_age - best_ref_age

            if thin_count == 0 and ref_nonzero:
                entry["horizon_status"] = "THIN_SYMBOL_ABSENT_REFERENCES_PRESENT"
                status_votes.append("absent_in_active_tables")
            elif thin_count > 0 and ref_nonzero and entry["thin_latest_gap_seconds_vs_best_ref"] is not None and entry["thin_latest_gap_seconds_vs_best_ref"] > 600:
                entry["horizon_status"] = "THIN_SYMBOL_STALE_VS_REFERENCES"
                status_votes.append("stale_vs_references")
            elif thin_count > 0 and ref_nonzero:
                avg_ref = sum(ref_nonzero.values()) / len(ref_nonzero)
                if avg_ref and thin_count < 0.25 * avg_ref:
                    entry["horizon_status"] = "THIN_SYMBOL_HISTORICALLY_SPARSE"
                    status_votes.append("historically_sparse")
                else:
                    entry["horizon_status"] = "THIN_SYMBOL_PRESENT_NOT_STRUCTURALLY_SPARSE"
            elif thin_count > 0 and not ref_nonzero:
                entry["horizon_status"] = "THIN_SYMBOL_PRESENT_REFERENCES_ABSENT"
            else:
                entry["horizon_status"] = "NO_REQUESTED_SYMBOLS"

        tables.append(entry)
finally:
    con.close()

vote_counts = {}
for vote in status_votes:
    vote_counts[vote] = vote_counts.get(vote, 0) + 1

if suffix_candidates:
    verdict = "POSSIBLE_SUFFIX_OR_NEAR_SYMBOL_ROUTE"
elif vote_counts.get("absent_in_active_tables", 0) >= 1:
    verdict = "USDJPY_ABSENT_FROM_ACTIVE_INSERTION_TABLES"
elif vote_counts.get("stale_vs_references", 0) >= 1:
    verdict = "USDJPY_STALE_VS_REFERENCES"
elif vote_counts.get("historically_sparse", 0) >= 1:
    verdict = "USDJPY_HISTORICALLY_SPARSE_IN_ACTIVE_TABLES"
else:
    verdict = "NO_CLEAR_USDJPY_HORIZON_DEFECT"

recommendations = []
if verdict == "POSSIBLE_SUFFIX_OR_NEAR_SYMBOL_ROUTE":
    recommendations.append("Near-symbol/suffix candidates exist. Check exact broker symbol naming and bridge normalization.")
elif verdict == "USDJPY_ABSENT_FROM_ACTIVE_INSERTION_TABLES":
    recommendations.append("USDJPY is absent from at least one active insertion table while references exist. Focus capture routing/allowlist/source feed.")
elif verdict == "USDJPY_STALE_VS_REFERENCES":
    recommendations.append("USDJPY exists but is stale versus references. Check whether USDJPY feed stalls after earlier capture.")
elif verdict == "USDJPY_HISTORICALLY_SPARSE_IN_ACTIVE_TABLES":
    recommendations.append("USDJPY exists but is structurally sparse in active tables. Add capture health monitoring per symbol before any scoring changes.")
else:
    recommendations.append("No clear active-table defect detected. Rerun during active market or inspect broader symbol universe.")

recommendations.append("Do not patch PowerFlow engine/scoring modules; T004 remains capture/routing/feed normalization.")

contract = {
    "contract": "POWERFLOW_T004_USDJPY_ACTIVE_TABLE_HORIZON",
    "created_at": started_at.isoformat().replace("+00:00", "Z"),
    "db_path": rel(db_path),
    "thin_symbol": THIN_SYMBOL,
    "reference_symbols": REFERENCE_SYMBOLS,
    "source_delta_contract": "Docs/Contracts/T004_ACTIVE_INSERTION_SYMBOL_DELTA.json" if source else None,
    "source_active_tables": source_active_tables,
    "verdict": verdict,
    "vote_counts": vote_counts,
    "suffix_candidates": suffix_candidates[:80],
    "tables": tables,
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_USDJPY_ACTIVE_TABLE_HORIZON.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_USDJPY_ACTIVE_TABLE_HORIZON_RESULT_" + stamp + ".md")
md = []
md.append("# T004-K USDJPY Active-Table Horizon Audit")
md.append("")
md.append("Date: " + started_at.isoformat().replace("+00:00", "Z"))
md.append("")
md.append("## Verdict")
md.append("")
md.append("- Verdict: " + verdict)
md.append("- DB: " + rel(db_path))
md.append("- Thin symbol: " + THIN_SYMBOL)
md.append("- Reference symbols: " + ", ".join(REFERENCE_SYMBOLS))
md.append("- Source active tables: " + ", ".join(source_active_tables))
md.append("")
md.append("## Vote counts")
md.append("")
if vote_counts:
    for k, v in sorted(vote_counts.items(), key=lambda x: (-x[1], x[0])):
        md.append("- " + k + ": " + str(v))
else:
    md.append("- none")
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Suffix / near-symbol candidates")
md.append("")
if suffix_candidates:
    for item in suffix_candidates[:40]:
        md.append("- " + item["table"] + " | " + str(item["symbol"]) + " count=" + str(item["count"]))
else:
    md.append("- none")
md.append("")
md.append("## Table horizons")
md.append("")
for table in tables:
    md.append("### " + table["table"])
    md.append("")
    if not table.get("exists"):
        md.append("- missing table")
        md.append("")
        continue
    md.append("- rows: " + str(table.get("row_count")))
    md.append("- symbol_col: " + str(table.get("symbol_col")))
    md.append("- time_col: " + str(table.get("time_col")))
    md.append("- horizon_status: " + str(table.get("horizon_status")))
    md.append("- thin_latest_gap_seconds_vs_best_ref: " + str(table.get("thin_latest_gap_seconds_vs_best_ref")))
    md.append("")
    md.append("per symbol:")
    for sym in ALL_SYMBOLS:
        data = table.get("per_symbol", {}).get(sym, {})
        md.append("- " + sym + " | count=" + str(data.get("count")) + " | max_time=" + str(data.get("max_time")) + " | age_seconds=" + str(data.get("age_seconds")))
    md.append("")
    if table.get("top_symbols"):
        md.append("top symbols:")
        for item in table["top_symbols"][:12]:
            md.append("- " + str(item.get("symbol")) + ": " + str(item.get("count")))
        md.append("")
    md.append("recent rows by symbol:")
    for sym in ALL_SYMBOLS:
        rows = table.get("per_symbol", {}).get(sym, {}).get("recent_rows", [])
        md.append("- " + sym + ": " + str(len(rows)) + " row(s) sampled")
        if rows:
            md.append("```json")
            md.append(json.dumps(rows[:2], indent=2, ensure_ascii=False, default=str))
            md.append("```")
    md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not patch engine/scoring modules. If USDJPY is absent/stale in active insertion tables, fix feed/routing/normalization upstream.")
md.append("")
md.append("## Next action")
md.append("")
md.append("T004-L should either close T004 with an operator action checklist, or create a minimal capture-health monitor if live diagnosis must continue.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_usdjpy_active_table_horizon_contract.py"
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
    "def test_t004_usdjpy_active_table_horizon_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_ACTIVE_TABLE_HORIZON.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_USDJPY_ACTIVE_TABLE_HORIZON"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert data["thin_symbol"] == "USDJPY"',
    '    assert isinstance(data["tables"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_usdjpy_active_table_horizon_verdict_known():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_ACTIVE_TABLE_HORIZON.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {',
    '        "POSSIBLE_SUFFIX_OR_NEAR_SYMBOL_ROUTE",',
    '        "USDJPY_ABSENT_FROM_ACTIVE_INSERTION_TABLES",',
    '        "USDJPY_STALE_VS_REFERENCES",',
    '        "USDJPY_HISTORICALLY_SPARSE_IN_ACTIVE_TABLES",',
    '        "NO_CLEAR_USDJPY_HORIZON_DEFECT",',
    '    }',
    '    assert data["verdict"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "verdict": verdict,
    "vote_counts": vote_counts,
    "suffix_candidate_count": len(suffix_candidates),
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running USDJPY active-table horizon audit"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-K active-table horizon audit failed"
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
    tests/test_t004_usdjpy_active_table_horizon_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-K tests failed"
}
Ok "T004-K tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_USDJPY_ACTIVE_TABLE_HORIZON.json",
    "tests/test_t004_usdjpy_active_table_horizon_contract.py",
    "scripts/t004_usdjpy_active_table_horizon.ps1"
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_USDJPY_ACTIVE_TABLE_HORIZON_RESULT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-K files"
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
    Warn "No staged T004-K changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): inspect USDJPY active table horizon"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_K_USDJPY_ACTIVE_TABLE_HORIZON.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-K USDJPY active-table horizon"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-K USDJPY active-table horizon audit"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- USDJPY active-table horizon audit created and executed."
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
    $content += "Use T004-K verdict to close T004 or create a minimal capture health monitor/operator action checklist."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-K USDJPY active-table horizon"
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

Ok "T004-K USDJPY active-table horizon complete"
Log "Final status"
git status --short
git log --oneline -7
