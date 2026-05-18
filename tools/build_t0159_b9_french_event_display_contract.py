from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_b9_french_event_display_contract import VERSION, build_contract, translate_event, validate_contract


def _load_json(path: str | None) -> Any:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_extra_entries(payload: Any) -> List[Dict[str, Any]]:
    if not payload:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("extra_entries", "events", "entries"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "enum_key",
        "label_fr_short",
        "phrase_fr_trader",
        "dashboard_text_fr",
        "telegram_text_fr",
        "technical_limit_fr",
        "forbidden_formulation_fr",
        "severity_hint",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def _write_md(path: Path, rows: List[Dict[str, str]], validation: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B9 French Event Display Contract V0",
        "",
        "## Résumé exécutif",
        "",
        f"Contrat: `{validation['contract_state']}`",
        f"Entrées: `{validation['entry_count']}`",
        "",
        "B9 garde ses enums techniques pour les tests. Dashboard et Telegram affichent en français trader.",
        "",
        "## Counts par catégorie",
        "",
    ]
    for cat, count in validation["category_counts"].items():
        lines.append(f"- `{cat}`: {count}")
    lines.extend(["", "## Entrées", ""])
    for row in rows:
        lines.append(f"### `{row['enum_key']}`")
        lines.append(f"- Catégorie: `{row['category']}`")
        lines.append(f"- Court: {row['label_fr_short']}")
        lines.append(f"- Trader: {row['phrase_fr_trader']}")
        lines.append(f"- Limite: {row['technical_limit_fr']}")
        lines.append("")
    lines.extend([
        "## Garde-fous",
        "",
        "- Read-only.",
        "- Aucun dashboard live.",
        "- Aucun envoi Telegram.",
        "- Aucune écriture `powerflow.db`.",
        "- Aucune écriture `tick_archive.db`.",
        "- Aucun ordre directionnel.",
        "- Aucun taux de réussite.",
        "",
        "B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _zip_dir(zip_path: Path, files: List[Path], base: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            if path.exists():
                zf.write(path, path.relative_to(base))


def run(args: argparse.Namespace) -> Dict[str, Any]:
    payload = _load_json(args.extra_events_json)
    rows = build_contract(_extract_extra_entries(payload))
    validation = validate_contract(rows)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json"
    csv_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.csv"
    md_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.md"
    manifest_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_MANIFEST.json"
    examples_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_EXAMPLES_V0.json"

    json_path.write_text(json.dumps({"version": VERSION, "validation": validation, "entries": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(csv_path, rows)
    _write_md(md_path, rows, validation)

    examples = [
        translate_event("SCENE_ACCEPTED", rows),
        translate_event("PULLBACK_ABSORBED", rows),
        translate_event("MEMORY_PARTIAL_COMPARABLE", rows),
        translate_event("B6_FALSE_POSITIVE_CONTEXT_HIGH", rows),
        translate_event("RAW_UNAVAILABLE_REJECTED", rows),
    ]
    examples_path.write_text(json.dumps({"version": VERSION, "examples": examples}, ensure_ascii=False, indent=2), encoding="utf-8")

    files = [json_path, csv_path, md_path, manifest_path, examples_path]
    zip_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.zip"
    manifest = {
        "version": VERSION,
        "output_dir": str(output_dir),
        "files": [str(p) for p in files if p.name != manifest_path.name] + [str(zip_path)],
        "validation": validation,
        "read_only": True,
        "db_write": False,
        "dashboard_live": False,
        "telegram_send": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    files = [json_path, csv_path, md_path, manifest_path, examples_path]
    _zip_dir(zip_path, files, output_dir)

    summary = {
        "version": VERSION,
        "contract_state": validation["contract_state"],
        "entry_count": validation["entry_count"],
        "category_counts": validation["category_counts"],
        "missing_required_fields": len(validation["missing_required_fields"]),
        "duplicate_enum_keys": len(validation["duplicate_enum_keys"]),
        "missing_categories": validation["missing_categories"],
        "forbidden_language_hits": validation["forbidden_language_hits"],
        "zip": str(zip_path),
    }
    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B9 French Event Display Contract V0")
    parser.add_argument("--extra-events-json", default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    summary = run(args)
    if summary["contract_state"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
