param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$NoGit,
    [switch]$NoCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Info($m) { Write-Host ("[T002-SURFACE] " + $m) }
function Ok($m) { Write-Host ("[OK] " + $m) }
function Warn($m) { Write-Host ("[WARN] " + $m) }
function Fail($m) { Write-Host ("[FAIL] " + $m); exit 1 }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Info "PowerFlow V7.6.7 T002 runtime surface audit"
Info ("RepoPath = " + $RepoPath)

if (-not (Test-Path ".git")) { Fail "Not a git repository" }
if (-not (Test-Path "Core\engine.py")) { Fail "Core\engine.py not found" }

Info "Git preflight"
git status --short
git branch --show-current
git log --oneline -5

if (Test-Path "Core\dashboard_data.json") {
    $dashStatus = git status --short -- "Core/dashboard_data.json"
    if ($dashStatus) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before audit commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$AuditDir = Join-Path $RepoPath "Docs\Audits"
New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null

$TempPy = Join-Path $RepoPath ".t002_runtime_surface_audit.py"
$PythonCode = @'
import argparse
import ast
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys

EXCLUDED_PARTS = {
    ".git", "archive", "archives", "backup", "backups", "avant",
    "__pycache__", ".venv", "venv", "env", "node_modules"
}

REFERENCE_PATTERNS = [
    "from engine import process_tick",
    "from engine import",
    "import engine",
    "engine.process_tick",
    "process_tick(",
    "engine.py",
    "scheduler_powerflow.py",
    "scheduler_powerflow_turbo_wrapper.py",
]

ENGINE_SIGNAL_PATTERNS = [
    "sqlite3.connect", "INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE",
    "open(", "Path(", "json.dump", "json.dumps", "output/", "output\\",
    "behavioral", "bus", "alert", "tick", "force", "snapshot", "process_tick",
]


def is_active_file(path: Path, repo: Path) -> bool:
    rel_parts = [p.lower() for p in path.relative_to(repo).parts]
    return not any(part in EXCLUDED_PARTS for part in rel_parts)


def rel(path: Path, repo: Path) -> str:
    return str(path.relative_to(repo)).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def one_line_signature(lines, node):
    idx = node.lineno - 1
    collected = []
    paren_balance = 0
    for j in range(idx, min(len(lines), idx + 12)):
        s = lines[j].strip()
        collected.append(s)
        paren_balance += s.count("(") - s.count(")")
        if s.endswith(":") and paren_balance <= 0:
            break
    sig = " ".join(collected)
    return re.sub(r"\s+", " ", sig)[:240]


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return (base + "." if base else "") + node.attr
    return ""


def extract_engine_surface(engine_path: Path):
    text = read_text(engine_path)
    lines = text.splitlines()
    tree = ast.parse(text)

    imports = []
    functions = []
    classes = []
    main_blocks = []
    calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = ", ".join([a.name + ((" as " + a.asname) if a.asname else "") for a in node.names])
            imports.append({"line": node.lineno, "import": "import " + names})
        elif isinstance(node, ast.ImportFrom):
            names = ", ".join([a.name + ((" as " + a.asname) if a.asname else "") for a in node.names])
            module = node.module or ""
            imports.append({"line": node.lineno, "import": "from " + module + " import " + names})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "signature": one_line_signature(lines, node),
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno)})
        elif isinstance(node, ast.If):
            test_text = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
            if "__name__" in test_text and "__main__" in test_text:
                main_blocks.append({"line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno), "test": test_text})
        elif isinstance(node, ast.Call):
            nm = call_name(node.func)
            if nm:
                calls.append({"line": getattr(node, "lineno", 0), "call": nm})

    process_tick = [f for f in functions if f["name"] == "process_tick"]

    signal_lines = []
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        for pat in ENGINE_SIGNAL_PATTERNS:
            if pat.lower() in low:
                signal_lines.append({"line": i, "pattern": pat, "text": line.strip()[:220]})
                break

    return {
        "line_count": len(lines),
        "imports": imports,
        "functions": functions,
        "classes": classes,
        "main_blocks": main_blocks,
        "process_tick": process_tick,
        "calls": calls,
        "signal_lines": signal_lines,
    }


def scan_references(repo: Path, py_files):
    refs = []
    for path in py_files:
        try:
            lines = read_text(path).splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            for pat in REFERENCE_PATTERNS:
                if pat in line:
                    refs.append({"file": rel(path, repo), "line": i, "pattern": pat, "text": line.strip()[:240]})
                    break
    return refs


def compile_file(path: Path):
    p = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    return {"ok": p.returncode == 0, "stdout": p.stdout, "stderr": p.stderr}


def write_report(repo: Path, data):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    out = repo / "Docs" / "Audits" / ("T002_RUNTIME_SURFACE_AUDIT_" + stamp + ".md")
    lines = []
    add = lines.append
    add("# T002 Runtime Surface Audit")
    add("")
    add("Date UTC: " + now.isoformat().replace("+00:00", "Z"))
    add("Repo: " + str(repo))
    add("")
    add("## Executive finding")
    add("")
    if data["surface"]["process_tick"]:
        add("- Core/engine.py exposes process_tick: YES")
        add("- process_tick signature: " + data["surface"]["process_tick"][0]["signature"])
    else:
        add("- Core/engine.py exposes process_tick: NO")
    add("- Hard runtime caller count: " + str(len(data["hard_callers"])))
    if data["hard_callers"]:
        add("- Main hard caller: " + data["hard_callers"][0]["file"] + ":" + str(data["hard_callers"][0]["line"]))
    add("- Recommendation: T002 must start as an adapter/extraction plan, not a blind refactor.")
    add("")

    add("## Hard runtime callers")
    add("")
    if data["hard_callers"]:
        for r in data["hard_callers"]:
            add("- " + r["file"] + ":" + str(r["line"]) + " | " + r["text"])
    else:
        add("- None found")
    add("")

    add("## Engine metrics")
    add("")
    add("- Lines: " + str(data["surface"]["line_count"]))
    add("- Imports: " + str(len(data["surface"]["imports"])))
    add("- Functions: " + str(len(data["surface"]["functions"])))
    add("- Classes: " + str(len(data["surface"]["classes"])))
    add("- Main blocks: " + str(len(data["surface"]["main_blocks"])))
    add("")

    add("## Functions")
    add("")
    for f in data["surface"]["functions"]:
        add("- line " + str(f["line"]) + "-" + str(f["end_line"]) + " | " + f["signature"])
    add("")

    add("## Classes")
    add("")
    if data["surface"]["classes"]:
        for c in data["surface"]["classes"]:
            add("- line " + str(c["line"]) + "-" + str(c["end_line"]) + " | class " + c["name"])
    else:
        add("- None")
    add("")

    add("## Imports")
    add("")
    for imp in data["surface"]["imports"]:
        add("- line " + str(imp["line"]) + " | " + imp["import"])
    add("")

    add("## Main block")
    add("")
    if data["surface"]["main_blocks"]:
        for b in data["surface"]["main_blocks"]:
            add("- line " + str(b["line"]) + "-" + str(b["end_line"]) + " | " + b["test"])
    else:
        add("- None")
    add("")

    add("## Signal lines in Core/engine.py")
    add("")
    for s in data["surface"]["signal_lines"][:120]:
        add("- line " + str(s["line"]) + " | " + s["pattern"] + " | " + s["text"])
    if len(data["surface"]["signal_lines"]) > 120:
        add("- Truncated: " + str(len(data["surface"]["signal_lines"]) - 120) + " more signal lines")
    add("")

    add("## Reference scan")
    add("")
    for r in data["references"][:200]:
        add("- " + r["file"] + ":" + str(r["line"]) + " | " + r["pattern"] + " | " + r["text"])
    if len(data["references"]) > 200:
        add("- Truncated: " + str(len(data["references"]) - 200) + " more references")
    add("")

    add("## Syntax check")
    add("")
    if data["compile"]["ok"]:
        add("- PASS py_compile Core/engine.py")
    else:
        add("- FAIL py_compile Core/engine.py")
        add("- stderr: " + data["compile"].get("stderr", "").replace("\n", " | ")[:1000])
    add("")

    add("## T002 decision")
    add("")
    add("T002 should be renamed from pf_engine.py refactor to Core/engine.py legacy boundary audit and extraction plan.")
    add("")
    add("Minimal safe sequence:")
    add("")
    add("1. Freeze the process_tick contract used by capture_bridge.py.")
    add("2. Add a small contract test that imports engine.process_tick and records its signature.")
    add("3. Identify side effects inside process_tick: DB writes, output files, alert bus writes.")
    add("4. Extract pure helpers only if they are not called directly by capture_bridge.py.")
    add("5. Keep engine.py as compatibility shell until capture_bridge.py is intentionally migrated.")
    add("")
    add("## Technical risks")
    add("")
    add("- Risk of breaking capture_bridge.py if process_tick signature changes.")
    add("- Risk of hidden side effects if engine.py writes DB/output/bus during tick processing.")
    add("- Risk of circular dependency if new pf_* module imports capture_* or cockpit_*.")
    add("- Risk of over-refactor while scheduler currently relies on wrappers/orchestrators.")
    add("")
    add("## PowerFlow rule")
    add("")
    add("No engine behavior change before the process_tick contract is frozen and tested.")
    add("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    engine_path = repo / "Core" / "engine.py"

    py_files = [p for p in repo.rglob("*.py") if is_active_file(p, repo)]
    surface = extract_engine_surface(engine_path)
    refs = scan_references(repo, py_files)

    hard_pats = {"from engine import process_tick", "from engine import", "import engine", "engine.process_tick"}
    hard_callers = [r for r in refs if r["pattern"] in hard_pats and r["file"] != "Core/engine.py"]

    comp = compile_file(engine_path)
    data = {
        "active_py_count": len(py_files),
        "surface": surface,
        "references": refs,
        "hard_callers": hard_callers,
        "compile": comp,
    }

    out = write_report(repo, data)
    print(json.dumps({
        "ok": True,
        "report": str(out),
        "active_py_count": len(py_files),
        "hard_callers": hard_callers[:20],
        "process_tick_found": bool(surface["process_tick"]),
        "compile_ok": comp["ok"],
    }, indent=2))

    if not comp["ok"]:
        sys.exit(2)

if __name__ == "__main__":
    main()
'@

Set-Content -Path $TempPy -Value $PythonCode -Encoding UTF8

Info "Running Python runtime surface audit"
python $TempPy --repo $RepoPath
if ($LASTEXITCODE -ne 0) { Fail "Python audit failed" }

if (Test-Path $TempPy) { Remove-Item $TempPy -Force }

Info "Git diff summary"
git status --short
git diff --stat

if (-not $NoGit) {
    if (Test-Path "scripts\auto_git_sync.ps1") {
        Info "Syncing runtime surface audit via auto_git_sync"
        & ".\scripts\auto_git_sync.ps1" -Message "audit(t002): inspect engine runtime surface"
    } else {
        Warn "auto_git_sync.ps1 not found. Manual git sync required."
    }
}

if (-not $NoCheckpoint) {
    if (Test-Path "scripts\auto_checkpoint_claude.ps1") {
        Info "Creating checkpoint"
        & ".\scripts\auto_checkpoint_claude.ps1" -Focus "T002 runtime surface audit"
    } else {
        Warn "auto_checkpoint_claude.ps1 not found. Manual checkpoint required."
    }
}

Ok "T002 runtime surface audit complete"
