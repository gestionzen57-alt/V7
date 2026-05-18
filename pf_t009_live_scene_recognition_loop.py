"""T0135 - B9 Live Scene Recognition Loop V0.

Read-only B9/B6 orchestration loop.
It assembles a B9 live scene, B6 similarity matches, false-positive context,
terrain synthesis, and French trader report into a single recognition packet.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

VERSION = "T0135_B9_LIVE_SCENE_RECOGNITION_LOOP_V0"
FORBIDDEN_PATTERNS = [r"\bBUY\b", r"\bSELL\b", r"\bACHETER\b", r"\bVENDRE\b", r"probabilit[eé]\s+de\s+succ[eè]s", r"success\s+probability", r"taux\s+de\s+r[eé]ussite"]
REQUIRED_LIVE_FIELDS = ["film_id", "memory_family", "memory_family_origin", "source_family", "source_mode", "data_visibility", "proxy_vs_raw_verdict"]
OUTPUT_NAMES = {
    "json": "B9_LIVE_SCENE_RECOGNITION_LOOP_V0.json",
    "md": "B9_LIVE_SCENE_RECOGNITION_LOOP_V0.md",
    "matches_csv": "B9_LIVE_SCENE_RECOGNITION_MATCHES_V0.csv",
    "flags_csv": "B9_LIVE_SCENE_RECOGNITION_FLAGS_V0.csv",
    "manifest": "B9_LIVE_SCENE_RECOGNITION_LOOP_MANIFEST.json",
    "zip": "B9_LIVE_SCENE_RECOGNITION_LOOP_V0.zip",
}


def _load(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _hash(payload: Any, n: int = 12) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha1(blob).hexdigest().upper()[:n]


def _pick(d: Mapping[str, Any], keys: Sequence[str], default: Any = "") -> Any:
    for k in keys:
        if d.get(k) not in (None, ""):
            return d[k]
    return default


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def forbidden_hits(payload: Any) -> List[Dict[str, str]]:
    text = json.dumps(payload, ensure_ascii=False, default=str)
    hits: List[Dict[str, str]] = []
    for pattern in FORBIDDEN_PATTERNS:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            hits.append({"pattern": pattern, "excerpt": text[max(0, m.start()-40):m.end()+40]})
    return hits


def normalize_live_scene(raw: Mapping[str, Any]) -> Dict[str, Any]:
    scene = dict(raw.get("live_scene", raw)) if isinstance(raw.get("live_scene", raw), dict) else {}
    if not scene.get("film_id"):
        scene["film_id"] = "LIVE_SCENE_" + _hash(scene, 10)
    scene.setdefault("memory_family", _pick(scene, ["b9_memory_family", "family"], "UNKNOWN_MEMORY_FAMILY"))
    scene.setdefault("memory_family_origin", "provided" if scene.get("memory_family") != "UNKNOWN_MEMORY_FAMILY" else "unknown")
    scene.setdefault("source_family", _pick(scene, ["summary_recovery_type", "source"], "LIVE_B9_SCENE"))
    scene.setdefault("source_mode", "LIVE_SCENE_INPUT")
    scene.setdefault("data_visibility", "LIVE_INPUT")
    scene.setdefault("proxy_vs_raw_verdict", _pick(scene, ["raw_agreement", "proxy_raw_agreement_state"], "RAW_CONTEXT_NOT_PROVIDED"))
    scene.setdefault("session", _pick(scene, ["b9_session"], "SESSION_UNKNOWN"))
    scene.setdefault("session_phase", _pick(scene, ["b9_session_phase"], "SESSION_PHASE_UNKNOWN"))
    scene.setdefault("retest_result", _pick(scene, ["b9_native_retest_judgment"], "RETEST_NOT_VISIBLE"))
    scene.setdefault("effort_result_progress_state", _pick(scene, ["b9_effort_result_progress_state"], "EFFORT_RESULT_PROGRESS_NOT_PROVIDED"))
    scene.setdefault("center_path_shape", _pick(scene, ["b9_center_path_shape"], "CENTER_PATH_NOT_PROVIDED"))
    scene.setdefault("source_quality_gate_state", _pick(scene, ["b9_source_quality_gate_state"], "SOURCE_QUALITY_NOT_PROVIDED"))
    return scene


def extract_matches(payload: Mapping[str, Any], top_k: int) -> List[Dict[str, Any]]:
    src: List[Any] = []
    for key in ("similar_films", "matches", "ranked_matches", "results"):
        if isinstance(payload.get(key), list):
            src = payload[key]
            break
    out: List[Dict[str, Any]] = []
    for i, item in enumerate(src[:top_k], 1):
        m = dict(item) if isinstance(item, dict) else {"raw_match": item}
        m.setdefault("rank", i)
        m.setdefault("film_id", _pick(m, ["historical_film_id", "match_film_id", "id"], f"MATCH_{i}"))
        m.setdefault("film_date", _pick(m, ["date", "historical_date"], "DATE_UNKNOWN"))
        m.setdefault("memory_family", _pick(m, ["family"], "UNKNOWN_MEMORY_FAMILY"))
        m.setdefault("similarity_score", _pick(m, ["score"], 0.0))
        m.setdefault("difference_summary_fr", _pick(m, ["differences_fr", "difference_summary", "technical_differences_fr"], "Différences non détaillées."))
        out.append(m)
    return out


def extract_flags(payload: Mapping[str, Any], top_k: int) -> List[Dict[str, Any]]:
    src: List[Any] = []
    for key in ("false_positive_context", "matches", "flags", "rows", "contexts"):
        if isinstance(payload.get(key), list):
            src = payload[key]
            break
    out: List[Dict[str, Any]] = []
    for i, item in enumerate(src[:top_k], 1):
        f = dict(item) if isinstance(item, dict) else {"raw_flag": item}
        f.setdefault("rank", i)
        f.setdefault("film_id", _pick(f, ["match_film_id", "historical_film_id"], f"MATCH_{i}"))
        f.setdefault("false_positive_state", _pick(f, ["state", "context_state"], "FALSE_POSITIVE_CONTEXT_NOT_PROVIDED"))
        f.setdefault("difference_explanation_fr", _pick(f, ["explanation_fr", "reason_fr"], "Différences non détaillées."))
        f.setdefault("technical_cautions_fr", _pick(f, ["cautions_fr", "technical_cautions_fr"], []))
        out.append(f)
    return out


def build_live_scene_recognition_loop(live_scene: Mapping[str, Any], similarity: Mapping[str, Any], false_positive: Mapping[str, Any], terrain: Mapping[str, Any], french_report: Optional[Mapping[str, Any]] = None, top_k: int = 5) -> Dict[str, Any]:
    scene = normalize_live_scene(live_scene)
    matches = extract_matches(similarity, top_k)
    flags = extract_flags(false_positive, top_k)
    family = str(scene.get("memory_family", "UNKNOWN_MEMORY_FAMILY"))
    cross_family = [m for m in matches if str(m.get("memory_family", "")) not in ("", "UNKNOWN_MEMORY_FAMILY", family)]
    low_trust = [m for m in matches if "LOW_TRUST" in json.dumps(m, ensure_ascii=False).upper()]
    raw_unavailable = [m for m in matches if "RAW_UNAVAILABLE" in json.dumps(m, ensure_ascii=False).upper()]
    missing = [f for f in REQUIRED_LIVE_FIELDS if not scene.get(f)]
    top = matches[0] if matches else {}
    terrain_available = bool(terrain)
    false_available = bool(flags)
    french_report = dict(french_report or {})
    state = "B9_LIVE_SCENE_RECOGNITION_READY"
    if missing:
        state = "B9_LIVE_SCENE_RECOGNITION_PARTIAL_INPUT"
    if cross_family or low_trust or raw_unavailable:
        state = "B9_LIVE_SCENE_RECOGNITION_REVIEW_REQUIRED"
    packet = {
        "version": VERSION,
        "loop_id": "B9LIVE_" + _hash({"scene": scene, "matches": matches}, 12),
        "recognition_state": state,
        "live_scene": scene,
        "memory_recognition": {
            "query_memory_family": family,
            "match_count": len(matches),
            "top_match_film_id": top.get("film_id", "NO_MATCH"),
            "top_match_date": top.get("film_date", "DATE_UNKNOWN"),
            "top_similarity_score": top.get("similarity_score", 0.0),
            "similar_films": matches,
        },
        "false_positive_context": {"available": false_available, "flags": flags},
        "terrain_synthesis": {
            "available": terrain_available,
            "family_counts": terrain.get("family_counts", terrain.get("memory_family_counts", {})),
            "terrain_reading_fr": terrain.get("terrain_reading_fr", terrain.get("summary_fr", "Synthèse terrain non fournie.")),
            "technical_limits": terrain.get("technical_limits", []),
        },
        "french_trader_report": {
            "available": bool(french_report),
            "reading_fr": french_report.get("reading_fr", french_report.get("report_fr", "Rapport FR trader non fourni.")),
        },
        "loop_checks": {
            "missing_live_scene_fields": missing,
            "cross_family_match_count": len(cross_family),
            "low_trust_in_results": bool(low_trust),
            "raw_unavailable_in_results": bool(raw_unavailable),
            "false_positive_context_available": false_available,
            "terrain_synthesis_available": terrain_available,
        },
        "technical_limits": [
            "Boucle read-only.",
            "La similarité est une proximité de mémoire, pas une répétition certaine.",
            "Une scène proxy reste proxy.",
            "Aucune base, surface ou transmission n'est modifiée.",
        ],
        "powerflow_contract": {"read_only": True, "db_write": False, "dashboard": False, "telegram": False, "execution_order": False, "success_rate": False},
    }
    hits = forbidden_hits(packet)
    packet["loop_checks"]["forbidden_language_hits"] = hits
    if hits:
        packet["recognition_state"] = "B9_LIVE_SCENE_RECOGNITION_FORBIDDEN_LANGUAGE_REVIEW"
    return packet


def render_markdown(packet: Mapping[str, Any]) -> str:
    scene = packet["live_scene"]
    mem = packet["memory_recognition"]
    checks = packet["loop_checks"]
    lines = [
        "# B9 Live Scene Recognition Loop V0", "",
        "## Résumé exécutif",
        f"État : `{packet['recognition_state']}`.",
        "B9 lit la scène. B6 compare les films. La boucle expose les pièges techniques sans décision d’exécution.", "",
        "## Scène live B9",
        f"- Scène : `{scene.get('film_id')}`",
        f"- Famille mémoire : `{scene.get('memory_family')}` (`{scene.get('memory_family_origin')}`)",
        f"- Session : `{scene.get('session')}` / `{scene.get('session_phase')}`",
        f"- Source : `{scene.get('source_family')}` / `{scene.get('source_mode')}` / `{scene.get('data_visibility')}`",
        f"- Accord raw : `{scene.get('proxy_vs_raw_verdict')}`",
        f"- Retest : `{scene.get('retest_result')}`",
        f"- Effort/résultat/progrès : `{scene.get('effort_result_progress_state')}`",
        f"- Chemin centre : `{scene.get('center_path_shape')}`", "",
        "## Films B6 proches",
        f"- Nombre : `{mem.get('match_count')}`",
        f"- Film le plus proche : `{mem.get('top_match_film_id')}`",
        f"- Score de similarité lecture : `{mem.get('top_similarity_score')}`", "",
        "## Pièges techniques",
    ]
    flags = packet.get("false_positive_context", {}).get("flags", [])
    if flags:
        for flag in flags[:5]:
            cautions = flag.get("technical_cautions_fr", [])
            cautions_text = "; ".join(cautions) if isinstance(cautions, list) else str(cautions)
            lines.append(f"- `{flag.get('film_id')}` : `{flag.get('false_positive_state')}` — {flag.get('difference_explanation_fr')} {cautions_text}")
    else:
        lines.append("- Aucun contexte T0117 fourni.")
    lines += ["", "## Synthèse terrain", str(packet.get("terrain_synthesis", {}).get("terrain_reading_fr", "Non fournie.")), "", "## Rapport FR trader", str(packet.get("french_trader_report", {}).get("reading_fr", "Non fourni.")), "", "## Contrôles", f"- Cross-family matches : `{checks.get('cross_family_match_count')}`", f"- Low trust : `{checks.get('low_trust_in_results')}`", f"- Raw unavailable : `{checks.get('raw_unavailable_in_results')}`", f"- Forbidden language hits : `{len(checks.get('forbidden_language_hits', []))}`", "", "## Ce que B9 ne peut pas conclure", "- La similarité ne garantit aucune répétition.", "- Une source proxy reste limitée.", "- Un retest non visible reste non visible.", "- La boucle ne transmet aucun ordre d’exécution."]
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run(live_scene_json: Path, output_dir: Path, similarity_query_json: Optional[Path] = None, false_positive_json: Optional[Path] = None, terrain_synthesis_json: Optional[Path] = None, french_report_json: Optional[Path] = None, top_k: int = 5) -> Dict[str, Any]:
    packet = build_live_scene_recognition_loop(_load(live_scene_json), _load(similarity_query_json), _load(false_positive_json), _load(terrain_synthesis_json), _load(french_report_json), top_k)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / OUTPUT_NAMES["json"]
    md_path = output_dir / OUTPUT_NAMES["md"]
    matches_csv = output_dir / OUTPUT_NAMES["matches_csv"]
    flags_csv = output_dir / OUTPUT_NAMES["flags_csv"]
    manifest_path = output_dir / OUTPUT_NAMES["manifest"]
    zip_path = output_dir / OUTPUT_NAMES["zip"]
    _write_json(json_path, packet)
    md_path.write_text(render_markdown(packet), encoding="utf-8")
    _write_csv(matches_csv, packet["memory_recognition"]["similar_films"], ["rank", "film_id", "film_date", "memory_family", "similarity_score", "difference_summary_fr"])
    _write_csv(flags_csv, packet["false_positive_context"]["flags"], ["rank", "film_id", "false_positive_state", "difference_explanation_fr", "technical_cautions_fr"])
    manifest = {
        "version": VERSION,
        "loop_id": packet["loop_id"],
        "recognition_state": packet["recognition_state"],
        "match_count": packet["memory_recognition"]["match_count"],
        "top_match_film_id": packet["memory_recognition"]["top_match_film_id"],
        "cross_family_match_count": packet["loop_checks"]["cross_family_match_count"],
        "low_trust_in_results": packet["loop_checks"]["low_trust_in_results"],
        "raw_unavailable_in_results": packet["loop_checks"]["raw_unavailable_in_results"],
        "false_positive_context_available": packet["loop_checks"]["false_positive_context_available"],
        "terrain_synthesis_available": packet["loop_checks"]["terrain_synthesis_available"],
        "forbidden_language_hits": packet["loop_checks"]["forbidden_language_hits"],
        "read_only": True, "db_write": False, "dashboard": False, "telegram": False, "execution_order": False, "success_rate": False,
        "outputs": [OUTPUT_NAMES[k] for k in ("json", "md", "matches_csv", "flags_csv", "manifest", "zip")],
    }
    _write_json(manifest_path, manifest)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in [json_path, md_path, matches_csv, flags_csv, manifest_path]:
            z.write(path, path.name)
    return manifest
