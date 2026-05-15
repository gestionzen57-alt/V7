param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-RUNTIME] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002 runtime integration boundary"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -10

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002 runtime commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$required = @(
    "Core\pf_engine_v6_core.py",
    "Core\pf_engine_v6_adapter.py",
    "Core\capture_bridge.py",
    "Docs\Contracts\T002_ENGINE_PROCESS_TICK_CONTRACT.json"
)
foreach ($p in $required) {
    if (!(Test-Path $p)) { throw "Required file missing: $p" }
}

$py = Join-Path $RepoPath ".t002_runtime_integration_patch.py"

@'
from __future__ import annotations

import ast
import datetime as dt
import json
from pathlib import Path
import shutil

repo = Path.cwd()
core_dir = repo / "Core"
docs_dir = repo / "Docs"
contracts_dir = docs_dir / "Contracts"
audits_dir = docs_dir / "Audits"
tests_dir = repo / "tests"

audits_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

adapter_path = core_dir / "pf_engine_v6_adapter.py"
core_path = core_dir / "pf_engine_v6_core.py"
capture_bridge_path = core_dir / "capture_bridge.py"
contract_path = contracts_dir / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"

contract = json.loads(contract_path.read_text(encoding="utf-8"))
expected_signature = contract.get("signature", "(tick: models.Tick, prev: models.Tick, brain: dict, send_alert)")

core_text = core_path.read_text(encoding="utf-8", errors="replace")
capture_text = capture_bridge_path.read_text(encoding="utf-8", errors="replace")

backup_path = adapter_path.with_name("pf_engine_v6_adapter.py.bak_T002_runtime_" + stamp)
shutil.copy2(adapter_path, backup_path)

