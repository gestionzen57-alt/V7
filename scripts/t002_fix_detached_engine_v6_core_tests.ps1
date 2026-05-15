param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-CORE-FIX] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-D detached core test repair"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t002_fix_engine_v6_core_test.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
core_path = repo / "Core" / "pf_engine_v6_core.py"
test_path = repo / "tests" / "test_t002_engine_v6_core.py"
audit_dir = repo / "Docs" / "Audits"
audit_dir.mkdir(parents=True, exist_ok=True)

if not core_path.exists():
    raise SystemExit("Missing Core/pf_engine_v6_core.py")
if not test_path.exists():
    raise SystemExit("Missing tests/test_t002_engine_v6_core.py")

core = core_path.read_text(encoding="utf-8", errors="replace")
core = core.replace("# - no import engine", "# - no legacy engine dependency")
core = core.replace("# - no import capture_bridge", "# - no capture bridge dependency")
core = core.replace("# - no dashboard/cockpit/telegram dependency", "# - no UI or outbound transmission dependency")
core_path.write_text(core, encoding="utf-8")

test_lines = [
    "from __future__ import annotations",
    "",
    "import ast",
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
    "def test_tick_context_to_dict_returns_plain_dict():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_tick_context, tick_context_to_dict",
    "",
    '    ctx = derive_tick_context({"symbol": "GBPUSD", "price": 1.25}, {"price": 1.24})',
    "    data = tick_context_to_dict(ctx)",
    "",
    "    assert data[\"symbol\"] == \"GBPUSD\"",
    "    assert data[\"price_delta\"] == 0.010000000000000009",
    "",
    "",
    "def test_pf_engine_v6_core_has_no_forbidden_runtime_imports():",
    '    core_file = _core() / "pf_engine_v6_core.py"',
    '    text = core_file.read_text(encoding="utf-8", errors="replace")',
    "    tree = ast.parse(text)",
    "",
    '    forbidden_roots = {"engine", "capture_bridge", "sqlite3", "telegram_v6"}',
    "    imports = []",
    "",
    "    for node in ast.walk(tree):",
    "        if isinstance(node, ast.Import):",
    "            for alias in node.names:",
    "                imports.append(alias.name.split('.')[0])",
    "        elif isinstance(node, ast.ImportFrom):",
    "            if node.module:",
    "                imports.append(node.module.split('.')[0])",
    "",
    "    for imported in imports:",
    "        assert imported not in forbidden_roots",
    "",
    "",
    "def test_pf_engine_v6_core_has_no_runtime_side_effect_tokens_outside_comments():",
    '    core_file = _core() / "pf_engine_v6_core.py"',
    '    lines = core_file.read_text(encoding="utf-8", errors="replace").splitlines()',
    "",
    "    code_lines = []",
    "    for line in lines:",
    "        stripped = line.strip()",
    "        if stripped.startswith('#'):",
    "            continue",
    "        code_lines.append(line)",
    "",
    "    code = '\\n'.join(code_lines)",
    '    forbidden_tokens = [".execute(", ".commit(", "send_alert(", "dashboard_", "cockpit_"]',
    "",
    "    for token in forbidden_tokens:",
    "        assert token not in code",
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = audit_dir / ("T002_ENGINE_V6_CORE_TEST_REPAIR_" + stamp + ".md")

report = []
report.append("# T002-D Detached Core Test Repair")
report.append("")
report.append("Date: " + now)
report.append("")
report.append("## Repair")
report.append("")
report.append("- Replaced fragile raw substring guard with AST import inspection.")
report.append("- Side-effect token scan now ignores comment-only lines.")
report.append("- Cleaned comments in Core/pf_engine_v6_core.py to avoid false positives.")
report.append("")
report.append("## Behavior")
report.append("")
report.append("- Core/engine.py unchanged.")
report.append("- Core/capture_bridge.py unchanged.")
report.append("- Core/pf_engine_v6_adapter.py unchanged.")
report.append("- pf_engine_v6_core.py remains detached from runtime.")
report.append("")
report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "core": str(core_path),
    "test": str(test_path),
    "report": str(report_path),
    "repair": "AST import guard + comment-safe side-effect scan",
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Applying detached core test repair"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "detached core test repair failed"
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
    throw "T002 tests failed after detached core repair"
}
Ok "T002 tests passed"

Log "Git diff summary"
git status --short
git diff --stat

if (Test-Path ".\scripts\auto_git_sync.ps1") {
    Log "Syncing detached core repair via auto_git_sync"
    & ".\scripts\auto_git_sync.ps1" -Message "fix(t002): repair detached engine v6 core tests"
} else {
    Warn "auto_git_sync.ps1 not found; leaving changes unstaged"
}

if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
    Log "Creating checkpoint"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002-D detached engine v6 core test repair"
} else {
    Warn "auto_checkpoint_claude.ps1 not found; checkpoint skipped"
}

Ok "T002-D detached core repair complete"
