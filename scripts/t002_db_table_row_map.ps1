param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-I] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-I DB table row map"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002-I commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t002_db_table_row_map.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3

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

legacy_fields = {"dev_a", "dev_b", "val_a", "val_b", "gap", "timeframe", "spread"}
price_fields = {"symbol", "timestamp", "time", "created_at", "logged_at", "bid", "ask", "price", "mid", "close"}
force_fields = {"force", "score", "currency", "base", "quote", "value", "strength"}

db_path = next((p for p in db_candidates if p.exists()), None)
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

status = "NO_DB"
tables = []
recommendations = []

if db_path is not None:
    status = "DB_FOUND"
    uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        raw_tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
        for table in raw_tables:
            try:
                info = con.execute(f"PRAGMA table_info(\"{table}\")").fetchall()
                columns = [row[1] for row in info]
                lower = {c.lower(): c for c in columns}

                try:
                    row_count = con.execute(f"SELECT COUNT(*) AS n FROM \"{table}\"").fetchone()["n"]
                except sqlite3.Error:
                    row_count = None

                legacy_hit = sorted([f for f in legacy_fields if f in lower])
                price_hit = sorted([f for f in price_fields if f in lower])
                force_hit = sorted([f for f in force_fields if f in lower])

                score = len(legacy_hit) * 5 + len(price_hit) * 2 + len(force_hit)
                if row_count:
                    score += 3

                sample = None
                if row_count and row_count > 0:
                    sample_cols = columns[:12]
                    select_cols = ", ".join('"' + c.replace('"', '""') + '"' for c in sample_cols)
                    try:
                        row = con.execute(f"SELECT {select_cols} FROM \"{table}\" LIMIT 1").fetchone()
                        if row:
                            sample = {k: row[k] for k in row.keys()}
                    except sqlite3.Error:
                        sample = None

                tables.append({
                    "table": table,
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": columns,
                    "legacy_hits": legacy_hit,
                    "price_hits": price_hit,
                    "force_hits": force_hit,
                    "score": score,
                    "sample": sample,
                })
            except sqlite3.Error as exc:
                tables.append({
                    "table": table,
                    "error": str(exc),
                    "row_count": None,
                    "column_count": 0,
                    "columns": [],
                    "legacy_hits": [],
                    "price_hits": [],
                    "force_hits": [],
                    "score": 0,
                    "sample": None,
                })
    finally:
        con.close()

    tables.sort(key=lambda x: (-(x.get("score") or 0), -(x.get("row_count") or 0), x.get("table", "")))

    populated = [t for t in tables if (t.get("row_count") or 0) > 0]
    legacy_populated = [t for t in populated if t.get("legacy_hits")]
    price_populated = [t for t in populated if t.get("price_hits")]
    force_populated = [t for t in populated if t.get("force_hits")]

    if legacy_populated:
        recommendations.append("Use populated legacy-like table: " + legacy_populated[0]["table"])
    elif price_populated:
        recommendations.append("No populated legacy table found. Use price-like populated table for derived context: " + price_populated[0]["table"])
    elif force_populated:
        recommendations.append("No tick/price table found. Use force-like populated table only for field mapping: " + force_populated[0]["table"])
    elif populated:
        recommendations.append("DB has populated tables but no obvious tick/legacy surface. Manual schema review needed.")
    else:
        recommendations.append("DB found but all inspected tables appear empty.")
else:
    recommendations.append("No powerflow.db found in expected locations.")

contract = {
    "contract": "POWERFLOW_T002_DB_TABLE_ROW_MAP",
    "created_at": now,
    "status": status,
    "db_path": str(db_path.relative_to(repo)) if db_path and db_path.is_relative_to(repo) else (str(db_path) if db_path else None),
    "table_count": len(tables),
    "tables": tables,
    "recommendations": recommendations,
    "runtime_wired": False,
    "read_only": True,
}
contract_path = contract_dir / "T002_DB_TABLE_ROW_MAP.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

