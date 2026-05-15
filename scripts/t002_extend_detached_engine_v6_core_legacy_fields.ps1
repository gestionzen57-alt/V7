param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-F] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-F extend detached core with legacy tick fields"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

# Clean only our own untracked recovery script from T002-E.
$ownRecovery = "scripts\t002e_targeted_checkpoint_recovery.ps1"
if (Test-Path $ownRecovery) {
    Warn "Removing local-only T002-E recovery script residue: $ownRecovery"
    Remove-Item $ownRecovery -Force
    Ok "Removed $ownRecovery"
}

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002 commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t002_extend_v6_core_legacy_fields.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
core_dir = repo / "Core"
tests_dir = repo / "tests"
audit_dir = repo / "Docs" / "Audits"
contract_path = repo / "Docs" / "Contracts" / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"

core_path = core_dir / "pf_engine_v6_core.py"
test_path = tests_dir / "test_t002_engine_v6_core.py"
new_test_path = tests_dir / "test_t002_engine_v6_core_legacy_surface.py"

if not core_path.exists():
    raise SystemExit("Missing Core/pf_engine_v6_core.py")
if not contract_path.exists():
    raise SystemExit("Missing Docs/Contracts/T002_ENGINE_TICK_SURFACE_CONTRACT.json")

contract = json.loads(contract_path.read_text(encoding="utf-8"))
expected_legacy = {"dev_a", "dev_b", "val_a", "val_b", "gap", "timeframe", "spread"}

uncovered = set(contract.get("uncovered_direct_fields", []))
missing_from_map = sorted(expected_legacy - (uncovered | set(contract.get("covered_direct_fields", []))))
if missing_from_map:
    raise SystemExit("Legacy expected fields not present in tick surface contract: " + ", ".join(missing_from_map))

core_lines = [
    "# pf_engine_v6_core.py",
    "# PowerFlow V7.6.7 - T002 detached pure helpers",
    "#",
    "# This module is a safe extraction destination for legacy engine.py.",
    "# It is intentionally NOT wired into runtime yet.",
    "#",
    "# Rules:",
    "# - no legacy engine dependency",
    "# - no capture bridge dependency",
    "# - no DB write",
    "# - no UI or outbound transmission dependency",
    "# - no alert sending",
    "# - pure tick/prev derived context only",
    "",
    "from __future__ import annotations",
    "",
    "from dataclasses import asdict, dataclass",
    "from typing import Any",
    "",
    "",
    'CORE_VERSION = "T002_V6_CORE_DETACHED_V2_LEGACY_SURFACE"',
    "",
    "",
    "@dataclass(frozen=True)",
    "class EngineTickContext:",
    "    # Derived tick context for future extraction from engine.process_tick.",
    "    # This is a small immutable measurement packet, not a decision object.",
    "",
    "    symbol: str | None",
    "    timestamp: Any",
    "    price: float | None",
    "    prev_price: float | None",
    "    price_delta: float | None",
    "    bid: float | None",
    "    ask: float | None",
    "    spread: float | None",
    "",
    "",
    "@dataclass(frozen=True)",
    "class LegacyTickSurface:",
    "    # Static legacy field surface seen in engine.process_tick.",
    "    # This is a compatibility measurement object only.",
    "",
    "    dev_a: str | None",
    "    dev_b: str | None",
    "    val_a: float | None",
    "    val_b: float | None",
    "    gap: float | None",
    "    timeframe: Any",
    "    spread: float | None",
    "",
    "",
    "def _read_attr(obj: Any, name: str, default: Any = None) -> Any:",
    "    if obj is None:",
    "        return default",
    "    if isinstance(obj, dict):",
    "        return obj.get(name, default)",
    "    return getattr(obj, name, default)",
    "",
    "",
    "def _to_float(value: Any) -> float | None:",
    "    if value is None:",
    "        return None",
    "    try:",
    "        return float(value)",
    "    except (TypeError, ValueError):",
    "        return None",
    "",
    "",
    "def _derive_price(tick: Any) -> float | None:",
    "    # Priority: explicit price/mid/close, then bid/ask midpoint, then bid or ask alone.",
    '    for field in ("price", "mid", "close"):',
    "        value = _to_float(_read_attr(tick, field))",
    "        if value is not None:",
    "            return value",
    "",
    '    bid = _to_float(_read_attr(tick, "bid"))',
    '    ask = _to_float(_read_attr(tick, "ask"))',
    "",
    "    if bid is not None and ask is not None:",
    "        return (bid + ask) / 2.0",
    "    if bid is not None:",
    "        return bid",
    "    if ask is not None:",
    "        return ask",
    "",
    "    return None",
    "",
    "",
    "def derive_tick_context(tick: Any, prev: Any, symbol: str | None = None) -> EngineTickContext:",
    "    # Build an immutable pure context from current and previous ticks.",
    "",
    "    price = _derive_price(tick)",
    "    prev_price = _derive_price(prev)",
    "",
    '    bid = _to_float(_read_attr(tick, "bid"))',
    '    ask = _to_float(_read_attr(tick, "ask"))',
    "",
    "    spread = None",
    "    if bid is not None and ask is not None:",
    "        spread = ask - bid",
    "",
    "    price_delta = None",
    "    if price is not None and prev_price is not None:",
    "        price_delta = price - prev_price",
    "",
    "    resolved_symbol = symbol",
    "    if resolved_symbol is None:",
    '        resolved_symbol = _read_attr(tick, "symbol", None)',
    "",
    '    timestamp = _read_attr(tick, "timestamp", _read_attr(tick, "time", None))',
    "",
    "    return EngineTickContext(",
    "        symbol=resolved_symbol,",
    "        timestamp=timestamp,",
    "        price=price,",
    "        prev_price=prev_price,",
    "        price_delta=price_delta,",
    "        bid=bid,",
    "        ask=ask,",
    "        spread=spread,",
    "    )",
    "",
    "",
    "def derive_legacy_tick_surface(tick: Any) -> LegacyTickSurface:",
    "    # Build the static legacy tick surface used by engine.process_tick.",
    "    # It supports object-like ticks and dict-like ticks.",
    "",
    '    explicit_spread = _to_float(_read_attr(tick, "spread"))',
    '    bid = _to_float(_read_attr(tick, "bid"))',
    '    ask = _to_float(_read_attr(tick, "ask"))',
    "",
    "    derived_spread = None",
    "    if bid is not None and ask is not None:",
    "        derived_spread = ask - bid",
    "",
    "    spread = explicit_spread if explicit_spread is not None else derived_spread",
    "",
    "    return LegacyTickSurface(",
    '        dev_a=_read_attr(tick, "dev_a", None),',
    '        dev_b=_read_attr(tick, "dev_b", None),',
    '        val_a=_to_float(_read_attr(tick, "val_a", None)),',
    '        val_b=_to_float(_read_attr(tick, "val_b", None)),',
    '        gap=_to_float(_read_attr(tick, "gap", None)),',
    '        timeframe=_read_attr(tick, "timeframe", None),',
    "        spread=spread,",
    "    )",
    "",
    "",
    "def tick_context_to_dict(context: EngineTickContext) -> dict[str, Any]:",
    "    return asdict(context)",
    "",
    "",
    "def legacy_tick_surface_to_dict(surface: LegacyTickSurface) -> dict[str, Any]:",
    "    return asdict(surface)",
    "",
    "",
    "__all__ = [",
    '    "CORE_VERSION",',
    '    "EngineTickContext",',
    '    "LegacyTickSurface",',
    '    "derive_tick_context",',
    '    "derive_legacy_tick_surface",',
    '    "tick_context_to_dict",',
    '    "legacy_tick_surface_to_dict",',
    "]",
    "",
]
core_path.write_text("\n".join(core_lines), encoding="utf-8")

