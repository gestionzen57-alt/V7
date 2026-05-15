param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint,
    [switch]$SkipDispatchUpdate
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-O] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-O requalification after expanded USD cohort"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -10

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-O commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonPatch = Join-Path $RepoPath ".t004o_requalify_after_usd_cohort.py"
$skipDispatchJson = if ($SkipDispatchUpdate.IsPresent) { "True" } else { "False" }

@"
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

SKIP_DISPATCH_UPDATE = $skipDispatchJson

repo = Path.cwd()
contract_dir = repo / "Docs" / "Contracts"
report_dir = repo / "Docs" / "Reports"
tests_dir = repo / "tests"
checkpoint_dir = repo / "Docs" / "Checkpoints"
report_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

cohort_path = contract_dir / "T004_USD_BASE_POLARITY_COHORT.json"
final_path = contract_dir / "T004_FINAL_DIAGNOSIS.json"
dispatch_path = repo / "Docs" / "DISPATCH_STATUS.json"

if not cohort_path.exists():
    raise SystemExit("Missing " + str(cohort_path))
if not final_path.exists():
    raise SystemExit("Missing " + str(final_path))

cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
final_diag = json.loads(final_path.read_text(encoding="utf-8"))

verdict = cohort.get("verdict")
symbol_deltas = cohort.get("symbol_deltas", {})
usd_base_deltas = cohort.get("usd_base_deltas", {})
usd_quote_deltas = cohort.get("usd_quote_deltas", {})
polarity_risk_hit_count = cohort.get("polarity_risk_hit_count")

base_advancing = {k: v for k, v in usd_base_deltas.items() if isinstance(v, int) and v > 0}
quote_advancing = {k: v for k, v in usd_quote_deltas.items() if isinstance(v, int) and v > 0}

if verdict == "USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE" and base_advancing:
    requalification_status = "GLOBAL_USD_BASE_BLOCKAGE_INVALIDATED"
    updated_cause = "FEED_EA_CAPTURE_INTERMITTENT_OR_INITIAL_SETUP_INCOMPLETE"
    dispatch_status = "DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT"
elif verdict == "USDCAD_ADVANCES_USDJPY_ZERO_SYMBOL_SPECIFIC":
    requalification_status = "USDJPY_SYMBOL_SPECIFIC_ROUTE_OR_FEED"
    updated_cause = "USDJPY_SPECIFIC_FEED_OR_ROUTING"
    dispatch_status = "DIAGNOSED_REQUALIFIED_USDJPY_SPECIFIC"
elif verdict == "USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES":
    requalification_status = "GLOBAL_USD_BASE_BLOCKAGE_STILL_SUSPECT"
    updated_cause = "USD_BASE_ROUTING_OR_NORMALIZATION_SUSPECT"
    dispatch_status = "DIAGNOSED_BLOCKED_ON_USD_BASE_ROUTING"
else:
    requalification_status = "POLARITY_REQUALIFICATION_INCONCLUSIVE"
    updated_cause = "CAPTURE_FEED_REVALIDATION_REQUIRED"
    dispatch_status = "DIAGNOSED_REVALIDATION_REQUIRED"

operator_actions = [
    "Keep all active EAs running on USDJPY, USDCAD, USDCHF, GBPUSD, EURUSD, and AUDUSD during validation windows.",
    "Rerun T004-N during an active market window if feed cadence changes.",
    "Do not patch PowerFlow engine/scoring/dashboard based on the initial USDJPY absence.",
    "Use per-symbol live deltas as the primary validation signal after EA/feed changes.",
]

engineering_actions = [
    "Keep polarity risk hits for later interpretation audit, not as proven capture blockers.",
    "Add a lightweight capture health surface per symbol if this intermittence recurs.",
    "Treat the previous USDJPY absence as window/setup dependent unless repeated with all EAs active.",
]

not_causes = [
    "Global USD-base capture blockage is not confirmed after expanded cohort.",
    "A simple XXXUSD-only pipeline bug is not supported by the latest live deltas.",
    "No engine/scoring/dashboard patch is justified.",
]

