from __future__ import annotations

import argparse
import csv
import json
import zipfile
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_telegram_fr_gate_candidate import build_telegram_gate_candidate, load_json, dump_json, VERSION


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_markdown(result: Dict[str, Any]) -> str:
    lines = [
        "# B9 Telegram FR Gate Candidate V0",
        "",
        "## Résumé",
        f"- gate_state: `{result['gate_state']}`",
        f"- candidate_id: `{result['candidate_id']}`",
        f"- scene_state: `{result['scene_state']}`",
        f"- price_verdict: `{result['price_verdict']}`",
        f"- match_count: `{result['match_count']}`",
        f"- top_match_film_id: `{result['top_match_film_id']}`",
        f"- false_positive_context_available: `{str(result['false_positive_context_available']).lower()}`",
        f"- no_send_guard: `{str(result['no_send_guard']).lower()}`",
        f"- no_trade_decision_guard: `{str(result['no_trade_decision_guard']).lower()}`",
        "",
        "## Message Telegram candidat — no-send",
        "```text",
        result["telegram_message_fr"],
        "```",
        "",
        "## Limites techniques",
    ]
    limits = result.get("technical_limits") or []
    if limits:
        lines.extend([f"- {x}" for x in limits])
    else:
        lines.append("- Aucune limite additionnelle fournie par l'entrée.")
    lines += [
        "",
        "## Doctrine",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l’effort.",
        "Le message Telegram candidat réveille l’attention, il ne décide pas.",
        "",
        "## Garde-fous",
        "- Read-only.",
        "- Aucun envoi Telegram.",
        "- Aucun dashboard live.",
        "- Aucune écriture powerflow.db.",
        "- Aucune écriture tick_archive.db.",
        "- Aucun ordre directionnel.",
        "- Aucun taux de réussite.",
    ]
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> Dict[str, Any]:
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = load_json(args.reality_board_payload_json)
    result = build_telegram_gate_candidate(data)

    dump_json(str(out / "B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json"), result)
    dump_json(str(out / "B9_TELEGRAM_FR_PAYLOAD_CANDIDATE_V0.json"), result["telegram_payload_candidate"])
    write_text(out / "B9_TELEGRAM_FR_GATE_CANDIDATE_V0.md", build_markdown(result))
    write_text(out / "B9_TELEGRAM_FR_MESSAGE_CANDIDATE_V0.txt", result["telegram_message_fr"] + "\n")

    with open(out / "B9_TELEGRAM_FR_GATE_CANDIDATE_V0.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "version", "gate_state", "candidate_id", "scene_state", "price_verdict",
            "memory_confidence_ladder", "match_count", "top_match_film_id",
            "false_positive_context_available", "no_send_guard", "no_trade_decision_guard",
            "forbidden_language_hits",
        ])
        writer.writeheader()
        row = dict(result)
        row["forbidden_language_hits"] = "|".join(result.get("forbidden_language_hits") or [])
        row.pop("technical_limits", None)
        row.pop("telegram_message_fr", None)
        row.pop("telegram_payload_candidate", None)
        writer.writerow({k: row.get(k, "") for k in writer.fieldnames})

    manifest = {
        "version": VERSION,
        "gate_state": result["gate_state"],
        "candidate_id": result["candidate_id"],
        "input": str(args.reality_board_payload_json),
        "outputs": [p.name for p in sorted(out.iterdir()) if p.is_file()],
        "read_only": True,
        "telegram_send": False,
        "dashboard_live": False,
        "db_write": False,
    }
    dump_json(str(out / "B9_TELEGRAM_FR_GATE_CANDIDATE_MANIFEST.json"), manifest)

    zip_path = out / "B9_TELEGRAM_FR_GATE_CANDIDATE_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):
            if p.is_file() and p != zip_path:
                z.write(p, p.name)

    return {
        "version": VERSION,
        "gate_state": result["gate_state"],
        "candidate_id": result["candidate_id"],
        "match_count": result["match_count"],
        "top_match_film_id": result["top_match_film_id"],
        "false_positive_context_available": result["false_positive_context_available"],
        "no_send_guard": result["no_send_guard"],
        "forbidden_language_hits": result["forbidden_language_hits"],
        "zip": str(zip_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B9 Telegram FR gate candidate V0")
    parser.add_argument("--reality-board-payload-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
