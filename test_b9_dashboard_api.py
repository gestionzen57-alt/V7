"""Test endpoint /api/b9-nodes-live.

Usage:
    python test_b9_dashboard_api.py
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_URL = "http://localhost:8880/api/b9-nodes-live?symbol=GBPUSD&limit=10"


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310 - local runtime test URL
        status = response.getcode()
        body = response.read().decode("utf-8")
    if status != 200:
        raise RuntimeError(f"HTTP {status}: {body[:200]}")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise AssertionError("La réponse API doit être un objet JSON")
    return data


def test_b9_api(url: str = DEFAULT_URL) -> bool:
    try:
        data = _fetch_json(url)
        if "nodes" not in data:
            raise AssertionError("Clé 'nodes' manquante")
        if not isinstance(data["nodes"], list):
            raise AssertionError("'nodes' doit être une liste")

        print(f"[API OK] {len(data['nodes'])} nodes récupérés")
        if data["nodes"]:
            node = data["nodes"][0]
            print(f"  Verdict: {node.get('price_verdict_candidate')}")
            print(f"  Confidence: {node.get('confidence')}")
            print(f"  Zone: {node.get('zone_bounds')}")
        return True
    except (urllib.error.URLError, TimeoutError, RuntimeError, AssertionError, json.JSONDecodeError) as exc:
        print(f"[API ERROR] {exc}")
        return False


if __name__ == "__main__":
    endpoint = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    raise SystemExit(0 if test_b9_api(endpoint) else 1)
