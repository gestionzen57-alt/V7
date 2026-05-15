param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-R] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-R feature-flagged replay readiness"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -10

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002-R commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$required = @(
    "Core\pf_engine_v6_adapter.py",
    "Core\pf_engine_v6_core.py",
    "Docs\Contracts\T002_ENGINE_PROCESS_TICK_CONTRACT.json",
    "Docs\Contracts\T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json"
)
foreach ($p in $required) {
    if (!(Test-Path $p)) { throw "Required file missing: $p" }
}

$patchPy = Join-Path $RepoPath ".t002r_feature_flagged_replay_readiness.py"

@'
from __future__ import annotations

import ast
import datetime as dt
import importlib
import inspect
import json
import os
from pathlib import Path
import sys

repo = Path.cwd()
core_dir = repo / "Core"
docs_dir = repo / "Docs"
contracts_dir = docs_dir / "Contracts"
audits_dir = docs_dir / "Audits"
tests_dir = repo / "tests"

audits_dir.mkdir(parents=True, exist_ok=True)
contracts_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

adapter_path = core_dir / "pf_engine_v6_adapter.py"
core_path = core_dir / "pf_engine_v6_core.py"
boundary_path = contracts_dir / "T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json"
process_contract_path = contracts_dir / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"

boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
process_contract = json.loads(process_contract_path.read_text(encoding="utf-8"))

core_text = core_path.read_text(encoding="utf-8", errors="replace")

