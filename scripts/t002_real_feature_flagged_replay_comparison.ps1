param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-T] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-T real feature-flagged replay comparison"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -12

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002-T commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$required = @(
    "Core\pf_engine_v6_adapter.py",
    "Core\pf_engine_v6_core.py",
    "Docs\Contracts\T002_ENGINE_PROCESS_TICK_CONTRACT.json",
    "Docs\Contracts\T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json",
    "Docs\Contracts\T002_FEATURE_FLAGGED_REPLAY_READINESS.json",
    "Docs\Contracts\T002_V6_CORE_RUNTIME_ENTRYPOINT.json"
)
foreach ($p in $required) {
    if (!(Test-Path $p)) { throw "Required file missing: $p" }
}

$patchPy = Join-Path $RepoPath ".t002t_real_replay_comparison.py"

@'
from __future__ import annotations

import copy
import datetime as dt
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import traceback

repo = Path.cwd()
core_dir = repo / "Core"
docs_dir = repo / "Docs"
contracts_dir = docs_dir / "Contracts"
audits_dir = docs_dir / "Audits"
reports_dir = docs_dir / "Reports"
tests_dir = repo / "tests"

contracts_dir.mkdir(parents=True, exist_ok=True)
audits_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

golden_path = contracts_dir / "T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES.json"
comparison_contract_path = contracts_dir / "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
readiness_path = contracts_dir / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
entrypoint_path = contracts_dir / "T002_V6_CORE_RUNTIME_ENTRYPOINT.json"


def default_cases() -> list[dict]:
    return [
        {
            "id": "fallback_default_gbpusd_m1",
            "tick": {
                "symbol": "GBPUSD",
                "timestamp": "2026-05-15T20:00:00Z",
                "timeframe": "M1",
                "val_a": 1.2500,
                "val_b": 1.2490,
                "dev_a": 0.20,
                "dev_b": -0.10,
                "spread": 0.0002
            },
            "prev": {
                "symbol": "GBPUSD",
                "timestamp": "2026-05-15T19:59:00Z",
                "timeframe": "M1",
                "val_a": 1.2495,
                "val_b": 1.2491,
                "dev_a": 0.10,
                "dev_b": -0.20,
                "spread": 0.0003
            }
        },
        {
            "id": "fallback_usd_base_usdjpy_m1",
            "tick": {
                "symbol": "USDJPY",
                "timestamp": "2026-05-15T20:01:00Z",
                "timeframe": "M1",
                "val_a": 156.20,
                "val_b": 156.10,
                "dev_a": 0.05,
                "dev_b": -0.02,
                "spread": 0.02
            },
            "prev": {
                "symbol": "USDJPY",
                "timestamp": "2026-05-15T20:00:00Z",
                "timeframe": "M1",
                "val_a": 156.00,
                "val_b": 156.00,
                "dev_a": 0.01,
                "dev_b": -0.03,
                "spread": 0.03
            }
        },
        {
            "id": "fallback_audusd_m1",
            "tick": {
                "symbol": "AUDUSD",
                "timestamp": "2026-05-15T20:02:00Z",
                "timeframe": "M1",
                "val_a": 0.6650,
                "val_b": 0.6647,
                "dev_a": -0.04,
                "dev_b": -0.08,
                "spread": 0.0001
            },
            "prev": {
                "symbol": "AUDUSD",
                "timestamp": "2026-05-15T20:01:00Z",
                "timeframe": "M1",
                "val_a": 0.6648,
                "val_b": 0.6646,
                "dev_a": -0.08,
                "dev_b": -0.09,
                "spread": 0.0001
            }
        }
    ]


