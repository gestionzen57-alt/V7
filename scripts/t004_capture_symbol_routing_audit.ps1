param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$ThinSymbol = "USDJPY",
    [string[]]$ReferenceSymbols = @("GBPUSD", "EURUSD"),
    [switch]$SkipRestoreDashboardData,
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Log($msg) { Write-Host "[T004-F] $msg" }
function Ok($msg) { Write-Host "[OK] $msg" }
function Warn($msg) { Write-Host "[WARN] $msg" }

$RepoPath = (Resolve-Path $RepoPath).Path
Set-Location $RepoPath

Log "PowerFlow V7.6.7 T004-F capture symbol routing audit"
Log "RepoPath = $RepoPath"
Log "ThinSymbol = $ThinSymbol"
Log "ReferenceSymbols = $($ReferenceSymbols -join ',')"

Log "Git preflight"
git status --short
git branch --show-current
git log --oneline -7

$dashboardData = Join-Path $RepoPath "Core\dashboard_data.json"
if (-not $SkipRestoreDashboardData -and (Test-Path $dashboardData)) {
    $statusLine = git status --short -- "Core/dashboard_data.json"
    if ($statusLine) {
        Warn "Core/dashboard_data.json is modified. Restoring runtime dashboard state before T004-F commit."
        git restore -- "Core/dashboard_data.json"
        Ok "Restored Core/dashboard_data.json"
    }
}

$pythonAudit = Join-Path $RepoPath ".t004f_capture_symbol_routing_audit.py"
$thinSymbolJson = ($ThinSymbol | ConvertTo-Json -Compress)
$refsJson = ($ReferenceSymbols | ConvertTo-Json -Compress)

@"
from __future__ import annotations

import ast
import datetime as dt
import json
from pathlib import Path
import re

THIN_SYMBOL = $thinSymbolJson
REFERENCE_SYMBOLS = $refsJson
ALL_SYMBOLS = [THIN_SYMBOL] + list(REFERENCE_SYMBOLS)

repo = Path.cwd()
audit_dir = repo / "Docs" / "Audits"
contract_dir = repo / "Docs" / "Contracts"
plan_dir = repo / "Docs" / "Plans"
tests_dir = repo / "tests"
audit_dir.mkdir(parents=True, exist_ok=True)
contract_dir.mkdir(parents=True, exist_ok=True)
plan_dir.mkdir(parents=True, exist_ok=True)
tests_dir.mkdir(parents=True, exist_ok=True)

root_cause_path = contract_dir / "T004_USDJPY_THIN_ROOT_CAUSE.json"
root_cause = {}
if root_cause_path.exists():
    root_cause = json.loads(root_cause_path.read_text(encoding="utf-8"))

now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path)

scan_roots = [
    repo / "Core",
    repo / "scripts",
    repo / "patch",
    repo / "tests",
]

allowed_suffixes = {".py", ".ps1", ".json", ".md", ".txt", ".log", ".mq4", ".mq5", ".ini", ".csv"}
exclude_parts = {".git", "__pycache__", ".venv", "venv", "Archive", "backup", "backups"}

patterns = [
    THIN_SYMBOL,
    *REFERENCE_SYMBOLS,
    "symbols",
    "symbol",
    "pair",
    "instrument",
    "allow",
    "filter",
    "MarketWatch",
    "Market Watch",
    "MT4",
    "MetaTrader",
    "socket",
    "TCP",
    "capture_bridge",
    "on_tick",
    "process_tick",
    "timeframe",
    "force_snapshots",
    "powerflow.db",
]

code_hits = []
for root in scan_roots:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed_suffixes:
            continue
        parts = set(path.relative_to(repo).parts)
        if parts & exclude_parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            lower = line.lower()
            matched = [pat for pat in patterns if pat.lower() in lower]
            if matched:
                hits.append({
                    "line": i,
                    "patterns": sorted(set(matched)),
                    "text": line.strip()[:260],
                })
        if hits:
            code_hits.append({
                "file": rel(path),
                "hit_count": len(hits),
                "hits": hits[:120],
            })

# AST focused extraction for Python files.
ast_files = [
    repo / "Core" / "capture_bridge.py",
    repo / "Core" / "system_config.py",
    repo / "Core" / "db.py",
]
ast_files.extend(sorted((repo / "Core").glob("capture_*.py")) if (repo / "Core").exists() else [])

ast_findings = []
symbol_literal_re = re.compile(r"\\b[A-Z]{6}\\b")
interesting_names = ["symbol", "symbols", "pair", "pairs", "instrument", "allow", "filter", "watch", "timeframe", "tf"]

