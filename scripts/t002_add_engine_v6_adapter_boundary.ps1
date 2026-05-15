param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-ADAPTER] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002 V6 adapter boundary patch"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -5

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before adapter commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t002_apply_engine_v6_adapter.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
core = repo / "Core"
tests_dir = repo / "tests"
audit_dir = repo / "Docs" / "Audits"
contract_path = repo / "Docs" / "Contracts" / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"

core.mkdir(exist_ok=True)
tests_dir.mkdir(exist_ok=True)
audit_dir.mkdir(parents=True, exist_ok=True)

capture_path = core / "capture_bridge.py"
adapter_path = core / "pf_engine_v6_adapter.py"
test_path = tests_dir / "test_t002_engine_v6_adapter.py"

if not contract_path.exists():
    raise SystemExit("Missing contract: Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json")

contract = json.loads(contract_path.read_text(encoding="utf-8"))
expected_sig = contract.get("signature")
expected = "(tick: models.Tick, prev: models.Tick, brain: dict, send_alert)"
if expected_sig != expected:
    raise SystemExit("Unexpected process_tick contract signature: " + str(expected_sig))

if not capture_path.exists():
    raise SystemExit("Missing Core/capture_bridge.py")

adapter_lines = [
    "# pf_engine_v6_adapter.py",
    "# PowerFlow V7.6.7 - T002 compatibility boundary",
    "#",
    "# Purpose:",
    "# - expose the stable process_tick contract used by capture_bridge.py;",
    "# - delegate to legacy engine.py without behavior change;",
    "# - create a safe V6 extraction seam for future refactor.",
    "#",
    "# This module must stay lightweight. It must not import cockpit_*, dashboard_*,",
    "# telegram_*, or write to DB. Legacy side effects remain inside engine.py.",
    "",
    "from __future__ import annotations",
    "",
    "import engine as _legacy_engine",
    "import models",
    "",
    "",
    'ADAPTER_VERSION = "T002_V6_ADAPTER_V1"',
    "",
    "",
    "def process_tick(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):",
    '    """Compatibility wrapper around legacy engine.process_tick.',
    "",
    "    Contract frozen in:",
    "    Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json",
    "",
    "    This wrapper intentionally delegates 1:1 to preserve runtime behavior.",
    "    Future T002 extraction can move internals behind this boundary while",
    "    keeping capture_bridge.py stable.",
    '    """',
    "    return _legacy_engine.process_tick(tick, prev, brain, send_alert)",
    "",
    "",
    '__all__ = ["process_tick", "ADAPTER_VERSION"]',
    "",
]
adapter_code = "\n".join(adapter_lines)

old_capture = capture_path.read_text(encoding="utf-8", errors="replace")
old_line = "from engine import process_tick"
new_line = "from pf_engine_v6_adapter import process_tick"

if old_line not in old_capture and new_line not in old_capture:
    raise SystemExit("capture_bridge.py does not contain expected process_tick import boundary")

if old_line in old_capture:
    new_capture = old_capture.replace(old_line, new_line, 1)
else:
    new_capture = old_capture

adapter_path.write_text(adapter_code, encoding="utf-8")
capture_path.write_text(new_capture, encoding="utf-8")

test_lines = [
    "from __future__ import annotations",
    "",
    "import inspect",
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
    "def test_adapter_signature_matches_frozen_engine_contract():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    import pf_engine_v6_adapter as adapter",
    "",
    '    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"',
    '    contract = json.loads(contract_path.read_text(encoding="utf-8"))',
    "",
    '    assert str(inspect.signature(adapter.process_tick)) == contract["signature"]',
    "",
    "",
    "def test_adapter_delegates_to_legacy_engine(monkeypatch):",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    import pf_engine_v6_adapter as adapter",
    "",
    "    calls = []",
    "",
    "    def fake_process_tick(tick, prev, brain, send_alert):",
    "        calls.append((tick, prev, brain, send_alert))",
    '        return {"delegated": True}',
    "",
    '    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_process_tick)',
    "",
    "    tick = object()",
    "    prev = object()",
    '    brain = {"state": "test"}',
    "    send_alert = lambda *args, **kwargs: None",
    "",
    "    result = adapter.process_tick(tick, prev, brain, send_alert)",
    "",
    '    assert result == {"delegated": True}',
    "    assert calls == [(tick, prev, brain, send_alert)]",
    "",
    "",
    "def test_capture_bridge_uses_adapter_boundary_not_legacy_direct_import():",
    '    capture_bridge = _repo() / "Core" / "capture_bridge.py"',
    '    text = capture_bridge.read_text(encoding="utf-8", errors="replace")',
    "",
    '    assert "from pf_engine_v6_adapter import process_tick" in text',
    '    assert "from engine import process_tick" not in text',
    "",
]
test_code = "\n".join(test_lines)
test_path.write_text(test_code, encoding="utf-8")

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
report_path = audit_dir / ("T002_ENGINE_V6_ADAPTER_PATCH_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".md")
lines = []
lines.append("# T002 Engine V6 Adapter Patch")
lines.append("")
lines.append("Date: " + now)
lines.append("")
lines.append("## Change")
lines.append("")
lines.append("- Created Core/pf_engine_v6_adapter.py.")
lines.append("- Redirected Core/capture_bridge.py from legacy direct import to adapter boundary.")
lines.append("- Added tests/test_t002_engine_v6_adapter.py.")
lines.append("")
lines.append("## Runtime behavior")
lines.append("")
lines.append("- No change intended.")
lines.append("- Adapter delegates 1:1 to legacy engine.process_tick.")
lines.append("- Existing frozen contract remains: " + str(expected_sig))
lines.append("")
lines.append("## Why")
lines.append("")
lines.append("- T002 was misnamed as pf_engine.py refactor.")
lines.append("- Active runtime boundary is capture_bridge.py -> engine.process_tick.")
lines.append("- The adapter creates a safe V6 seam before extracting legacy internals.")
lines.append("")
lines.append("## Technical risks")
lines.append("")
lines.append("- Import side effects remain in legacy engine.py until extraction.")
lines.append("- If capture_bridge.py depends on side effects from direct engine import, adapter must remain 1:1.")
lines.append("- Do not move logic into adapter yet; it is a boundary only.")
lines.append("")
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "adapter": str(adapter_path),
    "capture_bridge": str(capture_path),
    "test": str(test_path),
    "report": str(report_path),
    "capture_changed": old_capture != new_capture,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Applying V6 adapter boundary"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "V6 adapter patch failed"
}

Remove-Item $pythonPatch -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_adapter.py Core\capture_bridge.py
if ($LASTEXITCODE -ne 0) {
    throw "syntax checks failed"
}

Log "Running T002 contract and adapter tests"
python -m pytest tests/test_t002_engine_process_tick_contract.py tests/test_t002_engine_v6_adapter.py -q
if ($LASTEXITCODE -ne 0) {
    throw "T002 tests failed"
}
Ok "T002 tests passed"

Log "Git diff summary"
git status --short
git diff --stat

if (Test-Path ".\scripts\auto_git_sync.ps1") {
    Log "Syncing V6 adapter patch via auto_git_sync"
    & ".\scripts\auto_git_sync.ps1" -Message "refactor(t002): add V6 adapter boundary for engine process_tick"
} else {
    Warn "auto_git_sync.ps1 not found; leaving changes unstaged"
}

if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
    Log "Creating checkpoint"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002 V6 adapter boundary"
} else {
    Warn "auto_checkpoint_claude.ps1 not found; checkpoint skipped"
}

Ok "T002 V6 adapter boundary patch complete"
