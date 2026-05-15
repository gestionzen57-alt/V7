param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-CORE] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-D detached pf_engine_v6_core"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before core commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t002_create_engine_v6_core.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
core_dir = repo / "Core"
tests_dir = repo / "tests"
audit_dir = repo / "Docs" / "Audits"
core_dir.mkdir(exist_ok=True)
tests_dir.mkdir(exist_ok=True)
audit_dir.mkdir(parents=True, exist_ok=True)

core_path = core_dir / "pf_engine_v6_core.py"
test_path = tests_dir / "test_t002_engine_v6_core.py"

core_lines = [
    "# pf_engine_v6_core.py",
    "# PowerFlow V7.6.7 - T002 detached pure helpers",
    "#",
    "# This module is a safe extraction destination for legacy engine.py.",
    "# It is intentionally NOT wired into runtime yet.",
    "#",
    "# Rules:",
    "# - no import engine",
    "# - no import capture_bridge",
    "# - no DB write",
    "# - no dashboard/cockpit/telegram dependency",
    "# - no alert sending",
    "# - pure tick/prev derived context only",
    "",
    "from __future__ import annotations",
    "",
    "from dataclasses import asdict, dataclass",
    "from typing import Any",
    "",
    "",
    'CORE_VERSION = "T002_V6_CORE_DETACHED_V1"',
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
    "def tick_context_to_dict(context: EngineTickContext) -> dict[str, Any]:",
    "    return asdict(context)",
    "",
    "",
    "__all__ = [",
    '    "CORE_VERSION",',
    '    "EngineTickContext",',
    '    "derive_tick_context",',
    '    "tick_context_to_dict",',
    "]",
    "",
]
core_code = "\n".join(core_lines)

test_lines = [
    "from __future__ import annotations",
    "",
    "from pathlib import Path",
    "import sys",
    "from types import SimpleNamespace",
    "",
    "",
    "def _core() -> Path:",
    '    return Path(__file__).resolve().parents[1] / "Core"',
    "",
    "",
    "def test_derive_tick_context_from_bid_ask_objects():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_tick_context",
    "",
    '    tick = SimpleNamespace(symbol="GBPUSD", timestamp="2026-05-15T17:30:00Z", bid=1.2500, ask=1.2502)',
    '    prev = SimpleNamespace(symbol="GBPUSD", timestamp="2026-05-15T17:29:00Z", bid=1.2490, ask=1.2492)',
    "",
    "    ctx = derive_tick_context(tick, prev)",
    "",
    '    assert ctx.symbol == "GBPUSD"',
    "    assert ctx.price == 1.2501",
    "    assert round(ctx.prev_price, 6) == 1.2491",
    "    assert round(ctx.price_delta, 6) == 0.001",
    "    assert round(ctx.spread, 6) == 0.0002",
    "",
    "",
    "def test_derive_tick_context_from_dict_price_priority():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_tick_context",
    "",
    '    tick = {"symbol": "EURUSD", "timestamp": "t1", "price": "1.1000", "bid": 1.0, "ask": 2.0}',
    '    prev = {"symbol": "EURUSD", "timestamp": "t0", "price": "1.0990"}',
    "",
    "    ctx = derive_tick_context(tick, prev)",
    "",
    '    assert ctx.symbol == "EURUSD"',
    "    assert ctx.price == 1.1",
    "    assert ctx.prev_price == 1.099",
    "    assert round(ctx.price_delta, 6) == 0.001",
    "    assert ctx.spread == 1.0",
    "",
    "",
    "def test_tick_context_handles_missing_prev_without_crash():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_tick_context",
    "",
    '    ctx = derive_tick_context({"symbol": "USDJPY", "bid": 155.10, "ask": 155.12}, None)',
    "",
    '    assert ctx.symbol == "USDJPY"',
    "    assert ctx.price == 155.11",
    "    assert ctx.prev_price is None",
    "    assert ctx.price_delta is None",
    "",
    "",
    "def test_pf_engine_v6_core_is_detached_from_runtime_side_effects():",
    '    core_file = _core() / "pf_engine_v6_core.py"',
    '    text = core_file.read_text(encoding="utf-8", errors="replace")',
    "",
    "    forbidden = [",
    '        "import engine",',
    '        "from engine import",',
    '        "import capture_bridge",',
    '        "sqlite3",',
    '        ".execute(",',
    '        ".commit(",',
    '        "send_alert(",',
    '        "telegram",',
    '        "dashboard_",',
    '        "cockpit_",',
    "    ]",
    "",
    "    for token in forbidden:",
    "        assert token not in text",
    "",
]
test_code = "\n".join(test_lines)

core_path.write_text(core_code, encoding="utf-8")
test_path.write_text(test_code, encoding="utf-8")

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = audit_dir / ("T002_ENGINE_V6_CORE_DETACHED_" + stamp + ".md")

report = []
report.append("# T002-D Detached Engine V6 Core")
report.append("")
report.append("Date: " + now)
report.append("")
report.append("## Change")
report.append("")
report.append("- Created Core/pf_engine_v6_core.py.")
report.append("- Created tests/test_t002_engine_v6_core.py.")
report.append("")
report.append("## Purpose")
report.append("")
report.append("Create a detached pure-helper destination before extracting any code from legacy Core/engine.py.")
report.append("")
report.append("## Runtime behavior")
report.append("")
report.append("- No runtime wiring.")
report.append("- Core/engine.py unchanged.")
report.append("- Core/capture_bridge.py unchanged.")
report.append("- Core/pf_engine_v6_adapter.py unchanged.")
report.append("")
report.append("## Initial pure helper")
report.append("")
report.append("- derive_tick_context(tick, prev, symbol=None)")
report.append("- EngineTickContext immutable dataclass")
report.append("- tick_context_to_dict(context)")
report.append("")
report.append("## Guardrails")
report.append("")
report.append("- no engine import")
report.append("- no DB access")
report.append("- no alert transmission")
report.append("- no cockpit/dashboard/telegram dependency")
report.append("")
report.append("## Next extraction candidate")
report.append("")
report.append("Only after review: compare this derived context against values used inside engine.process_tick and add golden tests before wiring.")
report.append("")
report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "core": str(core_path),
    "test": str(test_path),
    "report": str(report_path),
    "runtime_wired": False,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Creating detached pf_engine_v6_core"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "pf_engine_v6_core creation failed"
}

Remove-Item $pythonPatch -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_core.py Core\pf_engine_v6_adapter.py Core\capture_bridge.py Core\engine.py
if ($LASTEXITCODE -ne 0) {
    throw "syntax checks failed"
}

Log "Running T002 tests"
python -m pytest tests/test_t002_engine_process_tick_contract.py tests/test_t002_engine_v6_adapter.py tests/test_t002_engine_v6_core.py -q
if ($LASTEXITCODE -ne 0) {
    throw "T002 tests failed"
}
Ok "T002 tests passed"

Log "Git diff summary"
git status --short
git diff --stat

if (Test-Path ".\scripts\auto_git_sync.ps1") {
    Log "Syncing detached V6 core via auto_git_sync"
    & ".\scripts\auto_git_sync.ps1" -Message "feat(t002): add detached engine v6 core helpers"
} else {
    Warn "auto_git_sync.ps1 not found; leaving changes unstaged"
}

if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
    Log "Creating checkpoint"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002-D detached engine v6 core"
} else {
    Warn "auto_checkpoint_claude.ps1 not found; checkpoint skipped"
}

Ok "T002-D detached pf_engine_v6_core complete"
