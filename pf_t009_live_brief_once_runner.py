"""T0148 - B9 Live Brief Once Runner V0.

Read-only orchestration layer for PowerFlow B9/B6 live brief generation.
It consumes existing JSON outputs and writes a single brief. It never writes DB,
never triggers dashboard/Telegram, and never produces execution advice.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

VERSION = "T0148_B9_LIVE_BRIEF_ONCE_RUNNER_V0"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b",
    r"\bSELL\b",
    r"\bACHETER\b",
    r"\bVENDRE\b",
    r"probabilit[ée]\s+de\s+succ[èe]s",
    r"taux\s+de\s+r[ée]ussite",
]

REQUIRED_INPUTS = [
    "latest_scene_json",
    "adapter_json",
    "similarity_query_json",
    "false_positive_json",
    "terrain_synthesis_json",
    "french_report_json",
]


def _read_json(path: Optional[str | Path]) -> Any:
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in (
            "similar_films",
            "false_positive_contexts",
            "matches",
            "rows",
            "items",
            "candidates",
            "moments",
            "false_positive_rows",
        ):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _first_text(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _short_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12].upper()


def forbidden_hits(text: str) -> List[str]:
    hits: List[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def _extract_latest_candidate(latest: Any, queue: Any) -> Dict[str, Any]:
    if isinstance(latest, dict):
        # Some outputs wrap the candidate, some are the candidate.
        if isinstance(latest.get("latest_scene_candidate"), dict):
            return dict(latest["latest_scene_candidate"])
        if isinstance(latest.get("candidate"), dict):
            return dict(latest["candidate"])
        return dict(latest)
    candidates = _as_list(queue)
    if candidates and isinstance(candidates[0], dict):
        return dict(candidates[0])
    return {}


def _extract_matches(similarity: Any, top_k: int) -> List[Dict[str, Any]]:
    matches = _as_list(similarity)
    out: List[Dict[str, Any]] = []
    for match in matches[:top_k]:
        if isinstance(match, dict):
            out.append(dict(match))
    return out


def _extract_fp_rows(false_positive: Any) -> List[Dict[str, Any]]:
    rows = _as_list(false_positive)
    return [dict(r) for r in rows if isinstance(r, dict)]


def _match_fp_for_film(fp_rows: Sequence[Dict[str, Any]], film_id: str) -> Dict[str, Any]:
    if not film_id:
        return {}
    for row in fp_rows:
        if _first_text(row.get("film_id"), row.get("match_film_id"), row.get("memory_film_id")) == film_id:
            return row
    return fp_rows[0] if fp_rows else {}


def _terrain_context(terrain: Any) -> Dict[str, Any]:
    if not isinstance(terrain, dict):
        return {}
    if isinstance(terrain.get("summary"), dict):
        return terrain["summary"]
    if isinstance(terrain.get("terrain_synthesis"), dict):
        return terrain["terrain_synthesis"]
    return terrain


def _french_report_text(report: Any) -> str:
    if isinstance(report, dict):
        for key in ("report_md", "markdown", "brief_md", "text"):
            if isinstance(report.get(key), str):
                return report[key]
        sections = report.get("sections")
        if isinstance(sections, dict):
            return "\n".join(str(v) for v in sections.values())
        return json.dumps(report, ensure_ascii=False)
    return ""


def _availability(paths: Mapping[str, Optional[str | Path]]) -> Tuple[Dict[str, bool], List[str]]:
    available: Dict[str, bool] = {}
    missing: List[str] = []
    for key in REQUIRED_INPUTS:
        p = paths.get(key)
        ok = bool(p) and Path(p).exists()
        available[key] = ok
        if not ok:
            missing.append(key)
    return available, missing


def build_live_brief(
    *,
    latest_scene_json: Optional[str | Path],
    queue_json: Optional[str | Path],
    adapter_json: Optional[str | Path],
    similarity_query_json: Optional[str | Path],
    false_positive_json: Optional[str | Path],
    terrain_synthesis_json: Optional[str | Path],
    french_report_json: Optional[str | Path],
    output_dir: str | Path,
    top_k: int = 3,
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_paths: Dict[str, Optional[str | Path]] = {
        "latest_scene_json": latest_scene_json,
        "queue_json": queue_json,
        "adapter_json": adapter_json,
        "similarity_query_json": similarity_query_json,
        "false_positive_json": false_positive_json,
        "terrain_synthesis_json": terrain_synthesis_json,
        "french_report_json": french_report_json,
    }
    available, missing = _availability(input_paths)

    latest = _read_json(latest_scene_json)
    queue = _read_json(queue_json)
    adapter = _read_json(adapter_json)
    similarity = _read_json(similarity_query_json)
    false_positive = _read_json(false_positive_json)
    terrain = _read_json(terrain_synthesis_json)
    french_report = _read_json(french_report_json)

    candidate = _extract_latest_candidate(latest, queue)
    adapter_payload = adapter if isinstance(adapter, dict) else {}
    matches = _extract_matches(similarity, top_k)
    fp_rows = _extract_fp_rows(false_positive)
    terrain_ctx = _terrain_context(terrain)

    top_match = matches[0] if matches else {}
    top_film_id = _first_text(
        top_match.get("film_id"),
        top_match.get("match_film_id"),
        top_match.get("memory_film_id"),
        default="",
    )
    fp_for_top = _match_fp_for_film(fp_rows, top_film_id)

    candidate_id = _first_text(
        candidate.get("candidate_id"),
        candidate.get("scene_candidate_id"),
        candidate.get("scene_id"),
        adapter_payload.get("film_id"),
        default="B9C_" + _short_hash(candidate or adapter_payload or input_paths),
    )

    source_state = _first_text(
        candidate.get("b9_source_quality_gate_state"),
        candidate.get("source_quality_state"),
        adapter_payload.get("source_quality_state"),
        default="SOURCE_QUALITY_NOT_PROVIDED",
    )
    scene_role = _first_text(
        candidate.get("b9_scene_role"),
        candidate.get("scene_role"),
        candidate.get("label_fr"),
        adapter_payload.get("scene_role"),
        default="SCENE_ROLE_NOT_PROVIDED",
    )
    verdict = _first_text(
        candidate.get("b9_price_verdict_state"),
        candidate.get("price_verdict"),
        default="PRICE_VERDICT_NOT_PROVIDED",
    )
    memory_ladder = _first_text(
        candidate.get("b9_memory_ladder_state"),
        candidate.get("b9_memory_confidence_ladder_state"),
        candidate.get("memory_confidence_state"),
        default="MEMORY_LADDER_NOT_PROVIDED",
    )
    family = _first_text(
        candidate.get("b9_b6_scene_family"),
        candidate.get("scene_family"),
        candidate.get("memory_family"),
        adapter_payload.get("memory_family"),
        default="MEMORY_FAMILY_NOT_PROVIDED",
    )

    low_trust = bool(similarity.get("low_trust_in_results")) if isinstance(similarity, dict) else False
    raw_unavailable = bool(similarity.get("raw_unavailable_in_results")) if isinstance(similarity, dict) else False
    cross_family = similarity.get("cross_family_match_count", 0) if isinstance(similarity, dict) else 0

    brief_state = "B9_LIVE_BRIEF_READY" if not missing else "BLOCKED_MISSING_INPUTS"
    if raw_unavailable:
        brief_state = "BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS"

    technical_blockers = []
    if missing:
        technical_blockers.append("Entrées runtime manquantes : " + ", ".join(missing))
    if raw_unavailable:
        technical_blockers.append("Résultats mémoire contiennent RAW_UNAVAILABLE : rejet de la brief active.")
    if low_trust:
        technical_blockers.append("Résultats mémoire contiennent LOW_TRUST : brief à relecture technique.")

    false_positive_state = _first_text(
        fp_for_top.get("b9_memory_false_positive_state"),
        fp_for_top.get("false_positive_context_state"),
        fp_for_top.get("state"),
        default="FALSE_POSITIVE_CONTEXT_NOT_PROVIDED",
    )
    similarity_caution = _first_text(
        fp_for_top.get("b9_memory_similarity_caution_fr"),
        fp_for_top.get("technical_cautions_fr"),
        fp_for_top.get("difference_explanation_fr"),
        default="Aucun piège mémoire détaillé fourni par l'entrée T0117/T0145.",
    )

    terrain_sentence = _first_text(
        terrain_ctx.get("terrain_summary_fr"),
        terrain_ctx.get("executive_summary_fr"),
        terrain_ctx.get("summary_fr"),
        default="Synthèse terrain non fournie.",
    )
    report_text = _french_report_text(french_report)

    sections = {
        "ce_que_b9_voit": f"B9 retient la scène candidate {candidate_id} avec le rôle {scene_role}.",
        "d_ou_vient_le_prix": _first_text(candidate.get("price_origin_fr"), candidate.get("d_ou_vient_le_prix"), default="Origine du prix non fournie dans la scène candidate."),
        "zone_active": _first_text(candidate.get("active_zone_fr"), candidate.get("zone_active"), candidate.get("zone_memory_state"), default="Zone active non fournie."),
        "effort_resultat_progres": _first_text(candidate.get("b9_effort_result_progress_reading_fr"), default="Lecture effort/résultat/progrès non fournie."),
        "retest_qui_juge": _first_text(candidate.get("retest_judgment_fr"), candidate.get("b9_native_retest_judgment"), default="Retest non fourni ou non visible."),
        "memoire_b6": f"Famille mémoire : {family}. Top film proche : {top_film_id or 'non disponible'}. Ladder : {memory_ladder}.",
        "pieges_techniques": similarity_caution,
        "terrain": terrain_sentence,
        "ce_que_b9_ne_peut_pas_conclure": "B9 ne conclut pas une exécution. La similarité mémoire reste une proximité de lecture, pas une répétition certaine.",
    }

    md_lines = [
        "# B9 Live Brief Once Runner V0",
        "",
        f"Brief state : `{brief_state}`",
        f"Candidate : `{candidate_id}`",
        f"Scene role : `{scene_role}`",
        f"Price verdict : `{verdict}`",
        f"Source quality : `{source_state}`",
        f"Memory family : `{family}`",
        f"Memory ladder : `{memory_ladder}`",
        f"Top B6 film : `{top_film_id or 'NONE'}`",
        "",
        "## Ce que B9 voit",
        sections["ce_que_b9_voit"],
        "",
        "## D'où vient le prix",
        sections["d_ou_vient_le_prix"],
        "",
        "## Zone active",
        sections["zone_active"],
        "",
        "## Effort / résultat / progrès",
        sections["effort_resultat_progres"],
        "",
        "## Retest qui juge",
        sections["retest_qui_juge"],
        "",
        "## Mémoire B6 proche",
        sections["memoire_b6"],
        "",
        "## Pièges techniques",
        sections["pieges_techniques"],
        "",
        "## Synthèse terrain",
        sections["terrain"],
        "",
        "## Ce que B9 ne peut pas conclure",
        sections["ce_que_b9_ne_peut_pas_conclure"],
    ]
    if technical_blockers:
        md_lines += ["", "## Blockers techniques", *[f"- {b}" for b in technical_blockers]]
    if report_text:
        md_lines += ["", "## Rapport FR source", report_text[:2500]]

    markdown = "\n".join(md_lines).strip() + "\n"
    hits = forbidden_hits(markdown)

    brief = {
        "version": VERSION,
        "brief_state": brief_state,
        "input_availability": available,
        "missing_inputs": missing,
        "candidate_id": candidate_id,
        "scene_role": scene_role,
        "price_verdict": verdict,
        "source_quality_state": source_state,
        "memory_family": family,
        "memory_ladder_state": memory_ladder,
        "match_count": len(matches),
        "top_match_film_id": top_film_id,
        "cross_family_match_count": int(_safe_float(cross_family, 0.0)),
        "low_trust_in_results": low_trust,
        "raw_unavailable_in_results": raw_unavailable,
        "false_positive_context_available": bool(fp_rows),
        "false_positive_state": false_positive_state,
        "terrain_synthesis_available": bool(terrain_ctx),
        "technical_blockers": technical_blockers,
        "forbidden_language_hits": hits,
        "sections": sections,
        "matches": matches,
    }
    if hits and brief_state == "B9_LIVE_BRIEF_READY":
        brief["brief_state"] = "BLOCKED_FORBIDDEN_LANGUAGE"

    md_path = out_dir / "B9_LIVE_BRIEF_ONCE_V0.md"
    json_path = out_dir / "B9_LIVE_BRIEF_ONCE_V0.json"
    csv_path = out_dir / "B9_LIVE_BRIEF_ONCE_MATCHES_V0.csv"
    manifest_path = out_dir / "B9_LIVE_BRIEF_ONCE_MANIFEST.json"
    zip_path = out_dir / "B9_LIVE_BRIEF_ONCE_V0.zip"

    md_path.write_text(markdown, encoding="utf-8")
    _write_json(json_path, brief)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "film_id", "memory_family", "similarity_score", "source_quality_state", "false_positive_state"])
        writer.writeheader()
        for idx, match in enumerate(matches, start=1):
            film_id = _first_text(match.get("film_id"), match.get("match_film_id"), match.get("memory_film_id"))
            fp_row = _match_fp_for_film(fp_rows, film_id)
            writer.writerow({
                "rank": idx,
                "film_id": film_id,
                "memory_family": _first_text(match.get("memory_family"), match.get("b6_memory_family")),
                "similarity_score": _first_text(match.get("similarity_score"), match.get("score")),
                "source_quality_state": _first_text(match.get("source_quality_state"), match.get("b9_source_quality_gate_state")),
                "false_positive_state": _first_text(fp_row.get("b9_memory_false_positive_state"), fp_row.get("state")),
            })

    manifest = {
        "version": VERSION,
        "brief_state": brief["brief_state"],
        "outputs": [md_path.name, json_path.name, csv_path.name, manifest_path.name, zip_path.name],
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
    }
    _write_json(manifest_path, manifest)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in [md_path, json_path, csv_path, manifest_path]:
            zf.write(p, p.name)

    brief["zip"] = str(zip_path)
    _write_json(json_path, brief)
    return brief
