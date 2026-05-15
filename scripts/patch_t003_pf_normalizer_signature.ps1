param(
    [string]$RepoPath = "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT",
    [switch]$NoGit,
    [switch]$UpdateDispatch
)

$ErrorActionPreference = "Stop"

function T003-Step($Message) {
    Write-Host "[T003] $Message"
}

function T003-Warn($Message) {
    Write-Host "[T003][WARN] $Message" -ForegroundColor Yellow
}

function T003-Fail($Message) {
    Write-Host "[T003][FAIL] $Message" -ForegroundColor Red
    throw $Message
}

T003-Step "Starting PowerFlow V7.6.7 T003 hotfix"
T003-Step "RepoPath = $RepoPath"

if (!(Test-Path $RepoPath)) {
    T003-Fail "RepoPath not found: $RepoPath"
}

Set-Location $RepoPath

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    T003-Fail "python command not found in PATH"
}

if (!(Test-Path ".git")) {
    T003-Warn ".git not found in RepoPath. Patch can continue, but git sync will be skipped."
    $NoGit = $true
}

if (-not $NoGit) {
    T003-Step "Git preflight"
    git status --short
    git branch --show-current
    git log --oneline -5
}

$patcherPath = Join-Path $RepoPath ".t003_patch_pf_normalizer.py"

@'
from __future__ import annotations

import ast
import datetime as _dt
import json
import re
import shutil
import sys
from pathlib import Path

MARKER = "T003_V767_SIGNATURE_COMPAT_PATCH"

WRAPPER = '''# --- {marker} START ---
def detect_tf_alignment(*args, **kwargs):
    """
    PowerFlow V7.6.7 T003 compatibility wrapper.

    Purpose:
      - keep the existing detect_tf_alignment implementation intact;
      - absorb caller/API signature drift from /api/cockpit-state;
      - ignore extra positional/keyword context arguments when the legacy
        implementation does not accept them.

    This wrapper does not decide market direction and does not modify DB state.
    It only adapts Python call shape to the legacy implementation signature.
    """
    import inspect as _pf_inspect

    impl = _detect_tf_alignment_impl
    sig = _pf_inspect.signature(impl)
    params = sig.parameters

    has_varargs = any(p.kind == p.VAR_POSITIONAL for p in params.values())
    has_varkw = any(p.kind == p.VAR_KEYWORD for p in params.values())

    positional_names = [
        name for name, p in params.items()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]

    if has_varargs:
        call_args = list(args)
    else:
        call_args = list(args[:len(positional_names)])

    already_filled = set(positional_names[:min(len(call_args), len(positional_names))])
    if has_varkw:
        call_kwargs = {k: v for k, v in kwargs.items() if k not in already_filled}
    else:
        call_kwargs = {
            k: v for k, v in kwargs.items()
            if k in params and k not in already_filled
        }

    try:
        return impl(*call_args, **call_kwargs)
    except TypeError as exc:
        msg = str(exc)
        signature_drift = (
            "positional" in msg
            or "unexpected keyword" in msg
            or "required positional" in msg
            or "multiple values" in msg
        )
        if not signature_drift:
            raise

        # Fallback: if one caller passed a state/payload dict, extract keys
        # matching the legacy implementation parameter names.
        payload_kwargs = dict(call_kwargs)
        for item in args:
            if isinstance(item, dict):
                for name in params:
                    if name in item and name not in payload_kwargs:
                        payload_kwargs[name] = item[name]

        if has_varkw:
            filtered_payload_kwargs = payload_kwargs
        else:
            filtered_payload_kwargs = {
                k: v for k, v in payload_kwargs.items()
                if k in params
            }

        try:
            return impl(**filtered_payload_kwargs)
        except TypeError:
            # Final fallback: call with trimmed positional args only.
            # If required data is genuinely absent, re-raise the original
            # signature error so the technical cause remains visible.
            try:
                return impl(*call_args)
            except TypeError:
                raise exc

# --- {marker} END ---

'''


def find_pf_normalizer(root: Path) -> Path:
    candidates = [p for p in root.rglob("pf_normalizer.py") if p.is_file()]
    if not candidates:
        raise FileNotFoundError("pf_normalizer.py not found under repo")

    def score(path: Path) -> tuple[int, int, str]:
        text_path = str(path).replace("\\", "/").lower()
        core_bonus = 0 if "/core/" in text_path or text_path.endswith("/pf_normalizer.py") else 1
        return (core_bonus, len(path.parts), str(path))

    return sorted(candidates, key=score)[0]


def patch_file(target: Path) -> dict:
    raw = target.read_text(encoding="utf-8")
    if MARKER in raw:
        return {"patched": False, "reason": "already_patched", "target": str(target)}

    tree = ast.parse(raw)
    funcs = [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "detect_tf_alignment"
    ]
    if not funcs:
        raise RuntimeError("top-level function detect_tf_alignment not found in pf_normalizer.py")

    node = funcs[0]
    lines = raw.splitlines(keepends=True)
    line_index = node.lineno - 1

    # Locate actual def line in case decorators or parser offsets create ambiguity.
    search_start = max(0, line_index - 3)
    search_end = min(len(lines), line_index + 5)
    def_line_index = None
    for i in range(search_start, search_end):
        if re.match(r"^\s*(async\s+)?def\s+detect_tf_alignment\s*\(", lines[i]):
            def_line_index = i
            break
    if def_line_index is None:
        raise RuntimeError("could not locate detect_tf_alignment def line for safe patch")

    indent = re.match(r"^(\s*)", lines[def_line_index]).group(1)
    if indent:
        raise RuntimeError("detect_tf_alignment is not top-level; refusing unsafe patch")

    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_name(f"{target.name}.bak_T003_{timestamp}")
    shutil.copy2(target, backup)

    lines[def_line_index] = re.sub(
        r"def\s+detect_tf_alignment\s*\(",
        "def _detect_tf_alignment_impl(",
        lines[def_line_index],
        count=1,
    )

    insert_index = node.decorator_list[0].lineno - 1 if node.decorator_list else def_line_index
    lines.insert(insert_index, WRAPPER.replace("{marker}", MARKER))
    target.write_text("".join(lines), encoding="utf-8")

    # Verify patched file is syntactically valid.
    ast.parse(target.read_text(encoding="utf-8"))

    return {
        "patched": True,
        "target": str(target),
        "backup": str(backup),
        "function": "detect_tf_alignment",
        "impl": "_detect_tf_alignment_impl",
    }


