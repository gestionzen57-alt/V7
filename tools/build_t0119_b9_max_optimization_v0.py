#!/usr/bin/env python3
"""T0119 — B9 Max Optimization V0.

Read-only lab/orchestration tool.

Purpose
-------
Audit B9/T009 scene summaries and generate an optimization contract for the
next native summarizer patches. This does not modify PowerFlow runtime files,
powerflow.db, tick_archive.db, dashboard, or Telegram outputs.

Doctrine
--------
B9 ne cherche pas le signal.
B9 cherche la trace laissee par l'effort.
B9 lit une situation, puis B6 compare des films.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

VERSION = "T0119_B9_MAX_OPTIMIZATION_V0"

DOCTRINE_LOCK = [
    "B9 ne cherche pas le signal.",
    "B9 cherche la trace laissee par l'effort.",
    "Ne lis pas l'absorption comme une direction.",
    "Lis ou elle deplace la memoire.",
    "Aucun BUY/SELL.",
    "Aucune probabilite de succes.",
    "Read-only: aucune ecriture powerflow.db / tick_archive.db.",
]

FIELD_GROUPS: Dict[str, Dict[str, Any]] = {
    "V1_WHY_HOW_NATIVE": {
        "priority": "P0",
        "description": "Chaque moment explique ce qui se passe, pourquoi cela compte, comment c'est arrive, le mecanisme et les preuves.",
        "fields": [
            "what_happens_fr",
            "why_it_matters_fr",
            "how_it_happened_fr",
            "mechanism_fr",
            "proof_summary_fr",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t009_sequence_summarizer_v1_why_how.py"],
    },
    "V2_SCENE_CAUSALITY_NATIVE": {
        "priority": "P0",
        "description": "Relier les moments en cause -> reaction -> consequence -> memoire.",
        "fields": [
            "previous_context_fr",
            "cause_fr",
            "reaction_fr",
            "consequence_fr",
            "memory_shift_fr",
            "retest_role_fr",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t009_sequence_summarizer_v2_causality.py"],
    },
    "V3_FRACTAL_SCENE_NATIVE": {
        "priority": "P0",
        "description": "Relier microfilm -> moment -> scene -> chapitre de session.",
        "fields": [
            "scene_id",
            "scene_role",
            "parent_scene",
            "child_moments",
            "session_chapter",
            "fractal_reading_fr",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t009_sequence_summarizer_v3_fractal_scene.py"],
    },
    "CENTER_PATH_INTERNAL_FILM": {
        "priority": "P0",
        "description": "Eviter le piege start/end: B9 doit lire le chemin interne du centre, les excursions et les inflexions.",
        "fields": [
            "center_min",
            "center_max",
            "center_range_pips",
            "max_favorable_excursion_pips",
            "max_adverse_excursion_pips",
            "center_path",
            "inflexion_points",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t009_center_path_contract.py"],
    },
    "EFFORT_RESULT_PROGRESS_NATIVE": {
        "priority": "P0",
        "description": "Classifier effort, resultat et progres sans transformer absorption en direction.",
        "fields": [
            "b9_effort_load",
            "b9_effort_result_ratio",
            "b9_directional_efficiency",
            "raw_delta_pips",
            "raw_range_pips",
            "b9_progress_state",
            "b9_effort_result_progress_reading_fr",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t009_effort_result_progress.py"],
    },
    "NATIVE_RETEST_JUDGE": {
        "priority": "P0",
        "description": "Le retest juge la zone: acceptation, echec, reintegration, zone consommee, en attente.",
        "fields": [
            "retest_source_fields_version",
            "retest_touch_count",
            "retest_first_touch_time",
            "retest_last_touch_time",
            "retest_outcome_hint",
            "b9_retest_source_status",
            "b9_retest_source_signal_state",
            "b9_retest_source_reading_fr",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t0111b_native_retest_source_fields.py"],
    },
    "SOURCE_QUALITY_NATIVE": {
        "priority": "P1",
        "description": "Garder source_mode, data_visibility, confidence_cap, raw agreement et limites visibles partout.",
        "fields": [
            "source_mode",
            "data_visibility",
            "confidence_cap",
            "proxy_vs_raw_verdict",
            "raw_texture_role",
            "raw_coverage",
            "source_quality_score",
            "source_quality_state",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t009_source_quality_visibility.py"],
    },
    "SESSION_CONTEXT_NATIVE": {
        "priority": "P1",
        "description": "Session Memory Overlay: une scene n'a pas le meme role a Asian, London, NY ou overlap.",
        "fields": [
            "session",
            "session_phase",
            "session_bias",
            "minutes_since_open",
        ],
        "recommended_files": ["pf_session_overlay.py", "pf_t009_sequence_summarizer.py", "tests/test_t009_session_context.py"],
    },
    "B6_MEMORY_HANDOFF_NATIVE": {
        "priority": "P1",
        "description": "Preparer l'interface B9 -> B6: film_id, memory_family, base/reaction/projection/judgment et limites.",
        "fields": [
            "film_id",
            "memory_family",
            "base",
            "reaction",
            "projection",
            "judgment",
            "memory_candidate_reason",
            "technical_limits",
        ],
        "recommended_files": ["pf_t009_sequence_summarizer.py", "pf_b6_field_memory_reader.py", "tests/test_t009_b6_handoff_contract.py"],
    },
}

PROHIBITED_PATTERNS = [
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"probabilit[ey]\s+of\s+success", re.IGNORECASE),
    re.compile(r"probabilite\s+de\s+succes", re.IGNORECASE),
    re.compile(r"take\s+profit", re.IGNORECASE),
    re.compile(r"stop\s+loss", re.IGNORECASE),
]

OPTIMIZATION_RULES = [
    {
        "rule_id": "B9_RULE_001",
        "name": "Event -> moment gate",
        "rule_fr": "Un event brut ne devient moment que si zone/reaction/migration/retest/source quality donnent une scene lisible.",
        "technical_risk_if_missing": "risque de bruit M1 et empilement d'events sans role",
        "priority": "P0",
    },
    {
        "rule_id": "B9_RULE_002",
        "name": "Effort/result/progress split",
        "rule_fr": "Effort fort + resultat faible = friction/absorption probable, pas direction dure.",
        "technical_risk_if_missing": "risque de lire l'absorption comme une direction",
        "priority": "P0",
    },
    {
        "rule_id": "B9_RULE_003",
        "name": "Retest is judge",
        "rule_fr": "Une cassure reste en attente tant que le retest n'a pas juge la zone.",
        "technical_risk_if_missing": "risque de validation prematuree d'une rupture proxy",
        "priority": "P0",
    },
    {
        "rule_id": "B9_RULE_004",
        "name": "Internal center path",
        "rule_fr": "B9 doit lire le chemin interne du centre, pas seulement center_start et center_end.",
        "technical_risk_if_missing": "risque de fusionner une vague progressive et un retrace dans un faux doji",
        "priority": "P0",
    },
    {
        "rule_id": "B9_RULE_005",
        "name": "Scene causality",
        "rule_fr": "Chaque moment doit porter cause, reaction, consequence et memoire deplacee ou non.",
        "technical_risk_if_missing": "risque de moments corrects mais film illisible",
        "priority": "P0",
    },
    {
        "rule_id": "B9_RULE_006",
        "name": "Source limits visible",
        "rule_fr": "M1 proxy, raw tick, source quality, raw agreement et limites restent visibles dans chaque sortie.",
        "technical_risk_if_missing": "risque de durcir une lecture reconstruite en verite raw",
        "priority": "P1",
    },
    {
        "rule_id": "B9_RULE_007",
        "name": "Session personality",
        "rule_fr": "La meme scene est qualifiee differemment selon Asian, London, NY, overlap ou dead zone.",
        "technical_risk_if_missing": "risque de faux positif inter-session",
        "priority": "P1",
    },
    {
        "rule_id": "B9_RULE_008",
        "name": "B6 handoff",
        "rule_fr": "B9 doit produire une scene suffisamment stable pour B6: film proche, differences, limites.",
        "technical_risk_if_missing": "risque de memoire B6 decorative au lieu de comparative",
        "priority": "P1",
    },
]


@dataclass
class FieldCoverage:
    group_id: str
    priority: str
    required_fields: int
    present_all_rows: int
    present_any_rows: int
    missing_all_fields: str
    partial_fields: str
    coverage_score: float
    implementation_state: str
    technical_risk: str


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_list_of_moments(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("moments", "sequence_moments", "film_cards", "cards", "events"):
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
    return []


def value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return False
    return True


def field_stats(moments: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> Tuple[int, int, List[str], List[str], Dict[str, int]]:
    counts: Dict[str, int] = {}
    total = len(moments)
    for field in fields:
        counts[field] = sum(1 for row in moments if value_present(row.get(field)))
    present_all = sum(1 for field, count in counts.items() if total > 0 and count == total)
    present_any = sum(1 for field, count in counts.items() if count > 0)
    missing = [field for field, count in counts.items() if count == 0]
    partial = [field for field, count in counts.items() if 0 < count < total]
    return present_all, present_any, missing, partial, counts


def classify_group_coverage(required: int, present_any: int, present_all: int) -> Tuple[float, str]:
    if required == 0:
        return 1.0, "NO_FIELDS_REQUIRED"
    any_score = present_any / required
    all_score = present_all / required
    score = round(0.7 * any_score + 0.3 * all_score, 4)
    if score >= 0.95:
        state = "B9_NATIVE_READY"
    elif score >= 0.60:
        state = "B9_PARTIAL_NATIVE_NEEDS_HARDENING"
    elif score > 0:
        state = "B9_PROXY_OR_INCOMPLETE_NEEDS_PATCH"
    else:
        state = "B9_MISSING_NATIVE_CONTRACT"
    return score, state


def technical_risk_for_group(group_id: str, state: str) -> str:
    risks = {
        "V1_WHY_HOW_NATIVE": "film lisible mais explication native absente",
        "V2_SCENE_CAUSALITY_NATIVE": "moments deconnectes; cause/reaction/consequence non tracables",
        "V3_FRACTAL_SCENE_NATIVE": "microfilm non relie au chapitre de session",
        "CENTER_PATH_INTERNAL_FILM": "risque start/end: chemin interne invisible",
        "EFFORT_RESULT_PROGRESS_NATIVE": "risque absorption lue comme direction si progress_state absent",
        "NATIVE_RETEST_JUDGE": "risque retest reconstruit ou verdict de zone trop faible",
        "SOURCE_QUALITY_NATIVE": "risque de durcir une lecture proxy en raw",
        "SESSION_CONTEXT_NATIVE": "risque de comparer Asian/London/NY comme scenes equivalentes",
        "B6_MEMORY_HANDOFF_NATIVE": "risque de B6 handoff incomplet pour query future",
    }
    risk = risks.get(group_id, "risque de contrat B9 incomplet")
    if state == "B9_NATIVE_READY":
        return "risque residuel faible: conserver tests de non-regression"
    return risk


def build_coverage(moments: Sequence[Mapping[str, Any]]) -> List[FieldCoverage]:
    rows: List[FieldCoverage] = []
    for group_id, spec in FIELD_GROUPS.items():
        fields = list(spec["fields"])
        present_all, present_any, missing, partial, _ = field_stats(moments, fields)
        score, state = classify_group_coverage(len(fields), present_any, present_all)
        rows.append(
            FieldCoverage(
                group_id=group_id,
                priority=str(spec["priority"]),
                required_fields=len(fields),
                present_all_rows=present_all,
                present_any_rows=present_any,
                missing_all_fields=";".join(missing),
                partial_fields=";".join(partial),
                coverage_score=score,
                implementation_state=state,
                technical_risk=technical_risk_for_group(group_id, state),
            )
        )
    return rows


def count_values(moments: Sequence[Mapping[str, Any]], field: str) -> Dict[str, int]:
    c = Counter()
    for row in moments:
        value = row.get(field)
        if isinstance(value, list):
            for item in value:
                c[str(item)] += 1
        elif value_present(value):
            c[str(value)] += 1
        else:
            c["__MISSING__"] += 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def inspect_native_retest_status(moments: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    versions = count_values(moments, "retest_source_fields_version")
    native_count = 0
    reconstructed_count = 0
    not_visible_count = 0
    for row in moments:
        version = str(row.get("retest_source_fields_version") or "")
        status = str(row.get("b9_retest_source_status") or row.get("retest_outcome_hint") or "")
        if "NATIVE" in version:
            native_count += 1
        if "T0110" in version or "PROXY" in version or "CANONICAL" in version:
            reconstructed_count += 1
        if "NOT_VISIBLE" in status or not status:
            not_visible_count += 1
    total = len(moments)
    return {
        "versions": versions,
        "native_count": native_count,
        "reconstructed_or_proxy_count": reconstructed_count,
        "not_visible_count": not_visible_count,
        "native_ratio": round(native_count / total, 4) if total else 0.0,
        "retest_visibility_ratio": round((total - not_visible_count) / total, 4) if total else 0.0,
    }


def scan_text_docs(paths: Sequence[Path]) -> Dict[str, Any]:
    keywords = [
        "effort sans resultat",
        "effort/resultat/progres",
        "retest",
        "centre de gravite",
        "vague progressive",
        "vague corrective",
        "absorption",
        "source quality",
        "M1_BAR_PROXY",
        "RECONSTRUCTED",
        "raw",
        "memoire",
        "scene",
        "B9 ne cherche pas le signal",
    ]
    doc_stats: List[Dict[str, Any]] = []
    aggregate = Counter()
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        normalized = text.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
        counts = {}
        for kw in keywords:
            norm_kw = kw.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
            count = normalized.count(norm_kw)
            counts[kw] = count
            aggregate[kw] += count
        doc_stats.append({"file": path.name, "keyword_counts": counts, "chars": len(text)})
    return {"documents": doc_stats, "aggregate_keyword_counts": dict(aggregate)}


def generate_patch_plan(coverage: Sequence[FieldCoverage], retest: Mapping[str, Any]) -> List[Dict[str, Any]]:
    ordered: List[Dict[str, Any]] = []
    sort_key = {"P0": 0, "P1": 1, "P2": 2}
    for item in sorted(coverage, key=lambda x: (sort_key.get(x.priority, 9), x.coverage_score)):
        spec = FIELD_GROUPS[item.group_id]
        if item.implementation_state == "B9_NATIVE_READY":
            action = "KEEP_AND_FREEZE_CONTRACT"
        elif item.priority == "P0":
            action = "PATCH_NOW"
        else:
            action = "PATCH_NEXT"
        ordered.append(
            {
                "patch_id": f"T0119_{item.group_id}",
                "priority": item.priority,
                "action": action,
                "group_id": item.group_id,
                "implementation_state": item.implementation_state,
                "why": spec["description"],
                "missing_fields": item.missing_all_fields,
                "partial_fields": item.partial_fields,
                "recommended_files": spec.get("recommended_files", []),
                "technical_risk": item.technical_risk,
            }
        )
    if retest.get("native_ratio", 0) < 0.5:
        ordered.insert(
            0,
            {
                "patch_id": "T0119_T0111B_NATIVE_RETEST_SOURCE_FIELDS",
                "priority": "P0",
                "action": "PATCH_NOW",
                "group_id": "NATIVE_RETEST_JUDGE",
                "implementation_state": "B9_RETEST_NOT_NATIVE_ENOUGH",
                "why": "Le retest doit etre produit nativement par le summarizer, pas reconstruit apres coup.",
                "missing_fields": "T0111_NATIVE_RETEST_SOURCE_FIELDS_V0",
                "partial_fields": "",
                "recommended_files": ["pf_t009_sequence_summarizer.py", "tests/test_t0111b_native_retest_source_fields.py"],
                "technical_risk": "risque de verdict retest partiel et de faux positif de similarite B6",
            },
        )
    return ordered


def generate_test_plan() -> List[Dict[str, Any]]:
    return [
        {
            "test_id": "B9_MAX_TEST_001",
            "target": "No forbidden language",
            "command": "python -m pytest tests/test_t0119_b9_max_optimization_v0_contract.py",
            "assertion": "Aucun BUY/SELL/probabilite de succes dans les sorties T0119.",
        },
        {
            "test_id": "B9_MAX_TEST_002",
            "target": "V1 why/how fields",
            "command": "python -m pytest tests/test_t009_sequence_summarizer_v1_why_how.py",
            "assertion": "Chaque moment porte what/why/how/mechanism/proof_summary en francais trader.",
        },
        {
            "test_id": "B9_MAX_TEST_003",
            "target": "V2 causality fields",
            "command": "python -m pytest tests/test_t009_sequence_summarizer_v2_causality.py",
            "assertion": "Cause/reaction/consequence/memory_shift/retest_role sont presents et non vides.",
        },
        {
            "test_id": "B9_MAX_TEST_004",
            "target": "V3 fractal scene fields",
            "command": "python -m pytest tests/test_t009_sequence_summarizer_v3_fractal_scene.py",
            "assertion": "scene_id, scene_role, parent_scene, child_moments, session_chapter, fractal_reading_fr presents.",
        },
        {
            "test_id": "B9_MAX_TEST_005",
            "target": "Center path hotfix guard",
            "command": "python -m pytest tests/test_t009_center_path_contract.py",
            "assertion": "center_min/max/range/excursions/path empechent le faux doji start/end.",
        },
        {
            "test_id": "B9_MAX_TEST_006",
            "target": "Native retest judge",
            "command": "python -m pytest tests/test_t0111b_native_retest_source_fields.py",
            "assertion": "T0111_NATIVE_RETEST_SOURCE_FIELDS_V0 emis directement par le summarizer.",
        },
    ]


def prohibited_hits_in_payload(payload: Any) -> List[str]:
    """Detect prohibited decision language while ignoring explicit prohibition lines.

    The PowerFlow reports must be allowed to say things like "Aucun BUY/SELL"
    or "no BUY/SELL language". Those are doctrine locks, not violations.
    """
    text = json.dumps(payload, ensure_ascii=False, default=str)
    hits = []
    skip_markers = (
        "aucun", "aucune", "pas de", "ne jamais", "no ",
        "without", "interdit", "prohibited", "doctrine", "lock",
    )
    for line in text.splitlines():
        low = line.lower()
        if any(marker in low for marker in skip_markers):
            continue
        for pattern in PROHIBITED_PATTERNS:
            if pattern.search(line):
                hits.append(pattern.pattern)
    return sorted(set(hits))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def markdown_table(rows: Sequence[Mapping[str, Any]], fields: Sequence[str], max_rows: int = 40) -> str:
    if not rows:
        return "_Aucune ligne._\n"
    out = []
    out.append("| " + " | ".join(fields) + " |")
    out.append("| " + " | ".join(["---"] * len(fields)) + " |")
    for row in rows[:max_rows]:
        vals = []
        for field in fields:
            val = str(row.get(field, ""))
            val = val.replace("|", "/").replace("\n", " ")
            if len(val) > 90:
                val = val[:87] + "..."
            vals.append(val)
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out) + "\n"


def write_report(path: Path, summary: Mapping[str, Any], coverage: Sequence[FieldCoverage], patch_plan: Sequence[Mapping[str, Any]], test_plan: Sequence[Mapping[str, Any]]) -> None:
    coverage_rows = [asdict(x) for x in coverage]
    p0_now = [x for x in patch_plan if x.get("priority") == "P0" and x.get("action") == "PATCH_NOW"]
    lines = [
        "# T0119 — B9 Max Optimization V0",
        "",
        "## Resume executif",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissee par l'effort.",
        "Ne lis pas l'absorption comme une direction. Lis ou elle deplace la memoire.",
        "",
        "T0119 est un audit/contrat d'optimisation read-only. Il ne modifie pas le moteur. Il dit exactement ce que B9 doit produire nativement pour atteindre le niveau maximal utile avant integration live.",
        "",
        "## Sources analysees",
        "",
        f"- input_moments: {summary.get('input_moments', 0)}",
        f"- docs_scanned: {summary.get('docs_scanned', 0)}",
        f"- generated_at_utc: {summary.get('generated_at_utc')}",
        "",
        "## Doctrine",
        "",
    ]
    for d in DOCTRINE_LOCK:
        lines.append(f"- {d}")
    lines.extend([
        "",
        "## Verdict optimisation",
        "",
        f"- groupes P0 a patcher maintenant: {len(p0_now)}",
        f"- native_retest_ratio: {summary.get('native_retest_ratio')}",
        f"- retest_visibility_ratio: {summary.get('retest_visibility_ratio')}",
        f"- forbidden_language_hits: {summary.get('forbidden_language_hits')}",
        "",
        "## Gap matrix",
        "",
        markdown_table(coverage_rows, ["group_id", "priority", "coverage_score", "implementation_state", "missing_all_fields", "technical_risk"], 30),
        "",
        "## Patch queue recommandee",
        "",
        markdown_table(patch_plan, ["patch_id", "priority", "action", "implementation_state", "why", "technical_risk"], 30),
        "",
        "## Tests a creer dans le summarizer natif",
        "",
        markdown_table(test_plan, ["test_id", "target", "assertion"], 20),
        "",
        "## Levier PowerFlow active par T0119",
        "",
        "T0119 active la logique du levier B6 Memory Engine en amont: B9 doit produire des scenes assez propres pour que B6 compare des films, sans probabilite de succes et sans decision automatique.",
        "",
        "Il active aussi trois leviers naturels:",
        "",
        "- Session Memory Overlay: ajouter session/session_phase/session_bias aux scenes B9.",
        "- Volatility/texture reading: garder raw texture, spread, effort/resultat, friction.",
        "- Fractal scene reading: relier microfilm -> moment -> scene -> chapitre.",
        "",
        "## Prochaine brique recommandee",
        "",
        "T0120 — B9 Native Summarizer V4 Contract Patch.",
        "",
        "Objectif T0120: appliquer les champs P0 directement dans `pf_t009_sequence_summarizer.py` avec tests natifs, en read-only, sans toucher DB/dashboard/Telegram.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_zip(zip_path: Path, files: Sequence[Path], base_dir: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if file.exists() and file.is_file():
                zf.write(file, file.relative_to(base_dir))


def build(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_json = Path(args.sequence_summary_json) if args.sequence_summary_json else None
    data: Any = {}
    moments: List[Dict[str, Any]] = []
    if input_json and input_json.exists():
        data = load_json(input_json)
        moments = ensure_list_of_moments(data)
    docs: List[Path] = []
    if args.analysis_docs:
        for item in args.analysis_docs:
            p = Path(item)
            if p.is_dir():
                docs.extend(sorted(p.glob("*.md")))
                docs.extend(sorted(p.glob("*.txt")))
            elif p.exists():
                docs.append(p)
    doc_scan = scan_text_docs(docs)
    coverage = build_coverage(moments)
    retest = inspect_native_retest_status(moments)
    patch_plan = generate_patch_plan(coverage, retest)
    test_plan = generate_test_plan()
    payload = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "doctrine_lock": DOCTRINE_LOCK,
        "inputs": {
            "sequence_summary_json": str(input_json) if input_json else None,
            "analysis_docs": [str(x) for x in docs],
        },
        "metrics": {
            "input_moments": len(moments),
            "source_mode_counts": count_values(moments, "source_mode"),
            "data_visibility_counts": count_values(moments, "data_visibility"),
            "proxy_vs_raw_counts": count_values(moments, "proxy_vs_raw_verdict"),
            "raw_texture_role_counts": count_values(moments, "raw_texture_role"),
            "retest": retest,
        },
        "field_coverage": [asdict(x) for x in coverage],
        "optimization_rules": OPTIMIZATION_RULES,
        "patch_plan": patch_plan,
        "test_plan": test_plan,
        "doc_scan": doc_scan,
        "next_task": {
            "id": "T0120",
            "name": "B9 Native Summarizer V4 Contract Patch",
            "branch": "feat/t0120-b9-native-summarizer-v4-contract",
            "commit_message": "feat(t0120): add B9 native summarizer v4 contract",
        },
    }
    forbidden_hits = prohibited_hits_in_payload(payload)
    summary = {
        "version": VERSION,
        "generated_at_utc": payload["generated_at_utc"],
        "input_moments": len(moments),
        "docs_scanned": len(docs),
        "native_retest_ratio": retest.get("native_ratio", 0),
        "retest_visibility_ratio": retest.get("retest_visibility_ratio", 0),
        "p0_patch_now_count": sum(1 for x in patch_plan if x.get("priority") == "P0" and x.get("action") == "PATCH_NOW"),
        "forbidden_language_hits": forbidden_hits,
        "output_dir": str(output_dir),
    }
    payload["summary"] = summary

    write_json(output_dir / "B9_MAX_OPTIMIZATION_V0.json", payload)
    write_report(output_dir / "B9_MAX_OPTIMIZATION_V0.md", summary, coverage, patch_plan, test_plan)
    write_csv(
        output_dir / "B9_MAX_OPTIMIZATION_GAP_MATRIX_V0.csv",
        [asdict(x) for x in coverage],
        ["group_id", "priority", "required_fields", "present_all_rows", "present_any_rows", "missing_all_fields", "partial_fields", "coverage_score", "implementation_state", "technical_risk"],
    )
    write_csv(
        output_dir / "B9_MAX_OPTIMIZATION_PATCH_QUEUE_V0.csv",
        patch_plan,
        ["patch_id", "priority", "action", "group_id", "implementation_state", "why", "missing_fields", "partial_fields", "recommended_files", "technical_risk"],
    )
    write_csv(
        output_dir / "B9_MAX_OPTIMIZATION_RULES_V0.csv",
        OPTIMIZATION_RULES,
        ["rule_id", "name", "rule_fr", "technical_risk_if_missing", "priority"],
    )
    write_csv(
        output_dir / "B9_MAX_OPTIMIZATION_TEST_PLAN_V0.csv",
        test_plan,
        ["test_id", "target", "command", "assertion"],
    )
    manifest = {
        "version": VERSION,
        "created_at_utc": payload["generated_at_utc"],
        "files": [
            "B9_MAX_OPTIMIZATION_V0.md",
            "B9_MAX_OPTIMIZATION_V0.json",
            "B9_MAX_OPTIMIZATION_GAP_MATRIX_V0.csv",
            "B9_MAX_OPTIMIZATION_PATCH_QUEUE_V0.csv",
            "B9_MAX_OPTIMIZATION_RULES_V0.csv",
            "B9_MAX_OPTIMIZATION_TEST_PLAN_V0.csv",
            "B9_MAX_OPTIMIZATION_MANIFEST.json",
            "B9_MAX_OPTIMIZATION_V0.zip",
        ],
        "summary": summary,
        "read_only": True,
        "db_writes": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }
    write_json(output_dir / "B9_MAX_OPTIMIZATION_MANIFEST.json", manifest)
    zip_files = [output_dir / name for name in manifest["files"] if name != "B9_MAX_OPTIMIZATION_V0.zip"]
    create_zip(output_dir / "B9_MAX_OPTIMIZATION_V0.zip", zip_files, output_dir)
    summary["zip"] = str(output_dir / "B9_MAX_OPTIMIZATION_V0.zip")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build T0119 B9 Max Optimization V0 outputs.")
    parser.add_argument("--sequence-summary-json", default="", help="B9/T009 sequence summary JSON to audit.")
    parser.add_argument("--analysis-docs", nargs="*", default=[], help="Optional markdown/txt analysis files or directories to scan.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    args = parser.parse_args(argv)
    summary = build(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