# Extend the original core test with a version check while preserving behavior.
if test_path.exists():
    original = test_path.read_text(encoding="utf-8", errors="replace")
    if "test_pf_engine_v6_core_version_is_legacy_surface_v2" not in original:
        original += "\n\n"
        original += "def test_pf_engine_v6_core_version_is_legacy_surface_v2():\n"
        original += "    sys.path.insert(0, str(_core()))\n\n"
        original += "    from pf_engine_v6_core import CORE_VERSION\n\n"
        original += '    assert CORE_VERSION == "T002_V6_CORE_DETACHED_V2_LEGACY_SURFACE"\n'
        test_path.write_text(original, encoding="utf-8")

legacy_test_lines = [
    "from __future__ import annotations",
    "",
    "from pathlib import Path",
    "import json",
    "import sys",
    "from types import SimpleNamespace",
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
    "def test_derive_legacy_tick_surface_from_object():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_legacy_tick_surface",
    "",
    '    tick = SimpleNamespace(dev_a="GBP", dev_b="USD", val_a="1.2", val_b="-0.4", gap="1.6", timeframe=1, spread="0.0002")',
    "    surface = derive_legacy_tick_surface(tick)",
    "",
    '    assert surface.dev_a == "GBP"',
    '    assert surface.dev_b == "USD"',
    "    assert surface.val_a == 1.2",
    "    assert surface.val_b == -0.4",
    "    assert surface.gap == 1.6",
    "    assert surface.timeframe == 1",
    "    assert surface.spread == 0.0002",
    "",
    "",
    "def test_derive_legacy_tick_surface_from_dict_and_derived_spread():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_legacy_tick_surface",
    "",
    '    tick = {"dev_a": "EUR", "dev_b": "USD", "val_a": 0.7, "val_b": -0.2, "gap": 0.9, "timeframe": 5, "bid": 1.1000, "ask": 1.1003}',
    "    surface = derive_legacy_tick_surface(tick)",
    "",
    '    assert surface.dev_a == "EUR"',
    '    assert surface.dev_b == "USD"',
    "    assert surface.val_a == 0.7",
    "    assert surface.val_b == -0.2",
    "    assert surface.gap == 0.9",
    "    assert surface.timeframe == 5",
    "    assert round(surface.spread, 6) == 0.0003",
    "",
    "",
    "def test_legacy_tick_surface_to_dict():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_legacy_tick_surface, legacy_tick_surface_to_dict",
    "",
    '    surface = derive_legacy_tick_surface({"dev_a": "GBP", "dev_b": "JPY", "val_a": 2, "val_b": 1, "gap": 1, "timeframe": 15})',
    "    data = legacy_tick_surface_to_dict(surface)",
    "",
    '    assert data["dev_a"] == "GBP"',
    '    assert data["dev_b"] == "JPY"',
    '    assert data["gap"] == 1.0',
    '    assert data["spread"] is None',
    "",
    "",
    "def test_legacy_surface_fields_match_t002_tick_contract_expectation():",
    '    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"',
    '    contract = json.loads(contract_path.read_text(encoding="utf-8"))',
    "",
    '    expected = {"dev_a", "dev_b", "val_a", "val_b", "gap", "timeframe", "spread"}',
    '    seen = set(contract["uncovered_direct_fields"]) | set(contract["covered_direct_fields"])',
    "",
    "    assert expected <= seen",
    "",
    "",
    "def test_pf_engine_v6_core_still_has_no_runtime_wiring_or_side_effects():",
    '    core_file = _core() / "pf_engine_v6_core.py"',
    '    text = core_file.read_text(encoding="utf-8", errors="replace")',
    "",
    '    forbidden_tokens = ["import engine", "from engine import", "import capture_bridge", "sqlite3", ".execute(", ".commit(", "send_alert(", "dashboard_", "cockpit_"]',
    "",
    "    for token in forbidden_tokens:",
    "        assert token not in text",
    "",
]
new_test_path.write_text("\n".join(legacy_test_lines) + "\n", encoding="utf-8")

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = audit_dir / ("T002_ENGINE_V6_CORE_LEGACY_FIELDS_" + stamp + ".md")

