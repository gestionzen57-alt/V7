param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$TaskId = "T004",
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-M] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-M dispatch close"
Log "RepoPath = $RepoPath"
Log "TaskId = $TaskId"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -8

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-M commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$dispatchPath = Join-Path $RepoPath "Docs\DISPATCH_STATUS.json"
if (!(Test-Path $dispatchPath)) {
    throw "Docs\DISPATCH_STATUS.json not found"
}

$finalContract = Join-Path $RepoPath "Docs\Contracts\T004_FINAL_DIAGNOSIS.json"
if (!(Test-Path $finalContract)) {
    throw "Docs\Contracts\T004_FINAL_DIAGNOSIS.json not found"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$dispatchPath.bak_T004M_$stamp"
Copy-Item $dispatchPath $backupPath -Force
Ok "Backup created: $backupPath"

$pythonPatch = Join-Path $RepoPath ".t004m_close_dispatch.py"

@'
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

repo = Path.cwd()
dispatch_path = repo / "Docs" / "DISPATCH_STATUS.json"
contract_path = repo / "Docs" / "Contracts" / "T004_FINAL_DIAGNOSIS.json"
report_dir = repo / "Docs" / "Reports"
report_dir.mkdir(parents=True, exist_ok=True)

task_id = "T004"
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
contract = json.loads(contract_path.read_text(encoding="utf-8"))

status_value = contract.get("recommended_dispatch_state") or "DIAGNOSED_BLOCKED_ON_CAPTURE_ROUTING_OR_SOURCE_FEED"

matches: list[dict[str, Any]] = []

def obj_mentions_task(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    text_parts = []
    for k, v in obj.items():
        if k.lower() in {"id", "task", "task_id", "code", "name", "title", "label", "description", "mission"}:
            text_parts.append(str(v))
    return task_id.lower() in " ".join(text_parts).lower()

def patch_obj(obj: dict[str, Any], path: str) -> None:
    before = dict(obj)
    obj["status"] = status_value
    obj["state"] = status_value
    obj["verdict"] = contract.get("status", "CAPTURE_ROUTING_USDJPY_ABSENT_FROM_ACTIVE_TABLES")
    obj["updated_at"] = now
    obj["last_update"] = now
    obj["owner_note"] = "Diagnosed: USDJPY thin data is capture/routing/source-feed side. No engine/scoring/dashboard patch."
    obj["next_action"] = "Operator: verify USDJPY source feed, exact broker symbol naming, Market Watch/subscription, and capture allowlist. Then rerun t004_active_insertion_symbol_delta.ps1."
    obj["evidence_contract"] = "Docs/Contracts/T004_FINAL_DIAGNOSIS.json"
    obj["evidence_report_glob"] = "Docs/Reports/T004_FINAL_DIAGNOSIS_*.md"
    obj["blocked_by"] = "USDJPY source feed / capture routing / symbol normalization"
    obj["engine_change_required"] = False
    matches.append({
        "path": path,
        "before_keys": sorted(before.keys()),
        "after_status": obj.get("status"),
        "after_verdict": obj.get("verdict"),
    })

def walk(node: Any, path: str = "$") -> None:
    if isinstance(node, dict):
        if obj_mentions_task(node):
            patch_obj(node, path)
        for k, v in list(node.items()):
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]")

walk(dispatch)

# If DISPATCH_STATUS is keyed by T004 directly.
if isinstance(dispatch, dict) and task_id in dispatch and isinstance(dispatch[task_id], dict):
    if not any(m["path"] == f"$.{task_id}" for m in matches):
        patch_obj(dispatch[task_id], f"$.{task_id}")

if not matches:
    # Do not silently mutate unknown schema; create report and fail safely.
    report_path = report_dir / f"T004_DISPATCH_CLOSE_FAILED_{stamp}.md"
    report_path.write_text(
        "# T004 Dispatch Close Failed\n\n"
        f"Date: {now}\n\n"
        "No matching T004 task object found in Docs/DISPATCH_STATUS.json.\n"
        "DISPATCH_STATUS was not modified by the Python patcher.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": False,
        "reason": "NO_T004_MATCH",
        "report": str(report_path),
    }, indent=2, ensure_ascii=False))
    raise SystemExit(2)

dispatch_path.write_text(json.dumps(dispatch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

report_path = report_dir / f"T004_DISPATCH_CLOSE_{stamp}.md"
md = []
md.append("# T004 Dispatch Close")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Result")
md.append("")
md.append("- Task: `T004`")
md.append("- Dispatch state: `" + status_value + "`")
md.append("- Final diagnosis: `" + str(contract.get("status")) + "`")
md.append("- Engine change required: `False`")
md.append("")
md.append("## Patched objects")
md.append("")
for m in matches:
    md.append("- `" + m["path"] + "` | status=`" + str(m["after_status"]) + "` | verdict=`" + str(m["after_verdict"]) + "`")
md.append("")
md.append("## Evidence")
md.append("")
md.append("- `Docs/Contracts/T004_FINAL_DIAGNOSIS.json`")
md.append("- `Docs/Reports/T004_FINAL_DIAGNOSIS_*.md`")
md.append("")
md.append("## Revalidation")
md.append("")
md.append("After source feed / routing correction:")
md.append("")
md.append("```powershell")
md.append(".\\scripts\\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10")
md.append("```")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "dispatch": str(dispatch_path),
    "report": str(report_path),
    "matches": matches,
    "status": status_value,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonPatch -Encoding UTF8

Log "Updating DISPATCH_STATUS for T004"
python $pythonPatch
if ($LASTEXITCODE -ne 0) {
    throw "T004-M dispatch update failed"
}
Remove-Item $pythonPatch -Force -ErrorAction SilentlyContinue

Log "Validating JSON"
python -m json.tool "Docs\DISPATCH_STATUS.json" | Out-Null
python -m json.tool "Docs\Contracts\T004_FINAL_DIAGNOSIS.json" | Out-Null
Ok "JSON validation passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/DISPATCH_STATUS.json",
    "scripts/t004_close_dispatch.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Reports" -Filter "T004_DISPATCH_CLOSE_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T004-M files"
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
    Warn "No staged T004-M changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "dispatch(t004): mark USDJPY thin data diagnosed"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_M_DISPATCH_CLOSE.md"

    $lastCommits = git log --oneline -8
    $content = @()
    $content += "# CHECKPOINT - T004-M dispatch close"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004 dispatch close"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- T004 marked as diagnosed/blocked on capture routing or source feed."
    $content += "- Runtime unchanged."
    $content += "- DB not written."
    $content += "- Engine change not required."
    $content += "- Dashboard runtime state restored before commit if needed."
    $content += ""
    $content += "## Current git log"
    $content += ""
    $content += '```text'
    $content += $lastCommits
    $content += '```'
    $content += ""
    $content += "## Revalidation"
    $content += ""
    $content += "After feed/routing correction, rerun t004_active_insertion_symbol_delta.ps1."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-M dispatch close"
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

Ok "T004-M dispatch close complete"
Log "Final status"
git status --short
git log --oneline -8
