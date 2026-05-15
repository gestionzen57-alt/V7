param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-CONTRACT] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002 process_tick contract freeze"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -5

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before contract commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t002_freeze_process_tick_contract.py"

@'
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import inspect
import json
from pathlib import Path
import sys

repo = Path.cwd()
core = repo / "Core"
engine_path = core / "engine.py"
contract_dir = repo / "Docs" / "Contracts"
audit_dir = repo / "Docs" / "Audits"
tests_dir = repo / "tests"

contract_dir.mkdir(parents=True, exist_ok=True)
audit_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

if not engine_path.exists():
    raise SystemExit("Core/engine.py not found")

sys.path.insert(0, str(core))

import engine  # noqa: E402

if not hasattr(engine, "process_tick"):
    raise SystemExit("engine.process_tick not found")

process_tick = engine.process_tick
sig = str(inspect.signature(process_tick))
source = inspect.getsource(process_tick)
source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()

engine_text = engine_path.read_text(encoding="utf-8", errors="replace")
tree = ast.parse(engine_text)
functions = []
classes = []
process_tick_node = None

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        functions.append({
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", None),
        })
        if node.name == "process_tick":
            process_tick_node = node
    elif isinstance(node, ast.ClassDef):
        classes.append({"name": node.name, "lineno": node.lineno, "end_lineno": getattr(node, "end_lineno", None)})

if process_tick_node is None:
    raise SystemExit("process_tick AST node not found")

side_effect_patterns = [
    "sqlite3",
    ".execute(",
    ".commit(",
    "INSERT ",
    "UPDATE ",
    "DELETE ",
    "open(",
    "Path(",
    "json.dump",
    "write_text",
    "append",
    "telegram",
    "requests",
    "print(",
]
side_effect_hits = []
for idx, line in enumerate(source.splitlines(), 1):
    for pat in side_effect_patterns:
        if pat in line:
            side_effect_hits.append({"line_in_function": idx, "pattern": pat, "text": line.strip()})

callers = []
patterns = ["from engine import process_tick", "engine.process_tick", "import engine", "from engine import"]
skip_parts = {".git", "__pycache__", ".venv", "venv", "Archive", "backups", "backup", "AVANT"}
for py in repo.rglob("*.py"):
    rel_parts = set(py.relative_to(repo).parts)
    if rel_parts & skip_parts:
        continue
    rel = str(py.relative_to(repo)).replace("\\", "/")
    if rel == ".t002_freeze_process_tick_contract.py":
        continue
    try:
        text = py.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    for lineno, line in enumerate(text.splitlines(), 1):
        for pat in patterns:
            if pat in line:
                callers.append({"file": rel, "line": lineno, "pattern": pat, "text": line.strip()})

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
contract = {
    "contract": "POWERFLOW_T002_ENGINE_PROCESS_TICK_CONTRACT",
    "created_at": now,
    "engine_file": "Core/engine.py",
    "callable": "engine.process_tick",
    "signature": sig,
    "source_sha256": source_hash,
    "source_start_line": process_tick_node.lineno,
    "source_end_line": getattr(process_tick_node, "end_lineno", None),
    "hard_callers": callers,
    "side_effect_hits": side_effect_hits,
    "notes": [
        "This contract freezes the current runtime boundary used by capture_bridge.py.",
        "It does not validate trading behavior.",
        "It prevents accidental interface drift before T002 refactor/extraction."
    ],
}
contract_path = contract_dir / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

test_path = tests_dir / "test_t002_engine_process_tick_contract.py"
test_code = '''from __future__ import annotations

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


def test_capture_bridge_still_uses_engine_process_tick_boundary():
    repo = Path(__file__).resolve().parents[1]
    capture_bridge = repo / "Core" / "capture_bridge.py"
    text = capture_bridge.read_text(encoding="utf-8", errors="replace")

    assert "from engine import process_tick" in text or "engine.process_tick" in text
'''
test_path.write_text(test_code, encoding="utf-8")

report_path = audit_dir / ("T002_PROCESS_TICK_CONTRACT_FREEZE_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".md")
lines = []
lines.append("# T002 Process Tick Contract Freeze")
lines.append("")
lines.append("Date: " + now)
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("- engine.process_tick exists: YES")
lines.append("- signature: " + sig)
lines.append("- source sha256: " + source_hash)
lines.append("- source lines: " + str(process_tick_node.lineno) + "-" + str(getattr(process_tick_node, "end_lineno", "")))
lines.append("")
lines.append("## Runtime boundary callers")
lines.append("")
if callers:
    for c in callers:
        lines.append("- " + c["file"] + ":" + str(c["line"]) + " | " + c["pattern"] + " | " + c["text"])
else:
    lines.append("- none found")
lines.append("")
lines.append("## Side-effect hints inside process_tick")
lines.append("")
if side_effect_hits:
    for h in side_effect_hits[:80]:
        lines.append("- line " + str(h["line_in_function"]) + " | " + h["pattern"] + " | " + h["text"])
    if len(side_effect_hits) > 80:
        lines.append("- truncated: " + str(len(side_effect_hits) - 80) + " more")
else:
    lines.append("- none detected by static scan")
lines.append("")
lines.append("## Active engine.py top-level surface")
lines.append("")
lines.append("### Functions")
for f in functions:
    lines.append("- " + f["name"] + " | lines " + str(f["lineno"]) + "-" + str(f.get("end_lineno") or ""))
lines.append("")
lines.append("### Classes")
if classes:
    for c in classes:
        lines.append("- " + c["name"] + " | lines " + str(c["lineno"]) + "-" + str(c.get("end_lineno") or ""))
else:
    lines.append("- none")
lines.append("")
lines.append("## Files created")
lines.append("")
lines.append("- Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json")
lines.append("- tests/test_t002_engine_process_tick_contract.py")
lines.append("")
lines.append("## Recommendation")
lines.append("")
lines.append("1. Treat T002 as a runtime-boundary stabilization task, not a blind refactor.")
lines.append("2. Keep capture_bridge.py compatible with engine.process_tick until the contract test has a replacement boundary.")
lines.append("3. Next step: build a V6 adapter around process_tick or extract internals behind the same signature.")
lines.append("")
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "signature": sig,
    "contract": str(contract_path),
    "test": str(test_path),
    "report": str(report_path),
    "callers": callers,
    "side_effect_hit_count": len(side_effect_hits),
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Freezing process_tick contract"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "process_tick contract freeze failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running contract tests"
python -m pytest tests/test_t002_engine_process_tick_contract.py -q
if ($LASTEXITCODE -ne 0) {
    throw "contract tests failed"
}
Ok "Contract tests passed"

Log "Git diff summary"
git status --short
git diff --stat

if (Test-Path ".\scripts\auto_git_sync.ps1") {
    Log "Syncing contract freeze via auto_git_sync"
    & ".\scripts\auto_git_sync.ps1" -Message "test(t002): freeze engine process_tick contract"
} else {
    Warn "auto_git_sync.ps1 not found; leaving changes unstaged"
}

if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
    Log "Creating checkpoint"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002 process_tick contract freeze"
} else {
    Warn "auto_checkpoint_claude.ps1 not found; checkpoint skipped"
}

Ok "T002 process_tick contract freeze complete"