for path in sorted(set(ast_files)):
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
            hay = (target + " " + value).lower()
            literals = symbol_literal_re.findall(value)
            if literals or any(name in hay for name in interesting_names):
                entries.append({
                    "line": getattr(node, "lineno", None),
                    "type": "assign",
                    "target": target,
                    "value": value[:320],
                    "symbols": sorted(set(literals)),
                })
        elif isinstance(node, ast.Call):
            try:
                call = ast.unparse(node)
            except Exception:
                continue
            hay = call.lower()
            if any(name in hay for name in ["socket", "recv", "send", "split", "json", "process_tick", "insert", "execute", "symbol"]):
                entries.append({
                    "line": getattr(node, "lineno", None),
                    "type": "call",
                    "expr": call[:320],
                    "symbols": sorted(set(symbol_literal_re.findall(call))),
                })
    ast_findings.append({"file": rel(path), "entries": entries[:160]})

# Logs: count symbol references if log files exist.
log_roots = [repo / "logs", repo / "Core" / "logs"]
log_summary = []
for root in log_roots:
    if not root.exists():
        continue
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".log", ".txt", ".json", ".md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        counts = {sym: text.upper().count(sym.upper()) for sym in ALL_SYMBOLS}
        if any(counts.values()):
            log_summary.append({
                "file": rel(path),
                "symbol_counts": counts,
                "size_bytes": path.stat().st_size,
            })

# Determine evidence categories.
thin_mentions = []
ref_mentions = {sym: [] for sym in REFERENCE_SYMBOLS}
symbol_list_candidates = []

for item in code_hits:
    for hit in item["hits"]:
        text = hit["text"]
        upper = text.upper()
        if THIN_SYMBOL.upper() in upper:
            thin_mentions.append({"file": item["file"], "line": hit["line"], "text": text})
        for sym in REFERENCE_SYMBOLS:
            if sym.upper() in upper:
                ref_mentions[sym].append({"file": item["file"], "line": hit["line"], "text": text})
        # possible symbol list/allowlist line
        if any(k in " ".join(hit["patterns"]).lower() for k in ["symbols", "allow", "filter"]) or any(sym in upper for sym in ALL_SYMBOLS):
            if any(sym in upper for sym in ALL_SYMBOLS):
                symbol_list_candidates.append({"file": item["file"], "line": hit["line"], "text": text})

# Heuristic risk flags.
risk_flags = []
if not thin_mentions:
    risk_flags.append("USDJPY_NOT_REFERENCED_IN_CODE_SCAN")
else:
    risk_flags.append("USDJPY_REFERENCED_IN_CODE_SCAN")

for sym, mentions in ref_mentions.items():
    if mentions and not thin_mentions:
        risk_flags.append("REFERENCES_PRESENT_BUT_USDJPY_MISSING_IN_CODE")

# If symbol list line contains refs but not USDJPY.
for cand in symbol_list_candidates:
    upper = cand["text"].upper()
    if any(sym.upper() in upper for sym in REFERENCE_SYMBOLS) and THIN_SYMBOL.upper() not in upper:
        risk_flags.append("POSSIBLE_SYMBOL_ALLOWLIST_EXCLUDES_USDJPY")
        break

if not log_summary:
    risk_flags.append("NO_SYMBOL_LOG_EVIDENCE_FOUND")
else:
    # compare log mentions
    total_counts = {sym: sum(item["symbol_counts"].get(sym, 0) for item in log_summary) for sym in ALL_SYMBOLS}
    if total_counts.get(THIN_SYMBOL, 0) == 0 and any(total_counts.get(sym, 0) > 0 for sym in REFERENCE_SYMBOLS):
        risk_flags.append("LOGS_REFERENCES_PRESENT_USDJPY_ABSENT")
    elif total_counts.get(THIN_SYMBOL, 0) > 0:
        risk_flags.append("LOGS_CONTAIN_USDJPY")

recommendations = [
    "Do not modify engine logic; T004 remains capture/routing/data-density.",
    "Verify USDJPY is present and enabled in MT4 Market Watch / source stream.",
    "Verify capture symbol list or allowlist includes USDJPY with exact broker suffix, if any.",
    "Verify USDJPY ticks reach capture_bridge before DB insertion.",
    "If source stream is confirmed, add a short capture health counter per symbol before any PowerFlow scoring change.",
]

