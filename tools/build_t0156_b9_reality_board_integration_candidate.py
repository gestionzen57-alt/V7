from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_reality_board_integration_candidate import run_from_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build T0156 B9 Reality Board integration candidate payload.")
    parser.add_argument("--attention-packet-json", required=True, help="Input T0155 trader attention packet JSON")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_from_file(Path(args.attention_packet_json), Path(args.output_dir))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
