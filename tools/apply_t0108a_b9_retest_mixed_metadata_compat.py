#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

START = "# --- T0108A_B9_RETEST_MIXED_METADATA_TEST_COMPAT_HOTFIX_START ---"
END = "# --- T0108A_B9_RETEST_MIXED_METADATA_TEST_COMPAT_HOTFIX_END ---"


def remove_old_block(text: str) -> str:
    start = text.find(START)
    if start == -1:
        return text
    end = text.find(END, start)
    if end == -1:
        return text[:start].rstrip() + "\n"
    end += len(END)
    return (text[:start] + text[end:]).rstrip() + "\n"


def patch_t0107_forward_compat(repo_root: Path) -> None:
    test_path = repo_root / "tests" / "test_t0107_b9_natural_flow_reading_v0.py"
    if not test_path.exists():
        raise FileNotFoundError(test_path)

    text = test_path.read_text(encoding="utf-8")
    old = 'assert payload["raw_calibration"]["version"] == "T0107_NATURAL_FLOW_READING_V0"'
    new = (
        'assert payload["raw_calibration"]["version"] in {'
        '"T0107_NATURAL_FLOW_READING_V0", "T0108_RETEST_MIXED_SPLIT_V0"}'
    )
    if old in text:
        text = text.replace(old, new, 1)
        test_path.write_text(text, encoding="utf-8")
        print("[OK] patched T0107 test forward-compatible with T0108")
    elif new in text:
        print("[OK] T0107 test already forward-compatible with T0108")
    else:
        raise RuntimeError("Could not locate T0107 raw_calibration version assertion")


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
        "T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_START",
        "b9_retest_natural_state",
        "b9_context_resolution_state",
        "T0107_NATURAL_FLOW_READING_V0",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("T0108A requires T0108 first. Missing: " + ", ".join(missing))

    block = append_file.read_text(encoding="utf-8").strip() + "\n"
    target.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")
    print("[OK] appended T0108A metadata compatibility block")

    patch_t0107_forward_compat(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