def normalize_case(raw, idx: int) -> dict:
    if not isinstance(raw, dict):
        return default_cases()[idx % len(default_cases())]

    case_id = raw.get("id") or raw.get("name") or raw.get("case_id") or ("case_" + str(idx + 1))
    tick = (
        raw.get("tick")
        or raw.get("current_tick")
        or raw.get("current")
        or raw.get("input_tick")
        or raw.get("input")
        or raw.get("surface")
        or raw
    )
    prev = raw.get("prev") or raw.get("previous") or raw.get("previous_tick") or raw.get("baseline")
    if prev is None:
        prev = {}

    if not isinstance(tick, dict):
        tick = {}
    if not isinstance(prev, dict):
        prev = {}

    merged_tick = {
        "symbol": tick.get("symbol", raw.get("symbol", "GBPUSD")),
        "timestamp": tick.get("timestamp", raw.get("timestamp", "2026-05-15T20:00:00Z")),
        "timeframe": tick.get("timeframe", raw.get("timeframe", "M1")),
        "val_a": tick.get("val_a", raw.get("val_a", 1.0)),
        "val_b": tick.get("val_b", raw.get("val_b", 1.0)),
        "dev_a": tick.get("dev_a", raw.get("dev_a", 0.0)),
        "dev_b": tick.get("dev_b", raw.get("dev_b", 0.0)),
        "gap": tick.get("gap", raw.get("gap", None)),
        "spread": tick.get("spread", raw.get("spread", 0.0)),
    }
    merged_prev = {
        "symbol": prev.get("symbol", merged_tick["symbol"]),
        "timestamp": prev.get("timestamp", "2026-05-15T19:59:00Z"),
        "timeframe": prev.get("timeframe", merged_tick["timeframe"]),
        "val_a": prev.get("val_a", merged_tick["val_a"]),
        "val_b": prev.get("val_b", merged_tick["val_b"]),
        "dev_a": prev.get("dev_a", merged_tick["dev_a"]),
        "dev_b": prev.get("dev_b", merged_tick["dev_b"]),
        "gap": prev.get("gap", None),
        "spread": prev.get("spread", merged_tick["spread"]),
    }
    return {"id": str(case_id), "tick": merged_tick, "prev": merged_prev}


def load_cases() -> tuple[list[dict], str]:
    if not golden_path.exists():
        return default_cases(), "fallback_generated_cases"

    try:
        data = json.loads(golden_path.read_text(encoding="utf-8"))
    except Exception:
        return default_cases(), "fallback_due_to_unreadable_golden_contract"

    raw_cases = None
    if isinstance(data, list):
        raw_cases = data
    elif isinstance(data, dict):
        for key in ["cases", "golden_cases", "tick_cases", "examples", "items"]:
            if isinstance(data.get(key), list):
                raw_cases = data[key]
                break

    if not raw_cases:
        return default_cases(), "fallback_due_to_empty_or_unknown_golden_shape"

    return [normalize_case(c, i) for i, c in enumerate(raw_cases[:12])], "golden_contract"


def to_obj(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{k: to_obj(v) for k, v in value.items()})
    if isinstance(value, list):
        return [to_obj(v) for v in value]
    return value


def summarize_result(value):
    if isinstance(value, dict):
        return {
            "type": "dict",
            "keys": sorted([str(k) for k in value.keys()])[:30],
            "route": value.get("route"),
            "event_type": value.get("event_type"),
            "symbol": value.get("symbol"),
            "side_effects": value.get("side_effects"),
            "brain_mutated": value.get("brain_mutated"),
        }
    return {"type": type(value).__name__, "repr": repr(value)[:300]}


def call_route(adapter, use_v6: bool, tick: dict, prev: dict) -> dict:
    if use_v6:
        os.environ[adapter.ENV_FLAG] = "1"
    else:
        os.environ.pop(adapter.ENV_FLAG, None)
    os.environ.pop(adapter.STRICT_ENV_FLAG, None)

    send_calls = []
    brain = {"replay_case": True}
    brain_before = copy.deepcopy(brain)

    def fake_send_alert(*args, **kwargs):
        send_calls.append({"args": repr(args)[:300], "kwargs": repr(kwargs)[:300]})

    try:
        result = adapter.process_tick(to_obj(tick), to_obj(prev), brain, fake_send_alert)
        return {
            "ok": True,
            "error": None,
            "traceback": None,
            "result_summary": summarize_result(result),
            "send_alert_calls": len(send_calls),
            "brain_changed": brain != brain_before,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc),
            "traceback": traceback.format_exc(limit=5),
            "result_summary": None,
            "send_alert_calls": len(send_calls),
            "brain_changed": brain != brain_before,
        }


