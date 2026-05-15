param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-S] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-S V6 core runtime entrypoint"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -10

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002-S commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$required = @(
    "Core\pf_engine_v6_core.py",
    "Core\pf_engine_v6_adapter.py",
    "Docs\Contracts\T002_ENGINE_PROCESS_TICK_CONTRACT.json",
    "Docs\Contracts\T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json",
    "Docs\Contracts\T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
)
foreach ($p in $required) {
    if (!(Test-Path $p)) { throw "Required file missing: $p" }
}

$patchPy = Join-Path $RepoPath ".t002s_core_runtime_entrypoint.py"

@'
from __future__ import annotations

import ast
import datetime as dt
import importlib
import inspect
import json
from pathlib import Path
import shutil
import sys

repo = Path.cwd()
core_dir = repo / "Core"
docs_dir = repo / "Docs"
contracts_dir = docs_dir / "Contracts"
audits_dir = docs_dir / "Audits"
tests_dir = repo / "tests"

contracts_dir.mkdir(parents=True, exist_ok=True)
audits_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

core_path = core_dir / "pf_engine_v6_core.py"
readiness_path = contracts_dir / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
entrypoint_contract_path = contracts_dir / "T002_V6_CORE_RUNTIME_ENTRYPOINT.json"

text = core_path.read_text(encoding="utf-8", errors="replace")
backup_path = core_path.with_name("pf_engine_v6_core.py.bak_T002S_" + stamp)
shutil.copy2(core_path, backup_path)

