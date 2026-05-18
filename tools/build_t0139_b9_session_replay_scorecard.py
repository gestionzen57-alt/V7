#!/usr/bin/env python3
"""
T0139 — B9 London / NY / Asian Replay Scorecard V0.

Read-only scorecard for B9/T009 replay summaries grouped by market session.
It consumes either:
  - a corpus scan CSV produced by a parallel workspace, or
  - a directory scan containing replay summary JSON files.

It never writes to any DB and never emits BUY/SELL/probability language.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "T0139_B9_SESSION_REPLAY_SCORECARD_V0"

FORBIDDEN_TERMS = [
    "BUY", "SELL", "ACHETER", "VENDRE", "TAKE PROFIT", "STOP LOSS",
    "PROBABILITY OF SUCCESS", "TAUX DE REUSSITE", "TAUX DE RÉUSSITE",
    "CONSEIL FINANCIER", "ORDRE D'EXECUTION", "ORDRE D’EXÉCUTION",
]

EXCLUDE_DIR_MARKERS = (
    "samples",
    "_validation",
    "_install_validation",
    "_git_validation",
    "_regenerated",
    "_extract",
    ".git",
    "__pycache__",
)

REQUIRED_OUTPUTS = [
    "B9_SESSION_REPLAY_SCORECARD_V0.md",
    "B9_SESSION_REPLAY_SCORECARD_V0.json",
    "B9_SESSION_REPLAY_SCORECARD_ROWS_V0.csv",
    "B9_SESSION_REPLAY_SCORECARD_SESSION_COUNTS_V0.csv",
    "B9_SESSION_REPLAY_SCORECARD_FAILURE_PATTERNS_V0.csv",
    "B9_SESSION_REPLAY_SCORECARD_KEEP_REVIEW_REJECT_V0.csv",
    "B9_SESSION_REPLAY_SCORECARD_MANIFEST.json",
    "B9_SESSION_REPLAY_SCORECARD_V0.zip",
]

V4_FIELDS = {
    "why_how": ["what_happens_fr", "why_it_matters_fr", "how_it_happened_fr", "mechanism_fr", "proof_summary_fr"],
    "causality": ["previous_context_fr", "cause_fr", "reaction_fr", "consequence_fr", "memory_shift_fr", "retest_role_fr"],
    "fractal": ["scene_id", "scene_role", "parent_scene", "session_chapter", "fractal_reading_fr"],
    "retest": ["retest_visible", "retest_source", "retest_result", "retest_judgment_fr"],
    "effort_result_progress": ["b9_effort_score", "b9_result_score", "b9_progress_score", "b9_effort_result_progress_state"],
    "center_path": ["b9_center_path_shape", "b9_internal_progress_state", "b9_center_range_pips"],
    "source_quality": ["source_mode", "data_visibility", "confidence_cap", "proxy_vs_raw_verdict"],
    "source_gate": ["b9_source_quality_gate_state", "b9_source_truth_family"],
    "session_overlay": ["b9_session", "b9_session_phase", "b9_session_bias"],
    "timestamp_policy": ["timestamp_policy", "b9_v4_timestamp_policy"],
}

@dataclass
class ReplayRow:
    path: str
    file_name: str
    source: str
    session: str
    session_phase: str
    date: str
    time_start: str
    time_end: str
    moments: int
    source_family: str
    summary_recovery_type: str
    source_mode: str
    data_visibility: str
    confidence_cap: str
    proxy_vs_raw_verdict: str
    raw_unavailable_count: int
    has_v4_core: bool
    has_retest: bool
    has_effort_result_progress: bool
    has_center_path: bool
    has_source_gate: bool
    has_session_overlay: bool
    has_timestamp_policy: bool
    forbidden_language_hits: int
    quality_score: float
    score_state: str
    decision: str
    failure_patterns: str
    notes_fr: str

def safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None

def as_list_moments(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "items", "rows", "scenes"):
        value = data.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    # Some tools wrap summary under enriched_summary/summary.
    for key in ("summary", "sequence_summary", "enriched_summary"):
        value = data.get(key)
        if isinstance(value, dict):
            nested = as_list_moments(value)
            if nested:
                return nested
    return []

def first_nonempty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""

def extract_from_moments(moments: Sequence[Dict[str, Any]], key: str) -> str:
    for m in moments:
        if key in m and str(m.get(key, "")).strip():
            return str(m.get(key, "")).strip()
    return ""

def parse_csv_rows(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]

def should_exclude_path(path: Path, allow_samples: bool = False) -> bool:
    parts = [p.lower() for p in path.parts]
    text = str(path).replace("\\", "/").lower()
    markers = EXCLUDE_DIR_MARKERS if not allow_samples else tuple(m for m in EXCLUDE_DIR_MARKERS if m != "samples")
    if any(marker in parts for marker in markers):
        return True
    if any(marker in text for marker in ("_validation", "_install_validation", "_git_validation", "_regenerated", "_extract")):
        return True
    return False

def discover_jsons(scan_root: Path) -> List[Path]:
    if not scan_root.exists():
        return []
    patterns = ["*t009*sequence*summary*.json", "*sequence_summary*.json", "*B9*summary*.json", "*b9*summary*.json"]
    found: List[Path] = []
    for pattern in patterns:
        for p in scan_root.rglob(pattern):
            if p.is_file() and not should_exclude_path(p, allow_samples=("samples" in [part.lower() for part in scan_root.parts])):
                found.append(p)
    # De-duplicate while preserving order.
    unique: List[Path] = []
    seen = set()
    for p in found:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique

def read_candidate_paths(scan_root: Path, input_index_csv: Optional[Path], scan_csv: Optional[Path]) -> List[Path]:
    candidate_strings: List[str] = []
    for csv_path in (input_index_csv, scan_csv):
        if csv_path and csv_path.exists():
            for row in parse_csv_rows(csv_path):
                # Accept several possible column names from collector/audit workspaces.
                for col in ("path", "file_path", "json_path", "summary_path", "absolute_path", "candidate_path"):
                    val = row.get(col)
                    if val and val.strip():
                        candidate_strings.append(val.strip().strip('"'))
                        break
    paths: List[Path] = []
    for s in candidate_strings:
        p = Path(s)
        if not p.is_absolute():
            p = scan_root / p
        if p.exists() and p.suffix.lower() == ".json" and not should_exclude_path(p, allow_samples=("samples" in [part.lower() for part in scan_root.parts])):
            paths.append(p)
    if paths:
        # De-duplicate.
        unique=[]; seen=set()
        for p in paths:
            rp=str(p.resolve())
            if rp not in seen:
                seen.add(rp); unique.append(p)
        return unique
    return discover_jsons(scan_root)

def find_time_text(data: Dict[str, Any], moments: Sequence[Dict[str, Any]], preferred: str) -> str:
    # preferred is start/end.
    keys = [
        f"time_{preferred}_real", f"time_{preferred}", f"orig_{preferred}",
        f"{preferred}_time", f"{preferred}", f"window_{preferred}",
    ]
    for k in keys:
        val = data.get(k)
        if val:
            return str(val)
    if moments:
        if preferred == "start":
            m = moments[0]
        else:
            m = moments[-1]
        for k in keys:
            val = m.get(k)
            if val:
                return str(val)
    return ""

def extract_hour_from_text(*texts: str) -> Optional[int]:
    for text in texts:
        if not text:
            continue
        # ISO or HH:MM
        m = re.search(r"(?:T|\s|^)([0-2]?\d):([0-5]\d)", text)
        if m:
            h = int(m.group(1))
            if 0 <= h <= 23:
                return h
        # Filename fragments 0800_1200, 14:00, 1400-2300
        m = re.search(r"(?:^|[_\-])(0?\d|1\d|2[0-3])(?:[0-5]\d)(?:[_\-]|$)", text)
        if m:
            h = int(m.group(1))
            if 0 <= h <= 23:
                return h
    return None

def classify_session(hour: Optional[int]) -> Tuple[str, str, str]:
    if hour is None:
        return "SESSION_UNKNOWN", "UNKNOWN", "Heure non disponible : session non qualifiée."
    if 12 <= hour < 16:
        return "OVERLAP", "MAX_VELOCITY_BATTLEFIELD", "Chevauchement London/NY : vélocité et bataille maximales possibles."
    if 7 <= hour < 12:
        return "LONDON", "IGNITION_OR_DECISION", "London : ignition, premier mouvement ou décision de zone."
    if 16 <= hour < 21:
        return "NY", "CONFIRMATION_OR_COUNTER_MOVE", "NY : confirmation, contre-mouvement ou digestion directionnelle."
    if 22 <= hour or hour < 7:
        return "ASIAN", "COMPRESSION_OR_RANGE", "Asian : compression lente, range ou préparation de relâchement."
    if 21 <= hour < 22:
        return "DEAD_ZONE", "LOW_LIQUIDITY_TRANSITION", "Dead zone : transition fragile, risque technique de lecture pauvre."
    return "SESSION_UNKNOWN", "UNKNOWN", "Session non qualifiée."

def count_forbidden(data: Any) -> int:
    text = json.dumps(data, ensure_ascii=False).upper()
    count = 0
    for term in FORBIDDEN_TERMS:
        count += text.count(term.upper())
    return count

def has_any_field(moments: Sequence[Dict[str, Any]], fields: Sequence[str]) -> bool:
    for m in moments:
        for f in fields:
            if f in m and str(m.get(f, "")).strip() not in ("", "None", "null"):
                return True
    return False

def count_raw_unavailable(moments: Sequence[Dict[str, Any]], data: Dict[str, Any]) -> int:
    count = 0
    for m in moments:
        text = " ".join(str(m.get(k, "")) for k in (
            "proxy_vs_raw_verdict", "source_quality_state", "b9_source_quality_gate_state",
            "source_quality_state", "technical_limits", "data_visibility"
        )).upper()
        if "RAW_UNAVAILABLE" in text:
            count += 1
    if count == 0:
        text = json.dumps(data, ensure_ascii=False).upper()
        # Do not overcount every mention in docs; top-level result is enough.
        if "RAW_UNAVAILABLE" in text and not moments:
            count = 1
    return count

def score_row(data: Dict[str, Any], moments: Sequence[Dict[str, Any]], path: Path, source: str) -> ReplayRow:
    file_name = path.name
    time_start = find_time_text(data, moments, "start")
    time_end = find_time_text(data, moments, "end")
    date = first_nonempty(data.get("date"), extract_from_moments(moments, "date"))
    if not date:
        m = re.search(r"(20\d{6}|20\d{2}-\d{2}-\d{2})", str(path))
        if m:
            raw = m.group(1)
            date = raw if "-" in raw else f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    hour = extract_hour_from_text(time_start, str(path))
    session, phase, session_reading = classify_session(hour)

    source_family = first_nonempty(data.get("source_family"), extract_from_moments(moments, "source_family"), data.get("summary_recovery_type"))
    summary_recovery_type = first_nonempty(data.get("summary_recovery_type"), extract_from_moments(moments, "summary_recovery_type"))
    source_mode = first_nonempty(data.get("source_mode"), extract_from_moments(moments, "source_mode"))
    data_visibility = first_nonempty(data.get("data_visibility"), extract_from_moments(moments, "data_visibility"))
    confidence_cap = first_nonempty(data.get("confidence_cap"), extract_from_moments(moments, "confidence_cap"))
    proxy_vs_raw_verdict = first_nonempty(data.get("proxy_vs_raw_verdict"), extract_from_moments(moments, "proxy_vs_raw_verdict"))
    raw_unavailable_count = count_raw_unavailable(moments, data)
    forbidden = count_forbidden(data)

    has_v4_core = all(has_any_field(moments, V4_FIELDS[k]) for k in ("why_how", "causality", "fractal"))
    has_retest = has_any_field(moments, V4_FIELDS["retest"])
    has_erp = has_any_field(moments, V4_FIELDS["effort_result_progress"])
    has_center = has_any_field(moments, V4_FIELDS["center_path"])
    has_source_quality = bool(source_mode or data_visibility or confidence_cap or proxy_vs_raw_verdict)
    has_source_gate = has_any_field(moments, V4_FIELDS["source_gate"])
    has_session_overlay = has_any_field(moments, V4_FIELDS["session_overlay"])
    has_timestamp_policy = has_any_field(moments, V4_FIELDS["timestamp_policy"]) or bool(data.get("timestamp_policy") or data.get("b9_v4_timestamp_policy"))

    components = [
        len(moments) > 0,
        has_source_quality,
        has_retest,
        has_erp,
        has_center,
        has_source_gate,
        has_session_overlay,
        has_timestamp_policy,
        has_v4_core,
    ]
    quality_score = round(sum(1 for x in components if x) / len(components), 4)
    failure_patterns: List[str] = []
    if not moments:
        failure_patterns.append("NO_MOMENTS")
    if not has_source_quality:
        failure_patterns.append("SOURCE_QUALITY_MISSING")
    if not has_retest:
        failure_patterns.append("RETEST_FIELDS_MISSING")
    if not has_erp:
        failure_patterns.append("EFFORT_RESULT_PROGRESS_MISSING")
    if not has_center:
        failure_patterns.append("CENTER_PATH_MISSING")
    if not has_timestamp_policy:
        failure_patterns.append("TIMESTAMP_POLICY_MISSING")
    if raw_unavailable_count and raw_unavailable_count >= max(1, len(moments)):
        failure_patterns.append("RAW_UNAVAILABLE_ONLY")
    if forbidden:
        failure_patterns.append("FORBIDDEN_LANGUAGE")
    if session == "SESSION_UNKNOWN":
        failure_patterns.append("SESSION_UNKNOWN")

    if forbidden or not moments or "RAW_UNAVAILABLE_ONLY" in failure_patterns:
        decision = "REJECT"
        score_state = "SESSION_REPLAY_REJECT"
    elif quality_score >= 0.70 and session != "SESSION_UNKNOWN":
        decision = "KEEP"
        score_state = "SESSION_REPLAY_KEEP"
    else:
        decision = "REVIEW"
        score_state = "SESSION_REPLAY_REVIEW"

    notes = session_reading
    if decision == "REVIEW":
        notes += " Champs incomplets : audit humain recommandé."
    elif decision == "REJECT":
        notes += " Rejeté pour mémoire active ou scorecard exploitable."

    return ReplayRow(
        path=str(path), file_name=file_name, source=source, session=session, session_phase=phase,
        date=date, time_start=time_start, time_end=time_end, moments=len(moments),
        source_family=source_family, summary_recovery_type=summary_recovery_type, source_mode=source_mode,
        data_visibility=data_visibility, confidence_cap=str(confidence_cap), proxy_vs_raw_verdict=proxy_vs_raw_verdict,
        raw_unavailable_count=raw_unavailable_count, has_v4_core=has_v4_core, has_retest=has_retest,
        has_effort_result_progress=has_erp, has_center_path=has_center, has_source_gate=has_source_gate,
        has_session_overlay=has_session_overlay, has_timestamp_policy=has_timestamp_policy,
        forbidden_language_hits=forbidden, quality_score=quality_score, score_state=score_state,
        decision=decision, failure_patterns="|".join(failure_patterns), notes_fr=notes,
    )

def rows_from_paths(paths: Sequence[Path], source: str) -> List[ReplayRow]:
    rows=[]
    for p in paths:
        data = safe_read_json(p)
        if not isinstance(data, dict):
            continue
        moments = as_list_moments(data)
        rows.append(score_row(data, moments, p, source))
    return rows

def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fields: Optional[Sequence[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        keys=[]
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        fields=keys
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

def summarize(rows: Sequence[ReplayRow]) -> Dict[str, Any]:
    session_counts: Dict[str, Dict[str, Any]] = {}
    failure_counts: Dict[str, int] = {}
    for r in rows:
        s=session_counts.setdefault(r.session, {"session": r.session, "files": 0, "keep": 0, "review": 0, "reject": 0, "moments": 0, "avg_quality_score": 0.0})
        s["files"] += 1
        s[r.decision.lower()] += 1
        s["moments"] += r.moments
        s["avg_quality_score"] += r.quality_score
        for pat in filter(None, r.failure_patterns.split("|")):
            failure_counts[pat] = failure_counts.get(pat, 0) + 1
    for s in session_counts.values():
        if s["files"]:
            s["avg_quality_score"] = round(s["avg_quality_score"] / s["files"], 4)
    keep=sum(1 for r in rows if r.decision=="KEEP")
    review=sum(1 for r in rows if r.decision=="REVIEW")
    reject=sum(1 for r in rows if r.decision=="REJECT")
    state = "PASS" if rows and (keep+review)>0 and sum(r.forbidden_language_hits for r in rows)==0 else "REVIEW_REQUIRED"
    if not rows:
        state="BLOCKED_NO_REPLAY_FILES"
    return {
        "version": VERSION,
        "scorecard_state": state,
        "files_processed": len(rows),
        "files_keep": keep,
        "files_review": review,
        "files_rejected": reject,
        "sessions_detected": sorted(session_counts.keys()),
        "total_moments": sum(r.moments for r in rows),
        "forbidden_language_files": sum(1 for r in rows if r.forbidden_language_hits),
        "raw_unavailable_rejected_files": sum(1 for r in rows if r.decision=="REJECT" and "RAW_UNAVAILABLE_ONLY" in r.failure_patterns),
        "session_counts": list(session_counts.values()),
        "failure_patterns": [{"pattern": k, "count": v} for k, v in sorted(failure_counts.items())],
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }

def write_markdown(output: Path, summary: Dict[str, Any], rows: Sequence[ReplayRow]) -> None:
    lines = []
    lines.append("# T0139 — B9 London / NY / Asian Replay Scorecard V0")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append(f"- État : `{summary['scorecard_state']}`")
    lines.append(f"- Fichiers traités : `{summary['files_processed']}`")
    lines.append(f"- KEEP : `{summary['files_keep']}`")
    lines.append(f"- REVIEW : `{summary['files_review']}`")
    lines.append(f"- REJECT : `{summary['files_rejected']}`")
    lines.append(f"- Moments : `{summary['total_moments']}`")
    lines.append("")
    lines.append("B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort. La session contextualise la scène ; elle ne décide pas.")
    lines.append("")
    lines.append("## Counts par session")
    lines.append("")
    lines.append("| Session | Fichiers | KEEP | REVIEW | REJECT | Moments | Score moyen |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for s in summary["session_counts"]:
        lines.append(f"| {s['session']} | {s['files']} | {s['keep']} | {s['review']} | {s['reject']} | {s['moments']} | {s['avg_quality_score']} |")
    lines.append("")
    lines.append("## Failure patterns")
    lines.append("")
    if summary["failure_patterns"]:
        lines.append("| Pattern | Count |")
        lines.append("|---|---:|")
        for f in summary["failure_patterns"]:
            lines.append(f"| {f['pattern']} | {f['count']} |")
    else:
        lines.append("Aucun pattern d’échec détecté.")
    lines.append("")
    lines.append("## Fichiers")
    lines.append("")
    lines.append("| Decision | Session | Moments | Score | Fichier | Limites |")
    lines.append("|---|---|---:|---:|---|---|")
    for r in rows:
        lines.append(f"| {r.decision} | {r.session} | {r.moments} | {r.quality_score} | `{r.file_name}` | {r.failure_patterns or 'OK'} |")
    lines.append("")
    lines.append("## Ce que B9 ne doit pas conclure")
    lines.append("")
    lines.append("- Aucun ordre d’exécution.")
    lines.append("- Aucun taux de réussite.")
    lines.append("- Une session ne transforme pas une scène proxy en vérité raw.")
    lines.append("- Une similarité de comportement ne signifie pas répétition certaine.")
    output.write_text("\n".join(lines)+"\n", encoding="utf-8")

def zip_outputs(out_dir: Path) -> Path:
    zip_path = out_dir / "B9_SESSION_REPLAY_SCORECARD_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in REQUIRED_OUTPUTS:
            p = out_dir / name
            if p.exists() and p != zip_path:
                z.write(p, arcname=p.name)
    return zip_path

def build(args: argparse.Namespace) -> Dict[str, Any]:
    scan_root = Path(args.scan_root).resolve()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    input_index_csv = Path(args.input_index_csv) if args.input_index_csv else None
    scan_csv = Path(args.scan_csv) if args.scan_csv else None

    paths = read_candidate_paths(scan_root, input_index_csv, scan_csv)
    rows = rows_from_paths(paths, source="scan_csv_or_index" if (input_index_csv or scan_csv) else "scan_root")
    summary = summarize(rows)
    summary["scan_root"] = str(scan_root)
    summary["input_index_csv"] = str(input_index_csv) if input_index_csv else ""
    summary["scan_csv"] = str(scan_csv) if scan_csv else ""

    row_dicts = [asdict(r) for r in rows]
    fields = list(asdict(rows[0]).keys()) if rows else list(ReplayRow.__annotations__.keys())
    write_csv(out_dir / "B9_SESSION_REPLAY_SCORECARD_ROWS_V0.csv", row_dicts, fields)
    write_csv(out_dir / "B9_SESSION_REPLAY_SCORECARD_SESSION_COUNTS_V0.csv", summary["session_counts"])
    write_csv(out_dir / "B9_SESSION_REPLAY_SCORECARD_FAILURE_PATTERNS_V0.csv", summary["failure_patterns"] or [{"pattern":"", "count":0}])
    write_csv(out_dir / "B9_SESSION_REPLAY_SCORECARD_KEEP_REVIEW_REJECT_V0.csv", [r for r in row_dicts if r.get("decision") in ("KEEP", "REVIEW", "REJECT")], fields)
    write_markdown(out_dir / "B9_SESSION_REPLAY_SCORECARD_V0.md", summary, rows)
    (out_dir / "B9_SESSION_REPLAY_SCORECARD_V0.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "version": VERSION,
        "outputs": REQUIRED_OUTPUTS,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }
    (out_dir / "B9_SESSION_REPLAY_SCORECARD_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = zip_outputs(out_dir)
    summary["zip"] = str(zip_path)
    # rewrite summary with zip
    (out_dir / "B9_SESSION_REPLAY_SCORECARD_V0.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="T0139 B9 session replay scorecard")
    parser.add_argument("--scan-root", default=".", help="Core root or sample directory to scan")
    parser.add_argument("--input-index-csv", default="", help="Optional T0126 KEEP csv")
    parser.add_argument("--scan-csv", default="", help="Optional parallel workspace replay corpus scan csv")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args(argv)
    summary = build(args)
    print(json.dumps({
        "version": summary["version"],
        "scorecard_state": summary["scorecard_state"],
        "files_processed": summary["files_processed"],
        "files_keep": summary["files_keep"],
        "files_review": summary["files_review"],
        "files_rejected": summary["files_rejected"],
        "sessions_detected": summary["sessions_detected"],
        "total_moments": summary["total_moments"],
        "forbidden_language_files": summary["forbidden_language_files"],
        "zip": summary.get("zip", ""),
    }, ensure_ascii=False, indent=2))
    return 0 if summary["scorecard_state"] in ("PASS", "REVIEW_REQUIRED") else 2

if __name__ == "__main__":
    raise SystemExit(main())
