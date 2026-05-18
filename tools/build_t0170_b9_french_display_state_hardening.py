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

from pf_b9_french_display_state_hardening import VERSION, write_outputs


def build(outputs_dir: Path, output_dir: Path, report_path: Path | None = None) -> Dict[str, object]:
    paths = write_outputs(outputs_dir, output_dir)
    zip_path = output_dir / "B9_FRENCH_DISPLAY_STATE_HARDENING_V0.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for value in paths.values():
            p = Path(value)
            zf.write(p, arcname=p.name)

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        md_text = Path(paths["md"]).read_text(encoding="utf-8")
        report_path.write_text(
            "\n".join(
                [
                    "# T0170 — B9 French Display State Hardening V0",
                    "",
                    "## Rapport intégré",
                    "",
                    md_text,
                    "",
                    "## Contraintes",
                    "",
                    "- Read-only.",
                    "- Aucune DB.",
                    "- Aucun dashboard live.",
                    "- Aucun envoi Telegram.",
                    "- Aucune décision d'exécution.",
                    "- Aucune probabilité de résultat.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    return {
        "version": VERSION,
        "outputs_dir": str(outputs_dir),
        "output_dir": str(output_dir),
        "json": paths["json"],
        "enum_csv": paths["enum_csv"],
        "leaks_csv": paths["leaks_csv"],
        "md": paths["md"],
        "zip": str(zip_path),
        "report": str(report_path) if report_path else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build T0170 B9 French Display State Hardening V0")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--output-dir", default="outputs/b9_french_display_state_hardening_v0")
    parser.add_argument("--report-path", default="Docs/Reports/T0170_B9_FRENCH_DISPLAY_STATE_HARDENING_REPORT.md")
    args = parser.parse_args()

    summary = build(Path(args.outputs_dir), Path(args.output_dir), Path(args.report_path) if args.report_path else None)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