if "POSSIBLE_SYMBOL_ALLOWLIST_EXCLUDES_USDJPY" in risk_flags:
    recommendations.insert(1, "A possible symbol allowlist line includes references but not USDJPY. Inspect symbol_list_candidates first.")

contract = {
    "contract": "POWERFLOW_T004_CAPTURE_SYMBOL_ROUTING_AUDIT",
    "created_at": now,
    "thin_symbol": THIN_SYMBOL,
    "reference_symbols": REFERENCE_SYMBOLS,
    "source_root_cause_contract": "Docs/Contracts/T004_USDJPY_THIN_ROOT_CAUSE.json" if root_cause else None,
    "likely_cause_from_t004e": root_cause.get("likely_cause"),
    "risk_flags": sorted(set(risk_flags)),
    "code_hits": code_hits[:180],
    "ast_findings": ast_findings,
    "symbol_list_candidates": symbol_list_candidates[:120],
    "thin_symbol_mentions": thin_mentions[:120],
    "reference_symbol_mentions": {k: v[:120] for k, v in ref_mentions.items()},
    "log_summary": log_summary[:120],
    "recommendations": recommendations,
    "read_only": True,
    "runtime_wired": False,
}
contract_path = contract_dir / "T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json"
contract_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")

plan_path = plan_dir / ("T004_CAPTURE_SYMBOL_ROUTING_OPERATOR_CHECKLIST_" + stamp + ".md")
md = []
md.append("# T004-F Capture Symbol Routing Operator Checklist")
md.append("")
md.append("Date: " + now)
md.append("")
md.append("## Context")
md.append("")
md.append("- Thin symbol: " + THIN_SYMBOL)
md.append("- Reference symbols: " + ", ".join(REFERENCE_SYMBOLS))
md.append("- T004-E likely cause: " + str(root_cause.get("likely_cause")))
md.append("- This is not an engine/scoring issue yet. It is capture/routing/data-density.")
md.append("")
md.append("## Risk flags")
md.append("")
if risk_flags:
    for flag in sorted(set(risk_flags)):
        md.append("- " + flag)
else:
    md.append("- none")
md.append("")
md.append("## Operator checklist")
md.append("")
md.append("- [ ] Confirm USDJPY is visible/enabled in MT4 Market Watch or the source feed.")
md.append("- [ ] Confirm the broker symbol name matches exactly: USDJPY vs USDJPY.suffix / USDJPYm / USDJPY.pro.")
md.append("- [ ] Confirm the bridge/EA emits USDJPY ticks at the same cadence as GBPUSD/EURUSD.")
md.append("- [ ] Confirm capture_bridge receives USDJPY before DB insertion.")
md.append("- [ ] Confirm any symbol allowlist includes USDJPY exactly.")
md.append("- [ ] Confirm no timeframe-specific filter excludes USDJPY.")
md.append("- [ ] Confirm Core/powerflow.db is the DB used by the live capture path.")
md.append("- [ ] Run a short live capture window and compare per-symbol tick counters.")
md.append("")
md.append("## Code findings to inspect first")
md.append("")
if symbol_list_candidates:
    for cand in symbol_list_candidates[:80]:
        md.append("- " + cand["file"] + ":" + str(cand["line"]) + " | " + cand["text"])
else:
    md.append("- no explicit symbol list candidates found")
md.append("")
md.append("## Focused AST findings")
md.append("")
for item in ast_findings:
    md.append("### " + item.get("file", "unknown"))
    md.append("")
    if item.get("error"):
        md.append("- error: " + item["error"])
    elif item.get("entries"):
        for entry in item["entries"][:80]:
            if entry["type"] == "assign":
                md.append("- line " + str(entry.get("line")) + " | assign | " + entry.get("target", "") + " = " + entry.get("value", ""))
            else:
                md.append("- line " + str(entry.get("line")) + " | call | " + entry.get("expr", ""))
    else:
        md.append("- no focused entries")
    md.append("")
md.append("## Log symbol evidence")
md.append("")
if log_summary:
    for item in log_summary[:60]:
        md.append("- " + item["file"] + " | " + json.dumps(item["symbol_counts"], ensure_ascii=False))
else:
    md.append("- no symbol log evidence found")
md.append("")
md.append("## Stop rule")
md.append("")
md.append("Do not patch Core/engine.py, pf_engine_v6_core.py, or scoring modules for this issue.")
md.append("Only capture/routing instrumentation or operator-side feed correction is justified at this stage.")
md.append("")
md.append("## Next action")
md.append("")
md.append("T004-G should add a lightweight read-only/operator capture health script or manual command that counts incoming ticks per symbol over a short window, without changing engine behavior.")
md.append("")
plan_path.write_text("\n".join(md) + "\n", encoding="utf-8")