def ast_function_names(text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    return [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

core_functions = ast_function_names(core_text)
core_process_candidates = [
    name for name in ["process_tick", "process_tick_v6", "process_tick_core", "build_tick_surface", "compute_tick_surface"]
    if name in core_functions
]

capture_uses_adapter = ("pf_engine_v6_adapter" in capture_text) or ("from pf_engine_v6_adapter import process_tick" in capture_text)
capture_direct_engine_import = "from engine import process_tick" in capture_text

adapter_runtime_text = """# pf_engine_v6_adapter.py
# PowerFlow V7.6.7 - T002 runtime adapter boundary
#
# Role:
# - preserve the legacy process_tick public contract;
# - keep runtime safe by defaulting to legacy engine path;
# - allow controlled V6 core runtime activation via environment flag;
# - never import dashboard/cockpit/telegram modules.

import os
from typing import Any, Callable, Optional

import models
import engine as _legacy_engine

try:
    import pf_engine_v6_core as _v6_core
    _V6_CORE_IMPORT_ERROR = None
except Exception as _exc:  # pragma: no cover
    _v6_core = None
    _V6_CORE_IMPORT_ERROR = _exc


ENGINE_ADAPTER_VERSION = "T002_RUNTIME_ADAPTER_V1"
ENV_FLAG = "POWERFLOW_T002_USE_V6_CORE"
STRICT_ENV_FLAG = "POWERFLOW_T002_V6_CORE_STRICT"

_CORE_ENTRYPOINT_CANDIDATES = (
    "process_tick",
    "process_tick_v6",
    "process_tick_core",
)


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "on", "y"}


def v6_core_runtime_enabled() -> bool:
    return _truthy(os.environ.get(ENV_FLAG))


def v6_core_strict_enabled() -> bool:
    return _truthy(os.environ.get(STRICT_ENV_FLAG))


def _find_v6_core_entrypoint() -> Optional[Callable[..., Any]]:
    if _v6_core is None:
        return None
    for name in _CORE_ENTRYPOINT_CANDIDATES:
        fn = getattr(_v6_core, name, None)
        if callable(fn):
            return fn
    return None


def runtime_adapter_status() -> dict:
    fn = _find_v6_core_entrypoint()
    return {
        "version": ENGINE_ADAPTER_VERSION,
        "env_flag": ENV_FLAG,
        "strict_env_flag": STRICT_ENV_FLAG,
        "v6_enabled": v6_core_runtime_enabled(),
        "v6_strict": v6_core_strict_enabled(),
        "v6_core_imported": _v6_core is not None,
        "v6_core_import_error": repr(_V6_CORE_IMPORT_ERROR) if _V6_CORE_IMPORT_ERROR else None,
        "v6_core_entrypoint": getattr(fn, "__name__", None) if fn else None,
        "fallback": "legacy_engine.process_tick",
    }


def _call_legacy(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    return _legacy_engine.process_tick(tick, prev, brain, send_alert)


def _call_v6_core(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    fn = _find_v6_core_entrypoint()
    if fn is None:
        msg = "T002 V6 core runtime requested but no compatible process_tick entrypoint is available"
        if v6_core_strict_enabled():
            raise RuntimeError(msg)
        return _call_legacy(tick, prev, brain, send_alert)

    try:
        return fn(tick, prev, brain, send_alert)
    except TypeError:
        if v6_core_strict_enabled():
            raise
        return _call_legacy(tick, prev, brain, send_alert)
    except Exception:
        if v6_core_strict_enabled():
            raise
        return _call_legacy(tick, prev, brain, send_alert)


def process_tick(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    if v6_core_runtime_enabled():
        return _call_v6_core(tick, prev, brain, send_alert)
    return _call_legacy(tick, prev, brain, send_alert)


__all__ = [
    "ENGINE_ADAPTER_VERSION",
    "ENV_FLAG",
    "STRICT_ENV_FLAG",
    "process_tick",
    "runtime_adapter_status",
    "v6_core_runtime_enabled",
    "v6_core_strict_enabled",
]
"""

adapter_path.write_text(adapter_runtime_text, encoding="utf-8")

capture_changed = False
if capture_direct_engine_import and "pf_engine_v6_adapter" not in capture_text:
    capture_backup = capture_bridge_path.with_name("capture_bridge.py.bak_T002_runtime_" + stamp)
    shutil.copy2(capture_bridge_path, capture_backup)
    capture_text = capture_text.replace("from engine import process_tick", "from pf_engine_v6_adapter import process_tick")
    capture_bridge_path.write_text(capture_text, encoding="utf-8")
    capture_changed = True
else:
    capture_backup = None

test_path = tests_dir / "test_t002_runtime_v6_core_adapter_boundary.py"
test_text = """from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def test_t002_runtime_adapter_signature_matches_frozen_contract(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert str(inspect.signature(adapter.process_tick)) == contract["signature"]


def test_t002_runtime_adapter_has_safe_flag_default(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    monkeypatch.delenv(adapter.ENV_FLAG, raising=False)
    assert adapter.v6_core_runtime_enabled() is False

    monkeypatch.setenv(adapter.ENV_FLAG, "1")
    assert adapter.v6_core_runtime_enabled() is True

    status = adapter.runtime_adapter_status()
    assert status["fallback"] == "legacy_engine.process_tick"
    assert status["env_flag"] == "POWERFLOW_T002_USE_V6_CORE"


def test_t002_runtime_adapter_has_no_ui_or_alert_imports():
    adapter_file = _core() / "pf_engine_v6_adapter.py"
    text = adapter_file.read_text(encoding="utf-8", errors="replace").lower()

    forbidden = [
        "import dashboard",
        "from dashboard",
        "import cockpit",
        "from cockpit",
        "import telegram",
        "from telegram",
    ]

    for token in forbidden:
        assert token not in text


def test_t002_capture_bridge_uses_adapter_boundary_when_possible():
    capture_bridge = _core() / "capture_bridge.py"
    text = capture_bridge.read_text(encoding="utf-8", errors="replace")

    assert "pf_engine_v6_adapter" in text or "from engine import process_tick" not in text
"""
test_path.write_text(test_text, encoding="utf-8")

contract_runtime = {
    "contract": "POWERFLOW_T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY",
    "created_at": now,
    "adapter": "Core/pf_engine_v6_adapter.py",
    "core": "Core/pf_engine_v6_core.py",
    "capture_bridge": "Core/capture_bridge.py",
    "mode": "feature_flagged_runtime_boundary",
    "env_flag": "POWERFLOW_T002_USE_V6_CORE",
    "strict_env_flag": "POWERFLOW_T002_V6_CORE_STRICT",
    "default_runtime_path": "legacy_engine.process_tick",
    "v6_runtime_path": "pf_engine_v6_core process_tick candidate when env flag is enabled",
    "expected_signature": expected_signature,
    "core_functions_detected": core_functions,
    "core_process_candidates_detected": core_process_candidates,
    "capture_uses_adapter_before_patch": capture_uses_adapter,
    "capture_direct_engine_import_before_patch": capture_direct_engine_import,
    "capture_changed": capture_changed,
    "runtime_wired": True,
    "default_live_behavior_changed": False,
    "engine_change_required": False,
    "safety_rule": "V6 core is wired behind feature flag; default live behavior remains legacy fallback until explicit activation."
}
contract_runtime_path = contracts_dir / "T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json"
contract_runtime_path.write_text(json.dumps(contract_runtime, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

report_path = audits_dir / ("T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY_" + stamp + ".md")
md = []
md.append("# T002 Runtime V6 Core Adapter Boundary")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Result")
md.append("")
md.append("- Adapter rewritten as a safe runtime boundary.")
md.append("- Public process_tick signature preserved.")
md.append("- Default runtime behavior remains legacy engine fallback.")
md.append("- V6 core activation requires environment flag POWERFLOW_T002_USE_V6_CORE=1.")
md.append("- Strict mode available with POWERFLOW_T002_V6_CORE_STRICT=1.")
md.append("")
md.append("## Capture bridge")
md.append("")
md.append("- Direct legacy import before patch: " + str(capture_direct_engine_import))
md.append("- Adapter present before patch: " + str(capture_uses_adapter))
md.append("- Capture bridge changed: " + str(capture_changed))
md.append("")
md.append("## Core entrypoints detected")
md.append("")
if core_process_candidates:
    for name in core_process_candidates:
        md.append("- " + name)
else:
    md.append("- No direct runtime process_tick candidate detected; adapter will fallback unless strict mode is enabled.")
md.append("")
md.append("## Safety")
md.append("")
md.append("This is a runtime boundary integration, not a default live behavior switch.")
md.append("Do not enable strict V6 mode live until a dedicated replay/backward compatibility test passes.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "adapter": str(adapter_path),
    "adapter_backup": str(backup_path),
    "capture_changed": capture_changed,
    "capture_backup": str(capture_backup) if capture_backup else None,
    "contract": str(contract_runtime_path),
    "report": str(report_path),
    "test": str(test_path),
    "core_process_candidates_detected": core_process_candidates,
    "default_live_behavior_changed": False,
    "env_flag": "POWERFLOW_T002_USE_V6_CORE"
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $py -Encoding UTF8

Log "Applying T002 runtime adapter boundary"
python $py
if ($LASTEXITCODE -ne 0) {
    throw "T002 runtime integration patch failed"
}
Remove-Item $py -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_adapter.py
python -m py_compile Core\pf_engine_v6_core.py
python -m py_compile Core\capture_bridge.py

Log "Running targeted T002 tests"
python -m pytest `
    tests/test_t002_engine_process_tick_contract.py `
    tests/test_t002_engine_v6_adapter.py `
    tests/test_t002_engine_v6_core.py `
    tests/test_t002_engine_v6_core_legacy_surface.py `
    tests/test_t002_engine_v6_core_golden_ticks.py `
    tests/test_t002_runtime_v6_core_adapter_boundary.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002 targeted tests failed"
}
Ok "T002 targeted tests passed"

Log "Updating DISPATCH_STATUS T002 if present"
$dispatchPath = Join-Path $RepoPath "Docs\DISPATCH_STATUS.json"
if (Test-Path $dispatchPath) {
    $dispatchPy = Join-Path $RepoPath ".t002_runtime_dispatch_update.py"
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
    hay = " ".join(str(v) for k, v in obj.items() if k.lower() in {"id", "task", "task_id", "code", "name", "title", "label", "description", "mission"})
    return "t002" in hay.lower()

def patch(obj: dict, path: str) -> None:
    obj["status"] = "in_progress_runtime_boundary_wired"
    obj["progress"] = max(int(obj.get("progress", 0) or 0), 85)
    obj["updated"] = "2026-05-15"
    obj["updated_at"] = now
    obj["runtime_boundary"] = "Core/pf_engine_v6_adapter.py feature-flagged V6 core route"
    obj["runtime_contract"] = "Docs/Contracts/T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json"
    obj["next_steps"] = [
        "Run feature-flagged replay with POWERFLOW_T002_USE_V6_CORE=1",
        "Compare adapter fallback vs V6 core output on golden ticks and live-like samples",
        "Only then consider default live activation"
    ]
    obj["notes"] = "Runtime boundary wired safely behind env flag. Default live behavior remains legacy fallback."
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
    if ($LASTEXITCODE -ne 0) {
        throw "T002 dispatch update failed"
    }
    Remove-Item $dispatchPy -Force -ErrorAction SilentlyContinue
    python -m json.tool Docs\DISPATCH_STATUS.json | Out-Null
    Ok "DISPATCH_STATUS updated and valid"
} else {
    Warn "Docs/DISPATCH_STATUS.json not found; skipping dispatch update"
}

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Core/pf_engine_v6_adapter.py",
    "Core/capture_bridge.py",
    "Docs/Contracts/T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY.json",
    "Docs/DISPATCH_STATUS.json",
    "tests/test_t002_runtime_v6_core_adapter_boundary.py",
    "scripts/t002_integrate_v6_core_runtime.ps1"
)

$latestAudit = Get-ChildItem ".\Docs\Audits" -Filter "T002_RUNTIME_V6_CORE_ADAPTER_BOUNDARY_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestAudit) { $pathsToAdd += $latestAudit.FullName }

Log "Targeted staging only T002 runtime files"
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
    Warn "No staged T002 runtime changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "feat(t002): wire V6 core runtime adapter boundary"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_RUNTIME_V6_CORE_BOUNDARY.md"
    $recent = @(git log --oneline -10)

    $ck = New-Object System.Collections.Generic.List[string]
    $ck.Add("# CHECKPOINT - T002 runtime V6 core boundary")
    $ck.Add("")
    $ck.Add("Date: $(Get-Date -Format o)")
    $ck.Add("Focus: T002 runtime integration boundary")
    $ck.Add("")
    $ck.Add("## Result")
    $ck.Add("")
    $ck.Add("- pf_engine_v6_adapter.py now exposes a feature-flagged V6 core runtime route.")
    $ck.Add("- Default live behavior remains legacy engine fallback.")
    $ck.Add("- Activation flag: POWERFLOW_T002_USE_V6_CORE=1.")
    $ck.Add("- Strict flag: POWERFLOW_T002_V6_CORE_STRICT=1.")
    $ck.Add("- Targeted T002 tests passed.")
    $ck.Add("")
    $ck.Add("## Next step")
    $ck.Add("")
    $ck.Add("- Run feature-flagged replay before default live activation.")
    $ck.Add("")
    $ck.Add("## Recent git log")
    $ck.Add("")
    foreach ($line in $recent) { $ck.Add("- $line") }

    Set-Content -Path $checkpointPath -Value $ck -Encoding UTF8
    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002 runtime V6 core boundary"
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

Ok "T002 runtime integration boundary complete"
Log "Final status"
git status --short
git log --oneline -10