def update_dispatch(root: Path, result: dict) -> dict:
    candidates = [root / "Docs" / "DISPATCH_STATUS.json", root / "DISPATCH_STATUS.json"]
    dispatch = next((p for p in candidates if p.exists()), None)
    if dispatch is None:
        return {"updated": False, "reason": "DISPATCH_STATUS.json not found"}

    data = json.loads(dispatch.read_text(encoding="utf-8"))
    now = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    tasks = data.setdefault("tasks", {})
    pending = tasks.setdefault("pending", [])
    completed = tasks.setdefault("completed", [])

    task = None
    for i, item in enumerate(list(pending)):
        if item.get("id") == "T003":
            task = pending.pop(i)
            break

    if task is None:
        for item in completed:
            if item.get("id") == "T003":
                task = item
                break

    if task is None:
        return {"updated": False, "reason": "T003 not found"}

    task.update({
        "owner": "GPT_1_Core_Engine",
        "assigned_to": "GPT_1_Core_Engine",
        "status": "completed",
        "completed_at": now,
        "output": "T003 hotfix: detect_tf_alignment compatibility wrapper in pf_normalizer.py",
        "technical_notes": [
            "Legacy implementation preserved as _detect_tf_alignment_impl",
            "Wrapper absorbs extra args/kwargs from /api/cockpit-state call drift",
            "No DB write, no dashboard contract change, no BUY/SELL semantics",
        ],
    })

    if not any(item.get("id") == "T003" for item in completed):
        completed.append(task)

    data["last_update"] = now
    metrics = data.setdefault("metrics", {})
    metrics["pending"] = len(tasks.get("pending", []))
    metrics["in_progress"] = len(tasks.get("in_progress", []))
    metrics["completed"] = len(tasks.get("completed", []))
    metrics["blocked"] = len(tasks.get("blocked", []))
    metrics["archived"] = len(tasks.get("archived", []))
    total = metrics.get("total_tasks") or sum(metrics[k] for k in ["pending", "in_progress", "completed", "blocked", "archived"])
    metrics["total_tasks"] = total
    metrics["completion_rate"] = round((metrics["completed"] / total) * 100, 2) if total else 0

    backup = dispatch.with_name(f"{dispatch.name}.bak_T003_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(dispatch, backup)
    dispatch.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"updated": True, "dispatch": str(dispatch), "backup": str(backup)}


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    should_update_dispatch = len(sys.argv) > 2 and sys.argv[2] == "--update-dispatch"
    target = find_pf_normalizer(root)
    result = patch_file(target)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if should_update_dispatch:
        dispatch_result = update_dispatch(root, result)
        print(json.dumps({"dispatch": dispatch_result}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@ | Set-Content -Path $patcherPath -Encoding UTF8

T003-Step "Applying local patcher"
if ($UpdateDispatch) {
    python $patcherPath $RepoPath --update-dispatch
} else {
    python $patcherPath $RepoPath
}

$pfFile = Get-ChildItem -Path $RepoPath -Recurse -Filter "pf_normalizer.py" -File | Select-Object -First 1
if (!$pfFile) {
    T003-Fail "pf_normalizer.py not found after patch"
}

T003-Step "Python syntax check"
python -m py_compile $pfFile.FullName

$extraCompileTargets = @(
    "dashboard_server.py",
    "dashboard_data_normalizer.py",
    "dashboard_v74_contract_check.py"
)

foreach ($name in $extraCompileTargets) {
    $hit = Get-ChildItem -Path $RepoPath -Recurse -Filter $name -File | Select-Object -First 1
    if ($hit) {
        T003-Step "Syntax check: $($hit.Name)"
        python -m py_compile $hit.FullName
    }
}

T003-Step "Call-site scan for detect_tf_alignment"
Get-ChildItem -Path $RepoPath -Recurse -Include *.py -File |
    Select-String -Pattern "detect_tf_alignment" |
    ForEach-Object { "{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() }

if (-not $NoGit) {
    T003-Step "Git diff summary"
    git diff --stat
    git diff -- pf_normalizer.py

    T003-Step "Staging and syncing through auto_git_sync if available"
    if (Test-Path ".\scripts\auto_git_sync.ps1") {
        .\scripts\auto_git_sync.ps1 -Message "T003 hotfix pf_normalizer detect_tf_alignment signature compatibility"
    } else {
        git add .
        git commit -m "T003 hotfix pf_normalizer detect_tf_alignment signature compatibility"
        git pull --rebase
        git push
    }
} else {
    T003-Warn "NoGit mode active: changes are local only. Run auto_git_sync manually after validation."
}

T003-Step "T003 hotfix finished"
T003-Step "Recommended final checkpoint: .\scripts\auto_checkpoint_claude.ps1 -Focus \"T003 pf_normalizer signature hotfix\""
