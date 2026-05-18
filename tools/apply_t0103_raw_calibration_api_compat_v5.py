#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path


START = "# --- T0103_RAW_CALIBRATION_FULL_API_COMPAT_V5_START ---"
END = "# --- T0103_RAW_CALIBRATION_FULL_API_COMPAT_V5_END ---"


def remove_old_v5_block(text: str) -> str:
    start = text.find(START)
    if start == -1:
        return text
    end = text.find(END, start)
    if end == -1:
        return text[:start].rstrip() + "\n"
    end += len(END)
    return (text[:start] + text[end:]).rstrip() + "\n"


def append_compat(repo_root: Path, compat_file: Path) -> None:
    target = repo_root / "pf_t009_raw_calibration.py"
    if not target.exists():
        raise FileNotFoundError(target)

    compat = compat_file.read_text(encoding="utf-8").strip() + "\n"
    text = target.read_text(encoding="utf-8")
    text = remove_old_v5_block(text)

    required = ["calibrate_summary_with_raw", "export_json", "export_markdown", "load_json"]
    missing = [name for name in required if f"def {name}" not in text]
    if missing or "class RawCalibrationConfig" not in text:
        target.write_text(text.rstrip() + "\n\n" + compat, encoding="utf-8")
        print("[OK] appended full T0103 API compat V5 block")
    else:
        # Still append V5 if the old config exists but runner API is incomplete.
        target.write_text(text.rstrip() + "\n\n" + compat, encoding="utf-8")
        print("[OK] refreshed full T0103 API compat V5 block")


def patch_runner(repo_root: Path) -> None:
    runner = repo_root / "scripts" / "RUN_T0103_WEEKLY_RAW_CALIBRATION_V36.ps1"
    if not runner.exists():
        raise FileNotFoundError(runner)

    text = runner.read_text(encoding="utf-8")
    changed = False

    if 'throw "Raw calibration failed for $safe"' not in text:
        needle = "    --raw-data-visibility $RawDataVisibility\n"
        if needle not in text:
            raise RuntimeError("Could not locate raw-data-visibility line in runner")
        text = text.replace(
            needle,
            needle + '    if ($LASTEXITCODE -ne 0) { throw "Raw calibration failed for $safe" }\n',
            1,
        )
        changed = True

    if 'throw "Weekly report aggregation failed"' not in text:
        needle = "  --shift-min $BrokerTimeShiftMin\n"
        if needle not in text:
            raise RuntimeError("Could not locate shift-min line in runner")
        text = text.replace(
            needle,
            needle + 'if ($LASTEXITCODE -ne 0) { throw "Weekly report aggregation failed" }\n',
            1,
        )
        changed = True

    if changed:
        runner.write_text(text, encoding="utf-8")
        print("[OK] patched runner fail-fast guards")
    else:
        print("[OK] runner fail-fast guards already present")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--compat-file", required=True)
    args = parser.parse_args()

    root = Path(args.repo_root)
    append_compat(root, Path(args.compat_file))
    patch_runner(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
