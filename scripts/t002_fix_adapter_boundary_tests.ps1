param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-ADAPTER-FIX] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002 adapter test repair"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -5

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before adapter-fix commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$adapterPath = Join-Path $RepoPath "Core\pf_engine_v6_adapter.py"
$contractTestPath = Join-Path $RepoPath "tests\test_t002_engine_process_tick_contract.py"
$adapterTestPath = Join-Path $RepoPath "tests\test_t002_engine_v6_adapter.py"
$auditDir = Join-Path $RepoPath "Docs\Audits"

if (!(Test-Path $adapterPath)) { throw "Missing Core\pf_engine_v6_adapter.py. Run adapter patch first." }
if (!(Test-Path $contractTestPath)) { throw "Missing tests\test_t002_engine_process_tick_contract.py" }

Log "Fixing adapter annotations"
$adapter = Get-Content $adapterPath -Raw
$adapter = $adapter -replace "from __future__ import annotations\r?\n\r?\n", ""
Set-Content -Path $adapterPath -Value $adapter -Encoding UTF8

Log "Updating contract test for adapter boundary"
$contractTest = @'
from __future__ import annotations

import inspect
import json
from pathlib import Path
import sys


def test_engine_process_tick_contract_signature_is_stable():
    repo = Path(__file__).resolve().parents[1]
    core = repo / "Core"
    sys.path.insert(0, str(core))

    import engine

    contract_path = repo / "Docs" / "Contracts" / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert hasattr(engine, "process_tick")
    assert callable(engine.process_tick)
    assert str(inspect.signature(engine.process_tick)) == contract["signature"]


def test_capture_bridge_uses_v6_adapter_boundary():
    repo = Path(__file__).resolve().parents[1]
    capture_bridge = repo / "Core" / "capture_bridge.py"
    text = capture_bridge.read_text(encoding="utf-8", errors="replace")

    assert "from pf_engine_v6_adapter import process_tick" in text
    assert "from engine import process_tick" not in text
'@
Set-Content -Path $contractTestPath -Value $contractTest -Encoding UTF8

if (Test-Path $adapterTestPath) {
    Log "Normalizing adapter test signature assertion"
    $adapterTest = Get-Content $adapterTestPath -Raw
    $adapterTest = $adapterTest -replace "from __future__ import annotations\r?\n\r?\n", "from __future__ import annotations`r`n`r`n"
    Set-Content -Path $adapterTestPath -Value $adapterTest -Encoding UTF8
}

if (!(Test-Path $auditDir)) { New-Item -ItemType Directory -Path $auditDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = Join-Path $auditDir "T002_ENGINE_V6_ADAPTER_TEST_REPAIR_$stamp.md"

$report = @()
$report += "# T002 Engine V6 Adapter Test Repair"
$report += ""
$report += "Date: $(Get-Date -Format o)"
$report += ""
$report += "## Repairs"
$report += ""
$report += "- Removed future annotations from Core/pf_engine_v6_adapter.py so inspect.signature matches the frozen contract."
$report += "- Updated tests/test_t002_engine_process_tick_contract.py to expect capture_bridge.py -> pf_engine_v6_adapter.process_tick."
$report += ""
$report += "## Why"
$report += ""
$report += "- The previous contract test still expected the old direct legacy import."
$report += "- The adapter boundary is intentional and should now be the protected runtime seam."
$report += ""
$report += "## Behavior"
$report += ""
$report += "- Core/engine.py remains unchanged."
$report += "- Adapter still delegates 1:1 to legacy engine.process_tick."
$report += "- No DB or runtime behavior change intended."
$report += ""
Set-Content -Path $reportPath -Value ($report -join "`n") -Encoding UTF8

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_adapter.py Core\capture_bridge.py
if ($LASTEXITCODE -ne 0) { throw "syntax checks failed" }

Log "Running T002 tests"
python -m pytest tests/test_t002_engine_process_tick_contract.py tests/test_t002_engine_v6_adapter.py -q
if ($LASTEXITCODE -ne 0) { throw "T002 tests failed after adapter test repair" }
Ok "T002 tests passed"

Log "Git diff summary"
git status --short
git diff --stat

if (Test-Path ".\scripts\auto_git_sync.ps1") {
    Log "Syncing adapter fix via auto_git_sync"
    & ".\scripts\auto_git_sync.ps1" -Message "fix(t002): repair adapter boundary tests"
} else {
    Warn "auto_git_sync.ps1 not found; leaving changes unstaged"
}

if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
    Log "Creating checkpoint"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002 adapter boundary test repair"
} else {
    Warn "auto_checkpoint_claude.ps1 not found; checkpoint skipped"
}

Ok "T002 adapter test repair complete"