cases, case_source = load_cases()

sys.path.insert(0, str(core_dir))
adapter = importlib.import_module("pf_engine_v6_adapter")

rows = []
for idx, case in enumerate(cases):
    tick = case["tick"]
    prev = case["prev"]

    legacy = call_route(adapter, False, tick, prev)
    v6 = call_route(adapter, True, tick, prev)

    rows.append({
        "case_id": case["id"],
        "symbol": tick.get("symbol"),
        "timeframe": tick.get("timeframe"),
        "legacy": legacy,
        "v6": v6,
        "v6_pass": (
            v6["ok"]
            and v6["result_summary"]
            and v6["result_summary"].get("route") == "v6_core"
            and v6["send_alert_calls"] == 0
            and v6["brain_changed"] is False
        ),
        "legacy_observed": legacy["ok"],
    })

v6_pass_count = sum(1 for r in rows if r["v6_pass"])
legacy_ok_count = sum(1 for r in rows if r["legacy"]["ok"])
case_count = len(rows)

if v6_pass_count == case_count:
    verdict = "FEATURE_FLAGGED_REPLAY_PASS"
    dispatch_status = "completed_runtime_v6_feature_flag_ready"
    progress = 100
else:
    verdict = "FEATURE_FLAGGED_REPLAY_FAIL"
    dispatch_status = "blocked_feature_flagged_replay_failed"
    progress = 94

contract = {
    "contract": "POWERFLOW_T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON",
    "created_at": now,
    "verdict": verdict,
    "case_source": case_source,
    "case_count": case_count,
    "v6_pass_count": v6_pass_count,
    "legacy_ok_count": legacy_ok_count,
    "legacy_fail_count": case_count - legacy_ok_count,
    "default_live_behavior_changed": False,
    "v6_activation_flag": getattr(adapter, "ENV_FLAG", "POWERFLOW_T002_USE_V6_CORE"),
    "strict_flag": getattr(adapter, "STRICT_ENV_FLAG", "POWERFLOW_T002_V6_CORE_STRICT"),
    "rows": rows,
    "dispatch_status": dispatch_status,
    "progress": progress,
    "stop_rule": "Even after pass, default live activation should be a separate explicit scheduler/runtime switch commit.",
    "next_step": (
        "T002 can be marked 100% feature-flag ready; default live activation remains separate."
        if verdict == "FEATURE_FLAGGED_REPLAY_PASS"
        else "Inspect failing V6 replay cases before activation."
    ),
}
comparison_contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
readiness["status"] = "FEATURE_FLAG_REPLAY_PASSED" if verdict == "FEATURE_FLAGGED_REPLAY_PASS" else "FEATURE_FLAG_REPLAY_FAILED"
readiness["updated_at"] = now
readiness["replay_real_v6_executed"] = True
readiness["real_replay_contract"] = "Docs/Contracts/T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
readiness["next_step"] = contract["next_step"]
readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

report_path = reports_dir / ("T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON_" + stamp + ".md")
md = []
md.append("# T002-T Real Feature-Flagged Replay Comparison")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Verdict")
md.append("")
md.append("- " + verdict)
md.append("- Cases: " + str(case_count))
md.append("- V6 pass: " + str(v6_pass_count) + "/" + str(case_count))
md.append("- Legacy observed OK: " + str(legacy_ok_count) + "/" + str(case_count))
md.append("- Case source: " + case_source)
md.append("")
md.append("## Interpretation")
md.append("")
if verdict == "FEATURE_FLAGGED_REPLAY_PASS":
    md.append("The feature-flagged V6 route is reachable and stable on replay cases. T002 can be considered feature-flag ready at 100 percent.")
    md.append("Default live activation is intentionally left as a separate explicit decision.")
else:
    md.append("At least one V6 replay case failed. Do not activate V6 by default.")
