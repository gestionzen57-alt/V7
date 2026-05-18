from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_trader_attention_packet import (  # noqa: E402
    VERSION,
    build_trader_attention_packet,
    load_json,
    packet_to_row,
    render_markdown,
    write_json,
)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def zip_outputs(output_dir: Path) -> Path:
    zip_path = output_dir / "B9_TRADER_ATTENTION_PACKET_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in output_dir.rglob("*"):
            if p.is_file() and p != zip_path:
                zf.write(p, p.relative_to(output_dir))
    return zip_path


def run(args: argparse.Namespace) -> dict:
    payload = load_json(args.input_json)
    packet = build_trader_attention_packet(payload)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    packet_json = out / "B9_TRADER_ATTENTION_PACKET_V0.json"
    packet_md = out / "B9_TRADER_ATTENTION_PACKET_V0.md"
    packet_csv = out / "B9_TRADER_ATTENTION_PACKET_V0.csv"
    manifest_json = out / "B9_TRADER_ATTENTION_PACKET_MANIFEST.json"

    write_json(packet_json, packet)
    packet_md.write_text(render_markdown(packet), encoding="utf-8", newline="\n")
    write_csv(packet_csv, [packet_to_row(packet)])

    summary = {
        "version": VERSION,
        "packet_state": packet["packet_state"],
        "packet_id": packet["packet_id"],
        "candidate_id": packet["candidate_id"],
        "scene_state": packet["scene_state"],
        "price_verdict": packet["price_verdict"],
        "match_count": packet["memory_context"].get("match_count", 0),
        "top_match_film_id": packet["memory_context"].get("top_match_film_id", ""),
        "false_positive_context_available": packet["memory_context"].get("false_positive_context_available", False),
        "no_trade_decision_guard": packet["no_trade_decision_guard"],
        "forbidden_language_hits": packet["evidence"].get("forbidden_language_hits", []),
        "blocked_reason": packet.get("blocked_reason", ""),
        "outputs": {
            "json": str(packet_json),
            "md": str(packet_md),
            "csv": str(packet_csv),
        },
    }
    write_json(manifest_json, summary)
    zip_path = zip_outputs(out)
    summary["zip"] = str(zip_path)
    write_json(manifest_json, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B9 Trader Attention Packet V0")
    parser.add_argument("--input-json", required=True, help="B9 enriched scene / live brief / payload JSON")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