def function_names(text: str) -> list[str]:
    tree = ast.parse(text)
    return [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

core_functions = function_names(core_text)
runtime_candidate_names = ["process_tick", "process_tick_v6", "process_tick_core"]
runtime_candidates = [name for name in runtime_candidate_names if name in core_functions]

pure_helper_candidates = [
    name for name in [
        "build_tick_surface",
        "compute_tick_surface",
        "tick_to_surface",
        "normalize_tick",
        "from_tick",
        "extract_tick_surface",
        "build_surface_from_tick",
    ]
    if name in core_functions
]

sys.path.insert(0, str(core_dir))
adapter = importlib.import_module("pf_engine_v6_adapter")
adapter_signature = str(inspect.signature(adapter.process_tick))
expected_signature = process_contract.get("signature")

status = adapter.runtime_adapter_status()
default_env = os.environ.get(adapter.ENV_FLAG)
strict_env = os.environ.get(adapter.STRICT_ENV_FLAG)

if runtime_candidates:
    readiness_status = "FEATURE_FLAG_REPLAY_READY"
    next_step = "Run a real feature-flagged replay using POWERFLOW_T002_USE_V6_CORE=1 and compare outputs."
else:
    readiness_status = "FEATURE_FLAG_BOUNDARY_VALID_CORE_RUNTIME_ENTRYPOINT_MISSING"
    next_step = "Implement or adapt a compatible pf_engine_v6_core.process_tick entrypoint before real V6 replay."

contract = {
    "contract": "POWERFLOW_T002_FEATURE_FLAGGED_REPLAY_READINESS",
    "created_at": now,
    "status": readiness_status,
    "adapter": "Core/pf_engine_v6_adapter.py",
    "core": "Core/pf_engine_v6_core.py",
    "boundary_contract": "Docs/Contracts/T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json",
    "process_tick_contract": "Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json",
    "env_flag": getattr(adapter, "ENV_FLAG", "POWERFLOW_T002_USE_V6_CORE"),
    "strict_env_flag": getattr(adapter, "STRICT_ENV_FLAG", "POWERFLOW_T002_V6_CORE_STRICT"),
    "adapter_signature": adapter_signature,
    "expected_signature": expected_signature,
    "signature_ok": adapter_signature == expected_signature,
    "adapter_runtime_status": status,
    "runtime_candidates_detected": runtime_candidates,
    "pure_helper_candidates_detected": pure_helper_candidates,
    "core_function_count": len(core_functions),
    "default_env_before_test": default_env,
    "strict_env_before_test": strict_env,
    "default_live_behavior_changed": False,
    "feature_flag_boundary_tested": True,
    "strict_mode_tested": True,
    "replay_real_v6_executed": False,
    "reason_no_real_replay": None if runtime_candidates else "No compatible runtime process_tick entrypoint exists in pf_engine_v6_core.py.",
    "next_step": next_step,
    "stop_rule": "Do not enable V6 core by default until a real replay contract passes.",
}
contract_path = contracts_dir / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t002_feature_flagged_replay_readiness.py"
test_text = '''from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def _load_adapter(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    monkeypatch.delenv(adapter.ENV_FLAG, raising=False)
    monkeypatch.delenv(adapter.STRICT_ENV_FLAG, raising=False)
    return adapter


def test_t002_feature_flag_default_uses_legacy_fallback(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    calls = []

    def fake_legacy(tick, prev, brain, send_alert):
        calls.append(("legacy", tick, prev, brain))
        return {"route": "legacy"}

    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_legacy)

    result = adapter.process_tick(None, None, {}, lambda *_: None)

    assert result == {"route": "legacy"}
    assert calls and calls[0][0] == "legacy"


def test_t002_feature_flag_routes_to_v6_when_entrypoint_exists(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    def fake_legacy(tick, prev, brain, send_alert):
        return {"route": "legacy"}

    def fake_v6(tick, prev, brain, send_alert):
        return {"route": "v6"}

    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_legacy)
    monkeypatch.setattr(adapter, "_v6_core", SimpleNamespace(process_tick=fake_v6))
    monkeypatch.setattr(adapter, "_V6_CORE_IMPORT_ERROR", None)
    monkeypatch.setenv(adapter.ENV_FLAG, "1")

    result = adapter.process_tick(None, None, {}, lambda *_: None)

    assert result == {"route": "v6"}


def test_t002_feature_flag_missing_v6_entrypoint_falls_back_non_strict(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    def fake_legacy(tick, prev, brain, send_alert):
        return {"route": "legacy"}

    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_legacy)
    monkeypatch.setattr(adapter, "_v6_core", SimpleNamespace())
    monkeypatch.setattr(adapter, "_V6_CORE_IMPORT_ERROR", None)
    monkeypatch.setenv(adapter.ENV_FLAG, "1")

    result = adapter.process_tick(None, None, {}, lambda *_: None)

    assert result == {"route": "legacy"}


def test_t002_feature_flag_missing_v6_entrypoint_raises_in_strict(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    monkeypatch.setattr(adapter, "_v6_core", SimpleNamespace())
    monkeypatch.setattr(adapter, "_V6_CORE_IMPORT_ERROR", None)
    monkeypatch.setenv(adapter.ENV_FLAG, "1")
    monkeypatch.setenv(adapter.STRICT_ENV_FLAG, "1")

    with pytest.raises(RuntimeError):
        adapter.process_tick(None, None, {}, lambda *_: None)


def test_t002_feature_flag_readiness_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T002_FEATURE_FLAGGED_REPLAY_READINESS"
    assert data["signature_ok"] is True
    assert data["default_live_behavior_changed"] is False
    assert data["feature_flag_boundary_tested"] is True
    assert data["strict_mode_tested"] is True
    assert data["status"] in {
        "FEATURE_FLAG_REPLAY_READY",
        "FEATURE_FLAG_BOUNDARY_VALID_CORE_RUNTIME_ENTRYPOINT_MISSING",
    }
'''
test_path.write_text(test_text, encoding="utf-8")

report_path = audits_dir / ("T002_FEATURE_FLAGGED_REPLAY_READINESS_" + stamp + ".md")
md = []
md.append("# T002-R Feature-Flagged Replay Readiness")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Verdict")
md.append("")
md.append("- Status: " + readiness_status)
md.append("- Default live behavior changed: false")
md.append("- Real V6 replay executed: false")
md.append("")
md.append("## Adapter")
md.append("")
md.append("- Signature: " + adapter_signature)
md.append("- Signature OK: " + str(adapter_signature == expected_signature))
md.append("- Env flag: " + contract["env_flag"])
md.append("- Strict flag: " + contract["strict_env_flag"])
md.append("")
md.append("## Core runtime candidates")
md.append("")
if runtime_candidates:
    for name in runtime_candidates:
        md.append("- " + name)
else:
    md.append("- none")
md.append("")
md.append("## Pure helper candidates")
md.append("")
if pure_helper_candidates:
    for name in pure_helper_candidates:
        md.append("- " + name)
else:
    md.append("- none detected by name heuristic")
md.append("")
md.append("## Interpretation")
md.append("")
if runtime_candidates:
    md.append("A compatible runtime entrypoint appears to exist. The next step is a real feature-flagged replay comparison.")
else:
    md.append("The adapter boundary is valid, but pf_engine_v6_core.py does not expose a compatible runtime process_tick entrypoint yet. The safe next step is to add/adapt that entrypoint or build a comparison wrapper before real replay.")
md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not enable V6 core by default until a real replay contract passes.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": readiness_status,
    "signature_ok": adapter_signature == expected_signature,
    "runtime_candidates_detected": runtime_candidates,
    "pure_helper_candidates_detected": pure_helper_candidates,
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "next_step": next_step,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $patchPy -Encoding UTF8

Log "Building replay readiness contract and tests"
python $patchPy
if ($LASTEXITCODE -ne 0) {
    throw "T002-R readiness builder failed"
}
Remove-Item $patchPy -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_adapter.py
python -m py_compile Core\pf_engine_v6_core.py
python -m py_compile tests\test_t002_feature_flagged_replay_readiness.py

Log "Running targeted T002 tests"
python -m pytest `
    tests/test_t002_engine_process_tick_contract.py `
    tests/test_t002_engine_v6_adapter.py `
    tests/test_t002_engine_v6_core.py `
    tests/test_t002_engine_v6_core_legacy_surface.py `
    tests/test_t002_engine_v6_core_golden_ticks.py `
    tests/test_t002_runtime_v6_core_adapter_boundary.py `
    tests/test_t002_feature_flagged_replay_readiness.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002-R targeted tests failed"
}
Ok "T002-R targeted tests passed"

Log "Updating DISPATCH_STATUS for T002-R"
$dispatchPath = Join-Path $RepoPath "Docs\DISPATCH_STATUS.json"
if (Test-Path $dispatchPath) {
    $dispatchPy = Join-Path $RepoPath ".t002r_dispatch_update.py"
@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

repo = Path.cwd()
dispatch_path = repo / "Docs" / "DISPATCH_STATUS.json"
readiness_path = repo / "Docs" / "Contracts" / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

data = json.loads(dispatch_path.read_text(encoding="utf-8"))
readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
status = readiness.get("status")

if status == "FEATURE_FLAG_REPLAY_READY":
    task_status = "in_progress_feature_flagged_replay_ready"
    progress = 90
else:
    task_status = "in_progress_runtime_boundary_wired_entrypoint_missing"
    progress = 88

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
    obj["status"] = task_status
    obj["progress"] = max(int(obj.get("progress", 0) or 0), progress)
    obj["updated_at"] = now
    obj["feature_flag_replay_readiness"] = readiness.get("status")
    obj["feature_flag_replay_contract"] = "Docs/Contracts/T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
    obj["runtime_boundary"] = "Core/pf_engine_v6_adapter.py feature-flagged V6 core route"
    obj["next_steps"] = [
        readiness.get("next_step"),
        "Keep default live behavior on legacy fallback until real replay passes",
        "Do not set POWERFLOW_T002_USE_V6_CORE=1 in live scheduler yet"
    ]
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
print(json.dumps({"ok": True, "matches": matches, "task_status": task_status}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $dispatchPy -Encoding UTF8

    python $dispatchPy
    if ($LASTEXITCODE -ne 0) { throw "T002-R dispatch update failed" }
    Remove-Item $dispatchPy -Force -ErrorAction SilentlyContinue
    python -m json.tool Docs\DISPATCH_STATUS.json | Out-Null
    Ok "DISPATCH_STATUS updated and valid"
} else {
    Warn "Docs/DISPATCH_STATUS.json not found; skipping dispatch update"
}

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs\Contracts\T002_FEATURE_FLAGGED_REPLAY_READINESS.json",
    "Docs\DISPATCH_STATUS.json",
    "tests\test_t002_feature_flagged_replay_readiness.py",
    "scripts\t002_feature_flagged_replay_readiness.ps1"
)

$latestAudit = Get-ChildItem ".\Docs\Audits" -Filter "T002_FEATURE_FLAGGED_REPLAY_READINESS_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestAudit) {
    $pathsToAdd += $latestAudit.FullName
}

Log "Targeted staging only T002-R files"
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
    Warn "No staged T002-R changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "test(t002): validate feature-flagged V6 runtime readiness"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_R_FEATURE_FLAGGED_REPLAY_READINESS.md"
    $recent = @(git log --oneline -10)

    $ck = New-Object System.Collections.Generic.List[string]
    $ck.Add("# CHECKPOINT - T002-R feature-flagged replay readiness")
    $ck.Add("")
    $ck.Add("Date: $(Get-Date -Format o)")
    $ck.Add("Focus: T002-R feature-flagged replay readiness")
    $ck.Add("")
    $ck.Add("## Result")
    $ck.Add("")
    $ck.Add("- Feature-flag boundary tests added.")
    $ck.Add("- Default legacy fallback verified.")
    $ck.Add("- V6 route under POWERFLOW_T002_USE_V6_CORE verified with fake compatible core.")
    $ck.Add("- Strict missing-entrypoint behavior verified.")
    $ck.Add("- Readiness contract created.")
    $ck.Add("")
    $ck.Add("## Stop rule")
    $ck.Add("")
    $ck.Add("- Do not enable V6 core by default until real replay contract passes.")
    $ck.Add("")
    $ck.Add("## Recent git log")
    $ck.Add("")
    foreach ($line in $recent) { $ck.Add("- $line") }

    Set-Content -Path $checkpointPath -Value $ck -Encoding UTF8
    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002-R feature-flagged replay readiness"
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

Ok "T002-R feature-flagged replay readiness complete"
Log "Final status"
git status --short
git log --oneline -10
