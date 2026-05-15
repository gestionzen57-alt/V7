param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-G] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-G golden tick comparison tests"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002-G commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t002_golden_tick_cases.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
core_dir = repo / "Core"
tests_dir = repo / "tests"
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"

core_path = core_dir / "pf_engine_v6_core.py"
tick_surface_contract = contract_dir / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"
golden_path = contract_dir / "T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES.json"
test_path = tests_dir / "test_t002_engine_v6_core_golden_ticks.py"

if not core_path.exists():
    raise SystemExit("Missing Core/pf_engine_v6_core.py")
if not tick_surface_contract.exists():
    raise SystemExit("Missing Docs/Contracts/T002_ENGINE_TICK_SURFACE_CONTRACT.json")

contract = json.loads(tick_surface_contract.read_text(encoding="utf-8"))
required = {"dev_a", "dev_b", "val_a", "val_b", "gap", "timeframe", "spread"}
seen = set(contract.get("covered_direct_fields", [])) | set(contract.get("uncovered_direct_fields", []))
missing = sorted(required - seen)
if missing:
    raise SystemExit("Tick surface contract missing required legacy fields: " + ", ".join(missing))

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
golden = {
    "contract": "POWERFLOW_T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES",
    "created_at": now,
    "purpose": "Golden fixtures for detached pf_engine_v6_core.py before any runtime wiring.",
    "runtime_wired": False,
    "cases": [
        {
            "id": "GBPUSD_M1_FULL_LEGACY_SURFACE",
            "tick": {
                "symbol": "GBPUSD",
                "timestamp": "2026-05-15T18:45:00Z",
                "bid": 1.2500,
                "ask": 1.2502,
                "dev_a": "GBP",
                "dev_b": "USD",
                "val_a": 1.4,
                "val_b": -0.3,
                "gap": 1.7,
                "timeframe": 1,
                "spread": 0.00025
            },
            "prev": {
                "symbol": "GBPUSD",
                "timestamp": "2026-05-15T18:44:00Z",
                "bid": 1.2490,
                "ask": 1.2492,
                "dev_a": "GBP",
                "dev_b": "USD",
                "val_a": 1.1,
                "val_b": -0.1,
                "gap": 1.2,
                "timeframe": 1,
                "spread": 0.00022
            },
            "expected_context": {
                "symbol": "GBPUSD",
                "timestamp": "2026-05-15T18:45:00Z",
                "price": 1.2501,
                "prev_price": 1.2491,
                "price_delta": 0.001,
                "bid": 1.25,
                "ask": 1.2502,
                "spread": 0.0002
            },
            "expected_legacy_surface": {
                "dev_a": "GBP",
                "dev_b": "USD",
                "val_a": 1.4,
                "val_b": -0.3,
                "gap": 1.7,
                "timeframe": 1,
                "spread": 0.00025
            }
        },
        {
            "id": "EURUSD_M5_DERIVED_SPREAD",
            "tick": {
                "symbol": "EURUSD",
                "timestamp": "2026-05-15T18:45:00Z",
                "price": 1.1000,
                "bid": 1.0999,
                "ask": 1.1003,
                "dev_a": "EUR",
                "dev_b": "USD",
                "val_a": 0.8,
                "val_b": -0.2,
                "gap": 1.0,
                "timeframe": 5
            },
            "prev": {
                "symbol": "EURUSD",
                "timestamp": "2026-05-15T18:40:00Z",
                "price": 1.0994,
                "dev_a": "EUR",
                "dev_b": "USD",
                "val_a": 0.5,
                "val_b": -0.1,
                "gap": 0.6,
                "timeframe": 5
            },
            "expected_context": {
                "symbol": "EURUSD",
                "timestamp": "2026-05-15T18:45:00Z",
                "price": 1.1,
                "prev_price": 1.0994,
                "price_delta": 0.0006,
                "bid": 1.0999,
                "ask": 1.1003,
                "spread": 0.0004
            },
            "expected_legacy_surface": {
                "dev_a": "EUR",
                "dev_b": "USD",
                "val_a": 0.8,
                "val_b": -0.2,
                "gap": 1.0,
                "timeframe": 5,
                "spread": 0.0004
            }
        },
        {
            "id": "USDJPY_M15_MISSING_PREV_PRICE",
            "tick": {
                "symbol": "USDJPY",
                "time": "2026-05-15T18:45:00Z",
                "bid": 155.10,
                "ask": 155.12,
                "dev_a": "USD",
                "dev_b": "JPY",
                "val_a": -0.4,
                "val_b": 0.9,
                "gap": -1.3,
                "timeframe": 15
            },
            "prev": None,
            "expected_context": {
                "symbol": "USDJPY",
                "timestamp": "2026-05-15T18:45:00Z",
                "price": 155.11,
                "prev_price": None,
                "price_delta": None,
                "bid": 155.10,
                "ask": 155.12,
                "spread": 0.02
            },
            "expected_legacy_surface": {
                "dev_a": "USD",
                "dev_b": "JPY",
                "val_a": -0.4,
                "val_b": 0.9,
                "gap": -1.3,
                "timeframe": 15,
                "spread": 0.02
            }
        }
    ]
}
golden_path.write_text(json.dumps(golden, indent=2, ensure_ascii=False), encoding="utf-8")

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
    "def _golden_cases():",
    '    path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    '    assert data["contract"] == "POWERFLOW_T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES"',
    '    assert data["runtime_wired"] is False',
    '    return data["cases"]',
    "",
    "",
    "def test_golden_tick_context_cases_match_expected_output():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_tick_context, tick_context_to_dict",
    "",
    "    for case in _golden_cases():",
    '        ctx = derive_tick_context(case["tick"], case["prev"])',
    "        actual = _rounded_dict(tick_context_to_dict(ctx))",
    '        expected = _rounded_dict(case["expected_context"])',
    '        assert actual == expected, case["id"]',
    "",
    "",
    "def test_golden_legacy_surface_cases_match_expected_output():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_legacy_tick_surface, legacy_tick_surface_to_dict",
    "",
    "    for case in _golden_cases():",
    '        surface = derive_legacy_tick_surface(case["tick"])',
    "        actual = _rounded_dict(legacy_tick_surface_to_dict(surface))",
    '        expected = _rounded_dict(case["expected_legacy_surface"])',
    '        assert actual == expected, case["id"]',
    "",
    "",
    "def test_golden_contract_keeps_core_detached_from_runtime():",
    '    core_file = _core() / "pf_engine_v6_core.py"',
    '    text = core_file.read_text(encoding="utf-8", errors="replace")',
    "",
    '    forbidden = ["import engine", "from engine import", "import capture_bridge", "send_alert(", "sqlite3", ".execute(", ".commit("]',
    "    for token in forbidden:",
    "        assert token not in text",
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = audit_dir / ("T002_ENGINE_V6_CORE_GOLDEN_TICKS_" + stamp + ".md")
report = []
report.append("# T002-G Golden Tick Comparison Tests")
report.append("")
report.append("Date: " + now)
report.append("")
report.append("## Change")
report.append("")
report.append("- Created Docs/Contracts/T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES.json.")
report.append("- Created tests/test_t002_engine_v6_core_golden_ticks.py.")
report.append("")
report.append("## Purpose")
report.append("")
report.append("Freeze expected outputs for detached pf_engine_v6_core.py before any runtime wiring.")
report.append("")
report.append("## Golden cases")
report.append("")
for case in golden["cases"]:
    report.append("- " + case["id"])
