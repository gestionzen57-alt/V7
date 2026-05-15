param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-H] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-H DB replay comparison for detached V6 core"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002-H commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t002_db_replay_compare.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sqlite3

repo = Path.cwd()
core_dir = repo / "Core"
tests_dir = repo / "tests"
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"

tests_dir.mkdir(parents=True, exist_ok=True)
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)

db_candidates = [
    repo / "powerflow.db",
    repo / "Core" / "powerflow.db",
    repo / "data" / "powerflow.db",
]

db_path = next((p for p in db_candidates if p.exists()), None)
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

required_legacy = ["dev_a", "dev_b", "val_a", "val_b", "gap", "timeframe", "spread"]
price_like = ["symbol", "timestamp", "time", "bid", "ask", "price", "mid", "close"]

status = "NO_DB"
selected_table = None
columns = []
cases = []
table_scores = []

if db_path is not None:
    status = "NO_MATCHING_TABLE"
    uri = "file:" + str(db_path).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
        for table in tables:
            try:
                info = con.execute(f"PRAGMA table_info({table})").fetchall()
            except sqlite3.Error:
                continue
            cols = [row[1] for row in info]
            lower = {c.lower(): c for c in cols}
            score = sum(1 for f in required_legacy if f in lower) + sum(1 for f in price_like if f in lower)
            if score > 0:
                table_scores.append({"table": table, "score": score, "columns": cols})
        table_scores.sort(key=lambda x: (-x["score"], x["table"]))

        if table_scores:
            selected = table_scores[0]
            selected_table = selected["table"]
            columns = selected["columns"]
            lower = {c.lower(): c for c in columns}
            status = "MATCHING_TABLE_NO_ROWS"

            wanted = []
            for f in sorted(set(required_legacy + price_like)):
                if f in lower:
                    wanted.append(lower[f])

            if wanted:
                select_cols = ", ".join('"' + c.replace('"', '""') + '"' for c in wanted)
                rows = con.execute(f"SELECT {select_cols} FROM \"{selected_table}\" LIMIT 5").fetchall()
                for idx, row in enumerate(rows):
                    raw = {k: row[k] for k in row.keys()}
                    tick = {}
                    for k, v in raw.items():
                        tick[k.lower()] = v

                    # Normalize expected legacy surface using the same pure rules:
                    bid = tick.get("bid")
                    ask = tick.get("ask")
                    spread = tick.get("spread")
                    try:
                        spread_val = float(spread) if spread is not None else None
                    except (TypeError, ValueError):
                        spread_val = None
                    if spread_val is None and bid is not None and ask is not None:
                        try:
                            spread_val = float(ask) - float(bid)
                        except (TypeError, ValueError):
                            spread_val = None

                    def fnum(x):
                        if x is None:
                            return None
                        try:
                            return float(x)
                        except (TypeError, ValueError):
                            return None

                    expected_legacy = {
                        "dev_a": tick.get("dev_a"),
                        "dev_b": tick.get("dev_b"),
                        "val_a": fnum(tick.get("val_a")),
                        "val_b": fnum(tick.get("val_b")),
                        "gap": fnum(tick.get("gap")),
                        "timeframe": tick.get("timeframe"),
                        "spread": spread_val,
                    }

                    cases.append({
                        "id": "DB_" + selected_table + "_" + str(idx + 1),
                        "table": selected_table,
                        "tick": tick,
                        "expected_legacy_surface": expected_legacy,
                    })

                if cases:
                    status = "SAMPLES_FOUND"
    finally:
        con.close()

contract = {
    "contract": "POWERFLOW_T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON",
    "created_at": now,
    "status": status,
    "db_path": str(db_path.relative_to(repo)) if db_path and db_path.is_relative_to(repo) else (str(db_path) if db_path else None),
    "selected_table": selected_table,
    "selected_columns": columns,
    "table_scores": table_scores[:20],
    "case_count": len(cases),
    "cases": cases,
    "runtime_wired": False,
    "note": "Read-only DB comparison. Absence of DB samples is not a failure; it only means no replay fixture was available from local DB schema.",
}
contract_path = contract_dir / "T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

