"""HTTP validation for PowerFlow B9 dashboard endpoint.

Run while the Flask cockpit server is active:
python test_b9_dashboard_api_v3.py
"""
from __future__ import annotations

import argparse
import json
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

DEFAULT_URL = "http://localhost:8880/api/b9-nodes-live?symbol=GBPUSD&limit=10"


def test_b9_api(url: str = DEFAULT_URL, timeout: float = 5.0) -> bool:
    try:
        with urlopen(url, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            payload = response.read().decode("utf-8")
    except (URLError, HTTPError, TimeoutError) as exc:
        print(f"[API ERROR] {exc}")
        return False
    except Exception as exc:  # pragma: no cover - operational guard
        print(f"[API ERROR] {exc}")
        return False

    if status != 200:
        print(f"[API ERROR] HTTP {status}")
        return False

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        print(f"[API ERROR] JSON invalide: {exc}")
        return False

    if "nodes" not in data or not isinstance(data["nodes"], list):
        print("[API ERROR] Cle 'nodes' manquante ou invalide")
        return False

    print(f"[API OK] {len(data['nodes'])} nodes recuperes")
    if data["nodes"]:
        node = data["nodes"][0]
        print(f"  Verdict: {node.get('price_verdict_candidate') or node.get('verdict')}")
        print(f"  Confidence: {node.get('confidence')}")
        print(f"  Zone: {node.get('zone_bounds')}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate /api/b9-nodes-live for dashboard panel.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    return 0 if test_b9_api(args.url, args.timeout) else 1


if __name__ == "__main__":
    raise SystemExit(main())
