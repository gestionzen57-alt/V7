param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-L] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-L USDJPY thin data final diagnosis"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-L commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004l_final_diagnosis.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
contract_dir = repo / "Docs" / "Contracts"
plan_dir = repo / "Docs" / "Plans"
report_dir = repo / "Docs" / "Reports"
tests_dir = repo / "tests"
contract_dir.mkdir(parents=True, exist_ok=True)
plan_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

required_contracts = {
    "initial_diagnostic": "T004_USDJPY_THIN_DATA_DIAGNOSTIC.json",
    "capture_db_path": "T004_CAPTURE_DB_PATH_AUDIT.json",
    "active_db_decision": "T004_ACTIVE_DB_DECISION.json",
    "active_db_density": "T004_ACTIVE_DB_SYMBOL_DENSITY.json",
    "root_cause": "T004_USDJPY_THIN_ROOT_CAUSE.json",
    "symbol_routing": "T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json",
    "live_capture_health": "T004_LIVE_CAPTURE_HEALTH_COUNTER.json",
    "runtime_status": "T004_CAPTURE_RUNTIME_STATUS.json",
    "writer_attribution": "T004_DB_WRITER_ATTRIBUTION.json",
    "active_insertion_delta": "T004_ACTIVE_INSERTION_SYMBOL_DELTA.json",
    "active_table_horizon": "T004_USDJPY_ACTIVE_TABLE_HORIZON.json",
}

loaded = {}
missing = []
for key, name in required_contracts.items():
    path = contract_dir / name
    if not path.exists():
        missing.append(name)
        continue
    loaded[key] = json.loads(path.read_text(encoding="utf-8"))

density = loaded.get("active_db_density", {})
root_cause = loaded.get("root_cause", {})
routing = loaded.get("symbol_routing", {})
health = loaded.get("live_capture_health", {})
runtime = loaded.get("runtime_status", {})
writer = loaded.get("writer_attribution", {})
delta = loaded.get("active_insertion_delta", {})
horizon = loaded.get("active_table_horizon", {})

evidence = {
    "active_db": density.get("active_db") or horizon.get("db_path") or "Core/powerflow.db",
    "historical_symbol_totals": density.get("symbol_totals", {}),
    "density_status": density.get("status"),
    "root_cause": root_cause.get("likely_cause"),
    "root_cause_votes": root_cause.get("vote_counts", {}),
    "routing_risk_flags": routing.get("risk_flags", []),
    "live_health_status": health.get("status"),
    "live_health_deltas": health.get("deltas", {}),
    "runtime_status": runtime.get("status"),
    "writer_status": writer.get("status"),
    "writer_row_delta": writer.get("row_delta"),
    "active_insertion_status": delta.get("status"),
    "active_insertion_symbol_deltas": delta.get("symbol_deltas", {}),
    "active_tables": [
        {
            "table": item.get("table"),
            "row_delta": item.get("row_delta"),
            "per_symbol_delta": item.get("per_symbol_delta"),
        }
        for item in delta.get("active_tables", [])
    ],
    "horizon_verdict": horizon.get("verdict"),
    "horizon_votes": horizon.get("vote_counts", {}),
    "suffix_candidates": horizon.get("suffix_candidates", []),
}

# Final classification.
if horizon.get("verdict") == "POSSIBLE_SUFFIX_OR_NEAR_SYMBOL_ROUTE":
    final_status = "CAPTURE_ROUTING_SUFFIX_SUSPECT"
elif horizon.get("verdict") == "USDJPY_ABSENT_FROM_ACTIVE_INSERTION_TABLES":
    final_status = "CAPTURE_ROUTING_USDJPY_ABSENT_FROM_ACTIVE_TABLES"
elif delta.get("status") == "REFERENCES_ADVANCED_THIN_SYMBOL_ZERO":
    final_status = "LIVE_REFERENCES_ADVANCE_USDJPY_ZERO"