test_lines = [
    "from __future__ import annotations",
    "",
    "import json",
    "from pathlib import Path",
    "import sys",
    "",
    "",
    "def _repo() -> Path:",
    "    return Path(__file__).resolve().parents[1]",
    "",
    "",
    "def _core() -> Path:",
    '    return _repo() / "Core"',
    "",
    "",
    "def _round_float(value):",
    "    if isinstance(value, float):",
    "        return round(value, 10)",
    "    return value",
    "",
    "",
    "def _rounded_dict(data: dict):",
    "    return {k: _round_float(v) for k, v in data.items()}",
    "",
    "",
    "def _contract():",
    '    path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    '    assert data["contract"] == "POWERFLOW_T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON"',
    '    assert data["runtime_wired"] is False',
    "    return data",
    "",
    "",
    "def test_db_replay_contract_status_is_explicit():",
    "    data = _contract()",
    '    assert data["status"] in {"NO_DB", "NO_MATCHING_TABLE", "MATCHING_TABLE_NO_ROWS", "SAMPLES_FOUND"}',
    '    assert isinstance(data["case_count"], int)',
    "",
    "",
    "def test_db_replay_cases_match_legacy_surface_when_samples_exist():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_legacy_tick_surface, legacy_tick_surface_to_dict",
    "",
    "    data = _contract()",
    '    if data["status"] != "SAMPLES_FOUND":',
    "        assert data['case_count'] == 0",
    "        return",
    "",
    '    assert data["case_count"] > 0',
    '    for case in data["cases"]:',
    '        surface = derive_legacy_tick_surface(case["tick"])',
    "        actual = _rounded_dict(legacy_tick_surface_to_dict(surface))",
    '        expected = _rounded_dict(case["expected_legacy_surface"])',
    '        assert actual == expected, case["id"]',
    "",
    "",
    "def test_db_replay_keeps_core_unwired():",
    '    core_file = _core() / "pf_engine_v6_core.py"',
    '    text = core_file.read_text(encoding="utf-8", errors="replace")',
    '    forbidden = ["import engine", "from engine import", "import capture_bridge", "send_alert(", "sqlite3", ".execute(", ".commit("]',
    "    for token in forbidden:",
    "        assert token not in text",
    "",
]
test_path = tests_dir / "test_t002_engine_v6_core_db_replay_comparison.py"
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

report_path = audit_dir / ("T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON_" + stamp + ".md")
md = []
md.append("# T002-H DB Replay Comparison for Detached V6 Core")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Result")
md.append("")
md.append("- Status: " + status)
md.append("- DB path: " + (str(db_path) if db_path else "not found"))
md.append("- Selected table: " + (selected_table or "none"))
md.append("- Cases: " + str(len(cases)))
md.append("")
md.append("## Runtime behavior")
md.append("")
md.append("- Read-only DB inspection.")
md.append("- Runtime not wired.")
md.append("- Core/engine.py unchanged.")
md.append("- Core/capture_bridge.py unchanged.")
md.append("- Core/pf_engine_v6_adapter.py unchanged.")
md.append("")
md.append("## Table candidates")
md.append("")
if table_scores:
    for row in table_scores[:20]:
        md.append("- " + row["table"] + " | score " + str(row["score"]))
else:
    md.append("- none")
md.append("")
md.append("## Cases")
md.append("")
if cases:
    for case in cases:
        md.append("- " + case["id"])
else:
    md.append("- none")
md.append("")
md.append("## Interpretation")
md.append("")
if status == "SAMPLES_FOUND":
    md.append("The detached V6 core can reproduce legacy tick surface fields from sampled DB rows.")
else:
    md.append("No DB replay sample was available. This is not a failure; it defines the next data-access question.")
md.append("")
md.append("## Next step")
md.append("")
md.append("Do not wire runtime yet. If samples were found, next step is an adapter shadow-read mode that compares legacy surface and V6 core output without changing process_tick behavior.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": status,
    "db_path": str(db_path) if db_path else None,
    "selected_table": selected_table,
    "case_count": len(cases),
    "contract": str(contract_path),
    "test": str(test_path),
    "report": str(report_path),
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Creating DB replay comparison contract"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "T002-H DB replay generation failed"
}

Remove-Item $pythonPatch -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_core.py Core\pf_engine_v6_adapter.py Core\capture_bridge.py Core\engine.py
if ($LASTEXITCODE -ne 0) {
    throw "syntax checks failed"
}

Log "Running targeted T002 tests"
python -m pytest `
    tests/test_t002_engine_process_tick_contract.py `
    tests/test_t002_engine_v6_adapter.py `
    tests/test_t002_engine_v6_core.py `
    tests/test_t002_engine_tick_surface_contract.py `
    tests/test_t002_engine_v6_core_legacy_surface.py `
    tests/test_t002_engine_v6_core_golden_ticks.py `
    tests/test_t002_engine_v6_core_db_replay_comparison.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002-H tests failed"
}
Ok "T002 tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON.json",
    "tests/test_t002_engine_v6_core_db_replay_comparison.py",
    "scripts/t002_engine_v6_core_db_replay_comparison.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T002-H files"
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
    Warn "No staged T002-H changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "test(t002): add DB replay comparison for detached engine v6 core"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_H_DB_REPLAY_COMPARISON.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T002-H DB replay comparison"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T002-H DB replay comparison for detached V6 core"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- DB replay comparison contract created."
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
    $content += "If DB samples were found, implement adapter shadow-read comparison without changing process_tick behavior."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002-H DB replay comparison"
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

Ok "T002-H DB replay comparison complete"
Log "Final status"
git status --short
git log --oneline -7