def function_names(src: str) -> list[str]:
    tree = ast.parse(src)
    return [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

before_functions = function_names(text)
had_process_tick = "process_tick" in before_functions

marker_start = "# === T002-S V6 CORE RUNTIME ENTRYPOINT START ==="
marker_end = "# === T002-S V6 CORE RUNTIME ENTRYPOINT END ==="

runtime_block = r'''
# === T002-S V6 CORE RUNTIME ENTRYPOINT START ===
# Pure runtime entrypoint for the feature-flagged adapter boundary.
# The function below keeps the legacy call signature while returning a deterministic
# V6 tick surface. It does not write storage, mutate UI layers, or transmit messages.

import models


PF_ENGINE_V6_CORE_RUNTIME_VERSION = "T002_S_V6_CORE_RUNTIME_ENTRYPOINT_V1"


def _pf_v6_get_tick_attr(tick, name: str, default=None):
    if tick is None:
        return default
    if isinstance(tick, dict):
        return tick.get(name, default)
    return getattr(tick, name, default)


def _pf_v6_float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pf_v6_string_or_none(value):
    if value is None:
        return None
    return str(value)


def _pf_v6_tick_surface(tick) -> dict:
    fields = {
        "symbol": _pf_v6_string_or_none(_pf_v6_get_tick_attr(tick, "symbol")),
        "timestamp": _pf_v6_string_or_none(_pf_v6_get_tick_attr(tick, "timestamp")),
        "timeframe": _pf_v6_string_or_none(_pf_v6_get_tick_attr(tick, "timeframe")),
        "val_a": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "val_a")),
        "val_b": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "val_b")),
        "dev_a": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "dev_a")),
        "dev_b": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "dev_b")),
        "gap": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "gap")),
        "spread": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "spread")),
    }

    val_a = fields["val_a"]
    val_b = fields["val_b"]
    if fields["gap"] is None and val_a is not None and val_b is not None:
        fields["gap"] = val_a - val_b

    return fields


def _pf_v6_tick_delta(current: dict, previous: dict) -> dict:
    deltas = {}
    for key in ("val_a", "val_b", "dev_a", "dev_b", "gap", "spread"):
        cur = current.get(key)
        prev = previous.get(key)
        if cur is not None and prev is not None:
            deltas[key] = cur - prev
        else:
            deltas[key] = None
    return deltas


def process_tick(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    current_surface = _pf_v6_tick_surface(tick)
    previous_surface = _pf_v6_tick_surface(prev)
    delta = _pf_v6_tick_delta(current_surface, previous_surface)

    return {
        "engine": "pf_engine_v6_core",
        "version": PF_ENGINE_V6_CORE_RUNTIME_VERSION,
        "event_type": "V6_CORE_TICK_SURFACE",
        "symbol": current_surface.get("symbol"),
        "timestamp": current_surface.get("timestamp"),
        "timeframe": current_surface.get("timeframe"),
        "surface": current_surface,
        "previous_surface": previous_surface,
        "delta": delta,
        "alerts": [],
        "side_effects": False,
        "brain_mutated": False,
        "route": "v6_core",
    }


try:
    __all__ = list(__all__)
except NameError:
    __all__ = []

for _name in [
    "PF_ENGINE_V6_CORE_RUNTIME_VERSION",
    "process_tick",
]:
    if _name not in __all__:
        __all__.append(_name)
# === T002-S V6 CORE RUNTIME ENTRYPOINT END ===
'''

if marker_start in text and marker_end in text:
    start = text.index(marker_start)
    end = text.index(marker_end) + len(marker_end)
    text = text[:start] + runtime_block.strip() + text[end:]
else:
    if not text.endswith("\n"):
        text += "\n"
    text += "\n\n" + runtime_block.strip() + "\n"

core_path.write_text(text, encoding="utf-8")

after_text = core_path.read_text(encoding="utf-8", errors="replace")
after_functions = function_names(after_text)

sys.path.insert(0, str(core_dir))
if "pf_engine_v6_core" in sys.modules:
    del sys.modules["pf_engine_v6_core"]
core_mod = importlib.import_module("pf_engine_v6_core")
core_signature = str(inspect.signature(core_mod.process_tick))

readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
readiness["status"] = "FEATURE_FLAG_REPLAY_READY"
readiness["updated_at"] = now
readiness["runtime_candidates_detected"] = ["process_tick"]
readiness["replay_real_v6_executed"] = False
readiness["reason_no_real_replay"] = "Core entrypoint added; real replay comparison is the next task."
readiness["next_step"] = "Run real feature-flagged replay comparison with POWERFLOW_T002_USE_V6_CORE=1 before default live activation."
readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

contract = {
    "contract": "POWERFLOW_T002_V6_CORE_RUNTIME_ENTRYPOINT",
    "created_at": now,
    "status": "V6_CORE_PROCESS_TICK_ENTRYPOINT_ADDED",
    "core": "Core/pf_engine_v6_core.py",
    "backup": str(backup_path),
    "had_process_tick_before": had_process_tick,
    "functions_before_count": len(before_functions),
    "functions_after_count": len(after_functions),
    "core_signature": core_signature,
    "expected_adapter_signature_family": "(tick: models.Tick, prev: models.Tick, brain: dict, send_alert)",
    "entrypoint_name": "process_tick",
    "runtime_version": "T002_S_V6_CORE_RUNTIME_ENTRYPOINT_V1",
    "returns": "deterministic V6 tick surface dict",
    "side_effects": False,
    "db_writes": False,
    "ui_dependency": False,
    "alert_transport_dependency": False,
    "default_live_behavior_changed": False,
    "adapter_flag_required": "POWERFLOW_T002_USE_V6_CORE=1",
    "next_step": "Run real feature-flagged replay comparison before default live activation."
}
entrypoint_contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t002_v6_core_runtime_entrypoint.py"
test_text = '''from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def test_t002_v6_core_process_tick_exists_and_is_pure_surface():
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_core as core

    assert callable(core.process_tick)

    tick = SimpleNamespace(
        symbol="GBPUSD",
        timestamp="2026-05-15T20:00:00Z",
        timeframe="M1",
        val_a=1.2500,
        val_b=1.2490,
        dev_a=0.2,
        dev_b=-0.1,
        spread=0.0002,
    )
    prev = SimpleNamespace(
        symbol="GBPUSD",
        timestamp="2026-05-15T19:59:00Z",
        timeframe="M1",
        val_a=1.2495,
        val_b=1.2491,
        dev_a=0.1,
        dev_b=-0.2,
        spread=0.0003,
    )

    calls = []

    def fake_transport(*args, **kwargs):
        calls.append((args, kwargs))

    brain = {"existing": True}
    result = core.process_tick(tick, prev, brain, fake_transport)

    assert result["route"] == "v6_core"
    assert result["engine"] == "pf_engine_v6_core"
    assert result["event_type"] == "V6_CORE_TICK_SURFACE"
    assert result["symbol"] == "GBPUSD"
    assert result["surface"]["gap"] == result["surface"]["val_a"] - result["surface"]["val_b"]
    assert result["delta"]["val_a"] == 0.0004999999999999449
    assert result["alerts"] == []
    assert result["side_effects"] is False
    assert result["brain_mutated"] is False
    assert brain == {"existing": True}
    assert calls == []


def test_t002_v6_core_accepts_dict_ticks():
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_core as core

    tick = {"symbol": "USDJPY", "timestamp": "t1", "timeframe": "M1", "val_a": 156.2, "val_b": 156.1}
    prev = {"symbol": "USDJPY", "timestamp": "t0", "timeframe": "M1", "val_a": 156.0, "val_b": 156.0}

    result = core.process_tick(tick, prev, {}, lambda *_: None)

    assert result["symbol"] == "USDJPY"
    assert result["surface"]["gap"] == 0.09999999999999432
    assert result["delta"]["val_a"] == 0.19999999999998863


def test_t002_adapter_reaches_real_v6_core_under_flag(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    monkeypatch.setenv(adapter.ENV_FLAG, "1")
    monkeypatch.delenv(adapter.STRICT_ENV_FLAG, raising=False)

    tick = {"symbol": "EURUSD", "timestamp": "t1", "timeframe": "M1", "val_a": 1.1, "val_b": 1.0}
    prev = {"symbol": "EURUSD", "timestamp": "t0", "timeframe": "M1", "val_a": 1.0, "val_b": 1.0}

    result = adapter.process_tick(tick, prev, {}, lambda *_: None)

    assert result["route"] == "v6_core"
    assert result["symbol"] == "EURUSD"


def test_t002_v6_core_entrypoint_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T002_V6_CORE_RUNTIME_ENTRYPOINT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T002_V6_CORE_RUNTIME_ENTRYPOINT"
    assert data["status"] == "V6_CORE_PROCESS_TICK_ENTRYPOINT_ADDED"
    assert data["side_effects"] is False
    assert data["db_writes"] is False
    assert data["default_live_behavior_changed"] is False


def test_t002_readiness_now_sees_runtime_entrypoint():
    path = _repo() / "Docs" / "Contracts" / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["status"] == "FEATURE_FLAG_REPLAY_READY"
    assert "process_tick" in data["runtime_candidates_detected"]
'''
test_path.write_text(test_text, encoding="utf-8")

report_path = audits_dir / ("T002_V6_CORE_RUNTIME_ENTRYPOINT_" + stamp + ".md")
md = []
md.append("# T002-S V6 Core Runtime Entrypoint")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Result")
md.append("")
md.append("- Added or refreshed pf_engine_v6_core.process_tick.")
md.append("- Entry point returns a deterministic V6 tick surface.")
md.append("- No storage write, no UI dependency, no transport dependency.")
md.append("- Default live behavior remains unchanged because adapter still requires POWERFLOW_T002_USE_V6_CORE=1.")
md.append("")
md.append("## Signature")
md.append("")
md.append("- " + core_signature)
md.append("")
md.append("## Readiness")
md.append("")
md.append("- T002_FEATURE_FLAGGED_REPLAY_READINESS status updated to FEATURE_FLAG_REPLAY_READY.")
md.append("")
md.append("## Next step")
md.append("")
md.append("- Run a real feature-flagged replay comparison before any default live activation.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "status": "V6_CORE_PROCESS_TICK_ENTRYPOINT_ADDED",
    "core": str(core_path),
    "backup": str(backup_path),
    "core_signature": core_signature,
    "entrypoint_contract": str(entrypoint_contract_path),
    "readiness_contract": str(readiness_path),
    "report": str(report_path),
    "test": str(test_path),
    "default_live_behavior_changed": False,
    "next_step": "Run real feature-flagged replay comparison."
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $patchPy -Encoding UTF8

Log "Adding V6 core runtime entrypoint"
python $patchPy
if ($LASTEXITCODE -ne 0) {
    throw "T002-S entrypoint builder failed"
}
Remove-Item $patchPy -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_core.py
python -m py_compile Core\pf_engine_v6_adapter.py
python -m py_compile tests\test_t002_v6_core_runtime_entrypoint.py

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
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002-S targeted tests failed"
}
Ok "T002-S targeted tests passed"

Log "Updating DISPATCH_STATUS for T002-S"
$dispatchPath = Join-Path $RepoPath "Docs\DISPATCH_STATUS.json"
if (Test-Path $dispatchPath) {
    $dispatchPy = Join-Path $RepoPath ".t002s_dispatch_update.py"
@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

repo = Path.cwd()
dispatch_path = repo / "Docs" / "DISPATCH_STATUS.json"
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

data = json.loads(dispatch_path.read_text(encoding="utf-8"))
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
    obj["status"] = "in_progress_feature_flagged_replay_ready"
    obj["progress"] = max(int(obj.get("progress", 0) or 0), 92)
    obj["updated_at"] = now
    obj["v6_core_runtime_entrypoint"] = "Core/pf_engine_v6_core.py::process_tick"
    obj["v6_core_runtime_contract"] = "Docs/Contracts/T002_V6_CORE_RUNTIME_ENTRYPOINT.json"
    obj["feature_flag_replay_readiness"] = "FEATURE_FLAG_REPLAY_READY"
    obj["feature_flag_replay_contract"] = "Docs/Contracts/T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
    obj["next_steps"] = [
        "Run real feature-flagged replay comparison with POWERFLOW_T002_USE_V6_CORE=1",
        "Compare legacy fallback outputs vs V6 core surface outputs on golden/live-like samples",
        "Keep default live scheduler on legacy fallback until replay contract passes"
    ]
    obj["notes"] = "V6 core process_tick entrypoint exists and is reachable through the adapter flag. Default live behavior remains unchanged."
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
    if ($LASTEXITCODE -ne 0) { throw "T002-S dispatch update failed" }
    Remove-Item $dispatchPy -Force -ErrorAction SilentlyContinue
    python -m json.tool Docs\DISPATCH_STATUS.json | Out-Null
    Ok "DISPATCH_STATUS updated and valid"
} else {
    Warn "Docs/DISPATCH_STATUS.json not found; skipping dispatch update"
}

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Core\pf_engine_v6_core.py",
    "Docs\Contracts\T002_V6_CORE_RUNTIME_ENTRYPOINT.json",
    "Docs\Contracts\T002_FEATURE_FLAGGED_REPLAY_READINESS.json",
    "Docs\DISPATCH_STATUS.json",
    "tests\test_t002_v6_core_runtime_entrypoint.py",
    "scripts\t002_add_v6_core_runtime_entrypoint.ps1"
)

