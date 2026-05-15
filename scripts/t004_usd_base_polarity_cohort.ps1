param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$DbPath = "Core/powerflow.db",
    [string[]]$UsdBaseSymbols = @("USDJPY", "USDCAD"),
    [string[]]$UsdQuoteSymbols = @("GBPUSD", "EURUSD"),
    [int]$WatchSeconds = 120,
    [int]$IntervalSeconds = 10,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-N] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

if ($WatchSeconds -lt 20) { throw "WatchSeconds must be >= 20" }
if ($IntervalSeconds -lt 2) { throw "IntervalSeconds must be >= 2" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-N USD base polarity cohort test"
Log "RepoPath = $RepoPath"
Log "DbPath = $DbPath"
Log "UsdBaseSymbols = $($UsdBaseSymbols -join ',')"
Log "UsdQuoteSymbols = $($UsdQuoteSymbols -join ',')"
Log "WatchSeconds = $WatchSeconds"
Log "IntervalSeconds = $IntervalSeconds"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -8

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-N commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004n_usd_base_polarity_cohort.py"
$dbPathJson = ($DbPath | ConvertTo-Json -Compress)
$baseJson = ($UsdBaseSymbols | ConvertTo-Json -Compress)
$quoteJson = ($UsdQuoteSymbols | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
import sqlite3
import time

DB_PATH_ARG = $dbPathJson
USD_BASE_SYMBOLS = $baseJson
USD_QUOTE_SYMBOLS = $quoteJson
WATCH_SECONDS = int($WatchSeconds)
INTERVAL_SECONDS = int($IntervalSeconds)
ALL_SYMBOLS = list(dict.fromkeys(list(USD_BASE_SYMBOLS) + list(USD_QUOTE_SYMBOLS)))

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

def parse_fx_symbol(symbol: str) -> dict:
    s = str(symbol).upper().strip()
    base = s[:3] if len(s) >= 6 else None
    quote = s[3:6] if len(s) >= 6 else None
    if base == "USD":
        polarity = "USD_BASE"
        usd_strength_sign = +1
    elif quote == "USD":
        polarity = "USD_QUOTE"
        usd_strength_sign = -1
    else:
        polarity = "NON_USD_OR_UNKNOWN"
        usd_strength_sign = 0
    return {"symbol": symbol, "base": base, "quote": quote, "polarity": polarity, "usd_strength_sign": usd_strength_sign}

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

def snapshot():
    snap = {
        "taken_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_exists": db_path.exists(),
        "total_rows": None,
        "tables": [],
        "symbol_totals": {sym: 0 for sym in ALL_SYMBOLS},
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
                    "symbol_col": symbol_col,
                    "time_col": time_col,
                    "id_col": id_col,
                    "per_symbol": {},
                    "top_symbols": [],
                }
                if symbol_col:
                    try:
                        rows = con.execute(
                            "SELECT " + quote_ident(symbol_col) + " AS sym, COUNT(*) AS n FROM "
                            + quote_ident(table) + " GROUP BY " + quote_ident(symbol_col)
                            + " ORDER BY n DESC LIMIT 30"
                        ).fetchall()
                        entry["top_symbols"] = [{"symbol": row["sym"], "count": row["n"]} for row in rows]
                    except Exception as exc:
                        entry["top_symbols_error"] = str(exc)

                    for sym in ALL_SYMBOLS:
                        result = {"count": 0, "max_time": None, "age_seconds": None, "near_symbol_candidates": []}
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
                            snap["symbol_totals"][sym] += result["count"]

                            # Near symbol / suffix candidates for this exact requested symbol.
                            try:
                                near_rows = con.execute(
                                    "SELECT " + quote_ident(symbol_col) + " AS sym, COUNT(*) AS n FROM "
                                    + quote_ident(table)
                                    + " WHERE UPPER(" + quote_ident(symbol_col) + ") LIKE ? "
                                    + "GROUP BY " + quote_ident(symbol_col)
                                    + " ORDER BY n DESC LIMIT 12",
                                    (sym.upper() + "%",),
                                ).fetchall()
                                result["near_symbol_candidates"] = [
                                    {"symbol": row["sym"], "count": row["n"]}
                                    for row in near_rows
                                    if str(row["sym"]).upper() != sym.upper()
                                ]
                            except Exception:
                                pass
                        except Exception as exc:
                            result["error"] = str(exc)
                        entry["per_symbol"][sym] = result
                snap["tables"].append(entry)
            snap["total_rows"] = total
        finally:
            con.close()
    except Exception as exc:
        snap["error"] = str(exc)
    return snap

before = snapshot()
time.sleep(WATCH_SECONDS)
after = snapshot()

symbol_deltas = {
    sym: (after.get("symbol_totals", {}).get(sym, 0) - before.get("symbol_totals", {}).get(sym, 0))
    for sym in ALL_SYMBOLS
}

table_deltas = []
before_tables = {t["table"]: t for t in before.get("tables", [])}
after_tables = {t["table"]: t for t in after.get("tables", [])}
for table, after_t in sorted(after_tables.items()):
    before_t = before_tables.get(table, {})
    before_rows = before_t.get("row_count")
    after_rows = after_t.get("row_count")
    row_delta = after_rows - before_rows if isinstance(before_rows, int) and isinstance(after_rows, int) else None
    per_symbol_delta = {}
    for sym in ALL_SYMBOLS:
        b = before_t.get("per_symbol", {}).get(sym, {}).get("count", 0)
        a = after_t.get("per_symbol", {}).get(sym, {}).get("count", 0)
        per_symbol_delta[sym] = a - b if isinstance(a, int) and isinstance(b, int) else None
    table_deltas.append({
        "table": table,
        "row_delta": row_delta,
        "symbol_col": after_t.get("symbol_col"),
        "time_col": after_t.get("time_col"),
        "per_symbol_delta": per_symbol_delta,
    })

active_tables = [t for t in table_deltas if isinstance(t["row_delta"], int) and t["row_delta"] > 0]

usd_base_deltas = {sym: symbol_deltas.get(sym, 0) for sym in USD_BASE_SYMBOLS}
usd_quote_deltas = {sym: symbol_deltas.get(sym, 0) for sym in USD_QUOTE_SYMBOLS}
base_advanced = {sym: d for sym, d in usd_base_deltas.items() if d and d > 0}
quote_advanced = {sym: d for sym, d in usd_quote_deltas.items() if d and d > 0}

# Historical totals and latest age at final snapshot.
final_symbol_state = {}
for sym in ALL_SYMBOLS:
    state = parse_fx_symbol(sym)
    state["total_count"] = after.get("symbol_totals", {}).get(sym, 0)
    max_age = None
    max_time = None
    near_candidates = []
    for table in after.get("tables", []):
        data = table.get("per_symbol", {}).get(sym, {})
        if data.get("max_time") is not None:
            age = data.get("age_seconds")
            if max_age is None or (age is not None and age < max_age):
                max_age = age
                max_time = data.get("max_time")
        for cand in data.get("near_symbol_candidates", []) or []:
            near_candidates.append({"table": table.get("table"), **cand})
    state["latest_time"] = max_time
    state["latest_age_seconds"] = max_age
    state["near_symbol_candidates"] = near_candidates
    state["delta"] = symbol_deltas.get(sym, 0)
    final_symbol_state[sym] = state

# Code audit for USD polarity assumptions.
code_patterns = [
    "endswith(\"USD\")",
    "endswith('USD')",
    ".endswith(\"USD\")",
    ".endswith('USD')",
    "quote == \"USD\"",
    "quote == 'USD'",
    "quote != \"USD\"",
    "quote != 'USD'",
    "startswith(\"USD\")",
    "startswith('USD')",
    "base == \"USD\"",
    "base == 'USD'",
    "base != \"USD\"",
    "base != 'USD'",
    "symbol[:3]",
    "symbol[3:",
    "USDJPY",
    "USDCAD",
    "GBPUSD",
    "EURUSD",
    "allowed_symbols",
    "symbols",
    "allowlist",
]
code_hits = []
for root in [repo / "Core", repo / "scripts", repo / "tests"]:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".ps1", ".json", ".md", ".txt"}:
            continue
        if any(part in {".git", "__pycache__", "Archive", "backup", "backups"} for part in path.relative_to(repo).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            lower = line.lower()
            matched = [p for p in code_patterns if p.lower() in lower]
            if matched:
                hits.append({"line": i, "patterns": matched, "text": line.strip()[:280]})
        if hits:
            code_hits.append({"file": rel(path), "hit_count": len(hits), "hits": hits[:100]})

polarity_risk_hits = []
for item in code_hits:
    for hit in item["hits"]:
        text = hit["text"]
        lower = text.lower()
        if "endswith" in lower and "usd" in lower:
            polarity_risk_hits.append({"risk": "ENDS_WITH_USD_ONLY", "file": item["file"], **hit})
        if "quote" in lower and "usd" in lower:
            polarity_risk_hits.append({"risk": "QUOTE_USD_ASSUMPTION", "file": item["file"], **hit})
        if "startswith" in lower and "usd" in lower:
            polarity_risk_hits.append({"risk": "STARTS_WITH_USD_PRESENT", "file": item["file"], **hit})
        if "base" in lower and "usd" in lower:
            polarity_risk_hits.append({"risk": "BASE_USD_PRESENT", "file": item["file"], **hit})

# Verdict classification.
if quote_advanced and not base_advanced:
    verdict = "USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES"
elif symbol_deltas.get("USDCAD", 0) > 0 and symbol_deltas.get("USDJPY", 0) == 0:
    verdict = "USDCAD_ADVANCES_USDJPY_ZERO_SYMBOL_SPECIFIC"
elif symbol_deltas.get("USDJPY", 0) > 0 and symbol_deltas.get("USDCAD", 0) == 0:
    verdict = "USDJPY_ADVANCES_USDCAD_ZERO_SYMBOL_SPECIFIC"
elif base_advanced and quote_advanced:
    verdict = "USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE"
elif base_advanced and not quote_advanced:
    verdict = "USD_BASE_ADVANCES_REFERENCES_IDLE"
elif not base_advanced and not quote_advanced:
    verdict = "NO_TRACKED_SYMBOL_ADVANCED"
else:
    verdict = "INCONCLUSIVE_POLARITY_COHORT"

recommendations = []
if verdict == "USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES":
    recommendations.append("Strong suspicion: capture/routing logic favors USD-quote pairs (XXXUSD) and does not pass USD-base pairs.")
    recommendations.append("Search and audit any symbol.endswith('USD') / quote == 'USD' filters before changing engine logic.")
elif verdict == "USDCAD_ADVANCES_USDJPY_ZERO_SYMBOL_SPECIFIC":
    recommendations.append("USDCAD advanced while USDJPY did not. USD-base polarity is not globally blocked; inspect USDJPY-specific feed/Market Watch/routing.")
elif verdict == "USDJPY_ADVANCES_USDCAD_ZERO_SYMBOL_SPECIFIC":
    recommendations.append("USDJPY advanced while USDCAD did not. Inspect USDCAD EA/source setup; it may not be feeding yet.")
elif verdict == "USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE":
    recommendations.append("Both USD-base and USD-quote cohorts advance. The prior USDJPY defect may be intermittent or symbol-specific.")
elif verdict == "NO_TRACKED_SYMBOL_ADVANCED":
    recommendations.append("No tracked symbols advanced during the window. Rerun while capture/feed is active.")
else:
    recommendations.append("Polarity cohort result is inconclusive. Inspect table deltas and code polarity hits.")

recommendations.append("Keep engine/scoring untouched. This test targets capture routing and USD base/quote normalization.")

contract = {
    "contract": "POWERFLOW_T004_USD_BASE_POLARITY_COHORT",
    "created_at": started_at.isoformat().replace("+00:00", "Z"),
    "db_path": rel(db_path),
    "watch_seconds": WATCH_SECONDS,
    "interval_seconds": INTERVAL_SECONDS,
    "usd_base_symbols": USD_BASE_SYMBOLS,
    "usd_quote_symbols": USD_QUOTE_SYMBOLS,
    "symbol_models": {sym: parse_fx_symbol(sym) for sym in ALL_SYMBOLS},
    "verdict": verdict,
    "symbol_deltas": symbol_deltas,
    "usd_base_deltas": usd_base_deltas,
    "usd_quote_deltas": usd_quote_deltas,
    "final_symbol_state": final_symbol_state,
    "active_tables": active_tables,
    "table_deltas": table_deltas,
    "polarity_risk_hits": polarity_risk_hits[:160],
    "code_hits": code_hits[:160],
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
    "engine_change_required": False,
}
contract_path = contract_dir / "T004_USD_BASE_POLARITY_COHORT.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_USD_BASE_POLARITY_COHORT_RESULT_" + stamp + ".md")
md = []
md.append("# T004-N USD Base Polarity Cohort Test")
md.append("")
md.append("Date: " + started_at.isoformat().replace("+00:00", "Z"))
md.append("")
md.append("## Question")
md.append("")
md.append("Does the pipeline reject or under-route pairs where USD is the base currency, such as USDJPY and USDCAD, while accepting USD-quote pairs such as GBPUSD and EURUSD?")
md.append("")
md.append("## Verdict")
md.append("")
md.append("- Verdict: `" + verdict + "`")
md.append("- DB: `" + rel(db_path) + "`")
md.append("- Watch seconds: `" + str(WATCH_SECONDS) + "`")
md.append("")
md.append("## Symbol model")
md.append("")
for sym in ALL_SYMBOLS:
    model = parse_fx_symbol(sym)
    md.append("- `" + sym + "` | base=" + str(model["base"]) + " | quote=" + str(model["quote"]) + " | polarity=" + model["polarity"] + " | usd_strength_sign=" + str(model["usd_strength_sign"]))
md.append("")
md.append("## Live deltas")
md.append("")
for sym in ALL_SYMBOLS:
    state = final_symbol_state.get(sym, {})
    md.append("- `" + sym + "` | delta=" + str(symbol_deltas.get(sym)) + " | total=" + str(state.get("total_count")) + " | latest=" + str(state.get("latest_time")) + " | age_seconds=" + str(state.get("latest_age_seconds")))
md.append("")
md.append("## Active tables")
md.append("")
if active_tables:
    for item in active_tables:
        md.append("- `" + item["table"] + "` | row_delta=" + str(item.get("row_delta")) + " | symbol_col=" + str(item.get("symbol_col")) + " | per_symbol_delta=`" + json.dumps(item.get("per_symbol_delta"), ensure_ascii=False) + "`")
else:
    md.append("- none")
md.append("")
md.append("## Polarity risk hits")
md.append("")
if polarity_risk_hits:
    for hit in polarity_risk_hits[:80]:
        md.append("- `" + hit["risk"] + "` | " + hit["file"] + ":" + str(hit["line"]) + " | " + hit["text"])
else:
    md.append("- none")
md.append("")
md.append("## Near-symbol / suffix candidates")
md.append("")
any_near = False
for sym, state in final_symbol_state.items():
    cands = state.get("near_symbol_candidates", [])
    if cands:
        any_near = True
        md.append("### " + sym)
        for cand in cands:
            md.append("- `" + str(cand.get("table")) + "` | `" + str(cand.get("symbol")) + "` count=" + str(cand.get("count")))
if not any_near:
    md.append("- none")
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not patch `Core/engine.py`, `pf_engine_v6_core.py`, dashboard, or scoring from this result. Patch only capture routing / symbol normalization if confirmed.")
md.append("")
md.append("## Revalidation")
md.append("")
md.append("After fixing feed/routing, rerun:")
md.append("")
md.append("```powershell")
md.append(".\\scripts\\t004_usd_base_polarity_cohort.ps1 -WatchSeconds 120 -IntervalSeconds 10")
md.append(".\\scripts\\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10")
md.append("```")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_usd_base_polarity_cohort_contract.py"
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
    "def test_t004_usd_base_polarity_cohort_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USD_BASE_POLARITY_COHORT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_USD_BASE_POLARITY_COHORT"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert data["engine_change_required"] is False',
    '    assert "USDJPY" in data["usd_base_symbols"]',
    '    assert "USDCAD" in data["usd_base_symbols"]',
    '    assert isinstance(data["symbol_deltas"], dict)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_usd_base_polarity_verdict_known():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_USD_BASE_POLARITY_COHORT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    allowed = {',
    '        "USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES",',
    '        "USDCAD_ADVANCES_USDJPY_ZERO_SYMBOL_SPECIFIC",',
    '        "USDJPY_ADVANCES_USDCAD_ZERO_SYMBOL_SPECIFIC",',
    '        "USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE",',
    '        "USD_BASE_ADVANCES_REFERENCES_IDLE",',
    '        "NO_TRACKED_SYMBOL_ADVANCED",',
    '        "INCONCLUSIVE_POLARITY_COHORT",',
    '    }',
    '    assert data["verdict"] in allowed',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "verdict": verdict,
    "symbol_deltas": symbol_deltas,
    "usd_base_deltas": usd_base_deltas,
    "usd_quote_deltas": usd_quote_deltas,
    "active_table_count": len(active_tables),
    "polarity_risk_hit_count": len(polarity_risk_hits),
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running USD base polarity cohort test"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-N USD base polarity cohort test failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usd_base_polarity_cohort_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-N tests failed"
}
Ok "T004-N tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_USD_BASE_POLARITY_COHORT.json",
    "tests/test_t004_usd_base_polarity_cohort_contract.py",
    "scripts/t004_usd_base_polarity_cohort.ps1"
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_USD_BASE_POLARITY_COHORT_RESULT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-N files"
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
    Warn "No staged T004-N changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): test USD base polarity routing with USDCAD"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_N_USD_BASE_POLARITY_COHORT.md"

    $lastCommits = git log --oneline -8
    $content = @()
    $content += "# CHECKPOINT - T004-N USD base polarity cohort"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-N USD base polarity cohort using USDCAD"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- USD base polarity cohort test created and executed."
    $content += "- Runtime unchanged."
    $content += "- DB read-only."
    $content += "- Engine change not required from this script alone."
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""
    $content += "## Revalidation"
    $content += ""
    $content += "Rerun after ensuring USDCAD EA/feed is active and market is moving."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-N USD base polarity cohort"
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

Ok "T004-N USD base polarity cohort complete"
Log "Final status"
git status --short
git log --oneline -8
