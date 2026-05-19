"""
PowerFlow B9 dashboard API live check.
Uses only Python stdlib to avoid dependency friction on Windows.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://localhost:8880/api/b9-nodes-live?symbol=GBPUSD&limit=10"


def test_b9_api(url: str = DEFAULT_URL, timeout: float = 5.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            if status != 200:
                print(f"[API ERROR] HTTP {status}")
                return False
            payload = response.read().decode("utf-8")

        data = json.loads(payload)
        if "nodes" not in data:
            print("[API ERROR] Cle 'nodes' manquante")
            return False
        if not isinstance(data["nodes"], list):
            print("[API ERROR] 'nodes' doit etre une liste")
            return False

        print(f"[API OK] {len(data['nodes'])} nodes recuperes")
        if data["nodes"]:
            node = data["nodes"][0]
            print(f"  Verdict: {node.get('price_verdict_candidate')}")
            print(f"  Confidence: {node.get('confidence')}")
            print(f"  Zone: {node.get('zone_bounds')}")
        return True
    except urllib.error.URLError as exc:
        print(f"[API ERROR] {exc}")
        return False
    except Exception as exc:
        print(f"[API ERROR] {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate live B9 nodes API.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    return 0 if test_b9_api(args.url, args.timeout) else 1


if __name__ == "__main__":
    raise SystemExit(main())
