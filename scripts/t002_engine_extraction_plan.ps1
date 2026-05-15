param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-PLAN] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-C extraction plan from internal map"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before plan commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPlan = Join-Path $RepoPath ".t002_build_extraction_plan.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
plan_dir = repo / "Docs" / "Plans"
plan_dir.mkdir(parents=True, exist_ok=True)

json_maps = sorted(audit_dir.glob("T002_ENGINE_INTERNAL_MAP_*.json"))
if not json_maps:
    raise SystemExit("No T002_ENGINE_INTERNAL_MAP_*.json found in Docs/Audits")

latest_json = json_maps[-1]
data = json.loads(latest_json.read_text(encoding="utf-8"))
pt = data["process_tick"]

category_counts = pt.get("category_counts", {})
side_effects = pt.get("side_effects", [])
local_helpers = pt.get("local_helpers", [])
statement_map = pt.get("statement_map", [])
top_calls = pt.get("top_calls", [])

def lines_for_category(category: str):
    return [s for s in statement_map if s.get("category") == category]

def helper_names():
    return [h.get("name", "") for h in local_helpers]

# Extraction strategy:
# - keep adapter as runtime seam
# - extract pure helpers first
# - never extract alert transmission or DB side effects first
# - add tests around any helper before moving code

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
plan_path = plan_dir / ("T002_ENGINE_EXTRACTION_PLAN_" + stamp + ".md")
summary_path = audit_dir / ("T002_ENGINE_EXTRACTION_PLAN_SUMMARY_" + stamp + ".json")

plan = []
plan.append("# T002-C Engine Extraction Plan")
plan.append("")
plan.append("Date: " + now)
plan.append("Source map: " + str(latest_json.relative_to(repo)))
plan.append("")
plan.append("## Current technical state")
plan.append("")
plan.append("- Runtime boundary is now: capture_bridge.py -> pf_engine_v6_adapter.process_tick -> engine.process_tick.")
plan.append("- Core/engine.py remains untouched.")
plan.append("- Frozen process_tick contract remains active.")
plan.append("- Existing T002 tests protect signature, adapter delegation and capture bridge boundary.")
plan.append("")
plan.append("## Internal map summary")
plan.append("")
plan.append("- process_tick line count: " + str(pt.get("line_count")))
plan.append("- statement count: " + str(pt.get("statement_count")))
plan.append("- local helpers called: " + str(len(local_helpers)))
plan.append("- side-effect hints: " + str(len(side_effects)))
plan.append("")
plan.append("### Statement category counts")
plan.append("")
for k, v in sorted(category_counts.items(), key=lambda x: (-x[1], x[0])):
    plan.append("- " + k + ": " + str(v))
plan.append("")
plan.append("## Interpretation")
plan.append("")
plan.append("process_tick is not a pure computation function. It mixes tick/price reading, alert transmission, helper calls and side-effect hints.")
plan.append("Therefore T002 must continue as progressive extraction behind the adapter, not as a direct rewrite.")
plan.append("")
plan.append("## Extraction order")
plan.append("")
plan.append("### Phase 0 - Keep boundary locked")
plan.append("")
plan.append("- Keep Core/pf_engine_v6_adapter.py as the only bridge used by capture_bridge.py.")
plan.append("- Keep Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json unchanged unless an intentional migration is documented.")
plan.append("- Keep tests/test_t002_engine_process_tick_contract.py and tests/test_t002_engine_v6_adapter.py green.")
plan.append("")
plan.append("### Phase 1 - Extract pure read/compute helpers only")
plan.append("")
plan.append("Candidate categories:")
plan.append("- TICK_PRICE")
plan.append("- FLOW_COMPUTE")
plan.append("")
plan.append("Candidate target module:")
plan.append("- Core/pf_engine_v6_core.py")
plan.append("")
plan.append("Allowed in Phase 1:")
plan.append("- stateless calculations")
plan.append("- tick/prev derived values")
plan.append("- score/force/angle helper wrappers")
plan.append("")
plan.append("Forbidden in Phase 1:")
plan.append("- DB writes")
plan.append("- send_alert calls")
plan.append("- brain mutation unless wrapped and tested")
plan.append("- dashboard/cockpit/telegram imports")
plan.append("")
plan.append("### Phase 2 - Extract alert payload construction, not sending")
plan.append("")
plan.append("Candidate target module:")
plan.append("- Core/pf_engine_v6_alert_payloads.py")
plan.append("")
plan.append("Allowed:")
plan.append("- build payload dictionaries")
plan.append("- format alert labels")
plan.append("- classify maturity / event type")
plan.append("")
plan.append("Forbidden:")
plan.append("- direct send_alert")
plan.append("- telegram import")
plan.append("- DB writes")
plan.append("")
plan.append("### Phase 3 - Wrap brain mutation")
plan.append("")
plan.append("Candidate target module:")
plan.append("- Core/pf_engine_v6_state.py")
plan.append("")
plan.append("Goal:")
plan.append("- isolate brain read/write semantics with golden tests.")
plan.append("")
plan.append("### Phase 4 - Persistence and side effects last")
plan.append("")
plan.append("Persistence, DB writes, file writes and alert transmission must stay inside legacy engine.py until all pure phases are tested.")
plan.append("")
plan.append("## Local helpers called by process_tick")
plan.append("")
if local_helpers:
    for h in local_helpers:
        plan.append("- " + h.get("name", "") + " | lines " + str(h.get("line")) + "-" + str(h.get("end_line")) + " | calls " + str(h.get("calls_from_process_tick")))
