#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

START = "# === T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_START ==="
END = "# === T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_END ==="
HELPER = """
# === T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_START ===
try:
    from pf_t009_sequence_summarizer_v4_integration import enrich_summary_v4_safe as _t0121_b9_v4_enrich
except Exception:
    def _t0121_b9_v4_enrich(summary):
        return summary
# === T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_END ===
"""


def patch_text(src: str) -> tuple[str, dict]:
    report = {"marker_already_present": START in src, "return_summary_replacements": 0, "state": ""}
    if START in src:
        report["state"] = "ALREADY_PATCHED"
        return src, report
    lines = src.splitlines()
    insert_at = 0
    for idx, line in enumerate(lines[:80]):
        stripped = line.strip()
        if stripped.startswith("from __future__") or stripped.startswith("import ") or stripped.startswith("from ") or stripped == "" or stripped.startswith("#"):
            insert_at = idx + 1
        elif idx > 0:
            break
    lines.insert(insert_at, HELPER.rstrip("\n"))
    patched = "\n".join(lines) + ("\n" if src.endswith("\n") else "")
    replacements = patched.count("return summary")
    patched2 = patched.replace("return summary", "return _t0121_b9_v4_enrich(summary)")
    report["return_summary_replacements"] = replacements
    report["state"] = "PATCHED_NATIVE_RETURN_SUMMARY" if replacements else "PATCHED_HELPER_ONLY_NO_SAFE_RETURN_SUMMARY_FOUND"
    return patched2, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summarizer", default="pf_t009_sequence_summarizer.py")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-report", default="outputs/b9_native_summarizer_v4_integration_patch_v0/T0121_INTEGRATION_APPLY_REPORT.json")
    args = parser.parse_args()
    path = Path(args.summarizer)
    if not path.exists():
        raise SystemExit(f"Summarizer not found: {path}")
    src = path.read_text(encoding="utf-8")
    patched, report = patch_text(src)
    report.update({
        "version": "T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_PATCH_V0",
        "summarizer": str(path),
        "dry_run": bool(args.dry_run),
        "read_only_db": True,
        "no_dashboard": True,
        "no_telegram": True,
        "no_buy_sell": True,
        "no_probability_of_success": True,
    })
    if not args.dry_run and patched != src:
        backup = path.with_suffix(path.suffix + ".t0121_backup")
        if not backup.exists():
            backup.write_text(src, encoding="utf-8")
        path.write_text(patched, encoding="utf-8")
        report["backup"] = str(backup)
    out = Path(args.output_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
