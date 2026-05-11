from __future__ import annotations

import argparse
import json
from pathlib import Path
from pf_session_overlay import get_session_context


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow Session Overlay V2 runner")
    parser.add_argument("--timestamp", default=None, help="UTC ISO timestamp, e.g. 2026-05-11T07:05:00Z")
    parser.add_argument("--output", default="output/session_context.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    data = get_session_context(args.timestamp)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
