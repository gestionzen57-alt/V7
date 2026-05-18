from __future__ import annotations

import argparse
import csv
import json
import zipfile
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_scene_role_requalifier import (
    VERSION,
    enrich_sequence_summary_scene_roles,
    validate_enriched_summary,
)


def read_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def moment_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows=[]
    for i, m in enumerate(summary.get('moments') or [], 1):
        if not isinstance(m, dict):
            continue
        evidence = m.get('b9_scene_role_evidence') or {}
        rows.append({
            'index': i,
            'time_start': m.get('time_start') or m.get('start_time') or '',
            'time_end': m.get('time_end') or m.get('end_time') or '',
            'label_fr': m.get('label_fr') or m.get('label') or m.get('moment_type') or '',
            'b9_scene_role_state': m.get('b9_scene_role_state') or '',
            'b9_scene_role_code': m.get('b9_scene_role_code') or '',
            'b9_scene_role_fr': m.get('b9_scene_role_fr') or '',
            'b9_scene_role_reason_fr': m.get('b9_scene_role_reason_fr') or '',
            'effort_result_progress_state': evidence.get('effort_result_progress_state') or m.get('b9_effort_result_progress_state') or '',
            'retest_result': evidence.get('retest_result') or m.get('retest_result') or m.get('b9_native_retest_judgment') or '',
            'source_gate_state': evidence.get('source_gate_state') or m.get('b9_source_quality_gate_state') or '',
            'center_delta_pips': evidence.get('center_delta_pips', ''),
            'center_range_pips': evidence.get('center_range_pips', ''),
            'limits': ' | '.join(m.get('b9_scene_role_limits') or []),
        })
    return rows


def counts_rows(counts: Dict[str, int], key_name: str) -> List[Dict[str, Any]]:
    return [{key_name: k, 'count': v} for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def write_markdown(path: Path, manifest: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    lines=[]
    lines.append('# T0140 — B9 Scene Role Requalifier V0')
    lines.append('')
    lines.append('## Résumé exécutif')
    lines.append('')
    lines.append('B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.')
    lines.append('T0140 requalifie les moments B9 en rôles de scène lisibles en français trader.')
    lines.append('')
    lines.append('## Counts')
    lines.append('')
    lines.append(f"- Moments: {manifest['moments']}")
    lines.append(f"- Forbidden language hits: {manifest['forbidden_language_hit_count']}")
    lines.append(f"- Missing required fields: {sum(manifest['missing_required_field_counts'].values()) if manifest['missing_required_field_counts'] else 0}")
    lines.append('')
    lines.append('## Role counts')
    lines.append('')
    for code,count in sorted(manifest['role_counts'].items(), key=lambda kv:(-kv[1], kv[0])):
        lines.append(f"- {code}: {count}")
    lines.append('')
    lines.append('## Moments')
    lines.append('')
    for r in rows:
        lines.append(f"### {r['index']}. {r['time_start']} → {r['time_end']}")
        lines.append(f"- Label: {r['label_fr']}")
        lines.append(f"- Rôle: {r['b9_scene_role_fr']} (`{r['b9_scene_role_code']}`)")
        lines.append(f"- Pourquoi: {r['b9_scene_role_reason_fr']}")
        lines.append(f"- Limites: {r['limits']}")
        lines.append('')
    lines.append('## Ce que B9 ne doit pas conclure')
    lines.append('')
    lines.append('- Aucun ordre directionnel.')
    lines.append('- Aucun ordre d’exécution.')
    lines.append('- Aucune statistique de réussite.')
    lines.append('- Une requalification de rôle n’est pas une prédiction.')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')


def zip_outputs(output_dir: Path) -> Path:
    zip_path = output_dir / 'B9_SCENE_ROLE_REQUALIFIER_V0.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in output_dir.iterdir():
            if p == zip_path or p.is_dir():
                continue
            z.write(p, p.name)
    return zip_path


def run(sequence_summary_json: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = read_json(sequence_summary_json)
    enriched = enrich_sequence_summary_scene_roles(summary)
    validation = validate_enriched_summary(enriched)
    rows = moment_rows(enriched)
    state_counts = validation['state_counts']
    role_counts = validation['role_counts']
    manifest = {
        'version': VERSION,
        'input': str(sequence_summary_json),
        'output_dir': str(output_dir),
        **validation,
        'read_only': True,
        'db_write': False,
        'dashboard': False,
        'telegram': False,
        'buy_sell': False,
        'probability_of_success': False,
    }
    write_json(output_dir/'B9_SCENE_ROLE_REQUALIFIER_V0.json', {'manifest': manifest, 'summary': enriched})
    write_json(output_dir/'B9_SCENE_ROLE_REQUALIFIER_ENRICHED_SUMMARY_V0.json', enriched)
    write_csv(output_dir/'B9_SCENE_ROLE_REQUALIFIER_ROWS_V0.csv', rows, [
        'index','time_start','time_end','label_fr','b9_scene_role_state','b9_scene_role_code','b9_scene_role_fr',
        'b9_scene_role_reason_fr','effort_result_progress_state','retest_result','source_gate_state',
        'center_delta_pips','center_range_pips','limits'
    ])
    write_csv(output_dir/'B9_SCENE_ROLE_REQUALIFIER_STATE_COUNTS_V0.csv', counts_rows(state_counts,'state'), ['state','count'])
    write_csv(output_dir/'B9_SCENE_ROLE_REQUALIFIER_ROLE_COUNTS_V0.csv', counts_rows(role_counts,'role_code'), ['role_code','count'])
    write_markdown(output_dir/'B9_SCENE_ROLE_REQUALIFIER_V0.md', manifest, rows)
    manifest['zip'] = str(zip_outputs(output_dir))
    write_json(output_dir/'B9_SCENE_ROLE_REQUALIFIER_MANIFEST.json', manifest)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description='T0140 B9 Scene Role Requalifier V0')
    ap.add_argument('--sequence-summary-json', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()
    manifest = run(Path(args.sequence_summary_json), Path(args.output_dir))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
