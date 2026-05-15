param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$DbPath = "",
    [string[]]$Symbols = @("USDJPY", "GBPUSD", "EURUSD"),
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-D] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-D symbol density on active populated DB"
Log "RepoPath = $RepoPath"
Log "Symbols = $($Symbols -join ',')"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-D commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004d_symbol_density_active_db.py"
$symbolsJson = ($Symbols | ConvertTo-Json -Compress)
$dbPathJson = ($DbPath | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3

SYMBOLS = $symbolsJson
REQUESTED_DB_PATH = $dbPathJson

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

decision_path = contract_dir / "T004_ACTIVE_DB_DECISION.json"
if not decision_path.exists() and not REQUESTED_DB_PATH:
    raise SystemExit("Missing Docs/Contracts/T004_ACTIVE_DB_DECISION.json and no -DbPath provided")

decision = {}
if decision_path.exists():
    decision = json.loads(decision_path.read_text(encoding="utf-8"))

def repo_path_from_contract(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    p = Path(path_text)
    if p.is_absolute():
        return p
    return repo / p

if REQUESTED_DB_PATH:
    active_db = repo_path_from_contract(REQUESTED_DB_PATH)
else:
    active_db = repo_path_from_contract((decision.get("best_populated_db") or {}).get("path"))

if active_db is None:
    raise SystemExit("No active DB candidate resolved")

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
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

status = "DB_NOT_FOUND"
tables = []
symbol_totals = {sym: 0 for sym in SYMBOLS}
symbol_indexed_tables = 0
populated_tables = 0
recommendations = []

if active_db.exists():
    status = "DB_FOUND"
    uri = "file:" + str(active_db).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        raw_tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
        for table in raw_tables:
            info = con.execute("PRAGMA table_info(" + quote_ident(table) + ")").fetchall()
            columns = [row[1] for row in info]
            lower = {c.lower(): c for c in columns}
            symbol_col = next((lower[c] for c in symbol_candidates if c in lower), None)
            time_col = next((lower[c] for c in time_candidates if c in lower), None)

            try:
                row_count = con.execute("SELECT COUNT(*) AS n FROM " + quote_ident(table)).fetchone()["n"]
            except sqlite3.Error:
                row_count = None

            if isinstance(row_count, int) and row_count > 0:
                populated_tables += 1

            entry = {
                "table": table,
                "row_count": row_count,
                "columns": columns,
                "symbol_col": symbol_col,
                "time_col": time_col,
                "per_symbol": {},
                "sample": None,
            }

            if isinstance(row_count, int) and row_count > 0:
                sample_cols = columns[:12]
                select_cols = ", ".join(quote_ident(c) for c in sample_cols)
                try:
                    row = con.execute("SELECT " + select_cols + " FROM " + quote_ident(table) + " LIMIT 1").fetchone()
                    if row:
                        entry["sample"] = {k: row[k] for k in row.keys()}
                except sqlite3.Error:
                    entry["sample"] = None

            if symbol_col:
                symbol_indexed_tables += 1
                for sym in SYMBOLS:
                    result = {"count": 0, "min_time": None, "max_time": None, "ratio_vs_table": None}
                    try:
                        if time_col:
                            sql = (
                                "SELECT COUNT(*) AS n, MIN(" + quote_ident(time_col) + ") AS min_t, "
                                "MAX(" + quote_ident(time_col) + ") AS max_t FROM " + quote_ident(table)
                                + " WHERE " + quote_ident(symbol_col) + " = ?"
                            )
                            row = con.execute(sql, (sym,)).fetchone()
                            count = row["n"]
                            result = {"count": count, "min_time": row["min_t"], "max_time": row["max_t"], "ratio_vs_table": None}
                        else:
                            sql = "SELECT COUNT(*) AS n FROM " + quote_ident(table) + " WHERE " + quote_ident(symbol_col) + " = ?"
                            row = con.execute(sql, (sym,)).fetchone()
                            count = row["n"]
                            result = {"count": count, "min_time": None, "max_time": None, "ratio_vs_table": None}

                        if isinstance(row_count, int) and row_count > 0:
                            result["ratio_vs_table"] = count / row_count
                        symbol_totals[sym] += count
                    except sqlite3.Error as exc:
                        result = {"count": None, "min_time": None, "max_time": None, "ratio_vs_table": None, "error": str(exc)}

                    entry["per_symbol"][sym] = result
            else:
                # Table-name fallback.
                lower_table = table.lower()
                for sym in SYMBOLS:
                    if sym.lower() in lower_table and isinstance(row_count, int):
                        entry["per_symbol"][sym] = {
                            "count": row_count,
                            "min_time": None,
                            "max_time": None,
                            "ratio_vs_table": 1.0,
                            "table_name_match": True,
                        }
                        symbol_totals[sym] += row_count

            tables.append(entry)
    finally:
        con.close()

    usd = symbol_totals.get("USDJPY", 0)
    refs = {sym: symbol_totals.get(sym, 0) for sym in SYMBOLS if sym != "USDJPY"}
    ref_nonzero = {sym: c for sym, c in refs.items() if c > 0}

    if symbol_indexed_tables == 0:
        recommendations.append("Active DB is populated but no symbol-indexed table was detected. Inspect schema before USDJPY-specific fixes.")
        status = "POPULATED_DB_NO_SYMBOL_TABLE" if populated_tables > 0 else "DB_FOUND_EMPTY"
    elif usd == 0 and ref_nonzero:
        recommendations.append("USDJPY has zero rows while reference symbols have rows. Likely USDJPY routing/filter/stream issue.")
        status = "USDJPY_ZERO_REFERENCES_PRESENT"
    elif usd == 0 and not ref_nonzero:
        recommendations.append("No requested symbols have rows in symbol-indexed tables. Active DB may not contain tick/symbol data.")
        status = "NO_REQUESTED_SYMBOL_ROWS"
    elif ref_nonzero:
        ref_avg = sum(ref_nonzero.values()) / len(ref_nonzero)
        if ref_avg > 0 and usd < 0.25 * ref_avg:
            recommendations.append("USDJPY exists but is thin relative to reference symbols. Investigate stream sparsity or filtering.")
            status = "USDJPY_THIN_RELATIVE"
        else:
            recommendations.append("USDJPY density is not obviously thin relative to requested reference symbols.")
            status = "USDJPY_PRESENT"
    else:
        recommendations.append("USDJPY has rows but reference symbols are absent; compare against intended symbol set.")
        status = "USDJPY_PRESENT_NO_REFERENCES"
else:
    recommendations.append("Active DB candidate does not exist: " + str(active_db))

contract = {
    "contract": "POWERFLOW_T004_ACTIVE_DB_SYMBOL_DENSITY",
    "created_at": now,
    "active_db": rel(active_db),
    "source_decision_contract": "Docs/Contracts/T004_ACTIVE_DB_DECISION.json" if decision else None,
    "status": status,
    "symbols": SYMBOLS,
    "symbol_totals": symbol_totals,
    "table_count": len(tables),
    "populated_table_count": populated_tables,
    "symbol_indexed_table_count": symbol_indexed_tables,
    "tables": tables,
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_ACTIVE_DB_SYMBOL_DENSITY.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

report_path = audit_dir / ("T004_ACTIVE_DB_SYMBOL_DENSITY_" + stamp + ".md")
md = []
md.append("# T004-D Active DB Symbol Density")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Result")
md.append("")
md.append("- Status: " + status)
md.append("- Active DB: " + rel(active_db))
md.append("- Symbols: " + ", ".join(SYMBOLS))
md.append("- Tables inspected: " + str(len(tables)))
md.append("- Populated tables: " + str(populated_tables))
md.append("- Symbol-indexed tables: " + str(symbol_indexed_tables))
md.append("")
md.append("## Symbol totals")
md.append("")
for sym in SYMBOLS:
    md.append("- " + sym + ": " + str(symbol_totals.get(sym, 0)))
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Table density")
md.append("")
if tables:
    for t in tables:
        md.append("### " + t["table"])
        md.append("")
        md.append("- rows: " + str(t.get("row_count")))
        md.append("- symbol_col: " + str(t.get("symbol_col")))
        md.append("- time_col: " + str(t.get("time_col")))
        if t.get("per_symbol"):
            for sym, result in t["per_symbol"].items():
                md.append("- " + sym + " | count=" + str(result.get("count")) + " | min=" + str(result.get("min_time")) + " | max=" + str(result.get("max_time")) + " | ratio=" + str(result.get("ratio_vs_table")))
        if t.get("sample"):
            md.append("")
            md.append("sample:")
            md.append("```json")
            md.append(json.dumps(t["sample"], indent=2, ensure_ascii=False, default=str))
            md.append("```")
        md.append("")
else:
    md.append("- none")
md.append("")
md.append("## Runtime behavior")
md.append("")
md.append("- DB opened read-only.")
md.append("- No runtime wiring.")
md.append("- No dashboard files touched.")
md.append("")
md.append("## Next action")
md.append("")
md.append("If USDJPY is zero while references are present, inspect symbol routing/filter and MT4 Market Watch for USDJPY.")
md.append("If no symbol-indexed table exists, map the populated schema before symbol debugging.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_active_db_symbol_density_contract.py"
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
    "def test_t004_active_db_symbol_density_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_SYMBOL_DENSITY.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_ACTIVE_DB_SYMBOL_DENSITY"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert "USDJPY" in data["symbols"]',
    '    assert isinstance(data["symbol_totals"], dict)',
    '    assert isinstance(data["tables"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_active_db_symbol_density_status_is_known():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_SYMBOL_DENSITY.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {',
    '        "DB_NOT_FOUND",',
    '        "DB_FOUND_EMPTY",',
    '        "POPULATED_DB_NO_SYMBOL_TABLE",',
    '        "USDJPY_ZERO_REFERENCES_PRESENT",',
    '        "NO_REQUESTED_SYMBOL_ROWS",',
    '        "USDJPY_THIN_RELATIVE",',
    '        "USDJPY_PRESENT",',
    '        "USDJPY_PRESENT_NO_REFERENCES",',
    '    }',
    '    assert data["status"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "active_db": rel(active_db),
    "symbol_totals": symbol_totals,
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running active DB symbol density"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-D active DB symbol density failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usdjpy_thin_data_diagnostic_contract.py `
    tests/test_t004_capture_db_path_audit_contract.py `
    tests/test_t004_active_db_decision_contract.py `
    tests/test_t004_active_db_symbol_density_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-D tests failed"
}
Ok "T004-D tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_ACTIVE_DB_SYMBOL_DENSITY.json",
    "tests/test_t004_active_db_symbol_density_contract.py",
    "scripts/t004_active_db_symbol_density.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T004_ACTIVE_DB_SYMBOL_DENSITY_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T004-D files"
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
    Warn "No staged T004-D changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): measure symbol density on active DB candidate"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_D_ACTIVE_DB_SYMBOL_DENSITY.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-D active DB symbol density"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-D active DB symbol density"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Symbol density measured on active DB candidate."
    $content += "- Runtime unchanged."
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
    $content += "Read Docs/Audits/T004_ACTIVE_DB_SYMBOL_DENSITY_*.md and decide whether USDJPY issue is symbol routing, schema mismatch, or no symbol-indexed data."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-D active DB symbol density"
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

Ok "T004-D active DB symbol density complete"
Log "Final status"
git status --short
git log --oneline -7
