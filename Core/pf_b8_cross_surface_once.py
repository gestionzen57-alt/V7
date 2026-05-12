from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, data: dict[str, Any], pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2 if pretty else None, ensure_ascii=False),
        encoding="utf-8",
    )


def write_txt(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"B8 CROSS SYMBOL | {data.get('status')} | {data.get('attention')}",
        f"symbols={','.join(data.get('symbols') or [])}",
        f"coverage={data.get('coverage_state')}",
        f"message={data.get('message')}",
        "",
        "ROLE",
        "- B8 qualifie la cohérence cross-symbol.",
        "- B8 ne bloque pas le scheduler.",
        "- B8 sert à distinguer compression vraie vs fake / confluence vs isolement.",
        "",
        "TECHNICAL RISKS",
    ]

    for r in data.get("technical_risks") or []:
        lines.append(f"- {r}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def classify(stdout: str, stderr: str, returncode: int) -> tuple[str, str, str, list[str]]:
    text = (stdout + "\n" + stderr).strip()

    if "B8_CROSS_SYMBOL_DEGRADED" in text or "Not enough usable cross pairs" in text:
        return (
            "DEGRADED",
            "WATCH_CONTEXT",
            "INSUFFICIENT_CROSS_COVERAGE",
            ["B8_INSUFFICIENT_CROSS_PAIR_COVERAGE"],
        )

    if returncode == 0:
        return (
            "OK",
            "CONTEXT",
            "B8_AVAILABLE",
            [],
        )

    return (
        "ERROR",
        "WATCH_CONTEXT",
        "B8_RUNTIME_ERROR_NON_BLOCKING",
        ["B8_RUNTIME_ERROR"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--output", default="output/dashboard_surface/b8_cross_surface.json")
    parser.add_argument("--txt", default="output/dashboard_surface/b8_cross_surface.txt")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "run_cross_symbol_validation_once.py",
        "--db", args.db,
        "--symbols", args.symbols,
        "--pretty",
    ]

    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    status, attention, coverage_state, risks = classify(stdout, stderr, proc.returncode)

    data = {
        "method": "B8_CROSS_SURFACE_V738B",
        "timestamp_utc": utc_now(),
        "status": status,
        "attention": attention,
        "coverage_state": coverage_state,
        "symbols": [s.strip().upper() for s in args.symbols.split(",") if s.strip()],
        "returncode": proc.returncode,
        "message": (stdout.strip() or stderr.strip()).replace("\n", " | ")[:1200],
        "technical_risks": risks,
        "role": "B8 cross-symbol validation qualifies confluence and fake-risk. It is non-blocking.",
        "inputs": {
            "db": args.db,
        },
    }

    write_json(Path(args.output), data, pretty=args.pretty)
    write_txt(Path(args.txt), data)

    print(
        f"B8_CROSS_SURFACE_OK | status={status} | attention={attention} | "
        f"coverage={coverage_state} | out={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
