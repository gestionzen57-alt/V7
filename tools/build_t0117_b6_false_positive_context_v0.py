#!/usr/bin/env python3
"""T0117 - B6 False Positive Context V0.

Read a T0115 B6 similarity query result and explain why each similarity can be
technically misleading. This is read-only and does not predict market outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0117_B6_FALSE_POSITIVE_CONTEXT_V0"
POLICY = "SIMILARITY_IS_NOT_REPETITION_FALSE_POSITIVE_CONTEXT_V0"
DOCTRINE = [
    "B6 ne predit pas.",
    "B6 compare des films.",
    "T0117 explique les pieges techniques de similarite.",
    "Une ressemblance n'est pas une repetition.",
    "Aucun BUY/SELL, aucune probabilite de succes, aucune ecriture DB.",
]

OUTPUT_JSON = "B6_FALSE_POSITIVE_CONTEXT_V0.json"
OUTPUT_MD = "B6_FALSE_POSITIVE_CONTEXT_V0.md"
OUTPUT_CSV = "B6_FALSE_POSITIVE_CONTEXT_V0.csv"
OUTPUT_MANIFEST = "B6_FALSE_POSITIVE_CONTEXT_V0_MANIFEST.json"
OUTPUT_ZIP = "B6_FALSE_POSITIVE_CONTEXT_V0.zip"

BASE_FIELDS = [
    "film_id",
    "film_date",
    "rank",
    "memory_family",
    "similarity_score",
    "false_positive_context_score",
    "false_positive_context_state",
    "risk_flags",
    "difference_explanation_fr",
    "technical_cautions_fr",
    "safe_comparison_reading_fr",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return default
        return float(value)
    text = str(value).strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        # Extract the first numeric token from strings such as "+6.600 pips".
        m = re.search(r"[-+]?\d+(?:\.\d+)?", text)
        if m:
            try:
                return float(m.group(0))
            except ValueError:
                return default
        return default


def normalize_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def lower_text(value: Any) -> str:
    return normalize_text(value).lower()


def sign(value: Any) -> int:
    n = safe_float(value, 0.0) or 0.0
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0


def compact_flags(flags: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for flag in flags:
        if flag and flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def value_of(scene: Dict[str, Any], key: str, fallback: Any = "") -> Any:
    return scene.get(key, fallback)


def match_value(match: Dict[str, Any], key: str, fallback: Any = "") -> Any:
    # T0115 matches are flat. Some future versions may nest film data.
    if key in match:
        return match.get(key, fallback)
    for nested_key in ("film", "candidate_film", "match_film"):
        nested = match.get(nested_key)
        if isinstance(nested, dict) and key in nested:
            return nested.get(key, fallback)
    return fallback


def infer_flag_from_dimension_scores(match: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    scores = match.get("dimension_scores") or {}
    if not isinstance(scores, dict):
        return flags
    thresholds = {
        "base_motion": 0.70,
        "reaction_profile": 0.70,
        "projection_shape": 0.70,
        "judgment_clarity": 0.80,
    }
    for dim, threshold in thresholds.items():
        val = safe_float(scores.get(dim), None)
        if val is not None and val < threshold:
            flags.append(f"DIMENSION_WEAK_{dim.upper()}")
    return flags


def score_dimension_penalty(match: Dict[str, Any]) -> float:
    scores = match.get("dimension_scores") or {}
    if not isinstance(scores, dict):
        return 0.0
    penalty = 0.0
    for dim, val in scores.items():
        f = safe_float(val, None)
        if f is None:
            continue
        if f < 0.50:
            penalty += 0.16
        elif f < 0.70:
            penalty += 0.10
        elif f < 0.80:
            penalty += 0.05
    return penalty


def flag_and_penalty(query_scene: Dict[str, Any], match: Dict[str, Any]) -> Tuple[List[str], float]:
    flags: List[str] = []
    penalty = 0.0

    q_family = normalize_text(query_scene.get("memory_family"))
    m_family = normalize_text(match_value(match, "memory_family"))
    if q_family and m_family and q_family != m_family:
        flags.append("MEMORY_FAMILY_DIFFERENCE")
        penalty += 0.45

    if "heuristic" in lower_text(query_scene.get("memory_family_origin")):
        flags.append("MEMORY_FAMILY_INFERRED")
        penalty += 0.13

    q_session = normalize_text(query_scene.get("session"))
    m_session = normalize_text(match_value(match, "session"))
    if q_session and m_session and q_session != m_session:
        flags.append("SESSION_DIFFERENCE")
        penalty += 0.08

    q_source_family = normalize_text(query_scene.get("source_family"))
    m_source_family = normalize_text(match_value(match, "source_family"))
    if q_source_family and m_source_family and q_source_family != m_source_family:
        flags.append("SOURCE_FAMILY_DIFFERENCE")
        penalty += 0.10

    q_recovery = normalize_text(query_scene.get("summary_recovery_type"))
    m_recovery = normalize_text(match_value(match, "summary_recovery_type"))
    if q_recovery and m_recovery and q_recovery != m_recovery:
        flags.append("SUMMARY_RECOVERY_TYPE_DIFFERENCE")
        penalty += 0.08

    q_mode = normalize_text(query_scene.get("source_mode"))
    m_mode = normalize_text(match_value(match, "source_mode"))
    if q_mode and m_mode and q_mode != m_mode:
        flags.append("SOURCE_MODE_DIFFERENCE")
        penalty += 0.08

    q_visibility = normalize_text(query_scene.get("data_visibility"))
    m_visibility = normalize_text(match_value(match, "data_visibility"))
    if q_visibility and m_visibility and q_visibility != m_visibility:
        flags.append("DATA_VISIBILITY_DIFFERENCE")
        penalty += 0.08

    q_raw = normalize_text(query_scene.get("raw_agreement") or query_scene.get("proxy_vs_raw_verdict"))
    m_raw = normalize_text(match_value(match, "raw_agreement") or match_value(match, "proxy_vs_raw_verdict"))
    if "NUANCED_BY_RAW" in q_raw:
        flags.append("QUERY_RAW_NUANCED")
        penalty += 0.08
    if "NUANCED_BY_RAW" in m_raw:
        flags.append("MATCH_RAW_NUANCED")
        penalty += 0.06
    if q_raw and m_raw and q_raw != m_raw:
        flags.append("RAW_AGREEMENT_MISMATCH")
        penalty += 0.12
    if "RAW_UNAVAILABLE" in q_raw or "RAW_UNAVAILABLE" in m_raw:
        flags.append("RAW_UNAVAILABLE_SHOULD_NOT_BE_ACTIVE")
        penalty += 0.50

    q_quality = normalize_text(query_scene.get("source_quality_state"))
    m_quality = normalize_text(match_value(match, "source_quality_state"))
    if q_quality and m_quality and q_quality != m_quality:
        flags.append("SOURCE_QUALITY_STATE_DIFFERENCE")
        penalty += 0.07
    if "LIVE_UNQUALIFIED" in q_quality:
        flags.append("QUERY_SOURCE_QUALITY_LIVE_UNQUALIFIED")
        penalty += 0.10

    q_texture = normalize_text(query_scene.get("raw_texture_role"))
    m_texture = normalize_text(match_value(match, "raw_texture_role"))
    if q_texture and m_texture and q_texture != m_texture:
        flags.append("RAW_TEXTURE_ROLE_DIFFERENCE")
        penalty += 0.07

    q_delta = safe_float(query_scene.get("raw_delta_pips"), None)
    m_delta = safe_float(match_value(match, "raw_delta_pips"), None)
    if q_delta is not None and m_delta is not None and sign(q_delta) != 0 and sign(m_delta) != 0 and sign(q_delta) != sign(m_delta):
        flags.append("RAW_DELTA_SIGN_OPPOSITE")
        penalty += 0.12

    q_range = abs(safe_float(query_scene.get("raw_range_pips"), 0.0) or 0.0)
    m_range = abs(safe_float(match_value(match, "raw_range_pips"), 0.0) or 0.0)
    if q_range > 0 and m_range > 0:
        ratio = max(q_range, m_range) / max(min(q_range, m_range), 1e-9)
        if ratio >= 2.0:
            flags.append("RAW_RANGE_SCALE_DIFFERENCE")
            penalty += 0.08

    q_ticks = abs(safe_float(query_scene.get("raw_tick_count"), 0.0) or 0.0)
    m_ticks = abs(safe_float(match_value(match, "raw_tick_count"), 0.0) or 0.0)
    if q_ticks > 0 and m_ticks > 0:
        ratio = max(q_ticks, m_ticks) / max(min(q_ticks, m_ticks), 1e-9)
        if ratio >= 4.0:
            flags.append("RAW_TICK_COUNT_SCALE_DIFFERENCE")
            penalty += 0.08

    text_blob = " ".join([
        lower_text(query_scene.get("base")), lower_text(query_scene.get("reaction")),
        lower_text(query_scene.get("projection")), lower_text(query_scene.get("judgment")),
        lower_text(query_scene.get("limits")), lower_text(match.get("ranking_reason_fr")),
        lower_text(match.get("retest_visibility")), lower_text(match.get("differences")),
    ])
    if "retest" not in text_blob or "not visible" in text_blob or "absent" in text_blob:
        flags.append("RETEST_VISIBILITY_WEAK_OR_ABSENT")
        penalty += 0.08

    dim_flags = infer_flag_from_dimension_scores(match)
    flags.extend(dim_flags)
    penalty += score_dimension_penalty(match)

    similarity = safe_float(match.get("similarity_score"), None)
    if similarity is not None:
        if similarity < 0.70:
            flags.append("LOW_SIMILARITY_SCORE")
            penalty += 0.18
        elif similarity < 0.82:
            flags.append("MODERATE_SIMILARITY_SCORE")
            penalty += 0.08

    return compact_flags(flags), min(1.0, round(penalty, 6))


def fp_state(score: float) -> str:
    if score >= 0.55:
        return "B6_FALSE_POSITIVE_CONTEXT_HIGH"
    if score >= 0.28:
        return "B6_FALSE_POSITIVE_CONTEXT_MEDIUM"
    if score >= 0.12:
        return "B6_FALSE_POSITIVE_CONTEXT_LOW"
    return "B6_FALSE_POSITIVE_CONTEXT_MINIMAL"


def flag_to_fr(flag: str) -> str:
    mapping = {
        "MEMORY_FAMILY_DIFFERENCE": "famille memoire differente",
        "MEMORY_FAMILY_INFERRED": "famille memoire inferee par heuristique",
        "SESSION_DIFFERENCE": "session differente",
        "SOURCE_FAMILY_DIFFERENCE": "famille de source differente",
        "SUMMARY_RECOVERY_TYPE_DIFFERENCE": "type de recuperation different",
        "SOURCE_MODE_DIFFERENCE": "mode source different",
        "DATA_VISIBILITY_DIFFERENCE": "visibilite data differente",
        "QUERY_RAW_NUANCED": "scene live nuancee par le raw",
        "MATCH_RAW_NUANCED": "film historique nuance par le raw",
        "RAW_AGREEMENT_MISMATCH": "accord proxy/raw different",
        "RAW_UNAVAILABLE_SHOULD_NOT_BE_ACTIVE": "raw unavailable present alors qu'il devrait etre exclu",
        "SOURCE_QUALITY_STATE_DIFFERENCE": "qualite source differente",
        "QUERY_SOURCE_QUALITY_LIVE_UNQUALIFIED": "qualite source live non encore qualifiee",
        "RAW_TEXTURE_ROLE_DIFFERENCE": "role de texture raw different",
        "RAW_DELTA_SIGN_OPPOSITE": "signe du delta raw oppose",
        "RAW_RANGE_SCALE_DIFFERENCE": "echelle de range raw differente",
        "RAW_TICK_COUNT_SCALE_DIFFERENCE": "densite de ticks tres differente",
        "RETEST_VISIBILITY_WEAK_OR_ABSENT": "retest faible, absent ou non visible",
        "LOW_SIMILARITY_SCORE": "similarite globale faible",
        "MODERATE_SIMILARITY_SCORE": "similarite globale moderee",
    }
    if flag.startswith("DIMENSION_WEAK_"):
        return "dimension de similarite faible: " + flag.replace("DIMENSION_WEAK_", "").lower()
    return flag.lower().replace("_", " ")


def explain_flags_fr(flags: List[str]) -> str:
    if not flags:
        return "Aucun piege technique majeur detecte dans la comparaison V0. La lecture reste comparative, sans prediction."
    readable = [flag_to_fr(f) for f in flags[:8]]
    return "Pieges techniques: " + "; ".join(readable) + "."


def safe_reading_fr(state: str, flags: List[str]) -> str:
    if state.endswith("HIGH"):
        return "Ressemblance a traiter comme fragile: le film rapproche des formes, mais plusieurs conditions de lecture different."
    if state.endswith("MEDIUM"):
        return "Ressemblance utile mais partielle: B6 reconnait une famille, T0117 signale les ecarts a regarder avant toute lecture forte."
    if state.endswith("LOW"):
        return "Ressemblance exploitable en contexte: quelques ecarts techniques restent visibles."
    return "Ressemblance propre en lecture V0: elle reste un contexte de reconnaissance, pas une repetition." 


def build_record(query_scene: Dict[str, Any], match: Dict[str, Any], rank: int) -> Dict[str, Any]:
    flags, score = flag_and_penalty(query_scene, match)
    state = fp_state(score)
    film_id = normalize_text(match_value(match, "film_id", f"MATCH_{rank}"))
    dimension_scores = match.get("dimension_scores") or {}
    differences = match.get("differences") or {}
    if not isinstance(differences, dict):
        differences = {"raw": str(differences)}
    record = {
        "rank": rank,
        "film_id": film_id,
        "film_date": normalize_text(match_value(match, "film_date") or match_value(match, "date")),
        "time_start": normalize_text(match_value(match, "time_start")),
        "time_end": normalize_text(match_value(match, "time_end")),
        "session": normalize_text(match_value(match, "session")),
        "memory_family": normalize_text(match_value(match, "memory_family")),
        "source_family": normalize_text(match_value(match, "source_family")),
        "summary_recovery_type": normalize_text(match_value(match, "summary_recovery_type")),
        "source_mode": normalize_text(match_value(match, "source_mode")),
        "data_visibility": normalize_text(match_value(match, "data_visibility")),
        "raw_agreement": normalize_text(match_value(match, "raw_agreement") or match_value(match, "proxy_vs_raw_verdict")),
        "source_quality_state": normalize_text(match_value(match, "source_quality_state")),
        "raw_texture_role": normalize_text(match_value(match, "raw_texture_role")),
        "similarity_score": safe_float(match.get("similarity_score"), 0.0),
        "dimension_scores": dimension_scores,
        "differences": differences,
        "false_positive_context_score": score,
        "false_positive_context_state": state,
        "risk_flags": flags,
        "difference_explanation_fr": explain_flags_fr(flags),
        "technical_cautions_fr": explain_flags_fr(flags),
        "safe_comparison_reading_fr": safe_reading_fr(state, flags),
        "not_prediction_notice": "Comparaison de films uniquement. Pas de BUY/SELL. Pas de probabilite de succes.",
    }
    return record


def has_unnegated_trade_terms(text: str) -> bool:
    lowered = text.lower()
    # Allow doctrine/limit phrases such as "no BUY/SELL", "aucun BUY/SELL", "pas de BUY/SELL".
    allowed_markers = ["no buy/sell", "aucun buy/sell", "pas de buy/sell", "sans buy/sell"]
    tmp = lowered
    for marker in allowed_markers:
        tmp = tmp.replace(marker, "")
    return bool(re.search(r"\b(buy|sell|achat|vente)\b", tmp, re.I))


def has_unnegated_prediction_terms(text: str) -> bool:
    lowered = text.lower()
    allowed = ["pas de probabilite de succes", "aucune probabilite de succes", "no probability of success", "not an outcome probability"]
    tmp = lowered
    for marker in allowed:
        tmp = tmp.replace(marker, "")
    return bool(re.search(r"probabilite de succes|probability of success|va faire|va monter|va baisser", tmp, re.I))


def build_false_positive_context(query_result: Dict[str, Any], top_k: int) -> Dict[str, Any]:
    query_scene = query_result.get("query_scene") or {}
    if not isinstance(query_scene, dict):
        raise ValueError("query_result.query_scene must be an object")
    matches = query_result.get("similar_films") or []
    if not isinstance(matches, list):
        raise ValueError("query_result.similar_films must be a list")

    output_records = []
    for i, match in enumerate(matches[:top_k], start=1):
        if not isinstance(match, dict):
            continue
        output_records.append(build_record(query_scene, match, i))

    states: Dict[str, int] = {}
    flags_count: Dict[str, int] = {}
    for r in output_records:
        states[r["false_positive_context_state"]] = states.get(r["false_positive_context_state"], 0) + 1
        for flag in r["risk_flags"]:
            flags_count[flag] = flags_count.get(flag, 0) + 1

    integrity = {
        "matches_reviewed": len(output_records),
        "cross_family_match_count": sum(1 for r in output_records if r.get("memory_family") and r.get("memory_family") != query_scene.get("memory_family")),
        "low_trust_in_results": any("LOW_TRUST" in json.dumps(r, ensure_ascii=False) for r in output_records),
        "raw_unavailable_in_results": any("RAW_UNAVAILABLE" in json.dumps(r, ensure_ascii=False) for r in output_records),
        "buy_sell_terms_present": any(has_unnegated_trade_terms(json.dumps(r, ensure_ascii=False)) for r in output_records),
        "prediction_terms_present": any(has_unnegated_prediction_terms(json.dumps(r, ensure_ascii=False)) for r in output_records),
    }

    return {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "policy": POLICY,
        "doctrine": DOCTRINE,
        "input_query_id": query_result.get("query_id", ""),
        "query_scene": query_scene,
        "false_positive_context_summary": {
            "matches_reviewed": len(output_records),
            "state_counts": states,
            "flag_counts": dict(sorted(flags_count.items(), key=lambda kv: (-kv[1], kv[0]))),
            "primary_message_fr": "La ressemblance n'est pas une repetition. B6 montre les similarites, T0117 montre les pieges de comparaison.",
        },
        "false_positive_contexts": output_records,
        "integrity_checks": integrity,
        "technical_limits": [
            "Read-only: no powerflow.db write and no tick_archive.db write.",
            "Uses T0115 similarity query result as input; does not rebuild T0114 index.",
            "False-positive context score is a technical caution score, not an outcome probability.",
            "Retest visibility is limited to fields present in query result / film cards.",
            "No dashboard, no Telegram, no BUY/SELL, no probability of success.",
        ],
    }


def write_markdown(path: Path, data: Dict[str, Any]) -> None:
    q = data.get("query_scene", {})
    summary = data.get("false_positive_context_summary", {})
    records = data.get("false_positive_contexts", [])
    lines = []
    lines.append("# T0117 — B6 False Positive Context V0")
    lines.append("")
    lines.append("## Phrase de cap")
    lines.append("")
    lines.append("La ressemblance n’est pas une répétition. B6 montre les similarités, T0117 montre les pièges de comparaison.")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append(f"- Query: `{data.get('input_query_id','')}`")
    lines.append(f"- Scene: `{q.get('film_id','')}`")
    lines.append(f"- Famille mémoire: `{q.get('memory_family','')}`")
    lines.append(f"- Matches revus: `{summary.get('matches_reviewed',0)}`")
    lines.append(f"- États: `{summary.get('state_counts',{})}`")
    lines.append("")
    lines.append("## Ce que T0117 fait")
    lines.append("")
    lines.append("T0117 prend le résultat T0115 et explique les pièges techniques de comparaison : source différente, session différente, raw nuancé, retest absent, famille inférée, dimensions faibles, échelles de ticks ou de range différentes.")
    lines.append("")
    lines.append("## Ce que T0117 ne fait pas")
    lines.append("")
    lines.append("- Pas de prédiction.")
    lines.append("- Pas de probabilité de succès.")
    lines.append("- Pas de BUY/SELL.")
    lines.append("- Pas d’écriture DB.")
    lines.append("- Pas de dashboard.")
    lines.append("- Pas de Telegram.")
    lines.append("")
    lines.append("## Matches et pièges")
    lines.append("")
    for r in records:
        lines.append(f"### Rank {r.get('rank')} — {r.get('film_id')}")
        lines.append("")
        lines.append(f"- Similarité T0115: `{r.get('similarity_score')}`")
        lines.append(f"- État T0117: `{r.get('false_positive_context_state')}`")
        lines.append(f"- Score contexte faux positif: `{r.get('false_positive_context_score')}`")
        lines.append(f"- Flags: `{', '.join(r.get('risk_flags', []))}`")
        lines.append(f"- Lecture: {r.get('safe_comparison_reading_fr')}")
        lines.append(f"- Différences: {r.get('difference_explanation_fr')}")
        lines.append("")
    lines.append("## Limites techniques")
    lines.append("")
    for lim in data.get("technical_limits", []):
        lines.append(f"- {lim}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BASE_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "film_id": r.get("film_id", ""),
                "film_date": r.get("film_date", ""),
                "rank": r.get("rank", ""),
                "memory_family": r.get("memory_family", ""),
                "similarity_score": r.get("similarity_score", ""),
                "false_positive_context_score": r.get("false_positive_context_score", ""),
                "false_positive_context_state": r.get("false_positive_context_state", ""),
                "risk_flags": ";".join(r.get("risk_flags", [])),
                "difference_explanation_fr": r.get("difference_explanation_fr", ""),
                "technical_cautions_fr": r.get("technical_cautions_fr", ""),
                "safe_comparison_reading_fr": r.get("safe_comparison_reading_fr", ""),
            })


def write_zip(zip_path: Path, files: List[Path], base_dir: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                zf.write(f, f.relative_to(base_dir).as_posix())


def validate_output(data: Dict[str, Any]) -> None:
    integrity = data.get("integrity_checks", {})
    if integrity.get("buy_sell_terms_present"):
        raise AssertionError("Forbidden BUY/SELL terms detected")
    if integrity.get("prediction_terms_present"):
        raise AssertionError("Forbidden prediction/probability terms detected")
    if integrity.get("raw_unavailable_in_results"):
        # T0117 can flag it if present, but V0 active query should not contain it.
        raise AssertionError("RAW_UNAVAILABLE present in active T0117 result")


def build(args: argparse.Namespace) -> Dict[str, Any]:
    in_path = Path(args.query_result_json)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = load_json(in_path)
    result = build_false_positive_context(data, top_k=args.top_k)
    validate_output(result)

    json_path = out_dir / OUTPUT_JSON
    md_path = out_dir / OUTPUT_MD
    csv_path = out_dir / OUTPUT_CSV
    manifest_path = out_dir / OUTPUT_MANIFEST
    zip_path = out_dir / OUTPUT_ZIP

    write_json(json_path, result)
    write_markdown(md_path, result)
    write_csv(csv_path, result.get("false_positive_contexts", []))
    manifest = {
        "version": VERSION,
        "generated_at_utc": result["generated_at_utc"],
        "input": str(in_path),
        "outputs": [OUTPUT_JSON, OUTPUT_MD, OUTPUT_CSV, OUTPUT_MANIFEST, OUTPUT_ZIP],
        "policy": POLICY,
        "read_only": True,
        "no_db_write": True,
        "no_dashboard": True,
        "no_telegram": True,
        "no_buy_sell": True,
        "no_success_probability": True,
        "integrity_checks": result.get("integrity_checks", {}),
    }
    write_json(manifest_path, manifest)
    write_zip(zip_path, [json_path, md_path, csv_path, manifest_path], out_dir)

    return {
        "version": VERSION,
        "input_query_id": result.get("input_query_id"),
        "matches_reviewed": len(result.get("false_positive_contexts", [])),
        "state_counts": result.get("false_positive_context_summary", {}).get("state_counts", {}),
        "cross_family_match_count": result.get("integrity_checks", {}).get("cross_family_match_count"),
        "low_trust_in_results": result.get("integrity_checks", {}).get("low_trust_in_results"),
        "raw_unavailable_in_results": result.get("integrity_checks", {}).get("raw_unavailable_in_results"),
        "output_dir": str(out_dir),
        "zip": str(zip_path),
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build T0117 B6 false positive context from T0115 query result.")
    p.add_argument("--query-result-json", required=True, help="Path to B6_SIMILARITY_QUERY_RESULT_V0.json")
    p.add_argument("--output-dir", required=True, help="Output directory")
    p.add_argument("--top-k", type=int, default=5, help="Number of matches to review")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    summary = build(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
