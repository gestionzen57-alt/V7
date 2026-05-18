#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

START = "# --- T0110B_B9_RETEST_SOURCE_FIELDS_LEGACY_METADATA_HOTFIX_START ---"
END = "# --- T0110B_B9_RETEST_SOURCE_FIELDS_LEGACY_METADATA_HOTFIX_END ---"


def remove_old_block(text: str) -> str:
    start = text.find(START)
    if start == -1:
        return text
    end = text.find(END, start)
    if end == -1:
        return text[:start].rstrip() + "\n"
    end += len(END)
    return (text[:start] + text[end:]).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--append-file", required=True)
    args = parser.parse_args()

    root = Path(args.repo_root)
    target = root / "pf_t009_raw_calibration.py"
    append_file = Path(args.append_file)

    if not target.exists():
        raise FileNotFoundError(target)
    if not append_file.exists():
        raise FileNotFoundError(append_file)

    text = target.read_text(encoding="utf-8")
    text = remove_old_block(text)

    required = [
        "T0110_B9_RETEST_SOURCE_FIELDS_V0_START",
        "T0110A_B9_RETEST_SOURCE_FIELDS_METADATA_COMPAT_HOTFIX_START",
        "b9_retest_source_status",
        "retest_source_fields",
        "natural_flow_factors",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(
            "T0110B requires T0110 + T0110A first. Missing: " + ", ".join(missing)
        )

    block = append_file.read_text(encoding="utf-8").strip() + "\n"
    target.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")
    print("[OK] appended T0110B legacy metadata compatibility hotfix block")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
