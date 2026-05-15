param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-B] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-B capture DB path audit"
Log "RepoPath = $RepoPath"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$ownRecovery = "scripts\t004_recover_index_lock_and_commit.ps1"
if (Test-Path $ownRecovery) {
    Warn "Removing local-only T004 recovery script residue: $ownRecovery"
    Remove-Item $ownRecovery -Force
    Ok "Removed $ownRecovery"
}

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-B commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004b_capture_db_path_audit.py"

@'
from __future__ import annotations

import ast
import datetime as dt
import json
from pathlib import Path
import re
import sqlite3

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

candidate_db_paths = [
    repo / "powerflow.db",
    repo / "Core" / "powerflow.db",
    repo / "data" / "powerflow.db",
    repo / "DB" / "powerflow.db",
    repo / "db" / "powerflow.db",
]

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path)

def db_summary(path: Path) -> dict:
    item = {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "tables": [],
        "total_rows": None,
        "error": None,
    }
    if not path.exists():
        return item
    try:
        uri = "file:" + str(path).replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        try:
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            total = 0
            for table in tables:
                try:
                    n = con.execute('SELECT COUNT(*) AS n FROM "' + table.replace('"', '""') + '"').fetchone()["n"]
                except Exception:
                    n = None
                if isinstance(n, int):
                    total += n
                item["tables"].append({"table": table, "rows": n})
            item["total_rows"] = total
        finally:
            con.close()
    except Exception as exc:
        item["error"] = str(exc)
    return item

db_candidates = [db_summary(p) for p in candidate_db_paths]

# Also discover every .db file under repo, excluding .git and archives/backups.
excluded_parts = {".git", "__pycache__", ".venv", "venv", "Archive", "backups", "backup", "AVANT"}
discovered_dbs = []
for path in repo.rglob("*.db"):
    parts = set(path.relative_to(repo).parts)
    if parts & excluded_parts:
        continue
    if path not in candidate_db_paths:
        discovered_dbs.append(db_summary(path))

# Inspect code for DB path/insertion/capture routing.
patterns = [
    "powerflow.db",
    "sqlite3.connect",
    "connect(",
    "INSERT INTO",
    "CREATE TABLE",
    "force_snapshots",
    "bars_m1",
    "capture_bridge",
    "DB_PATH",
    "database",
    "commit(",
    "execute(",
    "USDJPY",
    "symbols",
]
code_findings = []
core_roots = [repo / "Core", repo / "scripts"]
for root in core_roots:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".ps1", ".json", ".md", ".txt", ".log"}:
            continue
        rel_path = rel(path)
        if any(part in rel_path for part in ["__pycache__", ".venv", "Archive", "backup"]):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lines = text.splitlines()
        hits = []
        for i, line in enumerate(lines, 1):
            lower = line.lower()
            for pat in patterns:
                if pat.lower() in lower:
                    hits.append({"line": i, "pattern": pat, "text": line.strip()[:220]})
        if hits:
            code_findings.append({"file": rel_path, "hits": hits[:80]})

# AST focused scan for assignments and calls in key files.
key_files = [
    repo / "Core" / "capture_bridge.py",
    repo / "Core" / "db.py",
    repo / "Core" / "system_config.py",
    repo / "Core" / "pf_multi_symbol_db.py",
    repo / "Core" / "capture_bridge.py",
]
ast_findings = []
for path in key_files:
    if not path.exists():
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except Exception as exc:
        ast_findings.append({"file": rel(path), "error": str(exc)})
        continue

    entries = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            try:
                target = ", ".join(ast.unparse(t) for t in node.targets)
                value = ast.unparse(node.value)
            except Exception:
                continue
            if any(k.lower() in (target + value).lower() for k in ["db", "path", "powerflow", "sqlite"]):
                entries.append({"line": getattr(node, "lineno", None), "type": "assign", "target": target, "value": value[:220]})
        elif isinstance(node, ast.Call):
            try:
                call = ast.unparse(node)
            except Exception:
                continue
            if any(k.lower() in call.lower() for k in ["sqlite3.connect", "connect(", "insert", "execute", "commit"]):
                entries.append({"line": getattr(node, "lineno", None), "type": "call", "expr": call[:240]})
    ast_findings.append({"file": rel(path), "entries": entries[:120]})

# Inference.
existing_populated = [d for d in db_candidates + discovered_dbs if d.get("exists") and (d.get("total_rows") or 0) > 0]
existing_empty = [d for d in db_candidates + discovered_dbs if d.get("exists") and (d.get("total_rows") == 0)]
db_path_refs = []
for file_item in code_findings:
    for hit in file_item["hits"]:
        if hit["pattern"] in {"powerflow.db", "DB_PATH", "sqlite3.connect", "database"}:
            db_path_refs.append({"file": file_item["file"], **hit})

recommendations = []
if existing_populated:
    recommendations.append("At least one populated DB exists. Compare capture configured path against populated DB path before diagnosing USDJPY.")
elif existing_empty:
    recommendations.append("Only empty DB files found. Capture is likely writing elsewhere, not running, or insertion path is inactive.")
else:
    recommendations.append("No DB files found in inspected paths. Capture path/config must be located from code.")

if not db_path_refs:
    recommendations.append("No clear DB path references found in quick scan. Inspect capture_bridge.py and db.py manually.")
