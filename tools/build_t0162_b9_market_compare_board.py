#!/usr/bin/env python3
"""
T0162 - B9 Market Compare Board V0

Read-only market comparison board for PowerFlow B9 MAX.
It compares the current scene with B6 memory films and T0150 golden terrain cases.

Doctrine:
- Compare is not predict.
- No DB access.
- No dashboard direct write.
- No Telegram.
- No BUY/SELL.
- No probability of success.
- Technical risks only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = 'T0162_B9_MARKET_COMPARE_BOARD_V0'
OUTPUT_BASENAME = 'B9_MARKET_COMPARE_BOARD_V0'

FORBIDDEN_PATTERNS = [
    r'\bBUY\b',
    r'\bSELL\b',
    r'\bBUY_SIGNAL\b',
    r'\bSELL_SIGNAL\b',
    r'\bACHETER\b',
    r'\bVENDRE\b',
    r'probabilit[eé]\s+de\s+succ[eè]s',
    r'probability\s+of\s+success',
    r'taux\s+de\s+r[eé]ussite',
]

INPUT_CANDIDATES = {
    'live_brief': [
        'outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json',
        'outputs/b9_live_brief_v0/B9_LIVE_BRIEF_ONCE_V0.json',
        'B9_LIVE_BRIEF_ONCE_V0.json',
    ],
    'attention_packet': [
        'outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json',
        'outputs/b9_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json',
        'B9_TRADER_ATTENTION_PACKET_V0.json',
    ],
    'reality_board': [
        'outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json',
        'outputs/b9_reality_board_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json',
        'B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json',
    ],
    'human_terrain_synthesis': [
        'outputs/b9_human_terrain_synthesis_v0/B9_HUMAN_TERRAIN_SYNTHESIS_V0.json',
        'outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_SYNTHESIS_V0.json',
        'B9_HUMAN_TERRAIN_SYNTHESIS_V0.json',
        'B6_HUMAN_TERRAIN_SYNTHESIS_V0.json',
    ],
    'golden_cases_csv': [
        'outputs/t0150_b9_golden_terrain_cases_v1/T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv',
        'outputs/b9_golden_terrain_cases_v1/T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv',
        'Docs/Reports/T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv',
        'T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv',
    ],
    'memory_confidence_ladder_json': [
        'outputs/b9_memory_confidence_ladder_v0/B9_MEMORY_CONFIDENCE_LADDER_V0.json',
        'outputs/b9_memory_confidence_ladder_v0/B9_MEMORY_CONFIDENCE_LADDER_OUTPUT_V0.json',
        'B9_MEMORY_CONFIDENCE_LADDER_V0.json',
    ],
    'memory_confidence_ladder_csv': [
        'outputs/b9_memory_confidence_ladder_v0/B9_MEMORY_CONFIDENCE_LADDER_V0.csv',
        'outputs/b9_memory_confidence_ladder_v0/B9_MEMORY_CONFIDENCE_LADDER_MATCHES_V0.csv',
        'B9_MEMORY_CONFIDENCE_LADDER_V0.csv',
    ],
    'false_positive_explainer_json': [
        'outputs/b9_false_positive_memory_explainer_v0/B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.json',
        'outputs/b9_false_positive_memory_explainer_v0/B9_FALSE_POSITIVE_MEMORY_EXPLAINER_OUTPUT_V0.json',
        'B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.json',
    ],
    'false_positive_explainer_csv': [
        'outputs/b9_false_positive_memory_explainer_v0/B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.csv',
        'outputs/b9_false_positive_memory_explainer_v0/B9_FALSE_POSITIVE_MEMORY_EXPLAINER_TRAPS_V0.csv',
        'B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.csv',
    ],
}

SAMPLE_MAP = {
    'live_brief': 'sample_B9_LIVE_BRIEF_ONCE_V0.json',
    'attention_packet': 'sample_B9_TRADER_ATTENTION_PACKET_V0.json',
    'reality_board': 'sample_B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json',
    'human_terrain_synthesis': 'sample_B9_HUMAN_TERRAIN_SYNTHESIS_V0.json',
    'golden_cases_csv': 'sample_T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv',
    'memory_confidence_ladder_json': 'sample_B9_MEMORY_CONFIDENCE_LADDER_V0.json',
    'false_positive_explainer_json': 'sample_B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.json',
}

STOPWORDS = {
    'the','and','for','avec','sans','dans','sur','une','des','les','par','qui','que','est','pas','plus','moins',
    'current','scene','market','b9','powerflow','v0','v1','true','false','none','null','unknown','na','n/a','de','du','la','le','un','au','aux','ce','cet','cette'
}

@dataclass
class InputRecord:
    input_name: str
    required: bool
    found: bool
    path: str
    mode: str
    sha256: str = ''
    note: str = ''

@dataclass
class MatchRow:
    match_rank: int
    match_type: str
    source_family: str
    source_id: str
    source_label: str
    compare_score: float
    shared_markers: str
    missing_current_markers: str
    missing_reference_markers: str
    source_quality: str
    retest: str
    session: str
    center_path: str
    conclusion_boundary: str

@dataclass
class DifferenceRow:
    difference_rank: int
    difference_type: str
    current_marker: str
    reference_marker: str
    source_id: str
    impact: str
    technical_risk: str

@dataclass
class RiskRow:
    risk_rank: int
    risk_code: str
    severity: str
    source: str
    detail: str
    mitigation_b9_wording: str


def read_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Optional[Sequence[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: List[str] = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def flatten_strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key)
            yield from flatten_strings(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from flatten_strings(item)
    elif obj is not None:
        yield str(obj)


def normalize_token(text: str) -> str:
    return re.sub(r'[^a-z0-9_]+', '', text.lower())


def tokenize_obj(obj: Any) -> List[str]:
    tokens: List[str] = []
    for text in flatten_strings(obj):
        for raw in re.split(r'[^A-Za-z0-9_]+', text):
            token = normalize_token(raw)
            if len(token) >= 3 and token not in STOPWORDS and not token.startswith('_') and not token[0].isdigit():
                tokens.append(token)
    seen = set()
    ordered = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            ordered.append(token)
    return ordered


def get_first(obj: Any, keys: Sequence[str], default: str = '') -> str:
    if isinstance(obj, dict):
        for key in keys:
            if key in obj and obj[key] not in (None, ''):
                return stringify(obj[key])
        for value in obj.values():
            found = get_first(value, keys, '') if isinstance(value, (dict, list)) else ''
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = get_first(item, keys, '')
            if found:
                return found
    return default


def stringify(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def limit_join(items: Sequence[str], limit: int = 10) -> str:
    return ' | '.join(list(items)[:limit])


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def forbidden_hits(*objects: Any) -> List[Dict[str, str]]:
    hits = []
    for obj_index, obj in enumerate(objects):
        for text in flatten_strings(obj):
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    hits.append({'object_index': str(obj_index), 'pattern': pattern, 'excerpt': text[:180]})
    return hits


def find_input_runtime(core_root: Path, key: str) -> Tuple[Optional[Path], InputRecord]:
    for rel in INPUT_CANDIDATES.get(key, []):
        path = core_root / rel
        if path.exists():
            return path, InputRecord(key, key in ['live_brief','attention_packet','golden_cases_csv'], True, str(path), 'runtime', sha256_file(path))
    required = key in ['live_brief','attention_packet','golden_cases_csv']
    return None, InputRecord(key, required, False, '', 'runtime', note='missing')


def resolve_inputs(mode: str, core_root: Path, sample_dir: Path) -> Tuple[Dict[str, Path], List[InputRecord]]:
    resolved: Dict[str, Path] = {}
    records: List[InputRecord] = []
    if mode == 'sample':
        for key, filename in SAMPLE_MAP.items():
            path = sample_dir / filename
            required = key in ['live_brief','attention_packet','golden_cases_csv']
            found = path.exists()
            if found:
                resolved[key] = path
            records.append(InputRecord(key, required, found, str(path) if found else '', 'sample', sha256_file(path) if found else '', 'sample_fixture'))
        return resolved, records
    for key in INPUT_CANDIDATES:
        path, record = find_input_runtime(core_root, key)
        if path:
            resolved[key] = path
        records.append(record)
    return resolved, records


def load_payloads(paths: Dict[str, Path]) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for key, path in paths.items():
        if path.suffix.lower() == '.json':
            data[key] = read_json(path)
        elif path.suffix.lower() == '.csv':
            data[key] = read_csv(path)
    return data


def extract_current_scene(data: Dict[str, Any]) -> Dict[str, Any]:
    live = data.get('live_brief', {})
    packet = data.get('attention_packet', {})
    reality = data.get('reality_board', {})
    terrain = data.get('human_terrain_synthesis', {})
    scene = {
        'scene_id': get_first(live, ['scene_id','brief_id','id'], 'CURRENT_SCENE'),
        'symbol': get_first(live, ['symbol','pair'], get_first(packet, ['symbol','pair'], 'UNKNOWN_SYMBOL')),
        'timestamp': get_first(live, ['timestamp','as_of','generated_at'], get_first(packet, ['timestamp','as_of','generated_at'], 'UNKNOWN_TIME')),
        'current_scene': get_first(live, ['current_scene','scene','film_state','market_scene'], get_first(packet, ['scene','film_state'], 'SCENE_UNKNOWN')),
        'memory_family': get_first(live, ['memory_family','family','film_family'], get_first(terrain, ['memory_family','family'], 'MEMORY_FAMILY_UNKNOWN')),
        'source_quality': get_first(reality, ['source_quality','data_visibility','quality_state'], get_first(packet, ['source_quality','data_visibility'], 'SOURCE_QUALITY_UNKNOWN')),
        'retest': get_first(packet, ['retest','retest_state','native_retest'], get_first(reality, ['retest','retest_state'], 'RETEST_UNKNOWN')),
        'session': get_first(packet, ['session','session_phase'], get_first(live, ['session','session_phase'], 'SESSION_UNKNOWN')),
        'center_path': get_first(packet, ['center_path','center_path_state'], get_first(terrain, ['center_path','center_path_state'], 'CENTER_PATH_UNKNOWN')),
        'technical_traps': collect_named_list([live, packet, reality, terrain], ['technical_traps','traps','pitfalls','false_positive_risks']),
        'cannot_conclude': collect_named_list([live, packet, reality, terrain], ['cannot_conclude','b9_cannot_conclude','limits','limitations']),
        'watch_conditions': collect_named_list([live, packet, reality, terrain], ['watch','watch_condition','watch_conditions']),
    }
    return scene


def collect_named_list(objects: Sequence[Any], keys: Sequence[str]) -> List[str]:
    out: List[str] = []
    for obj in objects:
        if isinstance(obj, dict):
            for key in keys:
                value = obj.get(key)
                if isinstance(value, list):
                    out.extend(stringify(v) for v in value if v not in (None, ''))
                elif value not in (None, ''):
                    out.append(stringify(value))
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    out.extend(collect_named_list([value], keys))
        elif isinstance(obj, list):
            for item in obj:
                out.extend(collect_named_list([item], keys))
    seen = set()
    clean = []
    for item in out:
        if item not in seen:
            seen.add(item)
            clean.append(item)
    return clean


def rows_from_json_records(obj: Any) -> List[Dict[str, Any]]:
    candidates: List[Any] = []
    if isinstance(obj, list):
        candidates = obj
    elif isinstance(obj, dict):
        if not obj:
            return []
        for key in ['matches','top_films','films','memory_matches','ladder','rows','items','results','nearby_films','technical_traps']:
            value = obj.get(key)
            if isinstance(value, list):
                candidates.extend(value)
        if not candidates:
            candidates = [obj]
    rows: List[Dict[str, Any]] = []
    for item in candidates:
        if isinstance(item, dict):
            rows.append(dict(item))
    return rows


def extract_memory_films(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key in ['memory_confidence_ladder_json', 'false_positive_explainer_json', 'human_terrain_synthesis']:
        for row in rows_from_json_records(data.get(key, {})):
            row['_source'] = key
            rows.append(row)
    if 'memory_confidence_ladder_csv' in data:
        for row in data['memory_confidence_ladder_csv']:
            row['_source'] = 'memory_confidence_ladder_csv'
            rows.append(row)
    if 'false_positive_explainer_csv' in data:
        for row in data['false_positive_explainer_csv']:
            row['_source'] = 'false_positive_explainer_csv'
            rows.append(row)
    return rows


def extract_golden_cases(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = data.get('golden_cases_csv') or []
    for row in rows:
        row['_source'] = 'golden_cases_csv'
    return rows


def row_label(row: Dict[str, Any]) -> str:
    for key in ['label','case_label','film_label','title','name','scene','family','pattern']:
        if row.get(key):
            return stringify(row[key])
    return 'REFERENCE_SCENE'


def row_id(row: Dict[str, Any], prefix: str, idx: int) -> str:
    for key in ['id','case_id','film_id','memory_id','pattern_id','source_id']:
        if row.get(key):
            return stringify(row[key])
    return f'{prefix}_{idx:03d}'


def compare_reference(current_tokens: List[str], row: Dict[str, Any], match_type: str, idx: int) -> MatchRow:
    ref_tokens = tokenize_obj(row)
    shared = sorted(set(current_tokens) & set(ref_tokens))
    missing_current = sorted(set(ref_tokens) - set(current_tokens))
    missing_reference = sorted(set(current_tokens) - set(ref_tokens))
    base_score = jaccard(current_tokens, ref_tokens)
    prior = 0.0
    for key in ['confidence','confidence_score','memory_confidence','compare_score','similarity_score']:
        try:
            if row.get(key) not in (None, ''):
                val = float(row.get(key))
                prior = val if val <= 1 else val / 100.0
                break
        except Exception:
            pass
    score = round((0.75 * base_score) + (0.25 * prior), 4)
    return MatchRow(
        match_rank=idx,
        match_type=match_type,
        source_family=stringify(row.get('_source', match_type)),
        source_id=row_id(row, match_type.upper(), idx),
        source_label=row_label(row),
        compare_score=score,
        shared_markers=limit_join(shared, 14),
        missing_current_markers=limit_join(missing_current, 12),
        missing_reference_markers=limit_join(missing_reference, 12),
        source_quality=stringify(row.get('source_quality') or row.get('data_visibility') or row.get('quality') or ''),
        retest=stringify(row.get('retest') or row.get('retest_state') or ''),
        session=stringify(row.get('session') or row.get('session_phase') or ''),
        center_path=stringify(row.get('center_path') or row.get('center_path_state') or ''),
        conclusion_boundary='COMPARAISON_MEMOIRE_SEULEMENT_PAS_DE_PREDICTION',
    )


def build_matches(current_scene: Dict[str, Any], data: Dict[str, Any], top_k: int) -> Tuple[List[MatchRow], List[DifferenceRow]]:
    current_tokens = tokenize_obj(current_scene)
    refs: List[Tuple[str, Dict[str, Any]]] = []
    for row in extract_memory_films(data):
        refs.append(('B6_MEMORY_FILM', row))
    for row in extract_golden_cases(data):
        refs.append(('GOLDEN_TERRAIN_CASE', row))
    scored = [compare_reference(current_tokens, row, match_type, i + 1) for i, (match_type, row) in enumerate(refs)]
    scored.sort(key=lambda m: m.compare_score, reverse=True)
    matches = []
    for rank, row in enumerate(scored[:top_k], 1):
        row.match_rank = rank
        matches.append(row)
    differences: List[DifferenceRow] = []
    diff_rank = 1
    for match in matches:
        for token in (match.missing_current_markers.split(' | ') if match.missing_current_markers else [])[:5]:
            differences.append(DifferenceRow(diff_rank, 'REFERENCE_MARKER_ABSENT_FROM_CURRENT', '', token, match.source_id, 'Ne pas sur-lire la proximite memoire', 'film proche mais marqueur terrain absent'))
            diff_rank += 1
        for token in (match.missing_reference_markers.split(' | ') if match.missing_reference_markers else [])[:5]:
            differences.append(DifferenceRow(diff_rank, 'CURRENT_MARKER_ABSENT_FROM_REFERENCE', token, '', match.source_id, 'Scene actuelle partiellement hors film reference', 'comparaison incomplete'))
            diff_rank += 1
    return matches, differences


def build_risks(scene: Dict[str, Any], matches: List[MatchRow], records: List[InputRecord], forbidden: List[Dict[str, str]]) -> List[RiskRow]:
    risks: List[RiskRow] = []
    def add(code: str, severity: str, source: str, detail: str, wording: str) -> None:
        risks.append(RiskRow(len(risks)+1, code, severity, source, detail, wording))
    missing_required = [r.input_name for r in records if r.required and not r.found]
    if missing_required:
        add('MISSING_REQUIRED_INPUT', 'P0', 'input_resolution', ', '.join(missing_required), 'B9 compare partiel: entree requise absente.')
    optional_missing = [r.input_name for r in records if (not r.required) and (not r.found)]
    if optional_missing:
        add('OPTIONAL_MEMORY_INPUT_MISSING', 'P2', 'input_resolution', ', '.join(optional_missing), 'Memoire incomplete: comparaison limitee aux sources presentes.')
    if not matches:
        add('NO_COMPARISON_REFERENCE', 'P0', 'compare_engine', 'Aucun film ou golden case exploitable.', 'B9 ne peut pas situer la scene face a la memoire.')
    elif matches[0].compare_score < 0.12:
        add('LOW_MARKER_OVERLAP', 'P1', 'compare_engine', f'top_score={matches[0].compare_score}', 'Film proche faible: proximite terrain fragile.')
    q = str(scene.get('source_quality','')).upper()
    if any(x in q for x in ['PARTIAL','MISSING','STALE','DEGRADED','UNKNOWN','PROXY']):
        add('SOURCE_QUALITY_LIMIT', 'P1', 'source_quality', str(scene.get('source_quality')), 'Source quality limitee: B9 garde la conclusion courte.')
    if any('PROXY' in stringify(m).upper() for m in [scene] + [asdict(x) for x in matches]):
        add('PROXY_SOURCE_PRESENT', 'P1', 'source_quality', 'proxy marker detected', 'Source proxy: comparer la forme, pas conclure le film dur.')
    if scene.get('retest') in ('', 'RETEST_UNKNOWN'):
        add('RETEST_UNKNOWN', 'P2', 'retest', 'retest absent ou non resolu', 'Retest non tranche: B9 ne valide pas la reaction.')
    if forbidden:
        add('FORBIDDEN_LANGUAGE_HIT', 'P0', 'policy_guard', json.dumps(forbidden, ensure_ascii=False)[:400], 'Langage interdit detecte: corriger avant usage trader.')
    if not scene.get('cannot_conclude'):
        add('NO_CANNOT_CONCLUDE_SECTION', 'P2', 'board_contract', 'section cannot_conclude vide', 'Ajouter ce que B9 ne peut pas conclure.')
    return risks


def md_cell(value: Any) -> str:
    return stringify(value).replace('|', '/').replace('\n', ' ')


def render_md(board: Dict[str, Any], matches: List[MatchRow], differences: List[DifferenceRow], risks: List[RiskRow]) -> str:
    scene = board['current_scene']
    lines = []
    lines.append('# B9 MARKET COMPARE BOARD V0')
    lines.append('')
    lines.append('Doctrine: comparer n est pas predire. B9 montre la proximite terrain, les ecarts et les risques techniques.')
    lines.append('')
    lines.append('## Scene actuelle')
    lines.append('')
    for key in ['symbol','timestamp','current_scene','memory_family','source_quality','retest','session','center_path']:
        lines.append(f'- {key}: {scene.get(key, "")}')
    lines.append('')
    lines.append('## Top films proches')
    lines.append('')
    if matches:
        lines.append('| rank | type | source | score compare | marqueurs communs | frontiere |')
        lines.append('|---:|---|---|---:|---|---|')
        for m in matches:
            lines.append(f'| {m.match_rank} | {md_cell(m.match_type)} | {md_cell(m.source_label)} | {m.compare_score:.4f} | {md_cell(m.shared_markers)} | {md_cell(m.conclusion_boundary)} |')
    else:
        lines.append('Aucun film proche exploitable.')
    lines.append('')
    lines.append('## Golden terrain proche')
    lines.append('')
    golden = [m for m in matches if m.match_type == 'GOLDEN_TERRAIN_CASE']
    if golden:
        g = golden[0]
        lines.append(f'- {g.source_label} ({g.source_id})')
        lines.append(f'- score compare: {g.compare_score:.4f}')
        lines.append(f'- similarites: {g.shared_markers}')
        lines.append(f'- differences reference absentes: {g.missing_current_markers}')
    else:
        lines.append('Aucun golden case proche dans les sources presentes.')
    lines.append('')
    lines.append('## Differences clefs')
    lines.append('')
    for d in differences[:12]:
        marker = d.current_marker or d.reference_marker
        lines.append(f'- {d.difference_type}: {marker} | impact: {d.impact} | risque: {d.technical_risk}')
    if not differences:
        lines.append('- Aucune difference structuree extraite.')
    lines.append('')
    lines.append('## Pieges techniques')
    lines.append('')
    for trap in scene.get('technical_traps', [])[:10]:
        lines.append(f'- {trap}')
    if not scene.get('technical_traps'):
        lines.append('- Aucun piege explicite dans les entrees; garder HONEST_UNKNOWN.')
    lines.append('')
    lines.append('## Risques techniques board')
    lines.append('')
    for r in risks:
        lines.append(f'- [{r.severity}] {r.risk_code}: {r.detail} -> {r.mitigation_b9_wording}')
    lines.append('')
    lines.append('## Ce que B9 ne peut pas conclure')
    lines.append('')
    cannot = scene.get('cannot_conclude') or []
    if cannot:
        for item in cannot[:10]:
            lines.append(f'- {item}')
    else:
        lines.append('- B9 ne peut pas conclure une direction, une entree, un outcome ou une probabilite de succes depuis une comparaison memoire.')
    lines.append('')
    return '\n'.join(lines)


def build_board(mode: str, core_root: Path, sample_dir: Path, output_dir: Path, top_k: int) -> Dict[str, Any]:
    paths, records = resolve_inputs(mode, core_root, sample_dir)
    data = load_payloads(paths)
    scene = extract_current_scene(data)
    matches, differences = build_matches(scene, data, top_k)
    forbidden = forbidden_hits(scene, *[asdict(m) for m in matches], *[asdict(d) for d in differences])
    risks = build_risks(scene, matches, records, forbidden)
    required_total = sum(1 for r in records if r.required)
    required_found = sum(1 for r in records if r.required and r.found)
    board_state = 'PASS' if required_found == required_total and not forbidden else 'BLOCKED_MISSING_INPUTS' if required_found < required_total else 'BLOCKED_FORBIDDEN_LANGUAGE'
    board = {
        'version': VERSION,
        'mode': mode,
        'board_state': board_state,
        'doctrine': {
            'compare_is_not_predict': True,
            'read_only': True,
            'no_db': True,
            'no_dashboard_direct': True,
            'no_telegram': True,
            'no_buy_sell': True,
            'no_probability_of_success': True,
        },
        'input_summary': {
            'required_inputs_found': required_found,
            'required_inputs_total': required_total,
            'inputs': [asdict(r) for r in records],
        },
        'current_scene': scene,
        'compare_summary': {
            'match_count': len(matches),
            'top_match_id': matches[0].source_id if matches else '',
            'top_match_label': matches[0].source_label if matches else '',
            'top_match_type': matches[0].match_type if matches else '',
            'top_compare_score': matches[0].compare_score if matches else 0.0,
            'golden_match_count': len([m for m in matches if m.match_type == 'GOLDEN_TERRAIN_CASE']),
            'memory_match_count': len([m for m in matches if m.match_type == 'B6_MEMORY_FILM']),
        },
        'top_films_close': [asdict(m) for m in matches],
        'differences': [asdict(d) for d in differences],
        'technical_risks': [asdict(r) for r in risks],
        'cannot_conclude_default': [
            'B9 ne conclut pas une direction depuis une proximite memoire.',
            'B9 ne transforme pas un golden case proche en prediction.',
            'B9 ne produit pas de BUY/SELL.',
            'B9 ne produit aucune probabilite de succes.',
        ],
        'forbidden_language_hits': forbidden,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / f'{OUTPUT_BASENAME}.json', board)
    md = render_md(board, matches, differences, risks)
    (output_dir / f'{OUTPUT_BASENAME}.md').write_text(md, encoding='utf-8')
    write_csv(output_dir / f'{OUTPUT_BASENAME}_MATCHES_V0.csv', [asdict(m) for m in matches])
    write_csv(output_dir / f'{OUTPUT_BASENAME}_DIFFERENCES_V0.csv', [asdict(d) for d in differences])
    write_csv(output_dir / f'{OUTPUT_BASENAME}_TECHNICAL_RISKS_V0.csv', [asdict(r) for r in risks])
    write_csv(output_dir / f'{OUTPUT_BASENAME}_INPUTS_V0.csv', [asdict(r) for r in records])
    manifest = {
        'version': VERSION,
        'mode': mode,
        'board_state': board_state,
        'outputs': [
            f'{OUTPUT_BASENAME}.json',
            f'{OUTPUT_BASENAME}.md',
            f'{OUTPUT_BASENAME}_MATCHES_V0.csv',
            f'{OUTPUT_BASENAME}_DIFFERENCES_V0.csv',
            f'{OUTPUT_BASENAME}_TECHNICAL_RISKS_V0.csv',
            f'{OUTPUT_BASENAME}_INPUTS_V0.csv',
        ],
    }
    write_json(output_dir / f'{OUTPUT_BASENAME}_MANIFEST.json', manifest)
    zip_path = output_dir / f'{OUTPUT_BASENAME}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name in manifest['outputs'] + [f'{OUTPUT_BASENAME}_MANIFEST.json']:
            p = output_dir / name
            if p.exists():
                zf.write(p, arcname=name)
    return board


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Build T0162 B9 Market Compare Board V0')
    parser.add_argument('--mode', choices=['runtime','sample'], default='runtime')
    parser.add_argument('--core-root', default='.')
    parser.add_argument('--sample-dir', default='samples/b9_market_compare_board_v0')
    parser.add_argument('--output-dir', default='outputs/b9_market_compare_board_v0')
    parser.add_argument('--top-k', type=int, default=8)
    args = parser.parse_args(argv)
    board = build_board(args.mode, Path(args.core_root).resolve(), Path(args.sample_dir).resolve(), Path(args.output_dir).resolve(), args.top_k)
    print(json.dumps({'version': VERSION, 'board_state': board['board_state'], 'output_dir': str(Path(args.output_dir).resolve()), 'top_match': board['compare_summary'].get('top_match_label','')}, ensure_ascii=False, indent=2))
    return 0 if board['board_state'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