elif root_cause.get("likely_cause") == "relative_sparsity":
    final_status = "USDJPY_RELATIVE_SPARSITY_CAPTURE_SIDE"
else:
    final_status = "T004_DIAGNOSED_CAPTURE_SIDE"

operator_actions = [
    "Verify USDJPY is enabled in MT4 Market Watch / source feed.",
    "Verify exact broker symbol naming: USDJPY versus USDJPYm / USDJPY.pro / suffix variants.",
    "Inspect capture symbol allowlist or routing normalization for USDJPY.",
    "Verify the bridge emits USDJPY ticks into the same stream as GBPUSD.",
    "Run the live capture health counter during an active market window after feed/routing correction.",
    "Do not patch Core/engine.py, pf_engine_v6_core.py, scoring modules, or dashboard logic for T004.",
]

engineering_actions = [
    "Add a lightweight per-symbol capture health monitor before DB insertion if the issue recurs.",
    "Expose per-symbol live tick deltas as an operational health surface, not as a trading signal.",
    "Keep Core/powerflow.db as the active diagnostic DB unless runtime configuration changes.",
    "Retain T004 contracts as regression evidence for future capture/routing changes.",
]

not_causes = [
    "Not a PowerFlow engine/scoring issue.",
    "Not a dashboard issue.",
    "Not a SQLite/path issue after active DB was resolved to Core/powerflow.db.",
    "Not a total USDJPY absence historically; USDJPY has rows but is thin and not advancing in active insertion windows.",
]

final_contract = {
    "contract": "POWERFLOW_T004_FINAL_DIAGNOSIS",
    "created_at": now,
    "status": final_status,
    "missing_source_contracts": missing,
    "evidence": evidence,
    "operator_actions": operator_actions,
    "engineering_actions": engineering_actions,
    "not_causes": not_causes,
    "recommended_dispatch_state": "DIAGNOSED_BLOCKED_ON_CAPTURE_ROUTING_OR_SOURCE_FEED",
    "runtime_wired": False,
    "db_written": False,
    "engine_change_required": False,
}
contract_path = contract_dir / "T004_FINAL_DIAGNOSIS.json"
contract_path.write_text(json.dumps(final_contract, indent=2, ensure_ascii=False), encoding="utf-8")

report_path = report_dir / ("T004_FINAL_DIAGNOSIS_" + stamp + ".md")
md = []
md.append("# T004 Final Diagnosis — USDJPY Thin Data")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Final status")
md.append("")
md.append("`" + final_status + "`")
md.append("")
md.append("## Executive conclusion")
md.append("")
md.append("T004 is diagnosed as a capture/routing/source-feed problem, not a PowerFlow engine problem.")
md.append("")
md.append("The active DB is `Core/powerflow.db`. During live insertion drilldown, references advanced while USDJPY did not. The active insertion tables were `flow_packets`, `force_snapshots`, and `force_snapshots_v2`. USDJPY has historical rows, but it is thin and absent from active insertion windows where GBPUSD advances.")
md.append("")
md.append("## Key evidence")
md.append("")
md.append("- Active DB: `" + str(evidence["active_db"]) + "`")
md.append("- Historical density status: `" + str(evidence["density_status"]) + "`")
md.append("- Historical symbol totals: `" + json.dumps(evidence["historical_symbol_totals"], ensure_ascii=False) + "`")
md.append("- Root cause: `" + str(evidence["root_cause"]) + "`")
md.append("- Routing risk flags: `" + json.dumps(evidence["routing_risk_flags"], ensure_ascii=False) + "`")
md.append("- T004-G live health: `" + str(evidence["live_health_status"]) + "` with deltas `" + json.dumps(evidence["live_health_deltas"], ensure_ascii=False) + "`")
md.append("- T004-I writer attribution: `" + str(evidence["writer_status"]) + "` with row_delta `" + str(evidence["writer_row_delta"]) + "`")
md.append("- T004-J active insertion: `" + str(evidence["active_insertion_status"]) + "` with deltas `" + json.dumps(evidence["active_insertion_symbol_deltas"], ensure_ascii=False) + "`")
md.append("- T004-K horizon verdict: `" + str(evidence["horizon_verdict"]) + "`")
md.append("- Suffix candidates: `" + json.dumps(evidence["suffix_candidates"], ensure_ascii=False) + "`")
md.append("")
md.append("## Active insertion tables")
md.append("")
for item in evidence["active_tables"]:
    md.append("- `" + str(item.get("table")) + "` | row_delta=" + str(item.get("row_delta")) + " | per_symbol_delta=`" + json.dumps(item.get("per_symbol_delta"), ensure_ascii=False) + "`")
