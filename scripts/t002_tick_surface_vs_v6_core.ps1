param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-TICKMAP] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

function RunGit($argsArray) {
    & git @argsArray
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed: git $($argsArray -join ' ')"
    }
}

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-E legacy tick surface vs detached core"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T002 commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t002_tick_surface_vs_core.py"

@'
from __future__ import annotations

import ast
import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
core_dir = repo / "Core"
engine_path = core_dir / "engine.py"
v6_core_path = core_dir / "pf_engine_v6_core.py"
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

if not engine_path.exists():
    raise SystemExit("Missing Core/engine.py")
if not v6_core_path.exists():
    raise SystemExit("Missing Core/pf_engine_v6_core.py")

engine_text = engine_path.read_text(encoding="utf-8", errors="replace")
tree = ast.parse(engine_text)

process_tick = None
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "process_tick":
        process_tick = node
        break

if process_tick is None:
    raise SystemExit("process_tick not found")

def as_src(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__

def root_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return root_name(node.value)
    if isinstance(node, ast.Subscript):
        return root_name(node.value)
    if isinstance(node, ast.Call):
        return root_name(node.func)
    return None

def attr_chain(node: ast.AST) -> str | None:
    # tick.bid -> bid ; tick.price.close -> price.close
    if isinstance(node, ast.Attribute):
        root = root_name(node)
        if root not in {"tick", "prev"}:
            return None
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        return ".".join(reversed(parts))
    return None

def subscript_key(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Subscript):
        return None
    root = root_name(node)
    if root not in {"tick", "prev"}:
        return None
    sl = node.slice
    if isinstance(sl, ast.Constant):
        return str(sl.value)
    return as_src(sl)

tick_attrs = {}
prev_attrs = {}
tick_subscripts = {}
prev_subscripts = {}
tick_exprs = []
prev_exprs = []

for node in ast.walk(process_tick):
    root = root_name(node)
    if root not in {"tick", "prev"}:
        continue

    lineno = getattr(node, "lineno", None)
    expr = as_src(node)

    if root == "tick":
        tick_exprs.append({"line": lineno, "expr": expr})
    else:
        prev_exprs.append({"line": lineno, "expr": expr})

    chain = attr_chain(node)
    if chain:
        target = tick_attrs if root == "tick" else prev_attrs
        target.setdefault(chain, []).append(lineno)

    key = subscript_key(node)
    if key:
        target = tick_subscripts if root == "tick" else prev_subscripts
        target.setdefault(key, []).append(lineno)

supported_core_fields = {
    "symbol",
    "timestamp",
    "time",
    "price",
    "mid",
    "close",
    "bid",
    "ask",
}

legacy_fields = set(tick_attrs) | set(prev_attrs) | set(tick_subscripts) | set(prev_subscripts)
direct_fields = {f for f in legacy_fields if "." not in f}
covered_fields = sorted(direct_fields & supported_core_fields)
uncovered_fields = sorted(direct_fields - supported_core_fields)
nested_fields = sorted(f for f in legacy_fields if "." in f)

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

contract_path = contract_dir / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"
contract = {
    "contract": "POWERFLOW_T002_ENGINE_TICK_SURFACE_CONTRACT",
    "created_at": now,
    "source": "Core/engine.py process_tick AST scan",
    "process_tick_lines": [process_tick.lineno, getattr(process_tick, "end_lineno", None)],
    "tick_attrs": tick_attrs,
    "prev_attrs": prev_attrs,
    "tick_subscripts": tick_subscripts,
    "prev_subscripts": prev_subscripts,
    "supported_by_pf_engine_v6_core": sorted(supported_core_fields),
    "covered_direct_fields": covered_fields,
    "uncovered_direct_fields": uncovered_fields,
    "nested_fields": nested_fields,
    "interpretation": "This is a static surface map only. Uncovered fields are not failures; they define future extraction work.",
}
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

report_path = audit_dir / ("T002_ENGINE_TICK_SURFACE_VS_V6_CORE_" + stamp + ".md")
md = []
md.append("# T002-E Legacy Tick Surface vs Detached V6 Core")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Purpose")
md.append("")
md.append("Compare what legacy engine.process_tick reads from tick/prev against what detached pf_engine_v6_core currently derives.")
md.append("")
md.append("## Runtime behavior")
md.append("")
md.append("- No runtime wiring.")
md.append("- Core/engine.py unchanged.")
md.append("- Core/capture_bridge.py unchanged.")
md.append("- Core/pf_engine_v6_adapter.py unchanged.")
md.append("- Core/pf_engine_v6_core.py kept as detached pure helper.")
md.append("")
md.append("## process_tick tick/prev surface")
md.append("")
md.append("- process_tick lines: " + str(process_tick.lineno) + "-" + str(getattr(process_tick, "end_lineno", "")))
md.append("- tick attribute fields: " + str(len(tick_attrs)))
md.append("- prev attribute fields: " + str(len(prev_attrs)))
md.append("- tick subscript fields: " + str(len(tick_subscripts)))
md.append("- prev subscript fields: " + str(len(prev_subscripts)))
md.append("")
md.append("## Fields currently covered by pf_engine_v6_core")
md.append("")
if covered_fields:
    for field in covered_fields:
        md.append("- " + field)
else:
    md.append("- none")
md.append("")
md.append("## Direct fields not yet covered")
md.append("")
if uncovered_fields:
    for field in uncovered_fields:
        md.append("- " + field)
else:
    md.append("- none")
md.append("")
md.append("## Nested fields requiring manual interpretation")
md.append("")
if nested_fields:
    for field in nested_fields:
        md.append("- " + field)
else:
    md.append("- none")
md.append("")
md.append("## Raw tick attrs")
md.append("")
if tick_attrs:
    for field, lines in sorted(tick_attrs.items()):
        md.append("- tick." + field + " | lines " + ", ".join(str(x) for x in sorted(set(lines)) if x is not None))
else:
    md.append("- none")
md.append("")
md.append("## Raw prev attrs")
md.append("")
if prev_attrs:
    for field, lines in sorted(prev_attrs.items()):
        md.append("- prev." + field + " | lines " + ", ".join(str(x) for x in sorted(set(lines)) if x is not None))
else:
    md.append("- none")
md.append("")
md.append("## Raw tick subscript fields")
md.append("")
if tick_subscripts:
    for field, lines in sorted(tick_subscripts.items()):
        md.append("- tick[" + field + "] | lines " + ", ".join(str(x) for x in sorted(set(lines)) if x is not None))
else:
    md.append("- none")
md.append("")
md.append("## Raw prev subscript fields")
md.append("")
if prev_subscripts:
    for field, lines in sorted(prev_subscripts.items()):
        md.append("- prev[" + field + "] | lines " + ", ".join(str(x) for x in sorted(set(lines)) if x is not None))
else:
    md.append("- none")
md.append("")
md.append("## Next extraction rule")
md.append("")
md.append("Only promote a field into pf_engine_v6_core after adding a synthetic test and verifying it is genuinely used by process_tick logic.")
md.append("")
md.append("## Technical risk")
md.append("")
md.append("- Static AST can over-detect helper expressions.")
md.append("- Dynamic fields accessed through getattr or dict indirection may be invisible.")
md.append("- Coverage gap is not a failure; it is a migration map.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t002_engine_tick_surface_contract.py"
test_lines = [
    "from __future__ import annotations",
    "",
    "import json",
    "from pathlib import Path",
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
    "def test_tick_surface_contract_exists_and_is_static_map():",
    '    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"',
    '    contract = json.loads(contract_path.read_text(encoding="utf-8"))',
    "",
    '    assert contract["contract"] == "POWERFLOW_T002_ENGINE_TICK_SURFACE_CONTRACT"',
    '    assert "tick_attrs" in contract',
    '    assert "prev_attrs" in contract',
    '    assert "supported_by_pf_engine_v6_core" in contract',
    "",
    "",
    "def test_v6_core_derives_supported_surface_fields():",
    "    sys.path.insert(0, str(_core()))",
    "",
    "    from pf_engine_v6_core import derive_tick_context",
    "",
    '    tick = SimpleNamespace(symbol="GBPUSD", timestamp="t1", bid=1.2500, ask=1.2502)',
    '    prev = SimpleNamespace(symbol="GBPUSD", timestamp="t0", bid=1.2490, ask=1.2492)',
    "",
    "    ctx = derive_tick_context(tick, prev)",
    "",
    '    assert ctx.symbol == "GBPUSD"',
    '    assert ctx.timestamp == "t1"',
    "    assert round(ctx.price, 6) == 1.2501",
    "    assert round(ctx.prev_price, 6) == 1.2491",
    "    assert round(ctx.price_delta, 6) == 0.001",
    "    assert round(ctx.spread, 6) == 0.0002",
    "",
    "",
    "def test_uncovered_tick_fields_are_documented_not_silently_claimed():",
    '    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"',
    '    contract = json.loads(contract_path.read_text(encoding="utf-8"))',
    "",
    '    covered = set(contract["covered_direct_fields"])',
    '    supported = set(contract["supported_by_pf_engine_v6_core"])',
    "",
    "    assert covered <= supported",
    '    assert isinstance(contract["uncovered_direct_fields"], list)',
    '    assert isinstance(contract["nested_fields"], list)',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "covered_fields": covered_fields,
    "uncovered_fields": uncovered_fields,
    "nested_fields": nested_fields,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Building tick surface contract"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "tick surface audit failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running syntax checks"
python -m py_compile Core\pf_engine_v6_core.py Core\pf_engine_v6_adapter.py Core\capture_bridge.py Core\engine.py
if ($LASTEXITCODE -ne 0) {
    throw "syntax checks failed"
}

Log "Running targeted T002 tests"
python -m pytest tests/test_t002_engine_process_tick_contract.py tests/test_t002_engine_v6_adapter.py tests/test_t002_engine_v6_core.py tests/test_t002_engine_tick_surface_contract.py -q
if ($LASTEXITCODE -ne 0) {
    throw "T002 tick surface tests failed"
}
Ok "T002 tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T002_ENGINE_TICK_SURFACE_CONTRACT.json",
    "tests/test_t002_engine_tick_surface_contract.py"
)

# Add latest generated report only.
$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T002_ENGINE_TICK_SURFACE_VS_V6_CORE_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

# Add this script.
$pathsToAdd += "scripts/t002_tick_surface_vs_v6_core.ps1"

Log "Targeted staging only T002-E files"
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
    Warn "No staged T002-E changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }
    git commit -m "audit(t002): compare legacy tick surface with detached v6 core"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }

    Log "Pulling latest main"
    git pull origin main
    if ($LASTEXITCODE -ne 0) { throw "git pull failed" }

    Log "Pushing targeted commit"
    git push origin main
    if ($LASTEXITCODE -ne 0) { throw "git push failed" }
}

if (-not $SkipCheckpoint -and (Test-Path ".\scripts\auto_checkpoint_claude.ps1")) {
    Log "Creating checkpoint without auto git sync"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002-E tick surface vs detached V6 core" -NoGit
    if ($LASTEXITCODE -ne 0) { throw "checkpoint creation failed" }

    Log "Targeted staging checkpoint artifacts only"
    git add -- "Docs/CLAUDE.md" "Docs/Checkpoints"
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Auto-session checkpoint: T002-E tick surface vs detached V6 core"
        if ($LASTEXITCODE -ne 0) { throw "checkpoint commit failed" }
        git pull origin main
        if ($LASTEXITCODE -ne 0) { throw "git pull checkpoint failed" }
        git push origin main
        if ($LASTEXITCODE -ne 0) { throw "git push checkpoint failed" }
        Ok "Checkpoint committed and pushed"
    } else {
        Warn "No checkpoint changes staged"
    }
} elseif ($SkipCheckpoint) {
    Warn "Checkpoint skipped by flag"
} else {
    Warn "auto_checkpoint_claude.ps1 not found"
}

Ok "T002-E tick surface vs detached V6 core complete"
