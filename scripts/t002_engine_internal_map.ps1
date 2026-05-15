param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T002-INTERNAL] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T002-B engine internal map"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before audit commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t002_engine_internal_map.py"

@'
from __future__ import annotations

import ast
import datetime as dt
import json
from collections import Counter
from pathlib import Path

repo = Path.cwd()
engine_path = repo / "Core" / "engine.py"
audit_dir = repo / "Docs" / "Audits"
audit_dir.mkdir(parents=True, exist_ok=True)

if not engine_path.exists():
    raise SystemExit("Core/engine.py not found")

text = engine_path.read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()
tree = ast.parse(text)

def src(node):
    segment = ast.get_source_segment(text, node)
    if segment is None:
        start = max(getattr(node, "lineno", 1) - 1, 0)
        end = getattr(node, "end_lineno", getattr(node, "lineno", 1))
        segment = "\n".join(lines[start:end])
    return segment

def one_line(s):
    return " ".join(s.strip().split())[:180]

def call_name(node):
    f = node.func
    try:
        return ast.unparse(f)
    except Exception:
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return f.attr
        return type(f).__name__

def classify_statement(source_line):
    s = source_line.lower()
    if any(k in s for k in ["sqlite", ".execute(", ".commit(", "insert ", "update ", "delete ", "db.", "save_", "load_"]):
        return "DB_OR_PERSISTENCE"
    if any(k in s for k in ["send_alert", "alert", "telegram", "notify"]):
        return "ALERT_TRANSMISSION"
    if any(k in s for k in ["scene", "zone", "node", "regime", "film"]):
        return "SCENE_CONTEXT"
    if any(k in s for k in ["brain", "memory", "state"]):
        return "BRAIN_MEMORY"
    if any(k in s for k in ["force", "score", "momentum", "angle", "delta", "spread"]):
        return "FLOW_COMPUTE"
    if any(k in s for k in ["tick", "prev", "bid", "ask", "price"]):
        return "TICK_PRICE"
    if any(k in s for k in ["print(", "logging", "logger"]):
        return "LOGGING"
    return "OTHER"

top_functions = []
top_classes = []
top_imports = []
process_tick = None

for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        top_imports.append({"line": node.lineno, "text": one_line(src(node))})
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        item = {
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", None),
            "args": [a.arg for a in node.args.args],
        }
        top_functions.append(item)
        if node.name == "process_tick":
            process_tick = node
    elif isinstance(node, ast.ClassDef):
        top_classes.append({"name": node.name, "line": node.lineno, "end_line": getattr(node, "end_lineno", None)})

if process_tick is None:
    raise SystemExit("process_tick not found")

pt_source = src(process_tick)
pt_lines = pt_source.splitlines()

calls = Counter()
for node in ast.walk(process_tick):
    if isinstance(node, ast.Call):
        calls[call_name(node)] += 1

assigned = Counter()
for node in ast.walk(process_tick):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                assigned[target.id] += 1
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        assigned[elt.id] += 1
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        assigned[node.target.id] += 1
    elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
        assigned[node.target.id] += 1

statement_map = []
category_counts = Counter()

for stmt in process_tick.body:
    statement_src = one_line(src(stmt))
    category = classify_statement(statement_src)
    category_counts[category] += 1
    statement_map.append({
        "type": type(stmt).__name__,
        "line": stmt.lineno,
        "end_line": getattr(stmt, "end_lineno", None),
        "category": category,
        "preview": statement_src,
    })

side_effect_patterns = {
    "DB execute": ".execute(",
    "DB commit": ".commit(",
    "File open": "open(",
    "Path write": "write_text",
    "JSON dump": "json.dump",
    "Print": "print(",
    "Alert call": "send_alert",
    "List append": ".append(",
}
side_effects = []
for idx, line in enumerate(lines[getattr(process_tick, "lineno", 1)-1:getattr(process_tick, "end_lineno", getattr(process_tick, "lineno", 1))], process_tick.lineno):
    for label, pat in side_effect_patterns.items():
        if pat in line:
            side_effects.append({"line": idx, "type": label, "text": line.strip()})

# Find helper functions called by process_tick and defined in same file.
defined = {f["name"]: f for f in top_functions}
local_helpers = []
for name, count in calls.most_common():
    base = name.split(".")[-1]
    if base in defined and base != "process_tick":
        helper = dict(defined[base])
        helper["calls_from_process_tick"] = count
        local_helpers.append(helper)

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
json_path = audit_dir / ("T002_ENGINE_INTERNAL_MAP_" + stamp + ".json")
md_path = audit_dir / ("T002_ENGINE_INTERNAL_MAP_" + stamp + ".md")

