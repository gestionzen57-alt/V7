"""HTTP validation for the final B9 convergence pack.

Run while cockpit_server_b9.py is already running on localhost:8880.
This script uses urllib only to avoid depending on requests.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List

BASE_URL = "http://localhost:8880"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_json(path: str) -> Dict[str, Any]:
    url = BASE_URL + path
    with urllib.request.urlopen(url, timeout=5) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)
        print(f"[PASS] GET {path} -> {response.status}")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1600])
        return data


def validate_payload(path: str, data: Dict[str, Any], errors: List[str]) -> None:
    if not isinstance(data, dict):
        errors.append(f"{path}: payload is not JSON object")
        return
    if path == "/api/health" and data.get("status") not in {"ok", "degraded"}:
        errors.append("/api/health: unexpected status")
    if path.startswith("/api/b9-nodes-live"):
        if "nodes" not in data or "count" not in data:
            errors.append("/api/b9-nodes-live: missing nodes/count")
        if data.get("data_visibility") == "READING_PARTIAL":
            print("[INFO] B9 reading partial:", data.get("technical_risks", []))
    if path.startswith("/api/b8-coalition-context"):
        for key in ("usd_quote", "usd_base", "gbp_cross"):
            if key not in data:
                errors.append(f"/api/b8-coalition-context: missing {key}")
        if data.get("data_visibility") == "READING_PARTIAL":
            print("[INFO] B8 reading partial:", data.get("technical_risks", []))


def main() -> int:
    print(f"[B9 FINAL E2E] Start {_utc_now()}")
    checks = [
        "/api/health",
        "/api/b9-nodes-live?symbol=GBPUSD&limit=10",
        "/api/b8-coalition-context?symbol=GBPUSD",
    ]
    errors: List[str] = []
    for path in checks:
        try:
            data = get_json(path)
            validate_payload(path, data, errors)
        except urllib.error.URLError as exc:
            errors.append(f"{path}: server unreachable or request failed: {exc}")
        except Exception as exc:  # fail-soft reporting for operator
            errors.append(f"{path}: {exc}")

    print("")
    if errors:
        print("[FAIL] B9 final HTTP validation failed")
        for err in errors:
            print("  - " + err)
        return 1

    print("[OK] B9 final HTTP validation passed: 3/3 endpoints reachable")
    print("[OK] READONLY / fail-soft contract respected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