report.append("")
report.append("## Runtime behavior")
report.append("")
report.append("- No runtime wiring.")
report.append("- Core/engine.py unchanged.")
report.append("- Core/capture_bridge.py unchanged.")
report.append("- Core/pf_engine_v6_adapter.py unchanged.")
report.append("")
report.append("## Next rule")
report.append("")
report.append("Do not connect pf_engine_v6_core.py until these golden tests remain green after a real tick replay comparison.")
report.append("")
report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "golden": str(golden_path),
    "test": str(test_path),
    "report": str(report_path),
    "case_count": len(golden["cases"]),
    "runtime_wired": False,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Creating golden tick cases"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "T002-G golden case generation failed"
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
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T002-G tests failed"
}
Ok "T002 tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES.json",
    "tests/test_t002_engine_v6_core_golden_ticks.py",
    "scripts/t002_engine_v6_core_golden_ticks.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T002_ENGINE_V6_CORE_GOLDEN_TICKS_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T002-G files"
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
    Warn "No staged T002-G changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "test(t002): add golden tick cases for detached engine v6 core"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T002_G_GOLDEN_TICKS.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T002-G golden tick comparison tests"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T002-G golden tick comparison tests"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Golden tick cases created for detached pf_engine_v6_core.py."
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
    $content += "Run a real tick replay comparison before connecting pf_engine_v6_core.py into runtime."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T002-G golden tick cases"
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

Ok "T002-G golden tick comparison complete"
Log "Final status"
git status --short
git log --oneline -7