else:
    recommendations.append("DB path references found. Next step: inspect capture_bridge.py/db.py references in the audit report and align active DB path.")

if any("capture_bridge.py" in item["file"] for item in code_findings):
    recommendations.append("capture_bridge.py contains relevant DB/capture references; audit insertion function before changing engine logic.")

contract = {
    "contract": "POWERFLOW_T004_CAPTURE_DB_PATH_AUDIT",
    "created_at": now,
    "candidate_db_paths": db_candidates,
    "discovered_db_files": discovered_dbs,
    "existing_populated_db_files": existing_populated,
    "existing_empty_db_files": existing_empty,
    "db_path_references": db_path_refs[:120],
    "key_file_ast_findings": ast_findings,
    "code_findings": code_findings[:120],
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_CAPTURE_DB_PATH_AUDIT.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

report_path = audit_dir / ("T004_CAPTURE_DB_PATH_AUDIT_" + stamp + ".md")
md = []
md.append("# T004-B Capture DB Path Audit")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Executive finding")
md.append("")
if existing_populated:
    md.append("- Populated DB files found: " + ", ".join(d["path"] for d in existing_populated))
elif existing_empty:
    md.append("- DB files found, but inspected DB files are empty.")
else:
    md.append("- No DB files found in expected active locations.")
md.append("")
md.append("## Recommendations")
md.append("")
for rec in recommendations:
    md.append("- " + rec)
md.append("")
md.append("## Candidate DB paths")
md.append("")
for d in db_candidates:
    md.append("- " + d["path"] + " | exists=" + str(d["exists"]) + " | size=" + str(d["size_bytes"]) + " | total_rows=" + str(d["total_rows"]))
    if d["tables"]:
        for t in d["tables"]:
            md.append("  - " + t["table"] + " rows=" + str(t["rows"]))
md.append("")
md.append("## Discovered DB files")
md.append("")
if discovered_dbs:
    for d in discovered_dbs:
        md.append("- " + d["path"] + " | exists=" + str(d["exists"]) + " | size=" + str(d["size_bytes"]) + " | total_rows=" + str(d["total_rows"]))
else:
    md.append("- none")
md.append("")
md.append("## DB path references")
md.append("")
if db_path_refs:
    for ref in db_path_refs[:80]:
        md.append("- " + ref["file"] + ":" + str(ref["line"]) + " | " + ref["pattern"] + " | " + ref["text"])
else:
    md.append("- none")
md.append("")
md.append("## Key file AST findings")
md.append("")
for item in ast_findings:
    md.append("### " + item["file"])
    md.append("")
    if "error" in item:
        md.append("- error: " + item["error"])
    elif item.get("entries"):
        for entry in item["entries"][:60]:
            if entry["type"] == "assign":
                md.append("- line " + str(entry["line"]) + " | assign | " + entry["target"] + " = " + entry["value"])
            else:
                md.append("- line " + str(entry["line"]) + " | call | " + entry["expr"])
    else:
        md.append("- no DB/capture AST entries detected")
    md.append("")
md.append("## Runtime behavior")
md.append("")
md.append("- DB inspection is read-only.")
md.append("- No runtime wiring.")
md.append("- No dashboard files touched.")
md.append("")
md.append("## Next action")
md.append("")
md.append("If no populated DB is found, stop USDJPY-specific debugging and fix active capture/DB path first.")
md.append("If a populated DB is found elsewhere, point diagnostics at that DB or fix the runtime DB target.")
md.append("")
report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_capture_db_path_audit_contract.py"
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
    "def test_t004_capture_db_path_audit_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_DB_PATH_AUDIT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_CAPTURE_DB_PATH_AUDIT"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert isinstance(data["candidate_db_paths"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_capture_db_path_audit_db_entries_have_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_DB_PATH_AUDIT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    for item in data["candidate_db_paths"]:',
    '        assert "path" in item',
    '        assert "exists" in item',
    '        assert "total_rows" in item',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "contract": str(contract_path),
    "report": str(report_path),
    "test": str(test_path),
    "populated_db_count": len(existing_populated),
    "empty_db_count": len(existing_empty),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
'@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running capture DB path audit"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-B capture DB path audit failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usdjpy_thin_data_diagnostic_contract.py `
    tests/test_t004_capture_db_path_audit_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-B tests failed"
}
Ok "T004-B tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_CAPTURE_DB_PATH_AUDIT.json",
    "tests/test_t004_capture_db_path_audit_contract.py",
    "scripts/t004_capture_db_path_audit.ps1"
)

$latestReport = Get-ChildItem ".\Docs\Audits" -Filter "T004_CAPTURE_DB_PATH_AUDIT_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestReport) {
    $pathsToAdd += $latestReport.FullName
}

Log "Targeted staging only T004-B files"
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
    Warn "No staged T004-B changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): inspect capture DB path and insertion targets"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_B_CAPTURE_DB_PATH_AUDIT.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-B capture DB path audit"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-B capture DB path audit"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Capture DB path audit created."
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
    $content += "Read Docs/Audits/T004_CAPTURE_DB_PATH_AUDIT_*.md and decide whether to fix active DB path, capture insertion, or symbol routing."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-B capture DB path audit"
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

Ok "T004-B capture DB path audit complete"
Log "Final status"
git status --short
git log --oneline -7
