#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

START = "# --- T0110_B9_RETEST_SOURCE_FIELDS_V0_START ---"
END = "# --- T0110_B9_RETEST_SOURCE_FIELDS_V0_END ---"


def remove_old_block(text: str) -> str:
    start = text.find(START)
    if start == -1:
        return text
    end = text.find(END, start)
    if end == -1:
        return text[:start].rstrip() + "\n"
    end += len(END)
    return (text[:start] + text[end:]).rstrip() + "\n"


def patch_forward_tests(repo_root: Path) -> None:
    replacements = {
        repo_root / "tests" / "test_t0107_b9_natural_flow_reading_v0.py": [
            (
                'assert payload["raw_calibration"]["version"] in {"T0107_NATURAL_FLOW_READING_V0", "T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0"}',
                'assert payload["raw_calibration"]["version"] in {"T0107_NATURAL_FLOW_READING_V0", "T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0", "T0110_RETEST_SOURCE_FIELDS_V0"}',
            )
        ],
        repo_root / "tests" / "test_t0108_b9_natural_retest_mixed_split_v0.py": [
            (
                'assert payload["raw_calibration"]["version"] in {"T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0"}',
                'assert payload["raw_calibration"]["version"] in {"T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0", "T0110_RETEST_SOURCE_FIELDS_V0"}',
            )
        ],
        repo_root / "tests" / "test_t0108a_b9_retest_mixed_metadata_compat.py": [
            (
                'assert raw["version"] in {"T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0"}',
                'assert raw["version"] in {"T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0", "T0110_RETEST_SOURCE_FIELDS_V0"}',
            )
        ],
        repo_root / "tests" / "test_t0109_b9_retest_source_signals_v0.py": [
            (
                'assert payload["raw_calibration"]["version"] == "T0109_RETEST_SOURCE_SIGNALS_V0"',
                'assert payload["raw_calibration"]["version"] in {"T0109_RETEST_SOURCE_SIGNALS_V0", "T0110_RETEST_SOURCE_FIELDS_V0"}',
            )
        ],
    }

    for path, pairs in replacements.items():
        if not path.exists():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")
        changed = False
        for old, new in pairs:
            if old in text:
                text = text.replace(old, new, 1)
                changed = True
            elif new in text:
                pass
            else:
                raise RuntimeError(f"Could not locate assertion in {path}")
        if changed:
            path.write_text(text, encoding="utf-8")
            print(f"[OK] patched forward compatibility in {path.name}")
        else:
            print(f"[OK] forward compatibility already present in {path.name}")


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
        "T0109_B9_RETEST_SOURCE_SIGNALS_V0_START",
        "b9_retest_source_status",
        "b9_retest_source_evidence_score",
        "T0108_RETEST_MIXED_SPLIT_V0",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("T0110 requires T0109 first. Missing: " + ", ".join(missing))

    block = append_file.read_text(encoding="utf-8").strip() + "\n"
    target.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8")
    print("[OK] appended T0110 retest source fields V0 block")

    patch_forward_tests(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
