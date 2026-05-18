"""T0167 - B9/B6 Auto Realignment Runner V0.

Read-only utility that aligns the current B9 live scene candidate with the B6
memory query context. It is intentionally conservative: if required inputs are
missing, it returns a BLOCKED_* state instead of fabricating memory matches.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import csv
import hashlib
import json
import zipfile

VERSION = "T0167_B9_B6_AUTO_REALIGNMENT_RUNNER_V0"

FORBIDDEN_TERMS = (
    "BUY",
    "SELL",
    "achat immédiat",
    "vente immédiate",
    "probabilité de réussite",
    "signal gagnant",
    "conseil financier",
)

RAW_UNAVAILABLE_MARKERS = {
    "RAW_UNAVAILABLE",
    "SOURCE_RAW_UNAVAILABLE_REJECTED",
    "MEMORY_REJECTED_RAW_UNAVAILABLE",
    "B6_REJECT_RAW_UNAVAILABLE",
}

LOW_TRUST_MARKERS = {
    "B6_LOW_TRUST_CANDIDATE",
    "LOW_TRUST",
    "SOURCE_QUALITY_WEAK_LIMITED",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _csv_cell(row.get(k, "")) for k in fieldnames})


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def as_list(payload: Any, keys: Sequence[str] = ()) -> List[Any]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for key in ("moments", "records", "rows", "items", "cards", "film_cards", "active_index", "similar_films", "matches"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def first_non_empty(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if not isinstance(value, str):
            return str(value)
    return default


def nested_get(obj: Mapping[str, Any], *paths: str, default: Any = "") -> Any:
    for path in paths:
        cur: Any = obj
        ok = True
        for part in path.split("."):
            if isinstance(cur, Mapping) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, "", [], {}):
            return cur
    return default


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(p) for p in parts if p is not None)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12].upper()}"


def scan_forbidden_user_text(texts: Iterable[str]) -> List[str]:
    hits: List[str] = []
    joined = "\n".join(t for t in texts if t)
    upper = joined.upper()
    for term in FORBIDDEN_TERMS:
        if term.upper() in upper:
            hits.append(term)
    return hits


def normalize_candidate(payload: Mapping[str, Any]) -> Dict[str, Any]:
    candidate = payload.get("latest_scene_candidate") if isinstance(payload.get("latest_scene_candidate"), Mapping) else payload
    if isinstance(candidate.get("scene"), Mapping):
        scene = candidate["scene"]
    else:
        scene = candidate
    candidate_id = first_non_empty(
        nested_get(scene, "candidate_id", "scene_id", "film_id", "id"),
        nested_get(candidate, "candidate_id", "scene_id", "film_id", "id"),
        default=stable_id("B9LSC", nested_get(scene, "time_start", "date"), nested_get(scene, "label_fr")),
    )
    time_start = first_non_empty(nested_get(scene, "time_start", "start", "time"), nested_get(candidate, "time_start", "start"))
    time_end = first_non_empty(nested_get(scene, "time_end", "end"), nested_get(candidate, "time_end", "end"))
    memory_family = first_non_empty(
        nested_get(scene, "memory_family", "b6_memory_family", "query_memory_family"),
        nested_get(candidate, "memory_family", "b6_memory_family"),
        default="MEMORY_FAMILY_UNKNOWN",
    )
    source_state = first_non_empty(
        nested_get(scene, "b9_source_quality_gate_state", "source_quality_gate_state", "source_quality_state"),
        nested_get(candidate, "source_quality_state"),
        default="SOURCE_QUALITY_UNKNOWN",
    )
    raw_texture_state = first_non_empty(
        nested_get(scene, "raw_texture_state", "b9_raw_texture_state"),
        nested_get(candidate, "raw_texture_state"),
        default="RAW_TEXTURE_UNKNOWN",
    )
    normalized = {
        "candidate_id": candidate_id,
        "date": first_non_empty(nested_get(scene, "date"), time_start[:10] if time_start else ""),
        "time_start": time_start,
        "time_end": time_end,
        "label_fr": first_non_empty(nested_get(scene, "label_fr", "label", "what_b9_sees_fr"), nested_get(candidate, "label_fr")),
        "scene_role": first_non_empty(nested_get(scene, "scene_role", "b9_scene_role"), nested_get(candidate, "scene_role")),
        "scene_state": first_non_empty(nested_get(scene, "scene_state", "b9_scene_state"), nested_get(candidate, "scene_state")),
        "scene_family": first_non_empty(nested_get(scene, "scene_family", "b9_b6_scene_family"), nested_get(candidate, "scene_family")),
        "memory_family": memory_family,
        "price_verdict": first_non_empty(nested_get(scene, "price_verdict", "b9_price_verdict_state"), nested_get(candidate, "price_verdict")),
        "session": first_non_empty(nested_get(scene, "session", "b9_session"), nested_get(candidate, "session")),
        "source_quality_state": source_state,
        "raw_texture_state": raw_texture_state,
        "data_visibility": first_non_empty(nested_get(scene, "data_visibility"), nested_get(candidate, "data_visibility")),
        "proxy_vs_raw_verdict": first_non_empty(nested_get(scene, "proxy_vs_raw_verdict"), nested_get(candidate, "proxy_vs_raw_verdict")),
        "technical_limits": as_text_list(nested_get(scene, "technical_limits", "b9_source_quality_limits", default=[])),
    }
    return normalized


def as_text_list(value: Any) -> List[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, dict):
        return [json.dumps(value, ensure_ascii=False, sort_keys=True)]
    return [str(value)]


def load_b6_memory_entries(index_payload: Any = None, film_cards_payload: Any = None) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for payload in (index_payload, film_cards_payload):
        for item in as_list(payload, keys=("active_index", "indexed_cards", "film_cards", "cards", "rows", "items")):
            if isinstance(item, Mapping):
                entry = normalize_b6_entry(item)
                if entry.get("film_id"):
                    entries.append(entry)
    seen: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for entry in entries:
        key = entry["film_id"]
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique


def normalize_b6_entry(item: Mapping[str, Any]) -> Dict[str, Any]:
    film_id = first_non_empty(nested_get(item, "film_id", "id", "card_id", "memory_id"))
    memory_family = first_non_empty(nested_get(item, "memory_family", "b6_memory_family", "query_memory_family"), default="MEMORY_FAMILY_UNKNOWN")
    source_quality = first_non_empty(nested_get(item, "source_quality_state", "b9_source_quality_gate_state"), default="SOURCE_QUALITY_UNKNOWN")
    raw_state = "RAW_UNAVAILABLE" if any(str(v).upper() in RAW_UNAVAILABLE_MARKERS for v in item.values() if isinstance(v, str)) else "RAW_VISIBLE_OR_PROXY"
    candidate_state = first_non_empty(nested_get(item, "b6_memory_candidate_state", "memory_candidate_state", "candidate_state"), default="B6_MEMORY_CANDIDATE_STATE_UNKNOWN")
    return {
        "film_id": film_id,
        "date": first_non_empty(nested_get(item, "date"), str(nested_get(item, "time_start", default=""))[:10]),
        "time_start": first_non_empty(nested_get(item, "time_start", "start", "time")),
        "time_end": first_non_empty(nested_get(item, "time_end", "end")),
        "label_fr": first_non_empty(nested_get(item, "label_fr", "film_title_fr", "moment_type")),
        "scene_role": first_non_empty(nested_get(item, "scene_role", "dominant_scene_role", "moment_type")),
        "scene_family": first_non_empty(nested_get(item, "scene_family", "b9_b6_scene_family")),
        "memory_family": memory_family,
        "price_verdict": first_non_empty(nested_get(item, "price_verdict", "b9_price_verdict_state")),
        "session": first_non_empty(nested_get(item, "session", "b9_session")),
        "source_quality_state": source_quality,
        "candidate_state": candidate_state,
        "raw_state": raw_state,
        "technical_limits": as_text_list(nested_get(item, "technical_limits", "limits", default=[])),
    }


def is_rejected_entry(entry: Mapping[str, Any]) -> bool:
    joined = " ".join(str(v).upper() for v in entry.values() if isinstance(v, str))
    return any(marker in joined for marker in RAW_UNAVAILABLE_MARKERS)


def is_low_trust_entry(entry: Mapping[str, Any]) -> bool:
    joined = " ".join(str(v).upper() for v in entry.values() if isinstance(v, str))
    return any(marker in joined for marker in LOW_TRUST_MARKERS)


def score_match(candidate: Mapping[str, Any], entry: Mapping[str, Any]) -> Tuple[int, List[str], List[str]]:
    score = 0
    similarities: List[str] = []
    differences: List[str] = []
    if candidate.get("memory_family") and candidate.get("memory_family") == entry.get("memory_family"):
        score += 45
        similarities.append("Même famille mémoire B6.")
    else:
        differences.append("Famille mémoire différente ou inconnue.")
    if candidate.get("scene_family") and candidate.get("scene_family") == entry.get("scene_family"):
        score += 18
        similarities.append("Même famille de scène.")
    elif candidate.get("scene_family") and entry.get("scene_family"):
        differences.append("Famille de scène différente.")
    if candidate.get("scene_role") and candidate.get("scene_role") == entry.get("scene_role"):
        score += 12
        similarities.append("Rôle de scène proche.")
    elif candidate.get("scene_role") and entry.get("scene_role"):
        differences.append("Rôle de scène différent.")
    if candidate.get("price_verdict") and candidate.get("price_verdict") == entry.get("price_verdict"):
        score += 10
        similarities.append("Verdict prix comparable.")
    elif candidate.get("price_verdict") and entry.get("price_verdict"):
        differences.append("Verdict prix différent.")
    if candidate.get("session") and candidate.get("session") == entry.get("session"):
        score += 8
        similarities.append("Session comparable.")
    elif candidate.get("session") and entry.get("session"):
        differences.append("Session différente.")
    if entry.get("source_quality_state") in ("SOURCE_RAW_CONFIRMED", "SOURCE_QUALITY_STRONG", "FULL_RAW"):
        score += 7
        similarities.append("Source mémoire lisible.")
    if is_low_trust_entry(entry):
        score -= 20
        differences.append("Mémoire low-trust, comparaison limitée.")
    return max(0, min(100, score)), similarities, differences


def build_matches(candidate: Mapping[str, Any], entries: Sequence[Mapping[str, Any]], top_k: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    matches: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for entry in entries:
        if is_rejected_entry(entry):
            rejected.append({
                "film_id": entry.get("film_id", ""),
                "reason": "RAW_UNAVAILABLE_OR_REJECTED_MEMORY",
                "memory_family": entry.get("memory_family", ""),
            })
            continue
        score, similarities, differences = score_match(candidate, entry)
        if score <= 0:
            continue
        state = "ALIGNED_MEMORY_MATCH"
        if score < 55:
            state = "ALIGNED_MEMORY_REVIEW"
        matches.append({
            "film_id": entry.get("film_id", ""),
            "date": entry.get("date", ""),
            "time_start": entry.get("time_start", ""),
            "time_end": entry.get("time_end", ""),
            "label_fr": entry.get("label_fr", ""),
            "memory_family": entry.get("memory_family", ""),
            "scene_family": entry.get("scene_family", ""),
            "scene_role": entry.get("scene_role", ""),
            "price_verdict": entry.get("price_verdict", ""),
            "session": entry.get("session", ""),
            "source_quality_state": entry.get("source_quality_state", ""),
            "alignment_score": score,
            "alignment_state": state,
            "similarities_fr": similarities,
            "differences_fr": differences,
            "technical_limits": entry.get("technical_limits", []),
        })
    matches.sort(key=lambda r: (int(r.get("alignment_score", 0)), r.get("film_id", "")), reverse=True)
    return matches[:top_k], rejected


def build_query_payload(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "query_id": stable_id("B6Q_REALIGN", candidate.get("candidate_id"), candidate.get("memory_family"), candidate.get("time_start")),
        "source_candidate_id": candidate.get("candidate_id", ""),
        "query_scene": {
            "candidate_id": candidate.get("candidate_id", ""),
            "date": candidate.get("date", ""),
            "time_start": candidate.get("time_start", ""),
            "time_end": candidate.get("time_end", ""),
            "label_fr": candidate.get("label_fr", ""),
            "scene_role": candidate.get("scene_role", ""),
            "scene_state": candidate.get("scene_state", ""),
            "scene_family": candidate.get("scene_family", ""),
            "memory_family": candidate.get("memory_family", ""),
            "price_verdict": candidate.get("price_verdict", ""),
            "session": candidate.get("session", ""),
            "source_quality_state": candidate.get("source_quality_state", ""),
            "raw_texture_state": candidate.get("raw_texture_state", ""),
        },
        "alignment_contract": {
            "requires_same_candidate_id": True,
            "requires_same_memory_family_first": True,
            "false_positive_high_is_context_not_absence": True,
            "raw_unavailable_rejected_from_active_memory": True,
        },
    }


def compute_risks(candidate: Mapping[str, Any], match_count: int, rejected_count: int, b6_entries_count: int) -> List[Dict[str, str]]:
    risks: List[Dict[str, str]] = []
    if candidate.get("source_quality_state") in ("SOURCE_LIVE_UNQUALIFIED", "SOURCE_QUALITY_UNKNOWN", ""):
        risks.append({"risk_code": "SOURCE_LIVE_UNQUALIFIED", "risk_fr": "Source live candidate encore non qualifiée."})
    if candidate.get("raw_texture_state") in ("RAW_TEXTURE_MISSING", "RAW_TEXTURE_UNKNOWN", ""):
        risks.append({"risk_code": "RAW_TEXTURE_MISSING", "risk_fr": "Texture raw absente ou non visible pour la scène live."})
    if b6_entries_count <= 0:
        risks.append({"risk_code": "B6_MEMORY_SOURCE_MISSING", "risk_fr": "Aucune source mémoire B6 exploitable fournie au realignment."})
    if match_count <= 0 and b6_entries_count > 0:
        risks.append({"risk_code": "NO_ALIGNED_MEMORY_MATCH", "risk_fr": "Aucun film B6 aligné avec la scène courante."})
    if rejected_count > 0:
        risks.append({"risk_code": "RAW_UNAVAILABLE_MEMORY_REJECTED", "risk_fr": "Des films mémoire raw-unavailable ont été rejetés de la comparaison active."})
    if not risks:
        risks.append({"risk_code": "NO_BLOCKING_ALIGNMENT_RISK", "risk_fr": "Aucun blocage technique majeur détecté dans l’alignement B9/B6."})
    return risks


def build_markdown(summary: Mapping[str, Any]) -> str:
    candidate = summary.get("candidate", {})
    top = summary.get("top_match", {}) or {}
    lines = [
        "# T0167 — B9/B6 Auto Realignment Runner V0",
        "",
        "## Résumé",
        f"- État : `{summary.get('alignment_state', '')}`",
        f"- Candidat B9 : `{candidate.get('candidate_id', '')}`",
        f"- Famille mémoire : `{candidate.get('memory_family', '')}`",
        f"- Matches alignés : `{summary.get('match_count', 0)}`",
        f"- Top film : `{top.get('film_id', '')}`",
        "",
        "## Lecture PowerFlow",
        "B9 montre la scène courante. B6 compare les films. T0167 force l’alignement sur le même candidat avant de produire un brief.",
        "",
        "## Top match",
    ]
    if top:
        lines += [
            f"- Film : `{top.get('film_id', '')}`",
            f"- Label : {top.get('label_fr', '')}",
            f"- Score d’alignement : `{top.get('alignment_score', '')}`",
            f"- État : `{top.get('alignment_state', '')}`",
        ]
    else:
        lines.append("Aucun top match aligné disponible.")
    lines += ["", "## Risques techniques"]
    for risk in summary.get("technical_risks", []):
        lines.append(f"- `{risk.get('risk_code', '')}` — {risk.get('risk_fr', '')}")
    lines += [
        "",
        "## Ce que T0167 ne conclut pas",
        "- Aucune décision d’exécution.",
        "- Aucune probabilité de résultat.",
        "- Une mémoire comparable n’est pas une répétition certaine.",
        "- Une source proxy reste proxy.",
        "",
    ]
    return "\n".join(lines)


def run_alignment(
    latest_scene_json: Path,
    output_dir: Path,
    b6_index_json: Optional[Path] = None,
    film_cards_json: Optional[Path] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    missing_inputs: List[str] = []
    if not latest_scene_json.exists():
        missing_inputs.append(str(latest_scene_json))
        candidate: Dict[str, Any] = {}
        matches: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        entries: List[Dict[str, Any]] = []
        state = "BLOCKED_MISSING_LATEST_SCENE_CANDIDATE"
    else:
        candidate = normalize_candidate(read_json(latest_scene_json))
        if any(marker in " ".join(str(v).upper() for v in candidate.values() if isinstance(v, str)) for marker in RAW_UNAVAILABLE_MARKERS):
            entries = []
            matches = []
            rejected = []
            state = "BLOCKED_RAW_UNAVAILABLE_CANDIDATE"
        else:
            index_payload = read_json(b6_index_json) if b6_index_json and b6_index_json.exists() else None
            film_cards_payload = read_json(film_cards_json) if film_cards_json and film_cards_json.exists() else None
            entries = load_b6_memory_entries(index_payload=index_payload, film_cards_payload=film_cards_payload)
            if not entries:
                state = "BLOCKED_MISSING_B6_MEMORY_SOURCE"
                matches = []
                rejected = []
            else:
                matches, rejected = build_matches(candidate, entries, top_k=top_k)
                if matches:
                    if candidate.get("source_quality_state") == "SOURCE_LIVE_UNQUALIFIED":
                        state = "B9_B6_REALIGNMENT_READY_WITH_SOURCE_LIMITS"
                    else:
                        state = "B9_B6_REALIGNMENT_READY"
                else:
                    state = "B9_B6_REALIGNMENT_READY_NO_MATCHES"
    query_payload = build_query_payload(candidate) if candidate else {"version": VERSION, "alignment_contract": {"requires_same_candidate_id": True}}
    technical_risks = compute_risks(candidate, len(matches), len(rejected), len(entries))
    top_match = matches[0] if matches else {}
    user_texts = [candidate.get("label_fr", "") if candidate else "", build_markdown({"alignment_state": state, "candidate": candidate, "top_match": top_match, "match_count": len(matches), "technical_risks": technical_risks})]
    forbidden_hits = scan_forbidden_user_text(user_texts)
    summary = {
        "version": VERSION,
        "generated_at": _now_iso(),
        "alignment_state": state,
        "candidate": candidate,
        "query_payload": query_payload,
        "match_count": len(matches),
        "top_match_film_id": top_match.get("film_id", ""),
        "top_match": top_match,
        "matches": matches,
        "rejected_memory_count": len(rejected),
        "rejected_memory": rejected,
        "technical_risks": technical_risks,
        "missing_inputs": missing_inputs,
        "forbidden_language_hits": forbidden_hits,
        "read_only": True,
        "db_write": False,
        "dashboard_live": False,
        "telegram_send": False,
        "no_decision_guard": True,
    }
    write_json(output_dir / "B9_B6_AUTO_REALIGNMENT_V0.json", summary)
    write_json(output_dir / "B9_B6_ALIGNED_QUERY_PAYLOAD_V0.json", query_payload)
    (output_dir / "B9_B6_AUTO_REALIGNMENT_V0.md").write_text(build_markdown(summary), encoding="utf-8")
    match_fields = ["film_id", "date", "time_start", "time_end", "label_fr", "memory_family", "scene_family", "scene_role", "price_verdict", "session", "source_quality_state", "alignment_score", "alignment_state", "similarities_fr", "differences_fr", "technical_limits"]
    write_csv(output_dir / "B9_B6_AUTO_REALIGNMENT_MATCHES_V0.csv", matches, match_fields)
    write_csv(output_dir / "B9_B6_AUTO_REALIGNMENT_RISKS_V0.csv", technical_risks, ["risk_code", "risk_fr"])
    manifest = {
        "version": VERSION,
        "generated_at": summary["generated_at"],
        "files": [
            "B9_B6_AUTO_REALIGNMENT_V0.json",
            "B9_B6_ALIGNED_QUERY_PAYLOAD_V0.json",
            "B9_B6_AUTO_REALIGNMENT_V0.md",
            "B9_B6_AUTO_REALIGNMENT_MATCHES_V0.csv",
            "B9_B6_AUTO_REALIGNMENT_RISKS_V0.csv",
            "B9_B6_AUTO_REALIGNMENT_MANIFEST.json",
            "B9_B6_AUTO_REALIGNMENT_V0.zip",
        ],
        "read_only": True,
    }
    write_json(output_dir / "B9_B6_AUTO_REALIGNMENT_MANIFEST.json", manifest)
    zip_path = output_dir / "B9_B6_AUTO_REALIGNMENT_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in manifest["files"]:
            if name.endswith(".zip"):
                continue
            path = output_dir / name
            if path.exists():
                zf.write(path, arcname=name)
    summary["zip"] = str(zip_path)
    write_json(output_dir / "B9_B6_AUTO_REALIGNMENT_V0.json", summary)
    return summary
