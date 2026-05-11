"""
PowerFlow V7.2 - Behavioral Alert Mapper session_context patch helper

This patcher injects session_context into alerts produced by pf_behavioral_alert_mapper.py.
It is conservative: it creates a timestamped backup and only performs text patches when
known anchors are found. Session context is a qualifier only; it never filters alerts.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

IMPORT_LINE = "from pf_session_overlay import get_session_context"


def patch_source(source: str) -> tuple[str, bool]:
    changed = False
    text = source

    if IMPORT_LINE not in text:
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)
        text = "\n".join(lines) + ("\n" if source.endswith("\n") else "")
        changed = True

    # Common pattern: alert dict contains data_source or timestamp near the end.
    if '"session_context"' not in text and "'session_context'" not in text:
        candidates = [
            ('"data_source":', '"session_context": get_session_context(),\n        "data_source":'),
            ("'data_source':", "'session_context': get_session_context(),\n        'data_source':"),
            ('"timestamp":', '"session_context": get_session_context(),\n        "timestamp":'),
            ("'timestamp':", "'session_context': get_session_context(),\n        'timestamp':"),
        ]
        for needle, replacement in candidates:
            idx = text.find(needle)
            if idx != -1:
                text = text[:idx] + replacement + text[idx + len(needle):]
                changed = True
                break

    return text, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch pf_behavioral_alert_mapper.py with session_context")
    parser.add_argument("--file", default="pf_behavioral_alert_mapper.py")
    parser.add_argument("--check", action="store_true", help="Report whether patch would change the file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise FileNotFoundError(f"Missing target file: {path}")

    original = path.read_text(encoding="utf-8")
    patched, changed = patch_source(original)
    if args.check:
        print("PATCH_NEEDED" if changed else "ALREADY_PATCHED")
        return 1 if changed else 0

    if changed:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = path.with_suffix(path.suffix + f".backup_{stamp}")
        backup.write_text(original, encoding="utf-8")
        path.write_text(patched, encoding="utf-8")
        print(f"PATCHED {path} backup={backup}")
    else:
        print(f"ALREADY_PATCHED {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