test_path = tests_dir / "test_t004_capture_symbol_routing_audit_contract.py"
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
    "def test_t004_capture_symbol_routing_contract_shape():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    assert data["contract"] == "POWERFLOW_T004_CAPTURE_SYMBOL_ROUTING_AUDIT"',
    '    assert data["read_only"] is True',
    '    assert data["runtime_wired"] is False',
    '    assert data["thin_symbol"] == "USDJPY"',
    '    assert isinstance(data["risk_flags"], list)',
    '    assert isinstance(data["recommendations"], list)',
    "",
    "",
    "def test_t004_capture_symbol_routing_has_operator_recommendations():",
    '    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json"',
    '    data = json.loads(path.read_text(encoding="utf-8"))',
    "",
    '    joined = "\\n".join(data["recommendations"]).lower()',
    '    assert "engine" in joined',
    '    assert "usdjpy" in joined',
    "",
]
test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")

print(json.dumps({
    "ok": True,
    "contract": str(contract_path),
    "plan": str(plan_path),
    "test": str(test_path),
    "risk_flags": sorted(set(risk_flags)),
    "symbol_list_candidate_count": len(symbol_list_candidates),
    "thin_mentions": len(thin_mentions),
    "recommendations": recommendations,
}, indent=2, ensure_ascii=False))
"@ | Set-Content -Path $pythonAudit -Encoding UTF8

Log "Running capture symbol routing audit"
python $pythonAudit
if ($LASTEXITCODE -ne 0) {
    throw "T004-F capture symbol routing audit failed"
}

Remove-Item $pythonAudit -Force -ErrorAction SilentlyContinue

Log "Running targeted tests"
python -m pytest `
    tests/test_t004_usdjpy_thin_data_diagnostic_contract.py `
    tests/test_t004_capture_db_path_audit_contract.py `
    tests/test_t004_active_db_decision_contract.py `
    tests/test_t004_active_db_symbol_density_contract.py `
    tests/test_t004_usdjpy_thin_root_cause_contract.py `
    tests/test_t004_capture_symbol_routing_audit_contract.py `
    -q
if ($LASTEXITCODE -ne 0) {
    throw "T004-F tests failed"
}
Ok "T004-F tests passed"

Log "Targeted git status before commit"
git status --short

$pathsToAdd = @(
    "Docs/Contracts/T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json",
    "tests/test_t004_capture_symbol_routing_audit_contract.py",
    "scripts/t004_capture_symbol_routing_audit.ps1"
)

$latestPlan = Get-ChildItem ".\Docs\Plans" -Filter "T004_CAPTURE_SYMBOL_ROUTING_OPERATOR_CHECKLIST_*.md" | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -ne $latestPlan) {
    $pathsToAdd += $latestPlan.FullName
}

Log "Targeted staging only T004-F files"
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
    Warn "No staged T004-F changes. Skipping commit."
} else {
    Log "Staged files:"
    $staged | ForEach-Object { Write-Host "  $_" }

    git commit -m "audit(t004): inspect capture symbol routing for USDJPY thin data"
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
    $checkpointPath = Join-Path $checkpointDir "CHECKPOINT_${stamp}_T004_F_CAPTURE_SYMBOL_ROUTING.md"

    $lastCommits = git log --oneline -7
    $content = @()
    $content += "# CHECKPOINT - T004-F capture symbol routing"
    $content += ""
    $content += "Date: $(Get-Date -Format o)"
    $content += "Focus: T004-F capture symbol routing audit"
    $content += ""
    $content += "## Result"
    $content += ""
    $content += "- Capture symbol routing audit created."
    $content += "- Operator checklist created."
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
    $content += "T004-G should add a lightweight capture health counter or manual verification command."
    $content += ""

    Set-Content -Path $checkpointPath -Value ($content -join "`n") -Encoding UTF8

    git add -- $checkpointPath
    if ($LASTEXITCODE -ne 0) { throw "git add checkpoint failed" }

    $checkpointStaged = git diff --cached --name-only
    if ($checkpointStaged) {
        git commit -m "[CHECKPOINT] Targeted checkpoint: T004-F capture symbol routing"
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

Ok "T004-F capture symbol routing audit complete"
Log "Final status"
git status --short
git log --oneline -7
