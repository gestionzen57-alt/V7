#!/usr/bin/env python3
"""
T0115 — B6 Similarity Query CLI/API V0

Read-only query layer for the T0114 B6 Similarity Index V0.

Doctrine:
- B6 does not predict.
- B6 compares films.
- Similarity is recognition context, not a trading signal.
- No BUY/SELL, no probability of success, no DB write.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0115_B6_SIMILARITY_QUERY_CLI_API_V0"
POLICY = "QUERY_INDEX_ONLY_INTRA_MEMORY_FAMILY_V0"

DOCTRINE = [
    "B6 ne prédit pas.",
    "B6 compare des films.",
    "Une similarité est un contexte de reconnaissance, jamais une probabilité de succès.",
    "Aucun BUY/SELL, aucun conseil d'exécution, aucune écriture DB.",
]

DIMENSIONS = [
    {"name": "base_motion", "weight": 0.25},
    {"name": "reaction_profile", "weight": 0.25},
    {"name": "projection_shape", "weight": 0.25},
    {"name": "judgment_clarity", "weight": 0.25},
]

TEXT_FIELDS = {
    "base_motion": "base",
    "reaction_profile": "reaction",
    "projection_shape": "projection",
    "judgment_clarity": "judgment",
}

NUMERIC_FIELDS = {
    "reaction_profile": ["raw_delta_pips", "raw_range_pips", "raw_tick_count"],
    "projection_shape": ["raw_delta_pips", "raw_range_pips", "b6_memory_candidate_score"],
    "judgment_clarity": ["source_quality_score", "confidence_cap", "b6_memory_candidate_score"],
}

NUMERIC_SCALES = {
    "raw_delta_pips": 10.0,
    "raw_range_pips": 20.0,
    "raw_tick_count": 3000.0,
    "source_quality_score": 1.0,
    "confidence_cap": 1.0,
    "b6_memory_candidate_score": 1.0,
}

FAMILY_VALUES = {
    "DIRECTIONAL_PROGRESS_MEMORY",
    "FRICTION_ABSORPTION_MEMORY",
    "ROTATION_BREATH_MEMORY",
}

REJECTED_STATES = {"B6_LOW_TRUST_CANDIDATE", "B6_REJECT_RAW_UNAVAILABLE", "RAW_UNAVAILABLE"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any, length: int = 12) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length].upper()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "nan"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_tokens(text: Any) -> List[str]:
    if text is None:
        return []
    s = str(text).lower()
    s = re.sub(r"[^a-z0-9àâäçéèêëîïôöùûüÿñæœ_+-]+", " ", s)
    tokens = [t for t in s.split() if len(t) > 1]
    return tokens


def text_similarity(a: Any, b: Any) -> float:
    ta = set(normalize_tokens(a))
    tb = set(normalize_tokens(b))
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def numeric_similarity(a: Any, b: Any, scale: float) -> Optional[float]:
    fa = as_float(a)
    fb = as_float(b)
    if fa is None or fb is None:
        return None
    if scale <= 0:
        scale = 1.0
    return max(0.0, 1.0 - min(abs(fa - fb) / scale, 1.0))


def mean(values: Iterable[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def infer_memory_family(scene: Dict[str, Any]) -> Tuple[str, str]:
    explicit = str(scene.get("memory_family") or "").strip()
    if explicit in FAMILY_VALUES:
        return explicit, "EXPLICIT_MEMORY_FAMILY"

    texture = str(scene.get("raw_texture_role") or "").upper()
    moment_type = str(scene.get("moment_type") or "").upper()
    label = str(scene.get("label_fr") or "").lower()
    raw_delta = abs(as_float(scene.get("raw_delta_pips")) or 0.0)
    raw_range = abs(as_float(scene.get("raw_range_pips")) or 0.0)
    ratio = raw_delta / raw_range if raw_range > 0 else 0.0

    if "FRICTION" in texture or "ABSORPT" in texture or "absorption" in label or "EFFORT_WITHOUT_RESULT" in moment_type:
        return "FRICTION_ABSORPTION_MEMORY", "INFERRED_FROM_TEXTURE_OR_LABEL"
    if "ROTATION" in texture or "BREATH" in texture or "respiration" in label or raw_range <= 2.0:
        return "ROTATION_BREATH_MEMORY", "INFERRED_FROM_TEXTURE_OR_SMALL_RANGE"
    if "PROGRESS" in texture or "PROGRESS" in moment_type or ratio >= 0.35:
        return "DIRECTIONAL_PROGRESS_MEMORY", "INFERRED_FROM_PROGRESS_OR_DELTA_RANGE"
    return "FRICTION_ABSORPTION_MEMORY", "DEFAULT_INFERRED_LOW_CONFIDENCE"


def extract_query_film(index_entry: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(index_entry.get("query_film") or {})
    if "memory_family" not in q and index_entry.get("memory_family"):
        q["memory_family"] = index_entry.get("memory_family")
    return q


def validate_index(index: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries = index.get("film_similarity_index")
    if not isinstance(entries, list):
        raise ValueError("Invalid T0114 index: missing film_similarity_index list")
    films: List[Dict[str, Any]] = []
    seen = set()
    for entry in entries:
        film = extract_query_film(entry)
        film_id = str(film.get("film_id") or "").strip()
        if not film_id or film_id in seen:
            continue
        seen.add(film_id)
        state = str(film.get("b6_memory_candidate_state") or "").strip()
        verdict = str(film.get("proxy_vs_raw_verdict") or film.get("raw_agreement") or "").strip()
        family = str(film.get("memory_family") or "").strip()
        if state in REJECTED_STATES or verdict == "RAW_UNAVAILABLE" or family not in FAMILY_VALUES:
            continue
        films.append(film)
    return films


def dimension_score(query: Dict[str, Any], candidate: Dict[str, Any], dimension: str) -> Tuple[float, Dict[str, Any]]:
    text_field = TEXT_FIELDS[dimension]
    txt = text_similarity(query.get(text_field), candidate.get(text_field))
    numeric_parts: Dict[str, float] = {}
    for field in NUMERIC_FIELDS.get(dimension, []):
        score = numeric_similarity(query.get(field), candidate.get(field), NUMERIC_SCALES.get(field, 1.0))
        if score is not None:
            numeric_parts[field] = round(score, 6)
    num = mean(numeric_parts.values())
    if num is None:
        final = txt
    else:
        final = (0.55 * txt) + (0.45 * num)
    audit = {
        "text_similarity": round(txt, 6),
        "numeric_similarity": None if num is None else round(num, 6),
        "numeric_parts": numeric_parts,
    }
    return round(clamp01(final), 6), audit


def compare_scenes(query: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    dim_scores: Dict[str, float] = {}
    audit: Dict[str, Any] = {}
    weighted_total = 0.0
    for dim in DIMENSIONS:
        name = dim["name"]
        score, dim_audit = dimension_score(query, candidate, name)
        dim_scores[name] = score
        audit[name] = dim_audit
        weighted_total += score * float(dim["weight"])
    return {
        "similarity_score": round(clamp01(weighted_total), 6),
        "dimension_scores": dim_scores,
        "audit": audit,
    }


def numeric_delta(query: Dict[str, Any], candidate: Dict[str, Any], field: str, suffix: str) -> str:
    q = as_float(query.get(field))
    c = as_float(candidate.get(field))
    if q is None or c is None:
        return "not comparable"
    delta = c - q
    return f"{delta:+.3f} {suffix}".strip()


def delta_label(score: float, dimension: str) -> str:
    if score >= 0.90:
        state = "close"
    elif score >= 0.75:
        state = "partial"
    elif score >= 0.55:
        state = "distant"
    else:
        state = "very distant"
    return f"{state} ({dimension} similarity {score:.2f})"


def retest_visibility(film: Dict[str, Any]) -> str:
    text = " ".join(str(film.get(k, "")) for k in ["limits", "base", "reaction", "projection", "judgment", "raw_texture_role"])
    up = text.upper()
    if "RETEST_NOT_VISIBLE" in up or "RETEST_SOURCE_NOT_VISIBLE" in up:
        return "RETEST_NOT_VISIBLE_IN_FILM_CARD"
    if "RETEST" in up:
        return "RETEST_MENTIONED_IN_FILM_CARD"
    return "RETEST_NOT_EXPLICIT_IN_FILM_CARD"


def ranking_reason(dim_scores: Dict[str, float]) -> str:
    best = max(dim_scores.items(), key=lambda kv: kv[1])
    worst = min(dim_scores.items(), key=lambda kv: kv[1])
    return (
        "Film proche par comparaison 4D intra-famille: "
        f"force principale={best[0]} {best[1]:.2f}; "
        f"écart principal={worst[0]} {worst[1]:.2f}. "
        "Lecture de similarité uniquement, sans prédiction."
    )


def build_match(query: Dict[str, Any], candidate: Dict[str, Any], rank: int, comp: Dict[str, Any]) -> Dict[str, Any]:
    ds = comp["dimension_scores"]
    return {
        "rank": rank,
        "film_id": candidate.get("film_id"),
        "film_date": candidate.get("date"),
        "time_start": candidate.get("time_start"),
        "time_end": candidate.get("time_end"),
        "session": candidate.get("session"),
        "memory_family": candidate.get("memory_family"),
        "similarity_score": comp["similarity_score"],
        "dimension_scores": ds,
        "differences": {
            "base_delta": delta_label(ds["base_motion"], "base_motion"),
            "reaction_delta": delta_label(ds["reaction_profile"], "reaction_profile"),
            "projection_delta": delta_label(ds["projection_shape"], "projection_shape"),
            "judgment_delta": delta_label(ds["judgment_clarity"], "judgment_clarity"),
            "raw_delta_pips_delta": numeric_delta(query, candidate, "raw_delta_pips", "pips"),
            "raw_range_pips_delta": numeric_delta(query, candidate, "raw_range_pips", "pips"),
            "raw_tick_count_delta": numeric_delta(query, candidate, "raw_tick_count", "ticks"),
            "source_quality_score_delta": numeric_delta(query, candidate, "source_quality_score", ""),
        },
        "ranking_reason_fr": ranking_reason(ds),
        "retest_visibility": retest_visibility(candidate),
        "source_family": candidate.get("source_family"),
        "summary_recovery_type": candidate.get("summary_recovery_type"),
        "source_mode": candidate.get("source_mode"),
        "data_visibility": candidate.get("data_visibility"),
        "raw_agreement": candidate.get("raw_agreement") or candidate.get("proxy_vs_raw_verdict"),
        "source_quality_state": candidate.get("source_quality_state") or candidate.get("source_quality"),
        "raw_texture_role": candidate.get("raw_texture_role"),
        "limits": candidate.get("limits"),
        "audit": comp["audit"],
    }


def query_by_scene(index: Dict[str, Any], query_scene: Dict[str, Any], top_k: int, min_score: float = 0.0) -> Dict[str, Any]:
    films = validate_index(index)
    query = dict(query_scene)
    family, family_origin = infer_memory_family(query)
    query["memory_family"] = family
    if not query.get("film_id"):
        query["film_id"] = f"CURRENT_SCENE_{stable_hash(query, 10)}"
    if not query.get("date") and query.get("time_start"):
        query["date"] = str(query["time_start"])[:10]

    matches: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for film in films:
        if film.get("memory_family") != family:
            continue
        if str(film.get("film_id")) == str(query.get("film_id")):
            continue
        comp = compare_scenes(query, film)
        if comp["similarity_score"] >= min_score:
            matches.append((film, comp))
    matches.sort(key=lambda pair: pair[1]["similarity_score"], reverse=True)
    top = [build_match(query, film, i + 1, comp) for i, (film, comp) in enumerate(matches[:top_k])]

    family_counts = Counter(f.get("memory_family") for f in films)
    result = {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "query_id": f"B6Q_{stable_hash({'query': query, 'top_k': top_k}, 12)}",
        "policy": POLICY,
        "doctrine": DOCTRINE,
        "query_scene": {
            "film_id": query.get("film_id"),
            "date": query.get("date"),
            "time_start": query.get("time_start"),
            "time_end": query.get("time_end"),
            "session": query.get("session"),
            "memory_family": query.get("memory_family"),
            "memory_family_origin": family_origin,
            "source_family": query.get("source_family"),
            "summary_recovery_type": query.get("summary_recovery_type"),
            "source_mode": query.get("source_mode"),
            "data_visibility": query.get("data_visibility"),
            "confidence_cap": query.get("confidence_cap"),
            "moment_type": query.get("moment_type"),
            "label_fr": query.get("label_fr"),
            "raw_agreement": query.get("raw_agreement") or query.get("proxy_vs_raw_verdict"),
            "proxy_vs_raw_verdict": query.get("proxy_vs_raw_verdict"),
            "source_quality_state": query.get("source_quality_state") or query.get("source_quality"),
            "b6_memory_candidate_state": query.get("b6_memory_candidate_state"),
            "raw_texture_role": query.get("raw_texture_role"),
            "raw_delta_pips": query.get("raw_delta_pips"),
            "raw_range_pips": query.get("raw_range_pips"),
            "raw_tick_count": query.get("raw_tick_count"),
            "base": query.get("base"),
            "reaction": query.get("reaction"),
            "projection": query.get("projection"),
            "judgment": query.get("judgment"),
            "limits": query.get("limits"),
        },
        "similarity_dimensions": DIMENSIONS,
        "index_stats": {
            "active_indexed_cards": len(films),
            "family_counts": dict(family_counts),
            "query_family_candidate_count": family_counts.get(family, 0),
            "cross_family_policy": "excluded from results",
            "low_trust_policy": "excluded from active query results",
            "raw_unavailable_policy": "excluded from active query results",
        },
        "similar_films": top,
        "integrity_checks": {
            "read_only": True,
            "db_write": False,
            "dashboard": False,
            "telegram": False,
            "buy_sell_language": False,
            "probability_of_success": False,
            "low_trust_in_results": any(m.get("source_quality_state") == "LOW_TRUST" for m in top),
            "raw_unavailable_in_results": any(m.get("raw_agreement") == "RAW_UNAVAILABLE" for m in top),
            "cross_family_match_count": sum(1 for m in top if m.get("memory_family") != family),
        },
        "technical_limits": [
            "T0115 queries T0114 index only; it does not rebuild similarity index.",
            "Similarity is intra-memory-family in V0.",
            "Scores are comparative reading scores, not probabilities.",
            "Query scenes without explicit memory_family are assigned by heuristic and marked with memory_family_origin.",
            "Retest visibility is limited to fields present in the film cards/index.",
        ],
    }
    return result


def find_precomputed(index: Dict[str, Any], film_id: str) -> Optional[Dict[str, Any]]:
    for entry in index.get("film_similarity_index", []):
        q = entry.get("query_film") or {}
        if str(q.get("film_id")) == film_id:
            result = {
                "version": VERSION,
                "generated_at_utc": utc_now(),
                "query_id": f"B6Q_PRECOMPUTED_{film_id}",
                "policy": POLICY,
                "doctrine": DOCTRINE,
                "query_scene": q,
                "similarity_dimensions": DIMENSIONS,
                "index_stats": {
                    "active_indexed_cards": len(validate_index(index)),
                    "query_family_candidate_count": None,
                    "cross_family_policy": "excluded from results",
                    "low_trust_policy": "excluded from active query results",
                    "raw_unavailable_policy": "excluded from active query results",
                    "precomputed_from_t0114": True,
                },
                "similar_films": entry.get("similar_films") or [],
                "integrity_checks": {
                    "read_only": True,
                    "db_write": False,
                    "dashboard": False,
                    "telegram": False,
                    "buy_sell_language": False,
                    "probability_of_success": False,
                    "low_trust_in_results": False,
                    "raw_unavailable_in_results": any(m.get("raw_agreement") == "RAW_UNAVAILABLE" for m in entry.get("similar_films") or []),
                    "cross_family_match_count": sum(1 for m in entry.get("similar_films") or [] if m.get("memory_family") != q.get("memory_family")),
                },
                "technical_limits": [
                    "Result loaded from T0114 precomputed film_similarity_index.",
                    "Similarity is recognition context only, not a prediction.",
                ],
            }
            return result
    return None


def build_scene_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    scene = {
        "film_id": args.scene_id,
        "date": args.date,
        "time_start": args.time_start,
        "time_end": args.time_end,
        "session": args.session,
        "memory_family": args.memory_family,
        "source_family": args.source_family,
        "summary_recovery_type": args.summary_recovery_type,
        "source_mode": args.source_mode,
        "data_visibility": args.data_visibility,
        "confidence_cap": args.confidence_cap,
        "moment_type": args.moment_type,
        "label_fr": args.label_fr,
        "raw_agreement": args.raw_agreement,
        "proxy_vs_raw_verdict": args.raw_agreement,
        "source_quality_state": args.source_quality_state,
        "source_quality_score": args.source_quality_score,
        "b6_memory_candidate_state": args.b6_memory_candidate_state,
        "b6_memory_candidate_score": args.b6_memory_candidate_score,
        "raw_texture_role": args.raw_texture_role,
        "raw_delta_pips": args.raw_delta_pips,
        "raw_range_pips": args.raw_range_pips,
        "raw_tick_count": args.raw_tick_count,
        "base": args.base,
        "reaction": args.reaction,
        "projection": args.projection,
        "judgment": args.judgment,
        "limits": args.limits,
    }
    return {k: v for k, v in scene.items() if v not in (None, "")}


def render_markdown(result: Dict[str, Any]) -> str:
    q = result.get("query_scene", {})
    lines = [
        "# B6 Similarity Query Result V0",
        "",
        "## Doctrine",
        "",
        "```text",
        "B6 ne prédit pas.",
        "B6 compare des films.",
        "Une similarité est un contexte de reconnaissance, jamais une probabilité de succès.",
        "```",
        "",
        "## Query scene",
        "",
        f"- query_id: `{result.get('query_id')}`",
        f"- film_id: `{q.get('film_id')}`",
        f"- date: `{q.get('date')}`",
        f"- session: `{q.get('session')}`",
        f"- memory_family: `{q.get('memory_family')}`",
        f"- source_family: `{q.get('source_family')}`",
        f"- raw_agreement: `{q.get('raw_agreement') or q.get('proxy_vs_raw_verdict')}`",
        f"- source_quality_state: `{q.get('source_quality_state')}`",
        "",
        "## Similar films",
        "",
    ]
    matches = result.get("similar_films") or []
    if not matches:
        lines.append("No similar film found under current intra-family policy.")
    else:
        lines.append("| rank | film_id | date | session | family | score | raw agreement | reason |")
        lines.append("|---:|---|---|---|---|---:|---|---|")
        for m in matches:
            reason = str(m.get("ranking_reason_fr") or "").replace("|", "/")
            lines.append(
                f"| {m.get('rank')} | `{m.get('film_id')}` | {m.get('film_date')} | {m.get('session')} | "
                f"{m.get('memory_family')} | {m.get('similarity_score')} | {m.get('raw_agreement')} | {reason} |"
            )
    lines += [
        "",
        "## Integrity checks",
        "",
        "```json",
        json.dumps(result.get("integrity_checks", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Technical limits",
        "",
    ]
    for limit in result.get("technical_limits", []):
        lines.append(f"- {limit}")
    lines.append("")
    return "\n".join(lines)


def write_csv(path: Path, result: Dict[str, Any]) -> None:
    matches = result.get("similar_films") or []
    fields = [
        "query_id", "query_film_id", "rank", "film_id", "film_date", "time_start", "time_end", "session",
        "memory_family", "similarity_score", "base_motion", "reaction_profile", "projection_shape", "judgment_clarity",
        "source_family", "summary_recovery_type", "raw_agreement", "source_quality_state", "raw_texture_role", "ranking_reason_fr",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for m in matches:
            ds = m.get("dimension_scores", {})
            writer.writerow({
                "query_id": result.get("query_id"),
                "query_film_id": result.get("query_scene", {}).get("film_id"),
                "rank": m.get("rank"),
                "film_id": m.get("film_id"),
                "film_date": m.get("film_date"),
                "time_start": m.get("time_start"),
                "time_end": m.get("time_end"),
                "session": m.get("session"),
                "memory_family": m.get("memory_family"),
                "similarity_score": m.get("similarity_score"),
                "base_motion": ds.get("base_motion"),
                "reaction_profile": ds.get("reaction_profile"),
                "projection_shape": ds.get("projection_shape"),
                "judgment_clarity": ds.get("judgment_clarity"),
                "source_family": m.get("source_family"),
                "summary_recovery_type": m.get("summary_recovery_type"),
                "raw_agreement": m.get("raw_agreement"),
                "source_quality_state": m.get("source_quality_state"),
                "raw_texture_role": m.get("raw_texture_role"),
                "ranking_reason_fr": m.get("ranking_reason_fr"),
            })


def build_manifest(result: Dict[str, Any], output_dir: Path, index_path: Path) -> Dict[str, Any]:
    files = []
    for p in sorted(output_dir.glob("B6_SIMILARITY_QUERY_RESULT_V0*")):
        files.append({"path": p.name, "bytes": p.stat().st_size})
    return {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "input_index": str(index_path),
        "policy": POLICY,
        "query_id": result.get("query_id"),
        "query_memory_family": result.get("query_scene", {}).get("memory_family"),
        "similar_films_count": len(result.get("similar_films") or []),
        "files": files,
        "integrity_checks": result.get("integrity_checks"),
        "doctrine": DOCTRINE,
        "next_step": "Wire this CLI/API output into a read-only B6 query adapter when a live B9 scene is available.",
    }


def zip_outputs(output_dir: Path) -> Path:
    zip_path = output_dir / "B6_SIMILARITY_QUERY_RESULT_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output_dir.glob("B6_SIMILARITY_QUERY_RESULT_V0*")):
            if p == zip_path:
                continue
            z.write(p, arcname=p.name)
    return zip_path


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query T0114 B6 Similarity Index V0 without rebuilding it.")
    parser.add_argument("--similarity-index", required=True, help="Path to B6_SIMILARITY_INDEX_V0.json")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query-film-id", help="Existing film_id present in the T0114 index")
    group.add_argument("--query-json", help="JSON file containing a current scene / film-like payload")
    group.add_argument("--scene-id", help="Ad-hoc current scene id; use with scene field arguments")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.0)

    parser.add_argument("--date")
    parser.add_argument("--time-start")
    parser.add_argument("--time-end")
    parser.add_argument("--session")
    parser.add_argument("--memory-family")
    parser.add_argument("--source-family")
    parser.add_argument("--summary-recovery-type")
    parser.add_argument("--source-mode")
    parser.add_argument("--data-visibility")
    parser.add_argument("--confidence-cap")
    parser.add_argument("--moment-type")
    parser.add_argument("--label-fr")
    parser.add_argument("--raw-agreement")
    parser.add_argument("--source-quality-state")
    parser.add_argument("--source-quality-score")
    parser.add_argument("--b6-memory-candidate-state")
    parser.add_argument("--b6-memory-candidate-score")
    parser.add_argument("--raw-texture-role")
    parser.add_argument("--raw-delta-pips")
    parser.add_argument("--raw-range-pips")
    parser.add_argument("--raw-tick-count")
    parser.add_argument("--base")
    parser.add_argument("--reaction")
    parser.add_argument("--projection")
    parser.add_argument("--judgment")
    parser.add_argument("--limits")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    index_path = Path(args.similarity_index)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    index = load_json(index_path)
    if args.query_film_id:
        result = find_precomputed(index, args.query_film_id)
        if result is None:
            raise SystemExit(f"film_id not found in index: {args.query_film_id}")
        if args.top_k >= 0:
            result["similar_films"] = (result.get("similar_films") or [])[: args.top_k]
    elif args.query_json:
        query_scene = load_json(Path(args.query_json))
        if "query_scene" in query_scene and isinstance(query_scene["query_scene"], dict):
            query_scene = query_scene["query_scene"]
        result = query_by_scene(index, query_scene, top_k=args.top_k, min_score=args.min_score)
    else:
        query_scene = build_scene_from_args(args)
        result = query_by_scene(index, query_scene, top_k=args.top_k, min_score=args.min_score)

    out_json = output_dir / "B6_SIMILARITY_QUERY_RESULT_V0.json"
    out_md = output_dir / "B6_SIMILARITY_QUERY_RESULT_V0.md"
    out_csv = output_dir / "B6_SIMILARITY_QUERY_RESULT_V0.csv"
    write_json(out_json, result)
    write_text(out_md, render_markdown(result))
    write_csv(out_csv, result)
    manifest = build_manifest(result, output_dir, index_path)
    out_manifest = output_dir / "B6_SIMILARITY_QUERY_RESULT_V0_MANIFEST.json"
    write_json(out_manifest, manifest)
    zip_path = zip_outputs(output_dir)

    print(json.dumps({
        "version": VERSION,
        "query_id": result.get("query_id"),
        "matches": len(result.get("similar_films") or []),
        "query_memory_family": result.get("query_scene", {}).get("memory_family"),
        "cross_family_match_count": result.get("integrity_checks", {}).get("cross_family_match_count"),
        "low_trust_in_results": result.get("integrity_checks", {}).get("low_trust_in_results"),
        "raw_unavailable_in_results": result.get("integrity_checks", {}).get("raw_unavailable_in_results"),
        "output_dir": str(output_dir),
        "zip": str(zip_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
