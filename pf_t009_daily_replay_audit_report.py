"""T0151 - B9 Daily Replay Audit Report V0.

Read-only audit layer for B9 replay outputs.
It aggregates replay runner rows, session scorecards and optional golden terrain cases
into a French trader daily audit without producing trading decisions.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

VERSION = "T0151_B9_DAILY_REPLAY_AUDIT_REPORT_V0"

FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"\bACHETER\b", re.IGNORECASE),
    re.compile(r"\bVENDRE\b", re.IGNORECASE),
    re.compile(r"probabilit[ée]\s+de\s+succ[èe]s", re.IGNORECASE),
    re.compile(r"taux\s+de\s+r[ée]ussite", re.IGNORECASE),
]

SOURCE_WEAK_STATES = {
    "SOURCE_PROXY_ONLY",
    "SOURCE_RECONSTRUCTED_LIMITED",
    "SOURCE_QUALITY_WEAK_LIMITED",
    "SOURCE_UNKNOWN_LIMITED",
}
RAW_UNAVAILABLE_MARKERS = {"RAW_UNAVAILABLE", "SOURCE_RAW_UNAVAILABLE_REJECTED", "MEMORY_REJECTED_RAW_UNAVAILABLE"}


def _s(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _lower(value: Any) -> str:
    return _s(value).lower()


def _truthy(value: Any) -> bool:
    text = _lower(value)
    return text in {"1", "true", "yes", "oui", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def sha1_short(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:10].upper()


def find_forbidden_hits(obj: Any) -> List[str]:
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True) if not isinstance(obj, str) else obj
    hits: List[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return sorted(set(hits))


def extract_moments(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "b9_moments", "items"):
        val = summary.get(key)
        if isinstance(val, list):
            return [m for m in val if isinstance(m, dict)]
    if isinstance(summary.get("summary"), dict):
        return extract_moments(summary["summary"])
    return []


def load_sequence_summary(path: Optional[Path]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not path or not path.exists():
        return [], {}
    data = read_json(path)
    if isinstance(data, dict):
        return extract_moments(data), data
    return [], {}


def normalize_replay_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, r in enumerate(rows):
        path = _s(r.get("path") or r.get("file_path") or r.get("summary_path") or r.get("source_path") or r.get("file"))
        verdict = _s(r.get("verdict") or r.get("candidate_state") or r.get("status") or r.get("classification") or r.get("state"))
        if not verdict:
            verdict = "KEEP" if _truthy(r.get("keep")) else "REVIEW"
        session = _s(r.get("session") or r.get("b9_session") or r.get("dominant_session") or infer_session_from_text(path))
        source_quality = _s(r.get("source_quality_state") or r.get("b9_source_quality_gate_state") or r.get("source_state"))
        proxy_verdict = _s(r.get("proxy_vs_raw_verdict") or r.get("raw_verdict"))
        raw_unavailable = any(marker.lower() in _lower(r.get(k)) for k in r.keys() for marker in RAW_UNAVAILABLE_MARKERS)
        missing_fields = _s(r.get("missing_required_fields") or r.get("total_missing_required_fields") or r.get("missing_required_field_counts"))
        forbidden = _s(r.get("forbidden_language_hits") or r.get("forbidden_language_files") or r.get("forbidden_language_hit_count"))
        moments = int(_float(r.get("moments") or r.get("moment_count") or r.get("total_moments") or r.get("after_moments"), 0))
        timestamp_state = _s(r.get("timestamp_policy") or r.get("timestamp_guard_state") or r.get("b9_v4_timestamp_policy"))
        retest_state = _s(r.get("retest_result") or r.get("b9_native_retest_judgment") or r.get("retest_visibility") or r.get("retest_visible"))
        memory_state = _s(r.get("memory_confidence_ladder") or r.get("b9_memory_confidence_ladder") or r.get("memory_state"))
        label = _s(r.get("label") or r.get("label_fr") or r.get("reading_fr") or Path(path).stem if path else f"row_{i}")
        out.append({
            "row_id": f"R{i+1:03d}",
            "path": path,
            "label": label,
            "session": session or "SESSION_UNKNOWN",
            "verdict": verdict.upper(),
            "moments": moments,
            "source_quality_state": source_quality,
            "proxy_vs_raw_verdict": proxy_verdict,
            "timestamp_state": timestamp_state,
            "retest_state": retest_state,
            "memory_state": memory_state,
            "raw_unavailable": raw_unavailable,
            "missing_fields": missing_fields,
            "forbidden_language": forbidden,
        })
    return out


def infer_session_from_text(text: str) -> str:
    t = _lower(text)
    if any(x in t for x in ["0800", "0900", "1000", "1100", "london"]):
        return "LONDON"
    if any(x in t for x in ["1200", "1300", "overlap"]):
        return "OVERLAP"
    if any(x in t for x in ["1400", "1500", "1600", "1700", "1800", "ny"]):
        return "NY"
    if any(x in t for x in ["0500", "0600", "0700", "asian", "asia"]):
        return "ASIAN"
    if any(x in t for x in ["2000", "2100", "2200", "2300", "dead"]):
        return "DEAD_ZONE"
    return "SESSION_UNKNOWN"


def moments_to_replay_rows(moments: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for i, m in enumerate(moments):
        text_all = json.dumps(m, ensure_ascii=False)
        raw_unavailable = any(marker.lower() in text_all.lower() for marker in RAW_UNAVAILABLE_MARKERS)
        source_state = _s(m.get("b9_source_quality_gate_state") or m.get("source_quality_state"))
        proxy = _s(m.get("proxy_vs_raw_verdict"))
        session = _s(m.get("b9_session") or m.get("session") or infer_session_from_text(_s(m.get("time_start"))))
        retest = _s(m.get("b9_native_retest_judgment") or m.get("retest_result") or m.get("retest_visible"))
        memory = _s(m.get("b9_memory_confidence_ladder") or m.get("b9_memory_ladder_state") or m.get("b9_memory_comparison_state"))
        timestamp = _s(m.get("b9_v4_timestamp_policy") or m.get("timestamp_policy") or m.get("timestamp_guard_state"))
        label = _s(m.get("label_fr") or m.get("b9_scene_role") or m.get("moment_type") or f"moment_{i+1}")
        verdict = "REJECT" if raw_unavailable else "KEEP" if source_state not in SOURCE_WEAK_STATES else "REVIEW"
        rows.append({
            "path": _s(m.get("scene_id") or m.get("moment_id") or f"moment_{i+1}"),
            "label": label,
            "session": session or "SESSION_UNKNOWN",
            "verdict": verdict,
            "moments": 1,
            "source_quality_state": source_state,
            "proxy_vs_raw_verdict": proxy,
            "timestamp_state": timestamp,
            "retest_state": retest,
            "memory_state": memory,
            "raw_unavailable": raw_unavailable,
            "missing_fields": "",
            "forbidden_language": "",
        })
    return normalize_replay_rows(rows)


def load_golden_cases(path: Optional[Path]) -> List[Dict[str, Any]]:
    if not path or not path.exists():
        return []
    return [dict(r) for r in read_csv(path)]


def classify_row_seen_missed(row: Mapping[str, Any], golden_cases: Sequence[Mapping[str, Any]]) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    verdict = _s(row.get("verdict")).upper()
    if verdict == "REJECT" or _truthy(row.get("raw_unavailable")):
        return "B9_REJECTED_OR_UNUSABLE", ["raw unavailable ou rejet replay"]
    if _s(row.get("forbidden_language")) not in {"", "0", "[]"}:
        return "B9_AUDIT_BLOCKED_FORBIDDEN_LANGUAGE", ["langage interdit détecté"]
    if _s(row.get("missing_fields")) not in {"", "0", "{}", "[]"}:
        reasons.append("champs requis incomplets")
    if _s(row.get("source_quality_state")) in SOURCE_WEAK_STATES or "LIMITED" in _s(row.get("source_quality_state")):
        reasons.append("source quality limitée")
    if "NUANCED" in _s(row.get("proxy_vs_raw_verdict")):
        reasons.append("raw nuance la lecture")
    if "MISSING" in _s(row.get("memory_state")) or "RETEST_MISSING" in _s(row.get("memory_state")):
        reasons.append("mémoire comparable mais retest manquant")
    if "UNKNOWN" in _s(row.get("timestamp_state")) or "REMAP" in _s(row.get("timestamp_state")) or "SHIFT" in _s(row.get("timestamp_state")):
        reasons.append("timestamp à surveiller")
    if not _s(row.get("retest_state")) or _s(row.get("retest_state")).lower() in {"false", "0", "retest_not_visible"}:
        reasons.append("retest non visible")
    if reasons:
        return "B9_PARTIAL_OR_FRAGILE", reasons
    return "B9_SEEN_CLEANLY", ["scène lisible et exploitable pour audit"]


def compute_audit(replay_rows: Sequence[Mapping[str, Any]], golden_cases: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for row in replay_rows:
        state, reasons = classify_row_seen_missed(row, golden_cases)
        enriched = dict(row)
        enriched["audit_state"] = state
        enriched["audit_reason_fr"] = "; ".join(reasons)
        rows.append(enriched)

    state_counts = Counter(r["audit_state"] for r in rows)
    session_counts = Counter(_s(r.get("session") or "SESSION_UNKNOWN") for r in rows)
    source_fragile = [r for r in rows if "source" in _lower(r.get("audit_reason_fr")) or "NUANCED" in _s(r.get("proxy_vs_raw_verdict"))]
    retest_fragile = [r for r in rows if "retest" in _lower(r.get("audit_reason_fr"))]
    timestamp_fragile = [r for r in rows if "timestamp" in _lower(r.get("audit_reason_fr"))]
    memory_helped = [r for r in rows if _s(r.get("memory_state")) and "REJECTED" not in _s(r.get("memory_state"))]
    traps = [r for r in rows if any(word in _lower(r.get("audit_reason_fr")) for word in ["source", "retest", "timestamp", "nuance"])]
    forbidden_hits = find_forbidden_hits(rows)

    if forbidden_hits:
        audit_state = "BLOCKED_FORBIDDEN_LANGUAGE"
    elif not rows:
        audit_state = "BLOCKED_NO_REPLAY_ROWS"
    elif state_counts.get("B9_SEEN_CLEANLY", 0) > 0 and state_counts.get("B9_REJECTED_OR_UNUSABLE", 0) == 0:
        audit_state = "B9_DAILY_REPLAY_AUDIT_PASS"
    elif state_counts.get("B9_SEEN_CLEANLY", 0) + state_counts.get("B9_PARTIAL_OR_FRAGILE", 0) > 0:
        audit_state = "B9_DAILY_REPLAY_AUDIT_PARTIAL"
    else:
        audit_state = "B9_DAILY_REPLAY_AUDIT_BLOCKED"

    return {
        "version": VERSION,
        "audit_state": audit_state,
        "rows": rows,
        "counts": {
            "files_or_moments_processed": len(rows),
            "seen_cleanly": state_counts.get("B9_SEEN_CLEANLY", 0),
            "partial_or_fragile": state_counts.get("B9_PARTIAL_OR_FRAGILE", 0),
            "rejected_or_unusable": state_counts.get("B9_REJECTED_OR_UNUSABLE", 0),
            "blocked_forbidden_language": state_counts.get("B9_AUDIT_BLOCKED_FORBIDDEN_LANGUAGE", 0),
            "source_fragile": len(source_fragile),
            "retest_fragile": len(retest_fragile),
            "timestamp_fragile": len(timestamp_fragile),
            "memory_helped": len(memory_helped),
            "similarity_traps": len(traps),
            "golden_cases_reference_count": len(golden_cases),
        },
        "session_counts": dict(sorted(session_counts.items())),
        "state_counts": dict(sorted(state_counts.items())),
        "source_fragile_rows": source_fragile,
        "retest_fragile_rows": retest_fragile,
        "timestamp_fragile_rows": timestamp_fragile,
        "memory_helped_rows": memory_helped,
        "similarity_trap_rows": traps,
        "forbidden_language_hits": forbidden_hits,
    }


def render_markdown(audit: Mapping[str, Any]) -> str:
    counts = audit.get("counts", {})
    lines = [
        "# T0151 — B9 Daily Replay Audit Report V0",
        "",
        "## Résumé exécutif",
        "",
        f"État audit : `{audit.get('audit_state')}`",
        "",
        "B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.",
        "Ce rapport audite ce que B9 a vu, ce qu’il a lu partiellement, et ce qui reste fragile techniquement.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}` : {value}")
    lines += ["", "## Counts par session", ""]
    for key, value in audit.get("session_counts", {}).items():
        lines.append(f"- `{key}` : {value}")
    lines += ["", "## Ce que B9 a bien vu", ""]
    seen = [r for r in audit.get("rows", []) if r.get("audit_state") == "B9_SEEN_CLEANLY"]
    if not seen:
        lines.append("Aucune scène classée propre sans limite technique dans cet audit.")
    else:
        for r in seen[:20]:
            lines.append(f"- `{r.get('row_id')}` {r.get('label')} — session `{r.get('session')}` — {r.get('audit_reason_fr')}")
    lines += ["", "## Ce que B9 a lu partiellement", ""]
    partial = [r for r in audit.get("rows", []) if r.get("audit_state") == "B9_PARTIAL_OR_FRAGILE"]
    if not partial:
        lines.append("Aucune scène partielle détectée.")
    else:
        for r in partial[:30]:
            lines.append(f"- `{r.get('row_id')}` {r.get('label')} — {r.get('audit_reason_fr')}")
    lines += ["", "## Où le retest reste fragile", ""]
    if not audit.get("retest_fragile_rows"):
        lines.append("Aucune fragilité retest détectée.")
    else:
        for r in audit.get("retest_fragile_rows", [])[:20]:
            lines.append(f"- `{r.get('row_id')}` {r.get('label')} — retest: `{r.get('retest_state')}`")
    lines += ["", "## Où la source reste fragile", ""]
    if not audit.get("source_fragile_rows"):
        lines.append("Aucune fragilité source détectée.")
    else:
        for r in audit.get("source_fragile_rows", [])[:20]:
            lines.append(f"- `{r.get('row_id')}` {r.get('label')} — source: `{r.get('source_quality_state')}` / `{r.get('proxy_vs_raw_verdict')}`")
    lines += ["", "## Où la mémoire B6 a aidé", ""]
    if not audit.get("memory_helped_rows"):
        lines.append("Aucune trace mémoire exploitable détectée dans les entrées.")
    else:
        for r in audit.get("memory_helped_rows", [])[:20]:
            lines.append(f"- `{r.get('row_id')}` {r.get('label')} — mémoire: `{r.get('memory_state')}`")
    lines += ["", "## Pièges de similarité", ""]
    if not audit.get("similarity_trap_rows"):
        lines.append("Aucun piège de similarité détecté.")
    else:
        for r in audit.get("similarity_trap_rows", [])[:20]:
            lines.append(f"- `{r.get('row_id')}` {r.get('label')} — {r.get('audit_reason_fr')}")
    lines += [
        "",
        "## Ce que B9 ne doit pas conclure",
        "",
        "- B9 ne doit pas transformer une similarité en répétition certaine.",
        "- B9 ne doit pas transformer une source proxy en vérité raw.",
        "- B9 ne doit pas transformer un verdict prix en ordre d’exécution.",
        "- B9 ne doit pas produire de probabilité de succès.",
        "",
        "## Prochain geste recommandé",
        "",
        "Transformer les cas partiels en fixtures ciblées ou corriger les champs manquants à la source.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(audit: Mapping[str, Any], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "B9_DAILY_REPLAY_AUDIT_REPORT_V0.json"
    md_path = output_dir / "B9_DAILY_REPLAY_AUDIT_REPORT_V0.md"
    rows_path = output_dir / "B9_DAILY_REPLAY_AUDIT_ROWS_V0.csv"
    session_path = output_dir / "B9_DAILY_REPLAY_AUDIT_SESSION_COUNTS_V0.csv"
    fragility_path = output_dir / "B9_DAILY_REPLAY_AUDIT_FRAGILITIES_V0.csv"
    memory_path = output_dir / "B9_DAILY_REPLAY_AUDIT_MEMORY_HELPED_V0.csv"
    manifest_path = output_dir / "B9_DAILY_REPLAY_AUDIT_MANIFEST.json"
    zip_path = output_dir / "B9_DAILY_REPLAY_AUDIT_REPORT_V0.zip"

    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(audit), encoding="utf-8")
    row_fields = ["row_id", "path", "label", "session", "verdict", "audit_state", "audit_reason_fr", "moments", "source_quality_state", "proxy_vs_raw_verdict", "timestamp_state", "retest_state", "memory_state", "raw_unavailable"]
    write_csv(rows_path, audit.get("rows", []), row_fields)
    write_csv(session_path, [{"session": k, "count": v} for k, v in audit.get("session_counts", {}).items()], ["session", "count"])
    fragility_rows = list(audit.get("source_fragile_rows", [])) + list(audit.get("retest_fragile_rows", [])) + list(audit.get("timestamp_fragile_rows", []))
    write_csv(fragility_path, fragility_rows, row_fields)
    write_csv(memory_path, audit.get("memory_helped_rows", []), row_fields)

    manifest = {
        "version": VERSION,
        "audit_state": audit.get("audit_state"),
        "outputs": [p.name for p in [json_path, md_path, rows_path, session_path, fragility_path, memory_path]],
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [json_path, md_path, rows_path, session_path, fragility_path, memory_path, manifest_path]:
            z.write(p, arcname=p.name)

    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "rows_csv": str(rows_path),
        "session_csv": str(session_path),
        "fragilities_csv": str(fragility_path),
        "memory_csv": str(memory_path),
        "manifest": str(manifest_path),
        "zip": str(zip_path),
    }


def build_daily_replay_audit(
    replay_results_csv: Optional[Path] = None,
    session_scorecard_csv: Optional[Path] = None,
    golden_cases_csv: Optional[Path] = None,
    sequence_summary_json: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    replay_rows: List[Dict[str, Any]] = []
    if replay_results_csv and replay_results_csv.exists():
        replay_rows.extend(normalize_replay_rows(read_csv(replay_results_csv)))
    if session_scorecard_csv and session_scorecard_csv.exists():
        replay_rows.extend(normalize_replay_rows(read_csv(session_scorecard_csv)))
    moments, _summary = load_sequence_summary(sequence_summary_json)
    if moments:
        replay_rows.extend(moments_to_replay_rows(moments))
    golden_cases = load_golden_cases(golden_cases_csv)
    audit = compute_audit(replay_rows, golden_cases)
    if output_dir is not None:
        audit["output_files"] = write_outputs(audit, output_dir)
    return audit