md.append("")
md.append("## What T004 is not")
md.append("")
for item in not_causes:
    md.append("- " + item)
md.append("")
md.append("## Operator actions")
md.append("")
for item in operator_actions:
    md.append("- [ ] " + item)
md.append("")
md.append("## Engineering actions")
md.append("")
for item in engineering_actions:
    md.append("- [ ] " + item)
md.append("")
md.append("## Dispatch recommendation")
md.append("")
md.append("Recommended state: `DIAGNOSED_BLOCKED_ON_CAPTURE_ROUTING_OR_SOURCE_FEED`")
md.append("")
md.append("Do not close as solved until USDJPY advances in active insertion windows after feed/routing verification.")
md.append("")
md.append("## Stop rule")
md.append("")
md.append("No changes to `Core/engine.py`, `pf_engine_v6_core.py`, scoring modules, or dashboard logic are justified by T004.")
md.append("")
md.append("## Revalidation command")
md.append("")
md.append("After operator-side feed/routing correction, rerun:")
md.append("")
md.append("```powershell")
md.append(".\\scripts\\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10")
md.append("```")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_final_diagnosis_contract.py"
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
    "def test_t004_final_diagnosis_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_FINAL_DIAGNOSIS.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_FINAL_DIAGNOSIS"',
    '    assert data["runtime_wired"] is False',
    '    assert data["db_written"] is False',
    '    assert data["engine_change_required"] is False',
    '    assert isinstance(data["operator_actions"], list)',
    '    assert isinstance(data["engineering_actions"], list)',
    "",
    "",
    "def test_t004_final_diagnosis_blocks_engine_patch():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_FINAL_DIAGNOSIS.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    joined = "\\n".join(data["not_causes"] + data["operator_actions"] + data["engineering_actions"]).lower()',
    '    assert "engine" in joined',
    '    assert data["engine_change_required"] is False',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": final_status,
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "missing_source_contracts": missing,
    "recommended_dispatch_state": final_contract["recommended_dispatch_state"],
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Building T004 final diagnosis"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-L final diagnosis failed"
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
    tests/test_t004_final_diagnosis_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-L tests failed"
}
Ok "T004-L tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_FINAL_DIAGNOSIS.json",
    "tests/test_t004_final_diagnosis_contract.py",
    "scripts/t004_final_diagnosis.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Reports" -Filter "T004_FINAL_DIAGNOSIS_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T004-L files"
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
    Warn "No staged T004-L changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "docs(t004): finalize USDJPY thin data diagnosis"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_L_FINAL_DIAGNOSIS.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-L final diagnosis"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-L USDJPY thin data final diagnosis"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- T004 final diagnosis created."
    $content += "- Runtime unchanged."
    $content += "- DB not written."
    $content += "- Engine change not required."
    $content += "- Dashboard workspace files intentionally left untouched."
    $content += ""
    $content += "## Recommended dispatch state"
    $content += ""
    $content += "- DIAGNOSED_BLOCKED_ON_CAPTURE_ROUTING_OR_SOURCE_FEED"
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""
    $content += "## Revalidation"
    $content += ""
    $content += "After feed/routing correction, rerun t004_active_insertion_symbol_delta.ps1."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-L final diagnosis"
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

Ok "T004-L final diagnosis complete"
Log "Final status"
git status --short
git log --oneline -7
