from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT = Path("output/dashboard_surface")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        obj = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def run(cmd: list[str]) -> int:
    print("RUN:", " ".join(cmd))
    p = subprocess.run(cmd)
    return int(p.returncode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--zone-tf", type=int, default=15)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    args = ap.parse_args()

    py = sys.executable
    symbol = args.symbol.upper()

    rc = run([
        py,
        "pf_confluence_elastic.py",
        "--db",
        args.db,
        "--symbol",
        symbol,
        "--zone-tf",
        str(args.zone_tf),
        "--pretty",
    ])

    out_json = OUT / symbol / "eie_confluence.json"
    out_txt = OUT / symbol / "eie_confluence.txt"
    primary = load_json(out_json)

    missing_outputs = []
    if not out_json.exists():
        missing_outputs.append(str(out_json))
    if not out_txt.exists():
        missing_outputs.append(str(out_txt))

    if missing_outputs:
        rc = 2

    report = {
        "timestamp_utc": now_utc(),
        "method": "RUN_CONFLUENCE_ALERT_V74_SURFACE_ONLY",
        "symbol": symbol,
        "zone_tf": args.zone_tf,
        "dry_run": bool(args.dry_run),
        "send_requested": bool(args.send),
        "returncode": rc,
        "missing_outputs": missing_outputs,
        "outputs": {
            "eie_confluence_json": str(OUT / symbol / "eie_confluence.json"),
            "eie_confluence_txt": str(OUT / symbol / "eie_confluence.txt"),
        },
        "primary": primary,
        "note": "Surface-only EIE V7.4. Telegram gate will be added in next step.",
    }

    write_json(OUT / "eie_alert_queue.json", report)

    if missing_outputs:
        print("EIE_ALERT_QUEUE_FAIL | missing_outputs=" + ",".join(missing_outputs))
    else:
        print("EIE_ALERT_QUEUE_OK")
    print("json=", OUT / "eie_alert_queue.json")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
