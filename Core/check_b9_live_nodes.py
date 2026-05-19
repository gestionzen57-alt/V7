#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    core = Path(__file__).resolve().parent
    node_dir = core / "output" / "b9_nodes_live"
    files = sorted(node_dir.glob("*.json")) if node_dir.exists() else []
    print(f"[B9-NODES] dir={node_dir}")
    print(f"[B9-NODES] count={len(files)}")
    for path in files[-20:]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[B9-NODES] unreadable {path.name}: {exc}")
            continue
        node_id = data.get("node_id", data.get("id", path.stem))
        symbol = data.get("symbol", data.get("raw", {}).get("symbol", "UNKNOWN"))
        verdict = data.get("verdict", data.get("price_verdict_candidate", "UNKNOWN"))
        print(f"[B9-NODES] {path.name} node_id={node_id} symbol={symbol} verdict={verdict}")
    return 0 if files else 1


if __name__ == "__main__":
    raise SystemExit(main())