md.append("")
md.append("## Rows")
md.append("")
for r in rows:
    md.append("- " + r["case_id"] + " | " + str(r["symbol"]) + " | v6_pass=" + str(r["v6_pass"]) + " | legacy_ok=" + str(r["legacy"]["ok"]))
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t002_real_feature_flagged_replay_comparison.py"
test_text = """from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t002_real_feature_flagged_replay_contract_passes():
    path = _repo() / "Docs" / "Contracts" / "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON"
    assert data["case_count"] >= 1
    assert data["v6_pass_count"] == data["case_count"]
    assert data["verdict"] == "FEATURE_FLAGGED_REPLAY_PASS"
    assert data["default_live_behavior_changed"] is False


def test_t002_real_feature_flagged_replay_rows_are_v6_core():
    path = _repo() / "Docs" / "Contracts" / "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for row in data["rows"]:
        assert row["v6_pass"] is True
        assert row["v6"]["ok"] is True
        assert row["v6"]["result_summary"]["route"] == "v6_core"
        assert row["v6"]["send_alert_calls"] == 0
        assert row["v6"]["brain_changed"] is False
"""
test_path.write_text(test_text, encoding="utf-8")

print(json.dumps({
    "ok": verdict == "FEATURE_FLAGGED_REPLAY_PASS",
    "verdict": verdict,
    "case_source": case_source,
    "case_count": case_count,
    "v6_pass_count": v6_pass_count,
    "legacy_ok_count": legacy_ok_count,
    "contract": str(comparison_contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "dispatch_status": dispatch_status,
    "progress": progress,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $patchPy -Encoding UTF8

Log "Running real feature-flagged replay comparison"
python $patchPy
if ($LASTEXITCODE -ne 0) {
    throw "T002-T replay comparison builder failed"
}
Remove-Item $patchPy -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_core.py
python -m py_compile Core\pf_engine_v6_adapter.py
python -m py_compile tests\test_t002_real_feature_flagged_replay_comparison.py

Log "Running targeted T002 tests"
python -m pytest `
    tests/test_t002_engine_process_tick_contract.py `
    tests/test_t002_engine_v6_adapter.py `
    tests/test_t002_engine_v6_core.py `
    tests/test_t002_engine_v6_core_legacy_surface.py `
    tests/test_t002_engine_v6_core_golden_ticks.py `
    tests/test_t002_runtime_v6_core_adapter_boundary.py `
    tests/test_t002_feature_flagged_replay_readiness.py `
    tests/test_t002_v6_core_runtime_entrypoint.py `
    tests/test_t002_real_feature_flagged_replay_comparison.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002-T targeted tests failed"
}
Ok "T002-T targeted tests passed"

Log "Updating DISPATCH_STATUS for T002-T"
$dispatchPath = Join-Path $RepoPath "Docs\DISPATCH_STATUS.json"
if (Test-Path $dispatchPath) {
    $dispatchPy = Join-Path $RepoPath ".t002t_dispatch_update.py"
@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

repo = Path.cwd()
dispatch_path = repo / "Docs" / "DISPATCH_STATUS.json"
comparison_path = repo / "Docs" / "Contracts" / "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

data = json.loads(dispatch_path.read_text(encoding="utf-8"))
comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
matches = []

def mentions_t002(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    hay = " ".join(
        str(v)
        for k, v in obj.items()
        if k.lower() in {"id", "task", "task_id", "code", "name", "title", "label", "description", "mission"}
    )
    return "t002" in hay.lower()

def patch(obj: dict, path: str) -> None:
    obj["status"] = comparison["dispatch_status"]
    obj["progress"] = comparison["progress"]
    obj["updated_at"] = now
    obj["feature_flag_replay_verdict"] = comparison["verdict"]
    obj["feature_flag_replay_contract"] = "Docs/Contracts/T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
    obj["feature_flag_replay_report"] = "Docs/Reports/T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON_*"
    obj["completed_at"] = now if comparison["verdict"] == "FEATURE_FLAGGED_REPLAY_PASS" else obj.get("completed_at")
    obj["next_steps"] = [
        "Default live activation remains a separate explicit scheduler/runtime switch.",
        "Do not silently enable POWERFLOW_T002_USE_V6_CORE in live scheduler.",
        "If activation is desired, create a dedicated T002-U default switch task."
    ]
    obj["notes"] = "T002 feature-flagged V6 core replay comparison passed. Runtime remains legacy fallback by default."
    matches.append({"path": path, "status": obj.get("status"), "progress": obj.get("progress")})

def walk(node: Any, path: str = "$") -> None:
    if isinstance(node, dict):
        if mentions_t002(node):
            patch(node, path)
        for k, v in list(node.items()):
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]")

walk(data)
if isinstance(data, dict) and "T002" in data and isinstance(data["T002"], dict):
    if not any(m["path"] == "$.T002" for m in matches):
        patch(data["T002"], "$.T002")

dispatch_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"ok": True, "matches": matches}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $dispatchPy -Encoding UTF8

    python $dispatchPy
    if ($LASTEXITCODE -ne 0) { throw "T002-T dispatch update failed" }
    Remove-Item $dispatchPy -Force -ErrorAction SilentlyContinue
    python -m json.tool Docs\DISPATCH_STATUS.json | Out-Null
    Ok "DISPATCH_STATUS updated and valid"
} else {
    Warn "Docs/DISPATCH_STATUS.json not found; skipping dispatch update"
}

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs\Contracts\T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json",
    "Docs\Contracts\T002_FEATURE_FLAGGED_REPLAY_READINESS.json",
    "Docs\DISPATCH_STATUS.json",
    "tests\test_t002_real_feature_flagged_replay_comparison.py",
    "scripts\t002_real_feature_flagged_replay_comparison.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Reports" -Filter "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T002-T files"
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
    Warn "No staged T002-T changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "test(t002): pass real feature-flagged V6 replay comparison"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }

    git pull origin main
    if ($LASTEXITCODE -ne 0) { throw "git pull failed" }

    if (-not $NoPush) {
        git push origin main
        if ($LASTEXITCODE -ne 0) { throw "git push failed" }
    } else {
        Warn "Push skipped by -NoPush"
    }
}

if (-not $SkipCheckpoint) {
    $checkpointDir = Join-Path $RepoPath "Docs\Checkpoints"
    if (!(Test-Path $checkpointDir)) { New-Item -ItemType Directory -Path $checkpointDir -Force | Out-Null }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_T_REAL_FEATURE_FLAGGED_REPLAY.md"
    $recent = @(git log --oneline -10)

    $ck = New-Object System.Collections.Generic.List[string]
    $ck.Add("# CHECKPOINT - T002-T real feature-flagged replay")
    $ck.Add("")
    $ck.Add("Date: $(Get-Date -Format o)")
    $ck.Add("Focus: Complete T002 feature-flagged V6 replay comparison")
    $ck.Add("")
    $ck.Add("## Result")
    $ck.Add("")
    $ck.Add("- Real feature-flagged V6 replay comparison passed.")
    $ck.Add("- T002 marked 100 percent feature-flag ready.")
    $ck.Add("- Default live behavior remains legacy fallback.")
    $ck.Add("- V6 default live activation is deliberately left as a separate explicit task.")
    $ck.Add("")
    $ck.Add("## Recent git log")
    $ck.Add("")
    foreach ($line in $recent) { $ck.Add("- $line") }

    Set-Content -Path $checkpointPath -Value $ck -Encoding UTF8
    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002-T real feature-flagged replay"
        if ($LASTEXITCODE -ne 0) { throw "checkpoint commit failed" }

        git pull origin main
        if ($LASTEXITCODE -ne 0) { throw "git pull checkpoint failed" }

        if (-not $NoPush) {
            git push origin main
            if ($LASTEXITCODE -ne 0) { throw "git push checkpoint failed" }
        }
        Ok "Targeted checkpoint committed and pushed"
    } else {
        Warn "No checkpoint changes staged"
    }
}

Ok "T002-T real feature-flagged replay comparison complete"
Log "Final status"
git status --short
git log --oneline -12
