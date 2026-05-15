param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$ThinSymbol = "USDJPY",
    [string[]]$ReferenceSymbols = @("GBPUSD", "EURUSD"),
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-E] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-E USDJPY thin root-cause map"
Log "RepoPath = $RepoPath"
Log "ThinSymbol = $ThinSymbol"
Log "ReferenceSymbols = $($ReferenceSymbols -join ',')"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-E commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004e_usdjpy_thin_root_cause.py"
$thinSymbolJson = ($ThinSymbol | ConvertTo-Json -Compress)
$refsJson = ($ReferenceSymbols | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3

THIN_SYMBOL = $thinSymbolJson
REFERENCE_SYMBOLS = $refsJson

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
plan_dir = repo / "Docs" / "Plans"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
plan_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

density_path = contract_dir / "T004_ACTIVE_DB_SYMBOL_DENSITY.json"
if not density_path.exists():
    raise SystemExit("Missing Docs/Contracts/T004_ACTIVE_DB_SYMBOL_DENSITY.json")

density = json.loads(density_path.read_text(encoding="utf-8"))
active_db = repo / density["active_db"]

if not active_db.exists():
    raise SystemExit("Active DB not found: " + str(active_db))

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path)

def parse_dt(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
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

def age_seconds(max_time):
    parsed = parse_dt(max_time)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - parsed.astimezone(dt.timezone.utc)).total_seconds()

tables = []
root_cause_votes = []
symbols = [THIN_SYMBOL] + list(REFERENCE_SYMBOLS)

uri = "file:" + str(active_db).replace("\\", "/") + "?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.row_factory = sqlite3.Row
try:
    for source_table in density.get("tables", []):
        table = source_table.get("table")
        if not table:
            continue

        symbol_col = source_table.get("symbol_col")
        time_col = source_table.get("time_col")
        row_count = source_table.get("row_count")

        entry = {
            "table": table,
            "row_count": row_count,
            "symbol_col": symbol_col,
            "time_col": time_col,
            "per_symbol": {},
            "thin_ratio_vs_ref_avg": None,
            "thin_status": "NO_SYMBOL_COLUMN",
            "latest_gap_seconds_vs_ref_best": None,
            "top_symbols": [],
        }

        if symbol_col:
            # Top symbols in the table.
            try:
                sql = (
                    "SELECT " + quote_ident(symbol_col) + " AS sym, COUNT(*) AS n "
                    "FROM " + quote_ident(table) + " GROUP BY " + quote_ident(symbol_col)
                    + " ORDER BY n DESC LIMIT 20"
                )
                entry["top_symbols"] = [{"symbol": r["sym"], "count": r["n"]} for r in con.execute(sql).fetchall()]
            except sqlite3.Error as exc:
                entry["top_symbols_error"] = str(exc)

            for sym in symbols:
                result = {"count": 0, "min_time": None, "max_time": None, "age_seconds": None}
                try:
                    if time_col:
                        sql = (
                            "SELECT COUNT(*) AS n, MIN(" + quote_ident(time_col) + ") AS min_t, "
                            "MAX(" + quote_ident(time_col) + ") AS max_t FROM " + quote_ident(table)
                            + " WHERE " + quote_ident(symbol_col) + " = ?"
                        )
                        row = con.execute(sql, (sym,)).fetchone()
                        result["count"] = row["n"]
                        result["min_time"] = row["min_t"]
                        result["max_time"] = row["max_t"]
                        result["age_seconds"] = age_seconds(row["max_t"])
                    else:
                        sql = "SELECT COUNT(*) AS n FROM " + quote_ident(table) + " WHERE " + quote_ident(symbol_col) + " = ?"
                        row = con.execute(sql, (sym,)).fetchone()
                        result["count"] = row["n"]
                except sqlite3.Error as exc:
                    result["error"] = str(exc)

                entry["per_symbol"][sym] = result

            thin_count = entry["per_symbol"].get(THIN_SYMBOL, {}).get("count") or 0
            ref_counts = [
                entry["per_symbol"].get(sym, {}).get("count") or 0
                for sym in REFERENCE_SYMBOLS
            ]
            ref_nonzero = [c for c in ref_counts if c > 0]
            if ref_nonzero:
                ref_avg = sum(ref_nonzero) / len(ref_nonzero)
                entry["thin_ratio_vs_ref_avg"] = thin_count / ref_avg if ref_avg else None
                if thin_count == 0:
                    entry["thin_status"] = "ZERO_WHILE_REFERENCES_PRESENT"
                    root_cause_votes.append("symbol_absent_in_symbol_table")
                elif entry["thin_ratio_vs_ref_avg"] is not None and entry["thin_ratio_vs_ref_avg"] < 0.25:
                    entry["thin_status"] = "THIN_UNDER_25_PERCENT_REF_AVG"
                    root_cause_votes.append("relative_sparsity")
                elif entry["thin_ratio_vs_ref_avg"] is not None and entry["thin_ratio_vs_ref_avg"] < 0.75:
                    entry["thin_status"] = "MODERATELY_THIN"
                    root_cause_votes.append("mild_relative_sparsity")
                else:
                    entry["thin_status"] = "NOT_THIN_IN_THIS_TABLE"
            elif thin_count > 0:
                entry["thin_status"] = "THIN_PRESENT_REFERENCES_ABSENT"
            else:
                entry["thin_status"] = "NO_REQUESTED_SYMBOLS"

            thin_age = entry["per_symbol"].get(THIN_SYMBOL, {}).get("age_seconds")
            ref_ages = [
                entry["per_symbol"].get(sym, {}).get("age_seconds")
                for sym in REFERENCE_SYMBOLS
                if entry["per_symbol"].get(sym, {}).get("age_seconds") is not None
            ]
            if thin_age is not None and ref_ages:
                ref_best_age = min(ref_ages)
                entry["latest_gap_seconds_vs_ref_best"] = thin_age - ref_best_age
                if entry["latest_gap_seconds_vs_ref_best"] > 600:
                    root_cause_votes.append("freshness_lag")

        tables.append(entry)
