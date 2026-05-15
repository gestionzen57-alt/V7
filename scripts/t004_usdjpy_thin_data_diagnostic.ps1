param(
    [string]$RepoPath = (Get-Location).Path,
    [string[]]$Symbols = @("USDJPY", "GBPUSD", "EURUSD"),
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004 USDJPY thin data diagnostic"
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
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004 commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004_usdjpy_thin_data_diagnostic.py"
$symbolsJson = ($Symbols | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3
import sys

SYMBOLS = $symbolsJson

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

db_candidates = [
    repo / "powerflow.db",
    repo / "Core" / "powerflow.db",
    repo / "data" / "powerflow.db",
]

db_path = next((p for p in db_candidates if p.exists()), None)
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

time_candidates = [
    "created_at", "timestamp", "time", "logged_at", "detected_at",
    "source_created_at", "bar_time", "ts", "datetime"
]
symbol_candidates = ["symbol", "pair", "instrument"]

status = "NO_DB"
tables = []
symbol_matrix = {}
recommendations = []
log_findings = []

def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except Exception:
        return str(path)

if db_path is not None:
    status = "DB_FOUND"
    uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
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

            row_count = None
            try:
                row_count = con.execute("SELECT COUNT(*) AS n FROM " + quote_ident(table)).fetchone()["n"]
            except sqlite3.Error:
                pass

            table_entry = {
                "table": table,
                "row_count": row_count,
                "columns": columns,
                "symbol_col": symbol_col,
                "time_col": time_col,
                "per_symbol": {},
            }

            if symbol_col:
                for sym in SYMBOLS:
                    result = {"count": 0, "min_time": None, "max_time": None}
                    try:
                        if time_col:
                            sql = (
                                "SELECT COUNT(*) AS n, MIN(" + quote_ident(time_col) + ") AS min_t, "
                                "MAX(" + quote_ident(time_col) + ") AS max_t FROM " + quote_ident(table)
                                + " WHERE " + quote_ident(symbol_col) + " = ?"
                            )
                            row = con.execute(sql, (sym,)).fetchone()
                            result = {"count": row["n"], "min_time": row["min_t"], "max_time": row["max_t"]}
                        else:
                            sql = (
                                "SELECT COUNT(*) AS n FROM " + quote_ident(table)
                                + " WHERE " + quote_ident(symbol_col) + " = ?"
                            )
                            row = con.execute(sql, (sym,)).fetchone()
                            result = {"count": row["n"], "min_time": None, "max_time": None}
                    except sqlite3.Error as exc:
                        result = {"count": None, "min_time": None, "max_time": None, "error": str(exc)}
                    table_entry["per_symbol"][sym] = result

                    symbol_matrix.setdefault(sym, {})[table] = result
            else:
                # Try table names like bars_m1 without symbol column.
                table_lower = table.lower()
                if any(k in table_lower for k in ["usdjpy", "gbpusd", "eurusd"]):
                    for sym in SYMBOLS:
                        if sym.lower() in table_lower:
                            symbol_matrix.setdefault(sym, {})[table] = {
                                "count": row_count or 0,
                                "min_time": None,
                                "max_time": None,
                                "table_name_match": True,
                            }

            tables.append(table_entry)
    finally:
        con.close()

    # Build recommendations.
    usdjpy_counts = []
    ref_counts = []
    for table in tables:
        per = table.get("per_symbol", {})
        if "USDJPY" in per:
            c = per["USDJPY"].get("count")
            if isinstance(c, int):
                usdjpy_counts.append((table["table"], c))
        for ref in ["GBPUSD", "EURUSD"]:
            if ref in per:
                c = per[ref].get("count")
                if isinstance(c, int):
                    ref_counts.append((table["table"], ref, c))

    usdjpy_nonzero = [(t, c) for t, c in usdjpy_counts if c > 0]
    ref_nonzero = [(t, s, c) for t, s, c in ref_counts if c > 0]

    if not tables:
        recommendations.append("DB found but no tables detected.")
    elif not any((t.get("row_count") or 0) > 0 for t in tables):
        recommendations.append("DB found but all inspected tables have zero rows. Diagnose capture path or DB path mismatch first.")
    elif not usdjpy_nonzero and ref_nonzero:
        recommendations.append("Reference symbols have data but USDJPY has zero rows. Likely symbol routing / MT4 stream / bridge symbol filter issue.")
    elif not usdjpy_nonzero and not ref_nonzero:
        recommendations.append("No inspected symbol has rows. Likely empty DB, wrong DB path, or capture stopped.")
    else:
        recommendations.append("USDJPY has rows in at least one table. Compare freshness and density vs GBPUSD/EURUSD.")

else:
    recommendations.append("No powerflow.db found in expected locations.")

# Inspect lightweight logs/config/code references, no large file parsing.
search_roots = [repo / "Core", repo / "logs", repo / "scripts"]
patterns = ["USDJPY", "symbols", "symbol", "force_snapshots", "capture_bridge", "thin", "stale"]
for root in search_roots:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".ps1", ".json", ".txt", ".log", ".md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        hits = []
        for pat in patterns:
            if pat.lower() in text.lower():
                hits.append(pat)
        if hits:
            log_findings.append({
                "file": rel(path),
                "hits": sorted(set(hits)),
            })
        if len(log_findings) >= 80:
            break
    if len(log_findings) >= 80:
        break

contract = {
    "contract": "POWERFLOW_T004_USDJPY_THIN_DATA_DIAGNOSTIC",
    "created_at": now,
    "status": status,
    "db_path": rel(db_path) if db_path else None,
    "symbols": SYMBOLS,
    "table_count": len(tables),
    "tables": tables,
    "symbol_matrix": symbol_matrix,
    "recommendations": recommendations,
    "code_log_findings": log_findings,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_USDJPY_THIN_DATA_DIAGNOSTIC.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

report_path = audit_dir / ("T004_USDJPY_THIN_DATA_DIAGNOSTIC_" + stamp + ".md")
md = []
md.append("# T004 USDJPY Thin Data Diagnostic")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Result")
md.append("")
md.append("- Status: " + status)
md.append("- DB path: " + (rel(db_path) if db_path else "not found"))
md.append("- Symbols: " + ", ".join(SYMBOLS))
md.append("- Tables inspected: " + str(len(tables)))
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Per-symbol table matrix")
md.append("")
for sym in SYMBOLS:
    md.append("### " + sym)
    md.append("")
    entries = symbol_matrix.get(sym, {})
    if entries:
        for table, result in sorted(entries.items()):
            md.append("- " + table + " | count=" + str(result.get("count")) + " | min=" + str(result.get("min_time")) + " | max=" + str(result.get("max_time")))
    else:
        md.append("- no symbol-indexed table entries detected")
    md.append("")
md.append("## Table overview")
md.append("")
if tables:
    for t in tables:
        md.append("- " + t["table"] + " | rows=" + str(t.get("row_count")) + " | symbol_col=" + str(t.get("symbol_col")) + " | time_col=" + str(t.get("time_col")))
else:
    md.append("- none")
md.append("")
md.append("## Code/log references")
md.append("")
if log_findings:
    for item in log_findings[:80]:
        md.append("- " + item["file"] + " | hits=" + ", ".join(item["hits"]))
else:
    md.append("- none")
md.append("")
md.append("## Runtime behavior")
md.append("")
md.append("- DB opened read-only.")
md.append("- No runtime wiring.")
md.append("- No dashboard file touched.")
md.append("")
md.append("## Next action candidate")
md.append("")
md.append("If DB is empty, diagnose the active DB path and capture insertion path before changing any engine logic.")
md.append("If reference symbols have rows but USDJPY does not, inspect symbol filters / MT4 Market Watch / bridge symbol allowlist.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_usdjpy_thin_data_diagnostic_contract.py"
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
    "def test_t004_usdjpy_diagnostic_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_DATA_DIAGNOSTIC.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_USDJPY_THIN_DATA_DIAGNOSTIC"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert "USDJPY" in data["symbols"]',
    '    assert isinstance(data["tables"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_usdjpy_diagnostic_tables_have_required_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_DATA_DIAGNOSTIC.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    for table in data["tables"]:',
    '        assert "table" in table',
    '        assert "row_count" in table',
    '        assert "columns" in table',
    '        assert "per_symbol" in table',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "db_path": rel(db_path) if db_path else None,
    "table_count": len(tables),
    "recommendations": recommendations,
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running USDJPY thin data diagnostic"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004 diagnostic generation failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usdjpy_thin_data_diagnostic_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004 tests failed"
}
Ok "T004 tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_USDJPY_THIN_DATA_DIAGNOSTIC.json",
    "tests/test_t004_usdjpy_thin_data_diagnostic_contract.py",
    "scripts/t004_usdjpy_thin_data_diagnostic.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T004_USDJPY_THIN_DATA_DIAGNOSTIC_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T004 files"
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
    Warn "No staged T004 changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): diagnose USDJPY thin data path"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_USDJPY_THIN_DATA_DIAGNOSTIC.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004 USDJPY thin data diagnostic"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004 USDJPY thin data diagnostic"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- T004 diagnostic created."
    $content += "- DB read-only."
    $content += "- Runtime unchanged."
    $content += "- Dashboard workspace files were intentionally left untouched."
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""
    $content += "## Next step"
    $content += ""
    $content += "Read Docs/Audits/T004_USDJPY_THIN_DATA_DIAGNOSTIC_*.md and decide whether issue is DB path, capture insertion, or symbol routing."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004 USDJPY thin data diagnostic"
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

Ok "T004 USDJPY thin data diagnostic complete"
Log "Final status"
git status --short
git log --oneline -7
