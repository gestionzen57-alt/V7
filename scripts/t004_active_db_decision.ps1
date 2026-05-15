param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-C] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-C active DB decision report"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-C commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004c_active_db_decision.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
plan_dir = repo / "Docs" / "Plans"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
plan_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

source_contract_path = contract_dir / "T004_CAPTURE_DB_PATH_AUDIT.json"
if not source_contract_path.exists():
    raise SystemExit("Missing Docs/Contracts/T004_CAPTURE_DB_PATH_AUDIT.json")

source = json.loads(source_contract_path.read_text(encoding="utf-8"))

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

candidate_dbs = source.get("candidate_db_paths", [])
discovered_dbs = source.get("discovered_db_files", [])
all_dbs = candidate_dbs + discovered_dbs

populated = [d for d in all_dbs if d.get("exists") and (d.get("total_rows") or 0) > 0]
empty = [d for d in all_dbs if d.get("exists") and (d.get("total_rows") == 0)]
root_db = next((d for d in all_dbs if d.get("path") == "powerflow.db"), None)

# Extract path references and insertion clues.
db_path_refs = source.get("db_path_references", [])
ast_findings = source.get("key_file_ast_findings", [])
code_findings = source.get("code_findings", [])

def score_db(d: dict) -> int:
    score = 0
    rows = d.get("total_rows") or 0
    score += min(rows, 1000000) // 1000
    path = (d.get("path") or "").lower()
    if "core" in path:
        score += 10
    if path.endswith("powerflow.db"):
        score += 5
    table_names = " ".join(t.get("table", "").lower() for t in d.get("tables", []))
    if "force" in table_names:
        score += 5
    if "bar" in table_names:
        score += 3
    return int(score)

ranked_populated = sorted(populated, key=lambda d: (-score_db(d), -(d.get("total_rows") or 0), d.get("path") or ""))
best_populated = ranked_populated[0] if ranked_populated else None

# Build focused evidence from db.py / capture_bridge.py findings.
focused = []
for item in ast_findings:
    file = item.get("file", "")
    if file in {"Core/capture_bridge.py", "Core/db.py", "Core/system_config.py"} or "capture_bridge" in file or file.endswith("db.py"):
        focused.append(item)

path_ref_files = sorted(set(ref.get("file", "") for ref in db_path_refs if ref.get("file")))

decision = "UNKNOWN"
if root_db and root_db.get("exists") and (root_db.get("total_rows") == 0) and best_populated:
    decision = "ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS"
elif best_populated:
    decision = "POPULATED_DB_EXISTS"
elif root_db and root_db.get("exists") and (root_db.get("total_rows") == 0):
    decision = "ONLY_EMPTY_ROOT_DB_FOUND"
else:
    decision = "NO_POPULATED_DB_CONFIRMED"

recommendations = []
if decision == "ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS":
    recommendations.append("Do not debug USDJPY symbol yet. First align diagnostics/runtime to the populated DB or confirm why root powerflow.db is empty.")
    recommendations.append("Inspect Core/db.py and Core/capture_bridge.py DB path constants/imports before any engine change.")
    recommendations.append("Run a read-only symbol density diagnostic against the best populated DB candidate.")
elif decision == "POPULATED_DB_EXISTS":
    recommendations.append("Use the best populated DB candidate for next read-only USDJPY density diagnostic.")
elif decision == "ONLY_EMPTY_ROOT_DB_FOUND":
    recommendations.append("Capture is likely stopped or writing outside repo. Inspect MT4 bridge/runtime logs before code changes.")
else:
    recommendations.append("Manual DB path investigation needed; no populated DB candidate confirmed.")

if best_populated:
    recommendations.append("Best populated candidate by heuristic: " + best_populated.get("path", "unknown"))