report = []
report.append("# T002-F Detached V6 Core Legacy Fields")
report.append("")
report.append("Date: " + now)
report.append("")
report.append("## Change")
report.append("")
report.append("- Extended Core/pf_engine_v6_core.py with LegacyTickSurface.")
report.append("- Added derive_legacy_tick_surface(tick).")
report.append("- Added legacy_tick_surface_to_dict(surface).")
report.append("- Added tests/test_t002_engine_v6_core_legacy_surface.py.")
report.append("")
report.append("## Fields now explicitly supported")
report.append("")
for field in sorted(expected_legacy):
    report.append("- " + field)
report.append("")
report.append("## Runtime behavior")
report.append("")
report.append("- No runtime wiring.")
report.append("- Core/engine.py unchanged.")
report.append("- Core/capture_bridge.py unchanged.")
report.append("- Core/pf_engine_v6_adapter.py unchanged.")
report.append("")
report.append("## Why")
report.append("")
report.append("T002-E showed that legacy engine.process_tick reads dev_a, dev_b, val_a, val_b, gap, timeframe and spread.")
report.append("This patch gives the detached V6 core a pure typed surface for those fields before any migration.")
report.append("")
report.append("## Next rule")
report.append("")
report.append("Do not connect this into process_tick until a golden comparison test exists on real/synthetic ticks.")
report.append("")
report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "core": str(core_path),
    "test": str(new_test_path),
    "report": str(report_path),
    "fields": sorted(expected_legacy),
    "runtime_wired": False,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Extending detached V6 core with legacy fields"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "T002-F patch failed"
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
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002-F tests failed"
}
Ok "T002 tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Core/pf_engine_v6_core.py",
    "tests/test_t002_engine_v6_core.py",
    "tests/test_t002_engine_v6_core_legacy_surface.py",
    "scripts/t002_extend_detached_engine_v6_core_legacy_fields.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T002_ENGINE_V6_CORE_LEGACY_FIELDS_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T002-F files"
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
    Warn "No staged T002-F changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "feat(t002): extend detached engine v6 core legacy tick surface"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_F_LEGACY_TICK_SURFACE.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T002-F detached V6 core legacy tick surface"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T002-F detached V6 core legacy tick surface"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- pf_engine_v6_core.py now has a detached LegacyTickSurface."
    $content += "- Fields supported: dev_a, dev_b, val_a, val_b, gap, timeframe, spread."
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
    $content += "Build a golden comparison test before connecting pf_engine_v6_core.py into the adapter or legacy process_tick."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002-F legacy tick surface"
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

Ok "T002-F detached legacy tick surface complete"
Log "Final status"
git status --short
git log --oneline -7