else:
    plan.append("- none detected")
plan.append("")
plan.append("## Statement map by category")
plan.append("")
for category in ["FLOW_COMPUTE", "TICK_PRICE", "BRAIN_MEMORY", "SCENE_CONTEXT", "ALERT_TRANSMISSION", "DB_OR_PERSISTENCE", "OTHER"]:
    items = lines_for_category(category)
    if not items:
        continue
    plan.append("### " + category)
    plan.append("")
    for item in items:
        plan.append("- line " + str(item.get("line")) + "-" + str(item.get("end_line")) + " | " + item.get("type", "") + " | " + item.get("preview", ""))
    plan.append("")
plan.append("## Side-effect hints to avoid in early extraction")
plan.append("")
if side_effects:
    for item in side_effects:
        plan.append("- line " + str(item.get("line")) + " | " + item.get("type", "") + " | " + item.get("text", ""))
else:
    plan.append("- none detected")
plan.append("")
plan.append("## Proposed next coding step")
plan.append("")
plan.append("Create a no-behavior-change module skeleton:")
plan.append("")
plan.append("- Core/pf_engine_v6_core.py")
plan.append("- tests/test_t002_engine_v6_core_contract.py")
plan.append("")
plan.append("Initial content should be minimal:")
plan.append("")
plan.append("1. A dataclass or plain dict helper for derived tick context.")
plan.append("2. Tests using synthetic tick-like objects.")
plan.append("3. No connection to capture_bridge yet.")
plan.append("4. No call from process_tick yet.")
plan.append("")
plan.append("This creates a safe destination for future extraction without changing runtime.")
plan.append("")
plan.append("## Stop criteria")
plan.append("")
plan.append("- Any test failure in existing T002 tests.")
plan.append("- Any new import from pf_* to cockpit_*, dashboard_* or telegram_*.")
plan.append("- Any DB write moved into a new pf_* module.")
plan.append("- Any change to process_tick signature without updating contract intentionally.")
plan.append("")
plan.append("## Verdict")
plan.append("")
plan.append("T002 is now ready for a minimal Phase 1 code patch, but only as a detached pure-helper module first.")
plan.append("Do not move process_tick logic yet.")
plan.append("")
plan_path.write_text("\n".join(plan) + "\n", encoding="utf-8")

summary = {
    "created_at": now,
    "source_map": str(latest_json.relative_to(repo)),
    "plan": str(plan_path.relative_to(repo)),
    "process_tick_line_count": pt.get("line_count"),
    "statement_count": pt.get("statement_count"),
    "category_counts": category_counts,
    "local_helper_count": len(local_helpers),
    "side_effect_count": len(side_effects),
    "recommendation": "Create detached pure-helper module pf_engine_v6_core.py before moving runtime code.",
}
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "ok": True,
    "source_map": str(latest_json),
    "plan": str(plan_path),
    "summary": str(summary_path),
    "recommendation": summary["recommendation"],
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPlan -Encoding UTF8

Log "Building extraction plan from latest internal map"
python $pythonPlan
if ($LASTEXITCODE -ne 0) {
    throw "extraction plan generation failed"
}

Remove-Item $pythonPlan -Force -ErrorAction SilentlyContinue

Log "Running T002 tests"
python -m pytest tests/test_t002_engine_process_tick_contract.py tests/test_t002_engine_v6_adapter.py -q
if ($LASTEXITCODE -ne 0) {
    throw "T002 tests failed"
}
Ok "T002 tests passed"

Log "Git diff summary"
git status --short
git diff --stat

if (Test-Path ".\scripts\auto_git_sync.ps1") {
    Log "Syncing extraction plan via auto_git_sync"
    & ".\scripts\auto_git_sync.ps1" -Message "plan(t002): define safe engine extraction phases"
} else {
    Warn "auto_git_sync.ps1 not found; leaving changes unstaged"
}

if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
    Log "Creating checkpoint"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002-C safe extraction plan"
} else {
    Warn "auto_checkpoint_claude.ps1 not found; checkpoint skipped"
}

Ok "T002-C extraction plan complete"