report_path = audit_dir / ("T002_DB_TABLE_ROW_MAP_" + stamp + ".md")
md = []
md.append("# T002-I DB Table Row Map")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Result")
md.append("")
md.append("- Status: " + status)
md.append("- DB path: " + (str(db_path) if db_path else "not found"))
md.append("- Table count: " + str(len(tables)))
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Top table candidates")
md.append("")
if tables:
    for t in tables[:30]:
        md.append("- " + t["table"] + " | rows=" + str(t.get("row_count")) + " | cols=" + str(t.get("column_count")) + " | score=" + str(t.get("score")) + " | legacy=" + ",".join(t.get("legacy_hits", [])) + " | price=" + ",".join(t.get("price_hits", [])) + " | force=" + ",".join(t.get("force_hits", [])))
else:
    md.append("- none")
md.append("")
md.append("## Populated table samples")
md.append("")
sampled = [t for t in tables if t.get("sample")]
if sampled:
    for t in sampled[:20]:
        md.append("### " + t["table"])
        md.append("")
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
md.append("- Runtime not wired.")
md.append("- Core/engine.py unchanged.")
md.append("- Core/capture_bridge.py unchanged.")
md.append("- Core/pf_engine_v6_adapter.py unchanged.")
md.append("")
md.append("## Next step")
md.append("")
md.append("If a populated price-like table exists, generate a derived-context replay fixture from that table. If not, stop T002 runtime wiring and keep the detached core as tested extraction target only.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t002_db_table_row_map_contract.py"
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
    "def test_t002_db_table_row_map_contract_is_explicit():",
    '    path = _repo() / "Docs" / "Contracts" / "T002_DB_TABLE_ROW_MAP.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T002_DB_TABLE_ROW_MAP"',
    '    assert data["runtime_wired"] is False',
    '    assert data["read_only"] is True',
    '    assert data["status"] in {"NO_DB", "DB_FOUND"}',
    '    assert isinstance(data["table_count"], int)',
    '    assert isinstance(data["tables"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t002_db_table_row_map_entries_have_required_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T002_DB_TABLE_ROW_MAP.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    for table in data["tables"]:',
    '        assert "table" in table',
    '        assert "row_count" in table',
    '        assert "columns" in table',
    '        assert "score" in table',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "db_path": str(db_path) if db_path else None,
    "table_count": len(tables),
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Creating DB table row map"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "T002-I DB table row map generation failed"
}

Remove-Item $pythonPatch -Force -ErrorAction SilentlyContinue

Log "Running targeted T002 tests"
python -m pytest `
    tests/test_t002_engine_process_tick_contract.py `
    tests/test_t002_engine_v6_adapter.py `
    tests/test_t002_engine_v6_core.py `
    tests/test_t002_engine_tick_surface_contract.py `
    tests/test_t002_engine_v6_core_legacy_surface.py `
    tests/test_t002_engine_v6_core_golden_ticks.py `
    tests/test_t002_engine_v6_core_db_replay_comparison.py `
    tests/test_t002_db_table_row_map_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002-I tests failed"
}
Ok "T002 tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T002_DB_TABLE_ROW_MAP.json",
    "tests/test_t002_db_table_row_map_contract.py",
    "scripts/t002_db_table_row_map.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T002_DB_TABLE_ROW_MAP_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T002-I files"
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
    Warn "No staged T002-I changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t002): map DB tables for engine v6 replay source"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_I_DB_TABLE_ROW_MAP.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T002-I DB table row map"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T002-I DB table row map"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- DB table row map created in read-only mode."
    $content += "- Runtime remains unwired."
    $content += "- Dashboard workspace files were intentionally left untouched."
    $content += ""
    $content += "## Tests"
    $content += ""
    $content += "- T002 targeted tests passed during script run."
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""
    $content += "## Next step"
    $content += ""
    $content += "Use the populated table recommendation to decide whether a real replay fixture can be generated."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002-I DB table row map"
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

Ok "T002-I DB table row map complete"
Log "Final status"
git status --short
git log --oneline -7
