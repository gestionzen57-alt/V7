#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

START = "# --- T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_START ---"
END = "# --- T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_END ---"


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
        "T0107_B9_NATURAL_FLOW_READING_V0_START",
        "T0107A_B9_NATURAL_FLOW_GAPPY_THRESHOLD_HOTFIX_START",
        "b9_flow_intent_state",
        "b9_trap_risk_state",
        "b9_natural_flow_reading_fr",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(
            "T0108 requires T0107 + T0107A first. Missing: " + ", ".join(missing)
        )

    block = append_file.read_text(encoding="utf-8").strip() + "\n"
    target.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")
    print("[OK] appended T0108 natural retest + mixed split V0 block")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
