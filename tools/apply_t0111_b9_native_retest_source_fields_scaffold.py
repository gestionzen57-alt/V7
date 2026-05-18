#!/usr/bin/env python
"""T0111 safe installer helper.

This tool installs the T0111 helper module and, if a known summarizer
integration point exists, adds an opt-in import/comment marker only.

It deliberately avoids brittle monkey-patching of pf_t009_sequence_summarizer.py.
Claude or the main GPT can then wire the helper at the exact moment creation
point after inspecting the current summarizer code.
"""
from __future__ import annotations

import argparse
from pathlib import Path


MARKER = "# T0111_NATIVE_RETEST_SOURCE_FIELDS_AVAILABLE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    root = Path(args.repo_root)
    helper = root / "pf_t0111_native_retest_source_fields.py"
    summarizer = root / "pf_t009_sequence_summarizer.py"

    if not helper.exists():
        raise FileNotFoundError(helper)

    if not summarizer.exists():
        print("[WARN] pf_t009_sequence_summarizer.py not found; helper installed only")
        return 0

    text = summarizer.read_text(encoding="utf-8")
    if MARKER in text:
        print("[OK] T0111 marker already present in summarizer")
        return 0

    insert = (
        "\n# T0111 native retest source fields helper is available.\n"
        "# Wire enrich_moment_with_native_retest_source_fields(moment) at the exact\n"
        "# moment creation point after inspecting the summarizer structure.\n"
        f"{MARKER}\n"
    )

    # Safe marker only: no semantic modification.
    summarizer.write_text(text.rstrip() + "\n" + insert + "\n", encoding="utf-8")
    print("[OK] added T0111 availability marker to pf_t009_sequence_summarizer.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