finally:
    con.close()

vote_counts = {}
for vote in root_cause_votes:
    vote_counts[vote] = vote_counts.get(vote, 0) + 1

if vote_counts:
    likely_cause = sorted(vote_counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
else:
    likely_cause = "schema_or_no_symbol_table"

recommendations = []
if likely_cause == "relative_sparsity":
    recommendations.append("USDJPY is present but materially sparse versus references. Inspect upstream symbol stream/filter, not DB path.")
    recommendations.append("Check capture bridge symbol allowlist and MT4 Market Watch subscription for USDJPY.")
elif likely_cause == "freshness_lag":
    recommendations.append("USDJPY latest timestamp lags references. Inspect whether USDJPY stream stalls after startup.")
elif likely_cause == "symbol_absent_in_symbol_table":
    recommendations.append("USDJPY is absent in at least one symbol-indexed table where references exist. Inspect symbol routing/filter.")
elif likely_cause == "mild_relative_sparsity":
    recommendations.append("USDJPY is somewhat sparse. Use thresholded monitoring before code patch.")
else:
    recommendations.append("No clear symbol-density root cause from symbol-indexed tables. Inspect schema/top_symbols manually.")

recommendations.append("Do not change engine logic. This is capture/routing/data-density territory.")

contract = {
    "contract": "POWERFLOW_T004_USDJPY_THIN_ROOT_CAUSE",
    "created_at": now,
    "active_db": rel(active_db),
    "thin_symbol": THIN_SYMBOL,
    "reference_symbols": REFERENCE_SYMBOLS,
    "source_density_contract": "Docs/Contracts/T004_ACTIVE_DB_SYMBOL_DENSITY.json",
    "likely_cause": likely_cause,
    "vote_counts": vote_counts,
    "tables": tables,
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_USDJPY_THIN_ROOT_CAUSE.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_USDJPY_THIN_ROOT_CAUSE_PLAN_" + stamp + ".md")
md = []
md.append("# T004-E USDJPY Thin Root-Cause Map")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Verdict")
md.append("")
md.append("- Active DB: " + rel(active_db))
md.append("- Thin symbol: " + THIN_SYMBOL)
md.append("- Reference symbols: " + ", ".join(REFERENCE_SYMBOLS))
md.append("- Likely cause: " + likely_cause)
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
md.append("## Table details")
md.append("")
for table in tables:
    md.append("### " + table["table"])
    md.append("")
    md.append("- rows: " + str(table.get("row_count")))
    md.append("- symbol_col: " + str(table.get("symbol_col")))
    md.append("- time_col: " + str(table.get("time_col")))
    md.append("- thin_status: " + str(table.get("thin_status")))
    md.append("- thin_ratio_vs_ref_avg: " + str(table.get("thin_ratio_vs_ref_avg")))
    md.append("- latest_gap_seconds_vs_ref_best: " + str(table.get("latest_gap_seconds_vs_ref_best")))
    md.append("")
    if table.get("per_symbol"):
        md.append("per symbol:")
        for sym, result in table["per_symbol"].items():
            md.append("- " + sym + " | count=" + str(result.get("count")) + " | min=" + str(result.get("min_time")) + " | max=" + str(result.get("max_time")) + " | age_seconds=" + str(result.get("age_seconds")))
        md.append("")
    if table.get("top_symbols"):
        md.append("top symbols:")
        for item in table["top_symbols"][:12]:
            md.append("- " + str(item.get("symbol")) + ": " + str(item.get("count")))
        md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not patch Core/engine.py. Do not patch pf_engine_v6_core.py. T004 is a data capture/routing diagnosis.")
md.append("")
md.append("## Next action")
md.append("")
md.append("T004-F should inspect capture bridge symbol filters / MT4 symbol subscription references and produce a minimal operator checklist.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_usdjpy_thin_root_cause_contract.py"
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
    "def test_t004_usdjpy_root_cause_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_ROOT_CAUSE.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_USDJPY_THIN_ROOT_CAUSE"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert data["thin_symbol"] == "USDJPY"',
    '    assert isinstance(data["tables"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_usdjpy_root_cause_is_known_category():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_ROOT_CAUSE.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {"relative_sparsity", "freshness_lag", "symbol_absent_in_symbol_table", "mild_relative_sparsity", "schema_or_no_symbol_table"}',
    '    assert data["likely_cause"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "active_db": rel(active_db),
    "likely_cause": likely_cause,
    "vote_counts": vote_counts,
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running USDJPY thin root-cause map"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-E root-cause map failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usdjpy_thin_data_diagnostic_contract.py `
    tests/test_t004_capture_db_path_audit_contract.py `
    tests/test_t004_active_db_decision_contract.py `
    tests/test_t004_active_db_symbol_density_contract.py `
    tests/test_t004_usdjpy_thin_root_cause_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-E tests failed"
}
Ok "T004-E tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_USDJPY_THIN_ROOT_CAUSE.json",
    "tests/test_t004_usdjpy_thin_root_cause_contract.py",
    "scripts/t004_usdjpy_thin_root_cause.ps1"
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_USDJPY_THIN_ROOT_CAUSE_PLAN_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-E files"
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
    Warn "No staged T004-E changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "plan(t004): map USDJPY thin data root cause"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_E_USDJPY_THIN_ROOT_CAUSE.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-E USDJPY thin root-cause map"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-E USDJPY thin root-cause map"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- USDJPY thin root-cause map created."
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
    $content += "T004-F should inspect capture symbol filters and produce operator checklist."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-E USDJPY thin root cause"
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

Ok "T004-E USDJPY thin root-cause complete"
Log "Final status"
git status --short
git log --oneline -7
