from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_b9_french_event_display_contract import VERSION, validate_contract, write_json_csv_md


def build(output_dir: Path, report_path: Path | None = None) -> Dict[str, object]:
    paths = write_json_csv_md(output_dir)
    validation = validate_contract()

    zip_path = output_dir / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in paths.values():
            p = Path(item)
            zf.write(p, arcname=p.name)

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            "\n".join(
                [
                    "# T0159 — B9 French Event Display Contract V0",
                    "",
                    "## Résumé",
                    "",
                    "Contrat de traduction français trader pour les enums B9/B6 destinés aux surfaces d’affichage.",
                    "",
                    "## Sorties",
                    "",
                    f"- JSON : `{paths['json']}`",
                    f"- CSV : `{paths['csv']}`",
                    f"- Markdown : `{paths['md']}`",
                    f"- ZIP : `{zip_path}`",
                    "",
                    "## Validation",
                    "",
                    f"- Version : `{VERSION}`",
                    f"- Events couverts : `{validation['total_events']}`",
                    f"- Passed : `{validation['passed']}`",
                    f"- Forbidden display hits : `{len(validation['forbidden_display_hits'])}`",
                    "",
                    "## Contraintes respectées",
                    "",
                    "- Read-only.",
                    "- Aucune DB.",
                    "- Aucun dashboard live.",
                    "- Aucun envoi Telegram.",
                    "- Aucune décision d’exécution.",
                    "- Aucune probabilité de résultat.",
                    "",
                    "## Lecture PowerFlow",
                    "",
                    "Le moteur garde les clés techniques. Les surfaces lisent le français trader.",
                    "Un enum inconnu n’est pas masqué : il ressort comme traduction à ajouter.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    return {
        "version": VERSION,
        "output_dir": str(output_dir),
        "json": paths["json"],
        "csv": paths["csv"],
        "md": paths["md"],
        "zip": str(zip_path),
        "report": str(report_path) if report_path else "",
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build T0159 B9 French Event Display Contract V0")
    parser.add_argument("--output-dir", default="outputs/b9_french_event_display_contract_v0")
    parser.add_argument("--report-path", default="Docs/Reports/T0159_B9_FRENCH_EVENT_DISPLAY_CONTRACT_REPORT.md")
    args = parser.parse_args()

    summary = build(Path(args.output_dir), Path(args.report_path) if args.report_path else None)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["validation"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
