"""Patch a PowerFlow live runtime file to attach B9 runtime integration.

Safe behavior:
- Locates run_powerflow_live_stack_once.py or scheduler equivalents.
- Creates a timestamped backup before modifying.
- Inserts import/init block and wraps process_tick_window if present.
- Idempotent markers prevent duplicate insertion.
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

MARKER_START = "# --- B9 Runtime Integration V7.6.7 START ---"
MARKER_END = "# --- B9 Runtime Integration V7.6.7 END ---"

INTEGRATION_BLOCK = f'''\n{MARKER_START}\ntry:\n    from pf_b9_runtime_bridge import (\n        B9RuntimeBridge,\n        attach_b9_to_existing_process_tick_window,\n        append_runtime_log,\n    )\n\n    _B9_RUNTIME_BRIDGE = B9RuntimeBridge(enable_telegram=False, db_path="powerflow.db")\n    append_runtime_log("B9 runtime bridge initialized in DRY-RUN mode")\nexcept Exception as _b9_runtime_exc:\n    _B9_RUNTIME_BRIDGE = None\n    try:\n        append_runtime_log(f"B9 runtime bridge disabled: {{_b9_runtime_exc}}")\n    except Exception:\n        print(f"[B9_RUNTIME] disabled: {{_b9_runtime_exc}}")\n{MARKER_END}\n'''

WRAP_BLOCK = f'''\n{MARKER_START} WRAP\ntry:\n    if _B9_RUNTIME_BRIDGE is not None:\n        _b9_wrapped = attach_b9_to_existing_process_tick_window(globals(), _B9_RUNTIME_BRIDGE)\n        append_runtime_log(f"B9 process_tick_window wrapper active={{_b9_wrapped}}")\nexcept Exception as _b9_wrap_exc:\n    try:\n        append_runtime_log(f"B9 wrapper attach failed: {{_b9_wrap_exc}}")\n    except Exception:\n        print(f"[B9_RUNTIME] wrapper attach failed: {{_b9_wrap_exc}}")\n{MARKER_END} WRAP\n'''

CANDIDATE_NAMES = (
    "run_powerflow_live_stack_once.py",
    "scheduler_powerflow.py",
    "scheduler_powerflow_turbo_wrapper.py",
)


def find_target(root: Path, explicit: Optional[str] = None) -> Path:
    if explicit:
        target = Path(explicit)
        if not target.is_absolute():
            target = root / target
        if not target.exists():
            raise FileNotFoundError(f"Explicit target not found: {target}")
        return target

    for name in CANDIDATE_NAMES:
        matches = list(root.rglob(name))
        if matches:
            # Prefer Core/core paths.
            matches.sort(key=lambda p: ("core" not in str(p).lower(), len(str(p))))
            return matches[0]
    raise FileNotFoundError(
        "No runtime target found. Looked for: " + ", ".join(CANDIDATE_NAMES)
    )


def patch_file(target: Path) -> Path:
    text = target.read_text(encoding="utf-8")
    if MARKER_START in text:
        print(f"[B9 PATCH] Already patched: {target}")
        return target

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup = target.with_suffix(target.suffix + f".bak_b9_{stamp}")
    shutil.copy2(target, backup)
    print(f"[B9 PATCH] Backup: {backup}")

    lines = text.splitlines(keepends=True)
    insert_idx = 0
    # Put import/init after shebang, encoding, module docstring and __future__ imports when possible.
    for idx, line in enumerate(lines[:120]):
        stripped = line.strip()
        if stripped.startswith("from __future__") or stripped.startswith("import ") or stripped.startswith("from "):
            insert_idx = idx + 1
    patched = "".join(lines[:insert_idx]) + INTEGRATION_BLOCK + "".join(lines[insert_idx:])
    patched = patched.rstrip() + "\n" + WRAP_BLOCK + "\n"
    target.write_text(patched, encoding="utf-8")
    print(f"[B9 PATCH] Patched: {target}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch live runtime with B9 integration")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--target", default=None, help="Explicit runtime file path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    target = find_target(root, args.target)
    patch_file(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