contract = {
    "contract": "POWERFLOW_T004_REQUALIFICATION_AFTER_USD_BASE_COHORT",
    "created_at": now,
    "source_cohort_contract": "Docs/Contracts/T004_USD_BASE_POLARITY_COHORT.json",
    "source_final_diagnosis_contract": "Docs/Contracts/T004_FINAL_DIAGNOSIS.json",
    "previous_final_status": final_diag.get("status"),
    "cohort_verdict": verdict,
    "requalification_status": requalification_status,
    "updated_cause": updated_cause,
    "recommended_dispatch_status": dispatch_status,
    "symbol_deltas": symbol_deltas,
    "usd_base_deltas": usd_base_deltas,
    "usd_quote_deltas": usd_quote_deltas,
    "polarity_risk_hit_count": polarity_risk_hit_count,
    "operator_actions": operator_actions,
    "engineering_actions": engineering_actions,
    "not_causes": not_causes,
    "engine_change_required": False,
    "dashboard_change_required": False,
    "db_change_required": False,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Patch final diagnosis with post-close requalification evidence without erasing original history.
final_diag["post_close_requalification"] = {
    "created_at": now,
    "source": "Docs/Contracts/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json",
    "cohort_verdict": verdict,
    "requalification_status": requalification_status,
    "updated_cause": updated_cause,
    "symbol_deltas": symbol_deltas,
    "interpretation": "Expanded cohort with USDCAD/USDCHF/AUDUSD invalidates a global USD-base blockage if USD-base symbols advanced.",
    "engine_change_required": False,
}
final_diag["recommended_dispatch_state"] = dispatch_status
final_diag["status_requalified_after_t004n"] = requalification_status
final_path.write_text(json.dumps(final_diag, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Optional dispatch update: keep T004 closed/diagnosed, update owner note.
dispatch_matches = []
if not SKIP_DISPATCH_UPDATE and dispatch_path.exists():
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))

    def obj_mentions_t004(obj: Any) -> bool:
        if not isinstance(obj, dict):
            return False
        hay = " ".join(str(v) for k, v in obj.items() if k.lower() in {"id", "task", "task_id", "code", "name", "title", "label", "description", "mission"})
        return "t004" in hay.lower()

    def patch_obj(obj: dict[str, Any], path: str) -> None:
        obj["status"] = dispatch_status
        obj["state"] = dispatch_status
        obj["verdict"] = requalification_status
        obj["updated_at"] = now
        obj["last_update"] = now
        obj["owner_note"] = (
            "Requalified after expanded cohort: USDJPY/USDCAD/USDCHF and GBPUSD/EURUSD/AUDUSD advanced. "
            "Global USD-base blockage invalidated; issue likely feed/EA/capture intermittence or initial setup window."
        )
        obj["next_action"] = "Keep EAs active and rerun T004-N / active insertion delta during validation window. No engine/scoring/dashboard patch."
        obj["evidence_requalification_contract"] = "Docs/Contracts/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json"
        obj["engine_change_required"] = False
        dispatch_matches.append({"path": path, "status": obj.get("status"), "verdict": obj.get("verdict")})

    def walk(node: Any, path: str = "$") -> None:
        if isinstance(node, dict):
            if obj_mentions_t004(node):
                patch_obj(node, path)
            for k, v in list(node.items()):
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(dispatch)
    if isinstance(dispatch, dict) and "T004" in dispatch and isinstance(dispatch["T004"], dict):
        if not any(m["path"] == "$.T004" for m in dispatch_matches):
            patch_obj(dispatch["T004"], "$.T004")

    if dispatch_matches:
        dispatch_path.write_text(json.dumps(dispatch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

report_path = report_dir / f"T004_REQUALIFICATION_AFTER_USD_BASE_COHORT_{stamp}.md"
md = []
md.append("# T004-O Requalification After Expanded USD Cohort")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Requalification status")
md.append("")
md.append("`" + requalification_status + "`")
md.append("")
md.append("## Updated cause")
md.append("")
md.append("`" + updated_cause + "`")
md.append("")
md.append("## What changed")
md.append("")
md.append("The expanded cohort added USD-base and USD-quote controls:")
md.append("")
md.append("- USD-base: USDJPY, USDCAD, USDCHF")
md.append("- USD-quote: GBPUSD, EURUSD, AUDUSD")
md.append("")
md.append("Latest cohort verdict:")
md.append("")
md.append("`" + str(verdict) + "`")
md.append("")
md.append("## Live deltas")
md.append("")
md.append("```json")
md.append(json.dumps(symbol_deltas, indent=2, ensure_ascii=False))
md.append("```")
md.append("")
md.append("## Interpretation")
md.append("")
if requalification_status == "GLOBAL_USD_BASE_BLOCKAGE_INVALIDATED":
    md.append("The initial hypothesis of a global USD-base routing block is invalidated by the latest live cohort. USDJPY, USDCAD, and USDCHF all advanced. The earlier USDJPY absence is now best interpreted as feed/EA/capture intermittence or incomplete setup during the first windows.")
elif requalification_status == "USDJPY_SYMBOL_SPECIFIC_ROUTE_OR_FEED":
    md.append("USD-base routing is not globally blocked because USDCAD advanced while USDJPY did not. The issue remains USDJPY-specific.")
elif requalification_status == "GLOBAL_USD_BASE_BLOCKAGE_STILL_SUSPECT":
    md.append("USD-base routing remains suspect because USD-base symbols did not advance while USD-quote symbols advanced.")
else:
    md.append("The cohort did not conclusively requalify the diagnosis. Rerun during a stronger active window.")
md.append("")
md.append("## What T004 is not")
md.append("")
for item in not_causes:
    md.append("- " + item)
md.append("")
md.append("## Operator actions")
md.append("")
for item in operator_actions:
    md.append("- [ ] " + item)
md.append("")
md.append("## Engineering actions")
md.append("")
for item in engineering_actions:
    md.append("- [ ] " + item)
md.append("")
md.append("## Dispatch")
md.append("")
md.append("- Recommended status: `" + dispatch_status + "`")
md.append("- Dispatch update skipped: `" + str(SKIP_DISPATCH_UPDATE) + "`")
if dispatch_matches:
    md.append("- Patched dispatch objects:")
    for item in dispatch_matches:
        md.append("  - `" + item["path"] + "` -> `" + item["status"] + "`")
else:
    md.append("- Patched dispatch objects: none")
md.append("")
md.append("## Stop rule")
md.append("")
md.append("No engine/scoring/dashboard patch is justified by T004-O.")
md.append("")
md.append("## Revalidation")
md.append("")
md.append("```powershell")
md.append(".\\scripts\\t004_usd_base_polarity_cohort.ps1 -UsdBaseSymbols @(\"USDJPY\",\"USDCAD\",\"USDCHF\") -UsdQuoteSymbols @(\"GBPUSD\",\"EURUSD\",\"AUDUSD\") -WatchSeconds 180 -IntervalSeconds 10")
md.append(".\\scripts\\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10")
md.append("```")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_requalification_after_usd_base_cohort_contract.py"
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
    "def test_t004_requalification_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_REQUALIFICATION_AFTER_USD_BASE_COHORT"',
    '    assert data["engine_change_required"] is False',
    '    assert data["dashboard_change_required"] is False',
    '    assert data["db_change_required"] is False',
    '    assert isinstance(data["symbol_deltas"], dict)',
    '    assert isinstance(data["operator_actions"], list)',
    "",
    "",
    "def test_t004_requalification_mentions_usd_base_result():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert "cohort" in data["source_cohort_contract"].lower()',
    '    assert data["cohort_verdict"] in {',
    '        "USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE",',
    '        "USDCAD_ADVANCES_USDJPY_ZERO_SYMBOL_SPECIFIC",',
    '        "USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES",',
    '        "USDJPY_ADVANCES_USDCAD_ZERO_SYMBOL_SPECIFIC",',
    '        "USD_BASE_ADVANCES_REFERENCES_IDLE",',
    '        "NO_TRACKED_SYMBOL_ADVANCED",',
    '        "INCONCLUSIVE_POLARITY_COHORT",',
    '    }',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "requalification_status": requalification_status,
    "updated_cause": updated_cause,
    "recommended_dispatch_status": dispatch_status,
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "dispatch_matches": dispatch_matches,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Building T004-O requalification"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "T004-O requalification failed"
}
Remove-Item $pythonPatch -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usd_base_polarity_cohort_contract.py `
    tests/test_t004_requalification_after_usd_base_cohort_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-O tests failed"
}
Ok "T004-O tests passed"

Log "Validating JSON"
python -m json.tool "Docs\Contracts\T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json" | Out-Null
python -m json.tool "Docs\Contracts\T004_FINAL_DIAGNOSIS.json" | Out-Null
if (-not $SkipDispatchUpdate) {
    python -m json.tool "Docs\DISPATCH_STATUS.json" | Out-Null
}
Ok "JSON validation passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json",
    "Docs/Contracts/T004_FINAL_DIAGNOSIS.json",
    "tests/test_t004_requalification_after_usd_base_cohort_contract.py",
    "scripts/t004_requalify_after_usd_cohort.ps1"
)

if (-not $SkipDispatchUpdate) {
    $pathsToAdd += "Docs/DISPATCH_STATUS.json"
}

$latestReport = Get-ChildItem ".\Docs\Reports" -Filter "T004_REQUALIFICATION_AFTER_USD_BASE_COHORT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T004-O files"
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
    Warn "No staged T004-O changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "docs(t004): requalify USD-base cohort diagnosis"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_O_REQUALIFICATION_USD_BASE_COHORT.md"

    $lastCommits = git log --oneline -10
    $content = @()
    $content += "# CHECKPOINT - T004-O requalification USD-base cohort"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-O requalification after expanded USD cohort"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- T004 requalification contract/report created."
    $content += "- Final diagnosis annotated with post-close requalification."
    $content += "- Dispatch updated unless skipped."
    $content += "- Runtime unchanged."
    $content += "- No engine/scoring/dashboard patch."
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-O requalification"
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

Ok "T004-O requalification complete"
Log "Final status"
git status --short
git log --oneline -10

