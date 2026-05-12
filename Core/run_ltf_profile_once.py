from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("> " + " ".join(cmd))
    p = subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if p.stdout:
        print(p.stdout.strip())
    if p.stderr:
        print(p.stderr.strip())
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    base = Path("output/dashboard_surface") / args.symbol
    profile = base / "ltf_profile.json"
    mem = base / "ltf_session_memory.json"
    md = base / "ltf_session_memory.md"

    cmd = [sys.executable, "pf_time_profile_window.py", "--db", args.db, "--symbol", args.symbol, "--profile", "LTF", "--output", str(profile)]
    if args.pretty:
        cmd.append("--pretty")
    run(cmd)

    cmd = [sys.executable, "pf_time_profile_memory.py", "--profile-json", str(profile), "--memory-json", str(mem), "--memory-md", str(md)]
    if args.pretty:
        cmd.append("--pretty")
    run(cmd)

    print(f"LTF_PROFILE_ONCE_OK | symbol={args.symbol} | profile={profile} | memory={mem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