$latestAudit = Get-ChildItem ".\Docs\Audits" -Filter "T002_V6_CORE_RUNTIME_ENTRYPOINT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestAudit) {
    $pathsToAdd += $latestAudit.FullName
}

Log "Targeted staging only T002-S files"
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
    Warn "No staged T002-S changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "feat(t002): add V6 core runtime process_tick entrypoint"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_S_V6_CORE_RUNTIME_ENTRYPOINT.md"
    $recent = @(git log --oneline -10)

    $ck = New-Object System.Collections.Generic.List[string]
    $ck.Add("# CHECKPOINT - T002-S V6 core runtime entrypoint")
    $ck.Add("")
    $ck.Add("Date: $(Get-Date -Format o)")
    $ck.Add("Focus: Add pf_engine_v6_core.process_tick runtime entrypoint")
    $ck.Add("")
    $ck.Add("## Result")
    $ck.Add("")
    $ck.Add("- pf_engine_v6_core.process_tick added.")
    $ck.Add("- Adapter can now reach real V6 core route under POWERFLOW_T002_USE_V6_CORE=1.")
    $ck.Add("- Readiness contract moved to FEATURE_FLAG_REPLAY_READY.")
    $ck.Add("- Default live behavior remains legacy fallback.")
    $ck.Add("- Targeted T002 tests passed.")
    $ck.Add("")
    $ck.Add("## Next step")
    $ck.Add("")
    $ck.Add("- Run real feature-flagged replay comparison before default live activation.")
    $ck.Add("")
    $ck.Add("## Recent git log")
    $ck.Add("")
    foreach ($line in $recent) { $ck.Add("- $line") }

    Set-Content -Path $checkpointPath -Value $ck -Encoding UTF8
    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002-S V6 core runtime entrypoint"
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

Ok "T002-S V6 core runtime entrypoint complete"
Log "Final status"
git status --short
git log --oneline -10
