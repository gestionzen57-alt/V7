from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_golden_terrain_fixture_builder import build_from_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="T0168 B9 Golden Terrain Fixture Builder V0")
    parser.add_argument("--golden-cases-csv", required=True, help="Path to T0150 golden terrain cases CSV")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--min-ready", type=int, default=1)
    args = parser.parse_args()

    result = build_from_csv(Path(args.golden_cases_csv), Path(args.output_dir))
    summary = result["summary"]
    printable = {k: v for k, v in summary.items() if k != "files"}
    print(json.dumps(printable, ensure_ascii=False, indent=2))

    if summary.get("forbidden_language_hits"):
        return 1
    if summary.get("ready_count", 0) < args.min_ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
