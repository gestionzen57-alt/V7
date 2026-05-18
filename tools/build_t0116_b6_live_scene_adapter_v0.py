#!/usr/bin/env python3
"""
T0116 — B6 Live Scene Adapter V0

Read-only adapter that normalizes a current B9 scene / moment payload into a
T0115-compatible query JSON.

Doctrine:
- B9 reads the current scene.
- T0116 adapts that scene into a B6 query payload.
- T0115 compares against the B6 similarity index.
- B6 does not predict; B6 compares films.
- No BUY/SELL, no probability of success, no DB write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0116_B6_LIVE_SCENE_ADAPTER_V0"
POLICY = "ADAPT_LIVE_B9_SCENE_TO_T0115_QUERY_JSON_ONLY_V0"

DOCTRINE = [
    "B9 lit la scène.",
    "T0116 normalise la scène en payload de comparaison.",
    "B6 ne prédit pas.",
    "B6 compare des films.",
    "Aucun BUY/SELL, aucune probabilité de succès, aucune écriture DB.",
]

FAMILY_VALUES = {
    "DIRECTIONAL_PROGRESS_MEMORY",
    "FRICTION_ABSORPTION_MEMORY",
    "ROTATION_BREATH_MEMORY",
}

REJECTED_STATES = {"B6_LOW_TRUST_CANDIDATE", "B6_REJECT_RAW_UNAVAILABLE", "RAW_UNAVAILABLE"}

SESSION_RANGES = [
    (0, 6, "ASIAN_SESSION"),
    (6, 7, "ASIAN_LONDON_TRANSITION"),
    (7, 12, "LONDON_SESSION"),
    (12, 16, "LONDON_NY_OVERLAP"),
    (16, 21, "NY_AFTERNOON"),
    (21, 24, "LATE_SESSION"),
]

FIELD_ALIASES = {
    "time_start": ["time_start", "start_time", "start", "window_start", "raw_window_start_mt5", "timestamp"],
    "time_end": ["time_end", "end_time", "end", "window_end", "raw_window_end_mt5"],
    "moment_type": ["moment_type", "scene_type", "label", "tag", "event_type", "b9_moment_type"],
    "label_fr": ["label_fr", "reading_fr", "b9_natural_flow_reading_fr", "what_happens_fr", "description_fr"],
    "source_family": ["source_family", "source", "source_kind"],
    "summary_recovery_type": ["summary_recovery_type", "recovery_type"],
    "source_mode": ["source_mode", "raw_source_mode", "mode"],
    "data_visibility": ["data_visibility", "raw_data_visibility", "visibility"],
    "confidence_cap": ["confidence_cap", "raw_volume_confidence_cap"],
    "proxy_vs_raw_verdict": ["proxy_vs_raw_verdict", "raw_agreement", "proxy_raw_verdict"],
    "proxy_raw_agreement_state": ["proxy_raw_agreement_state", "proxy_raw_agreement", "agreement_state"],
    "source_quality_state": ["source_quality_state", "source_quality", "quality_state", "b9_microfilm_quality_state"],
    "source_quality_score": ["source_quality_score", "b9_microfilm_texture_score", "quality_score"],
    "raw_texture_role": ["raw_texture_role", "raw_role", "texture_role"],
    "raw_delta_pips": ["raw_delta_pips", "pip_delta", "delta_pips", "center_delta"],
    "raw_range_pips": ["raw_range_pips", "center_range", "range_pips", "price_range_pips"],
    "raw_tick_count": ["raw_tick_count", "raw_tick_count_dedup", "tick_count", "ticks"],
    "memory_family": ["memory_family", "b6_memory_family", "family"],
    "base": ["base", "base_motion", "base_fr"],
    "reaction": ["reaction", "reaction_profile", "reaction_fr"],
    "projection": ["projection", "projection_shape", "projection_fr"],
    "judgment": ["judgment", "judgment_clarity", "judgment_fr"],
    "limits": ["limits", "technical_limits", "b9_direct_factor_limits", "b9_natural_flow_limits"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any, length: int = 12) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length].upper()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def first_non_empty(payload: Dict[str, Any], aliases: Iterable[str], default: Any = None) -> Any:
    for key in aliases:
        if key in payload:
            value = payload.get(key)
            if value is not None:
                if isinstance(value, str) and not value.strip():
                    continue
                return value
    return default


def nested_candidates(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, dict):
        for key in ["query_scene", "scene", "current_scene", "moment", "payload", "film_card"]:
            value = obj.get(key)
            if isinstance(value, dict):
                return [value]
        for key in ["moments", "scenes", "items", "cards"]:
            value = obj.get(key)
            if isinstance(value, list):
                return [v for v in value if isinstance(v, dict)]
        return [obj]
    if isinstance(obj, list):
        return [v for v in obj if isinstance(v, dict)]
    return []


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "nan", "not_visible", "n/a"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_datetime_hour(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"T(\d{2}):", text)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d{2}):(\d{2})", text)
    if match:
        return int(match.group(1))
    return None


def derive_date(time_start: Any) -> str:
    if not time_start:
        return "UNKNOWN_DATE"
    text = str(time_start)
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return match.group(0) if match else "UNKNOWN_DATE"


def infer_session(time_start: Any) -> str:
    hour = parse_datetime_hour(time_start)
    if hour is None:
        return "SESSION_NOT_VISIBLE"
    for start, end, label in SESSION_RANGES:
        if start <= hour < end:
            return label
    return "SESSION_NOT_VISIBLE"


def normalize_limits(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(x) for x in value if x is not None)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def source_family_from(payload: Dict[str, Any], summary_recovery_type: str) -> str:
    explicit = first_non_empty(payload, FIELD_ALIASES["source_family"])
    if explicit:
        return str(explicit)
    upper = str(summary_recovery_type).upper()
    if "FORCE_SNAPSHOT_DERIVED" in upper:
        return "FORCE_SNAPSHOT_DERIVED"
    if "RECOVERED" in upper:
        return "RECOVERED_EXISTING_B9_SUMMARY"
    if "ORIGINAL" in upper:
        return "ORIGINAL_AVAILABLE_SUMMARY"
    return "B9_LIVE_SCENE_ADAPTED"


def normalize_family(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip().upper()
    if text in FAMILY_VALUES:
        return text
    aliases = {
        "DIRECTIONAL": "DIRECTIONAL_PROGRESS_MEMORY",
        "PROGRESS": "DIRECTIONAL_PROGRESS_MEMORY",
        "FRICTION": "FRICTION_ABSORPTION_MEMORY",
        "ABSORPTION": "FRICTION_ABSORPTION_MEMORY",
        "ROTATION": "ROTATION_BREATH_MEMORY",
        "BREATH": "ROTATION_BREATH_MEMORY",
    }
    return aliases.get(text)


def infer_memory_family(payload: Dict[str, Any]) -> Tuple[str, str]:
    explicit = normalize_family(first_non_empty(payload, FIELD_ALIASES["memory_family"]))
    if explicit:
        return explicit, "explicit_payload"

    text_blob = " ".join(
        str(first_non_empty(payload, FIELD_ALIASES.get(k, [k]), ""))
        for k in ["moment_type", "label_fr", "raw_texture_role", "base", "reaction", "projection", "judgment"]
    ).upper()
    raw_delta = as_float(first_non_empty(payload, FIELD_ALIASES["raw_delta_pips"]))
    raw_range = as_float(first_non_empty(payload, FIELD_ALIASES["raw_range_pips"]))
    ratio = None
    if raw_delta is not None and raw_range not in (None, 0):
        ratio = abs(raw_delta) / max(abs(raw_range), 0.0001)

    if any(token in text_blob for token in ["ABSORPTION", "FRICTION", "EFFORT_WITHOUT_RESULT", "BRAKE", "FAILED_DISPLACEMENT"]):
        return "FRICTION_ABSORPTION_MEMORY", "heuristic_text_friction_absorption"
    if any(token in text_blob for token in ["BREATH", "RESPIRATION", "ROTATION", "MIXED", "COUNTER"]):
        return "ROTATION_BREATH_MEMORY", "heuristic_text_rotation_breath"
    if any(token in text_blob for token in ["PROGRESS", "MIGRATION", "RELEASE", "BREAK", "WAVE", "FLOW", "RAW_PROGRESS"]):
        return "DIRECTIONAL_PROGRESS_MEMORY", "heuristic_text_directional_progress"
    if ratio is not None:
        if ratio >= 0.45:
            return "DIRECTIONAL_PROGRESS_MEMORY", "heuristic_raw_delta_range_ratio"
        if ratio <= 0.20 and raw_range and raw_range >= 2.0:
            return "FRICTION_ABSORPTION_MEMORY", "heuristic_raw_effort_without_directional_result"
    return "DIRECTIONAL_PROGRESS_MEMORY", "default_directional_progress_low_visibility"


def default_label(moment_type: str) -> str:
    mt = str(moment_type or "").upper()
    if "ABSORPTION" in mt or "FRICTION" in mt:
        return "Friction / absorption live"
    if "PROGRESS" in mt or "WAVE" in mt:
        return "Vague progressive live"
    if "BREATH" in mt or "ROTATION" in mt:
        return "Respiration / rotation live"
    if mt:
        return f"Scène live {mt}"
    return "Scène live B9 adaptée"


def build_reading_fields(payload: Dict[str, Any], normalized: Dict[str, Any]) -> None:
    moment_type = normalized.get("moment_type") or "B9_LIVE_SCENE"
    label_fr = normalized.get("label_fr") or default_label(moment_type)
    raw_delta = normalized.get("raw_delta_pips")
    raw_range = normalized.get("raw_range_pips")
    raw_ticks = normalized.get("raw_tick_count")
    raw_role = normalized.get("raw_texture_role") or "RAW_TEXTURE_NOT_PROVIDED"
    verdict = normalized.get("proxy_vs_raw_verdict") or normalized.get("raw_agreement") or "RAW_AGREEMENT_NOT_VISIBLE"
    quality = normalized.get("source_quality_state") or "SOURCE_QUALITY_LIVE_UNQUALIFIED"
    candidate_state = normalized.get("b6_memory_candidate_state") or "B6_LIVE_QUERY_ONLY_NOT_CANDIDATE"

    if not normalized.get("base"):
        normalized["base"] = f"Base scene: {label_fr} ({moment_type})."
    if not normalized.get("reaction"):
        normalized["reaction"] = (
            f"Reaction live: raw role {raw_role}, delta {raw_delta}, range {raw_range}, ticks {raw_ticks}."
        )
    if not normalized.get("projection"):
        family = normalized.get("memory_family")
        if family == "FRICTION_ABSORPTION_MEMORY":
            projection = "Projection de lecture: effort/friction à comparer aux films d'absorption, sans direction conclue."
        elif family == "ROTATION_BREATH_MEMORY":
            projection = "Projection de lecture: respiration/rotation à comparer aux films de breath, sans décision."
        else:
            projection = "Projection de lecture: progression/migration à comparer aux films directionnels, sans prédiction."
        normalized["projection"] = projection
    if not normalized.get("judgment"):
        normalized["judgment"] = f"Judgment technique: {candidate_state}, {verdict}, {quality}."


def adapt_scene(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for field, aliases in FIELD_ALIASES.items():
        value = first_non_empty(payload, aliases)
        if value is not None:
            normalized[field] = normalize_limits(value) if field == "limits" else value

    time_start = normalized.get("time_start") or utc_now()
    normalized["time_start"] = time_start
    normalized.setdefault("time_end", normalized.get("time_start"))
    normalized.setdefault("date", derive_date(normalized.get("time_start")))
    normalized.setdefault("session", infer_session(normalized.get("time_start")))

    normalized.setdefault("summary_recovery_type", "LIVE_B9_SCENE_ADAPTED")
    normalized["source_family"] = source_family_from(payload, str(normalized.get("summary_recovery_type", "")))
    normalized.setdefault("source_mode", "B9_LIVE_SCENE_ADAPTER")
    normalized.setdefault("data_visibility", "LIVE_SCENE_ADAPTED_FROM_PAYLOAD")
    normalized.setdefault("confidence_cap", "LIVE_NOT_CAPPED_BY_T0116")
    normalized.setdefault("moment_type", "B9_LIVE_SCENE")
    normalized.setdefault("label_fr", default_label(str(normalized.get("moment_type"))))

    family, family_origin = infer_memory_family({**payload, **normalized})
    normalized["memory_family"] = family
    normalized["memory_family_origin"] = family_origin

    normalized.setdefault("proxy_vs_raw_verdict", normalized.get("raw_agreement") or "RAW_AGREEMENT_NOT_VISIBLE")
    normalized.setdefault("raw_agreement", normalized.get("proxy_vs_raw_verdict"))
    normalized.setdefault("proxy_raw_agreement_state", "PROXY_RAW_AGREEMENT_NOT_EVALUATED_BY_T0116")
    normalized.setdefault("source_quality_state", "SOURCE_QUALITY_LIVE_UNQUALIFIED")
    normalized.setdefault("b6_memory_candidate_state", "B6_LIVE_QUERY_ONLY_NOT_CANDIDATE")
    normalized.setdefault("raw_texture_role", "RAW_TEXTURE_NOT_PROVIDED")

    for numeric_field in ["source_quality_score", "raw_delta_pips", "raw_range_pips", "raw_tick_count"]:
        if numeric_field in normalized and normalized[numeric_field] is not None:
            # Keep JSON-friendly original numeric values when possible.
            f = as_float(normalized[numeric_field])
            if f is not None:
                if numeric_field == "raw_tick_count":
                    normalized[numeric_field] = int(round(f))
                else:
                    normalized[numeric_field] = round(f, 6)

    build_reading_fields(payload, normalized)

    existing_limits = normalize_limits(normalized.get("limits"))
    adapter_limits = [
        "T0116 adapter normalization only",
        "source payload is not rewritten",
        "memory_family may be heuristic if not explicit",
        "payload is for T0115 comparison only",
        "no DB write",
        "no dashboard",
        "no Telegram",
        "no BUY/SELL",
        "no probability of success",
    ]
    normalized["limits"] = "; ".join([x for x in [existing_limits, *adapter_limits] if x])

    normalized["film_id"] = normalized.get("film_id") or f"LIVE_SCENE_{stable_hash(normalized, 10)}"
    return normalized


def adapter_quality(payload: Dict[str, Any], query_scene: Dict[str, Any]) -> Dict[str, Any]:
    required_for_query = ["base", "reaction", "projection", "judgment", "memory_family"]
    missing = [field for field in required_for_query if not query_scene.get(field)]
    raw_present = any(query_scene.get(k) not in (None, "", "RAW_AGREEMENT_NOT_VISIBLE") for k in ["raw_delta_pips", "raw_range_pips", "raw_tick_count", "proxy_vs_raw_verdict"])
    family_origin = query_scene.get("memory_family_origin")
    state = "ADAPTER_READY"
    if missing:
        state = "ADAPTER_INCOMPLETE"
    elif not raw_present:
        state = "ADAPTER_READY_WITHOUT_RAW_TEXTURE"
    elif str(family_origin).startswith("heuristic") or str(family_origin).startswith("default"):
        state = "ADAPTER_READY_HEURISTIC_FAMILY"
    return {
        "adapter_state": state,
        "missing_query_fields": missing,
        "raw_texture_visible": raw_present,
        "memory_family_origin": family_origin,
        "t0115_compatible": not missing and query_scene.get("memory_family") in FAMILY_VALUES,
    }


def build_markdown(result: Dict[str, Any]) -> str:
    q = result["query_scene"]
    quality = result["adapter_quality"]
    lines = [
        "# T0116 — B6 Live Scene Adapter V0",
        "",
        "## Résumé exécutif",
        "",
        "T0116 convertit une scène B9 actuelle en payload JSON compatible T0115.",
        "Il ne compare pas lui-même les films. Il prépare la scène pour la couche de query B6.",
        "",
        "```text",
        "B9 lit la scène.",
        "T0116 adapte la scène.",
        "T0115 interroge l'index.",
        "B6 compare les films.",
        "```",
        "",
        "## Doctrine",
        "",
        "```text",
        "B6 ne prédit pas.",
        "B6 compare des films.",
        "Une query live est une reconnaissance de contexte, pas un signal.",
        "Aucun BUY/SELL. Aucune probabilité de succès. Aucune écriture DB.",
        "```",
        "",
        "## Payload adapté",
        "",
        f"- film_id: `{q.get('film_id')}`",
        f"- date: `{q.get('date')}`",
        f"- time_start: `{q.get('time_start')}`",
        f"- time_end: `{q.get('time_end')}`",
        f"- session: `{q.get('session')}`",
        f"- memory_family: `{q.get('memory_family')}`",
        f"- memory_family_origin: `{q.get('memory_family_origin')}`",
        f"- source_family: `{q.get('source_family')}`",
        f"- source_mode: `{q.get('source_mode')}`",
        f"- data_visibility: `{q.get('data_visibility')}`",
        f"- proxy_vs_raw_verdict: `{q.get('proxy_vs_raw_verdict')}`",
        f"- source_quality_state: `{q.get('source_quality_state')}`",
        "",
        "## Lecture 4D pour T0115",
        "",
        f"- base: {q.get('base')}",
        f"- reaction: {q.get('reaction')}",
        f"- projection: {q.get('projection')}",
        f"- judgment: {q.get('judgment')}",
        "",
        "## Qualité adaptateur",
        "",
        f"- adapter_state: `{quality.get('adapter_state')}`",
        f"- t0115_compatible: `{quality.get('t0115_compatible')}`",
        f"- raw_texture_visible: `{quality.get('raw_texture_visible')}`",
        f"- missing_query_fields: `{quality.get('missing_query_fields')}`",
        "",
        "## Limites techniques",
        "",
        "- Normalisation de payload uniquement.",
        "- Pas de lecture DB.",
        "- Pas d'écriture DB.",
        "- Pas de dashboard.",
        "- Pas de Telegram.",
        "- Pas de BUY/SELL.",
        "- Pas de probabilité de succès.",
        "- Si `memory_family` n'est pas explicite, elle est inférée et tracée dans `memory_family_origin`.",
    ]
    return "\n".join(lines) + "\n"


def build_manifest(result: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "policy": POLICY,
        "output_dir": str(output_dir),
        "files": [
            "B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json",
            "B6_LIVE_SCENE_ADAPTER_REPORT_V0.md",
            "B6_LIVE_SCENE_ADAPTER_MANIFEST_V0.json",
            "B6_LIVE_SCENE_ADAPTER_V0.zip",
        ],
        "query_scene": {
            "film_id": result.get("query_scene", {}).get("film_id"),
            "memory_family": result.get("query_scene", {}).get("memory_family"),
            "memory_family_origin": result.get("query_scene", {}).get("memory_family_origin"),
            "t0115_compatible": result.get("adapter_quality", {}).get("t0115_compatible"),
        },
        "integrity_checks": result.get("integrity_checks"),
        "next_step": "Run T0115 with --query-json B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json",
    }


def write_zip(zip_path: Path, files: List[Path], root: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            zf.write(file_path, file_path.relative_to(root))


def adapt_file(input_json: Path, output_dir: Path, scene_index: int = 0) -> Dict[str, Any]:
    obj = load_json(input_json)
    candidates = nested_candidates(obj)
    if not candidates:
        raise SystemExit(f"No scene-like object found in {input_json}")
    if scene_index < 0 or scene_index >= len(candidates):
        raise SystemExit(f"scene_index out of range: {scene_index}; available={len(candidates)}")
    source_scene = candidates[scene_index]
    query_scene = adapt_scene(source_scene)
    result = {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "policy": POLICY,
        "doctrine": DOCTRINE,
        "source_input": str(input_json),
        "source_scene_index": scene_index,
        "query_scene": query_scene,
        "adapter_quality": adapter_quality(source_scene, query_scene),
        "integrity_checks": {
            "read_only": True,
            "db_write": False,
            "dashboard": False,
            "telegram": False,
            "buy_sell_language": False,
            "probability_of_success": False,
            "low_trust_used_as_active_memory": False,
            "raw_unavailable_used_as_active_memory": False,
        },
        "technical_limits": [
            "T0116 does not query the DB.",
            "T0116 does not rebuild the similarity index.",
            "T0116 only emits a T0115-compatible query JSON.",
            "If memory_family is heuristic, use the origin field for audit.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    payload_path = output_dir / "B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json"
    report_path = output_dir / "B6_LIVE_SCENE_ADAPTER_REPORT_V0.md"
    manifest_path = output_dir / "B6_LIVE_SCENE_ADAPTER_MANIFEST_V0.json"
    zip_path = output_dir / "B6_LIVE_SCENE_ADAPTER_V0.zip"

    write_json(payload_path, result["query_scene"])
    write_text(report_path, build_markdown(result))
    manifest = build_manifest(result, output_dir)
    write_json(manifest_path, manifest)
    write_zip(zip_path, [payload_path, report_path, manifest_path], output_dir)

    print(json.dumps({
        "version": VERSION,
        "film_id": query_scene.get("film_id"),
        "memory_family": query_scene.get("memory_family"),
        "memory_family_origin": query_scene.get("memory_family_origin"),
        "adapter_state": result["adapter_quality"].get("adapter_state"),
        "t0115_compatible": result["adapter_quality"].get("t0115_compatible"),
        "output_dir": str(output_dir),
        "zip": str(zip_path),
    }, ensure_ascii=False, indent=2))
    return result


def self_test() -> None:
    sample = {
        "time_start": "2026-05-18T10:15:00+00:00",
        "time_end": "2026-05-18T10:23:00+00:00",
        "moment_type": "T009_MOMENT_PROGRESSIVE_WAVE",
        "label_fr": "Vague progressive live",
        "raw_texture_role": "RAW_PROGRESS_CONFIRMED",
        "raw_delta_pips": 8.4,
        "raw_range_pips": 10.1,
        "raw_tick_count": 420,
        "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
        "source_quality_state": "SOURCE_QUALITY_LIVE_UNQUALIFIED",
    }
    adapted = adapt_scene(sample)
    assert adapted["memory_family"] == "DIRECTIONAL_PROGRESS_MEMORY"
    assert adapted["memory_family_origin"].startswith("heuristic")
    assert adapted["base"]
    assert adapted["reaction"]
    assert adapted["projection"]
    assert adapted["judgment"]
    assert adapter_quality(sample, adapted)["t0115_compatible"] is True
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description="T0116 B6 Live Scene Adapter V0")
    parser.add_argument("--input-json", help="B9 live scene / moment JSON to adapt")
    parser.add_argument("--output-dir", default="outputs/b6_live_scene_adapter_v0", help="Output directory")
    parser.add_argument("--scene-index", type=int, default=0, help="Index when input JSON contains a list of scenes")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.input_json:
        raise SystemExit("--input-json is required unless --self-test is used")
    adapt_file(Path(args.input_json), Path(args.output_dir), scene_index=args.scene_index)


if __name__ == "__main__":
    main()
