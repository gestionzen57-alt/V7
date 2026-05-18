from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import sys
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pf_t009_source_quality_hard_gate import (
    VERSION,
    enrich_summary_source_quality,
    get_moments,
    summarize,
)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            cleaned = dict(row)
            for key, value in list(cleaned.items()):
                if isinstance(value, (list, dict)):
                    cleaned[key] = json.dumps(value, ensure_ascii=False)
            writer.writerow(cleaned)


def write_md(path: Path, summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    lines = [
        '# T0133 — B9 Source Quality Hard Gate V0',
        '',
        '## Phrase de cap',
        '',
        'B9 ne cherche pas le signal.  ',
        "B9 cherche la trace laissée par l'effort.  ",
        'Une scène proxy ne devient jamais une vérité raw.',
        '',
        '## Résumé exécutif',
        '',
        f"- Moments analysés : {summary['moments']}",
        f"- Raw claim allowed : {summary['raw_claim_allowed_count']}",
        f"- Confirmation claim allowed : {summary['confirmation_claim_allowed_count']}",
        f"- NUANCED promus à confirmed : {summary['nuanced_promoted_to_confirmed_count']}",
        f"- RAW_UNAVAILABLE autorisés : {summary['raw_unavailable_allowed_count']}",
        '',
        '## Counts par état',
        '',
    ]
    for state, count in sorted(summary['state_counts'].items()):
        lines.append(f'- {state}: {count}')
    lines += ['', '## Counts par famille source', '']
    for family, count in sorted(summary['family_counts'].items()):
        lines.append(f'- {family}: {count}')
    lines += ['', '## Règles hard gate', '',
        '- FORCE_SNAPSHOT_DERIVED reste séparé de RECOVERED_EXISTING_B9_SUMMARY.',
        '- NUANCED_BY_RAW ne doit jamais être présenté comme CONFIRMED_BY_RAW.',
        '- RAW_UNAVAILABLE sort de la mémoire active.',
        '- Une source proxy ou reconstruite garde sa provenance visible.',
        '- Un claim raw n’est permis que si la visibilité raw complète est explicite.',
        '',
        '## Échantillon de scènes',
        ''
    ]
    for row in rows[:10]:
        ident = row.get('moment_id') or row.get('scene_id') or row.get('time_start') or 'moment'
        lines.append(f"### {ident}")
        lines.append(f"- Famille : {row.get('b9_source_truth_family')}")
        lines.append(f"- Gate : {row.get('b9_source_quality_gate_state')}")
        lines.append(f"- Lecture : {row.get('b9_source_quality_reading_fr')}")
        lines.append('')
    lines += ['## Ce que B9 ne doit pas conclure', '',
        '- Pas de BUY/SELL.',
        '- Pas de probabilité de succès.',
        '- Pas de durcissement proxy vers raw.',
        '- Pas de confusion entre nuanced et confirmed.',
        '',
        '## Prochaine brique',
        '',
        'T0134 — B9 French Trader Scene Report V0.',
        ''
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines), encoding='utf-8', newline='\n')


def build(sequence_summary_json: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = load_json(sequence_summary_json)
    enriched = enrich_summary_source_quality(summary)
    moments = get_moments(enriched)
    manifest = summarize(enriched)
    manifest['input_json'] = str(sequence_summary_json)
    manifest['output_dir'] = str(output_dir)

    base_fields = [
        'moment_id','scene_id','date','time_start','time_end','source_family','summary_recovery_type','source_mode','data_visibility','confidence_cap',
        'proxy_vs_raw_verdict','proxy_raw_agreement_state','source_quality_score','source_quality_state','raw_tick_count',
        'b9_source_truth_family','b9_source_quality_gate_state','b9_source_quality_gate_severity','b9_source_quality_flags',
        'b9_source_confidence_cap_effective','b9_raw_claim_allowed','b9_confirmation_claim_allowed','b9_source_quality_reading_fr','b9_source_quality_limits'
    ]

    rows = [dict(m) for m in moments]
    write_json(output_dir / 'B9_SOURCE_QUALITY_HARD_GATE_V0.json', manifest)
    write_json(output_dir / 'B9_SOURCE_QUALITY_HARD_GATE_ENRICHED_SUMMARY_V0.json', enriched)
    write_csv(output_dir / 'B9_SOURCE_QUALITY_HARD_GATE_ROWS_V0.csv', rows, base_fields)
    count_rows = [{'kind': 'state', 'name': k, 'count': v} for k, v in sorted(manifest['state_counts'].items())]
    count_rows += [{'kind': 'family', 'name': k, 'count': v} for k, v in sorted(manifest['family_counts'].items())]
    write_csv(output_dir / 'B9_SOURCE_QUALITY_HARD_GATE_COUNTS_V0.csv', count_rows, ['kind','name','count'])
    write_md(output_dir / 'B9_SOURCE_QUALITY_HARD_GATE_V0.md', manifest, rows)

    zip_path = output_dir / 'B9_SOURCE_QUALITY_HARD_GATE_V0.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in output_dir.iterdir():
            if p.is_file() and p.name != zip_path.name:
                z.write(p, arcname=p.name)
    manifest['zip'] = str(zip_path)
    write_json(output_dir / 'B9_SOURCE_QUALITY_HARD_GATE_MANIFEST.json', manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description='T0133 B9 Source Quality Hard Gate V0')
    parser.add_argument('--sequence-summary-json', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    manifest = build(Path(args.sequence_summary_json), Path(args.output_dir))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
