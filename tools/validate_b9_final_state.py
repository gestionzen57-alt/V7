"""Local filesystem validation for the final B9 convergence pack."""
from __future__ import annotations

from pathlib import Path

REQUIRED_ANY = [
    ["Core/pf_engine_b9.py"],
    ["Core/pf_packet_requalifier_v767.py"],
    ["Core/cockpit_server_b9.py"],
    ["Core/pf_b9_runtime_bridge.py", "Core/scheduler_powerflow.py"],
    ["Core/dashboard_powerflow_v74.html", "dashboard_powerflow_v74.html"],
]


def main() -> int:
    root = Path.cwd()
    if root.name.lower() == "core":
        root = root.parent
    print(f"[B9-FINAL-STATE] repo_root={root}")
    missing = []
    for group in REQUIRED_ANY:
        if not any((root / p).exists() for p in group):
            missing.append(" or ".join(group))
    if missing:
        print("[B9-FINAL-STATE] MISSING")
        for item in missing:
            print("  - " + item)
        return 1
    print("[B9-FINAL-STATE] OK required surfaces present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