decision_contract = {
    "contract": "POWERFLOW_T004_ACTIVE_DB_DECISION",
    "created_at": now,
    "source_contract": "Docs/Contracts/T004_CAPTURE_DB_PATH_AUDIT.json",
    "decision": decision,
    "root_db": root_db,
    "populated_db_count": len(populated),
    "empty_db_count": len(empty),
    "ranked_populated_db_files": ranked_populated,
    "best_populated_db": best_populated,
    "db_path_reference_files": path_ref_files,
    "focused_ast_findings": focused,
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
decision_path = contract_dir / "T004_ACTIVE_DB_DECISION.json"
decision_path.write_text(json.dumps(decision_contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_ACTIVE_DB_DECISION_PLAN_" + stamp + ".md")
md = []
md.append("# T004-C Active DB Decision Report")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Decision")
md.append("")
md.append("- Decision: " + decision)
md.append("- Populated DB count: " + str(len(populated)))
md.append("- Empty DB count: " + str(len(empty)))
md.append("")
md.append("## Key interpretation")
md.append("")
if decision == "ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS":
    md.append("The inspected root `powerflow.db` is empty, but populated DB files exist elsewhere.")
    md.append("USDJPY THIN cannot be treated as a symbol-specific issue until the active DB path is resolved.")
elif decision == "POPULATED_DB_EXISTS":
    md.append("At least one populated DB exists. Next diagnostic should run against the best populated candidate.")
elif decision == "ONLY_EMPTY_ROOT_DB_FOUND":
    md.append("Only an empty root DB is confirmed. Capture/runtime insertion may be inactive or writing outside the repo.")
else:
    md.append("No populated DB candidate is confirmed.")
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Root DB")
md.append("")
if root_db:
    md.append("- " + root_db.get("path", "unknown") + " | exists=" + str(root_db.get("exists")) + " | rows=" + str(root_db.get("total_rows")) + " | size=" + str(root_db.get("size_bytes")))
    for t in root_db.get("tables", []):
        md.append("  - " + t.get("table", "") + " rows=" + str(t.get("rows")))
else:
    md.append("- root powerflow.db not found in audit contract")
md.append("")
md.append("## Ranked populated DB candidates")
md.append("")
if ranked_populated:
    for d in ranked_populated:
        md.append("- " + d.get("path", "unknown") + " | rows=" + str(d.get("total_rows")) + " | size=" + str(d.get("size_bytes")) + " | score=" + str(score_db(d)))
        for t in d.get("tables", [])[:20]:
            md.append("  - " + t.get("table", "") + " rows=" + str(t.get("rows")))
else:
    md.append("- none")
md.append("")
md.append("## DB path reference files")
md.append("")
if path_ref_files:
    for file in path_ref_files:
        md.append("- " + file)
else:
    md.append("- none")
md.append("")
md.append("## Focused AST findings")
md.append("")
for item in focused:
    md.append("### " + item.get("file", "unknown"))
    md.append("")
    if item.get("entries"):
        for entry in item.get("entries", [])[:80]:
            if entry.get("type") == "assign":
                md.append("- line " + str(entry.get("line")) + " | assign | " + entry.get("target", "") + " = " + entry.get("value", ""))
            elif entry.get("type") == "call":
                md.append("- line " + str(entry.get("line")) + " | call | " + entry.get("expr", ""))
    else:
        md.append("- no entries")
    md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not patch USDJPY logic or engine logic while active DB path is ambiguous.")
md.append("")
md.append("## Next action")
md.append("")
md.append("T004-D should run a read-only symbol density check against the best populated DB candidate, if any.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_active_db_decision_contract.py"
test_lines = [
    "from __future__ import annotations",
    "",
    "import json",
    "from pathlib import Path",
    "",
    "",
    "def _repo() -> Path:",
    "    return Path(__file__).resolve().parents[1]",
    "",
    "",
    "def test_t004_active_db_decision_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_DECISION.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_ACTIVE_DB_DECISION"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert data["decision"] in {"ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS", "POPULATED_DB_EXISTS", "ONLY_EMPTY_ROOT_DB_FOUND", "NO_POPULATED_DB_CONFIRMED"}',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_active_db_decision_blocks_symbol_debug_when_root_empty_and_populated_exists():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_DECISION.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    if data["decision"] == "ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS":',
    '        assert data["best_populated_db"] is not None',
    '        assert data["root_db"]["total_rows"] == 0',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "decision": decision,
    "populated_db_count": len(populated),
    "empty_db_count": len(empty),
    "best_populated_db": best_populated.get("path") if best_populated else None,
    "contract": str(decision_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Building active DB decision report"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-C active DB decision failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usdjpy_thin_data_diagnostic_contract.py `
    tests/test_t004_capture_db_path_audit_contract.py `
    tests/test_t004_active_db_decision_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-C tests failed"
}
Ok "T004-C tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_ACTIVE_DB_DECISION.json",
    "tests/test_t004_active_db_decision_contract.py",
    "scripts/t004_active_db_decision.ps1"
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_ACTIVE_DB_DECISION_PLAN_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-C files"
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
    Warn "No staged T004-C changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "plan(t004): decide active DB path before USDJPY symbol debug"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_C_ACTIVE_DB_DECISION.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-C active DB decision"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-C active DB decision"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Active DB decision contract created."
    $content += "- Runtime unchanged."
    $content += "- Dashboard workspace files intentionally left untouched."
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""
    $content += "## Next step"
    $content += ""
    $content += "Run T004-D read-only symbol density against best populated DB candidate if present."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-C active DB decision"
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

Ok "T004-C active DB decision complete"
Log "Final status"
git status --short
git log --oneline -7