data = {
    "created_at": now,
    "engine_file": "Core/engine.py",
    "process_tick": {
        "line": process_tick.lineno,
        "end_line": getattr(process_tick, "end_lineno", None),
        "line_count": len(pt_lines),
        "args": [a.arg for a in process_tick.args.args],
        "statement_count": len(statement_map),
        "category_counts": dict(category_counts),
        "top_calls": calls.most_common(40),
        "assigned_names": assigned.most_common(80),
        "side_effects": side_effects,
        "statement_map": statement_map,
        "local_helpers": local_helpers,
    },
    "top_level": {
        "imports": top_imports,
        "functions": top_functions,
        "classes": top_classes,
    }
}
json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

md = []
md.append("# T002-B Engine Internal Map")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Executive finding")
md.append("")
md.append("- Target: Core/engine.py")
md.append("- Runtime callable: process_tick")
md.append("- process_tick lines: " + str(process_tick.lineno) + "-" + str(getattr(process_tick, "end_lineno", "")))
md.append("- process_tick line count: " + str(len(pt_lines)))
md.append("- process_tick args: " + ", ".join([a.arg for a in process_tick.args.args]))
md.append("")
md.append("## Statement categories inside process_tick")
md.append("")
for category, count in category_counts.most_common():
    md.append("- " + category + ": " + str(count))
md.append("")
md.append("## Top calls inside process_tick")
md.append("")
for name, count in calls.most_common(30):
    md.append("- " + name + ": " + str(count))
md.append("")
md.append("## Local helpers called by process_tick")
md.append("")
if local_helpers:
    for h in local_helpers:
        md.append("- " + h["name"] + " | lines " + str(h["line"]) + "-" + str(h.get("end_line") or "") + " | calls " + str(h["calls_from_process_tick"]))
else:
    md.append("- none")
md.append("")
md.append("## Side-effect hints")
md.append("")
if side_effects:
    for sfx in side_effects[:80]:
        md.append("- line " + str(sfx["line"]) + " | " + sfx["type"] + " | " + sfx["text"])
    if len(side_effects) > 80:
        md.append("- truncated: " + str(len(side_effects) - 80) + " more")
else:
    md.append("- none detected")
md.append("")
md.append("## process_tick statement map")
md.append("")
for item in statement_map:
    md.append("- line " + str(item["line"]) + "-" + str(item.get("end_line") or "") + " | " + item["category"] + " | " + item["type"] + " | " + item["preview"])
md.append("")
md.append("## Recommended extraction order")
md.append("")
md.append("1. Do not move process_tick yet. Keep pf_engine_v6_adapter as the stable boundary.")
md.append("2. Extract pure helper computations first: force, score, price/tick transforms.")
md.append("3. Extract alert formatting after helper computations are stable.")
md.append("4. Extract DB or persistence last because it carries side effects.")
md.append("5. Add a targeted test before each extraction.")
md.append("")
md.append("## Technical risks")
md.append("")
md.append("- Import side effects from engine.py remain active.")
md.append("- process_tick may mix compute, memory, alerting and persistence.")
md.append("- Moving DB writes before tests risks silent runtime drift.")
md.append("- Moving send_alert before tests risks alert payload drift.")
md.append("")
md.append("## Files")
md.append("")
md.append("- JSON map: " + str(json_path.relative_to(repo)))
md.append("- Markdown report: " + str(md_path.relative_to(repo)))
md.append("")
md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "json": str(json_path),
    "report": str(md_path),
    "process_tick_line_count": len(pt_lines),
    "statement_count": len(statement_map),
    "category_counts": dict(category_counts),
    "local_helper_count": len(local_helpers),
    "side_effect_count": len(side_effects),
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running engine internal map audit"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "engine internal map audit failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running syntax and T002 tests"
python -m py_compile Core\engine.py Core\pf_engine_v6_adapter.py Core\capture_bridge.py
if ($LASTEXITCODE -ne 0) {
    throw "syntax check failed"
}

python -m pytest tests/test_t002_engine_process_tick_contract.py tests/test_t002_engine_v6_adapter.py -q
if ($LASTEXITCODE -ne 0) {
    throw "T002 tests failed"
}
Ok "Syntax and T002 tests passed"

Log "Git diff summary"
git status --short
git diff --stat

if (Test-Path ".\scripts\auto_git_sync.ps1") {
    Log "Syncing internal map via auto_git_sync"
    & ".\scripts\auto_git_sync.ps1" -Message "audit(t002): map engine process_tick internals"
} else {
    Warn "auto_git_sync.ps1 not found; leaving changes unstaged"
}

if (Test-Path ".\scripts\auto_checkpoint_claude.ps1") {
    Log "Creating checkpoint"
    & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002-B engine internal map"
} else {
    Warn "auto_checkpoint_claude.ps1 not found; checkpoint skipped"
}

Ok "T002-B engine internal map complete"
