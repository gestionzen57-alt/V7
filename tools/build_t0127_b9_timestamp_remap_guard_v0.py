#!/usr/bin/env python3
"""T0127 - B9 Timestamp Remap Guard V0.

Read-only validator for B9/T009 summaries. It detects replay/shifted timestamps,
normalizes raw vs real time fields, and writes an audit pack.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0127_B9_TIMESTAMP_REMAP_GUARD_V0"
FORBIDDEN_TERMS = ("BUY", "SELL", "ACHETER", "VENDRE", "probability_of_success", "probabilite de succes", "probabilité de succès")

RAW_START_KEYS = ("time_start", "start_time", "timestamp_start", "started_at", "start")
RAW_END_KEYS = ("time_end", "end_time", "timestamp_end", "ended_at", "end")
REAL_START_KEYS = ("orig_start", "real_time_start", "time_start_real", "original_start", "start_real")
REAL_END_KEYS = ("orig_end", "real_time_end", "time_end_real", "original_end", "end_real")
LABEL_KEYS = ("label_fr", "label", "moment_label", "title", "type")

REQUIRED_FIELDS = [
    "moment_index",
    "label_fr",
    "time_start_raw",
    "time_end_raw",
    "time_start_real",
    "time_end_real",
    "timestamp_source",
    "timestamp_policy",
    "is_replay_shifted",
    "replay_shift_minutes",
    "technical_limits",
]

@dataclass
class TimestampRow:
    moment_index: int
    label_fr: str
    time_start_raw: str
    time_end_raw: str
    time_start_real: str
    time_end_real: str
    timestamp_source: str
    timestamp_policy: str
    is_replay_shifted: bool
    replay_shift_minutes: int
    technical_limits: str


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def extract_moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Any] = [
        summary.get("moments"),
        summary.get("sequence_moments"),
        summary.get("b9_moments"),
        summary.get("summary", {}).get("moments") if isinstance(summary.get("summary"), dict) else None,
        summary.get("data", {}).get("moments") if isinstance(summary.get("data"), dict) else None,
    ]
    for item in candidates:
        if isinstance(item, list):
            return [m for m in item if isinstance(m, dict)]
    # Allow a single moment object for tiny tests.
    if any(k in summary for k in RAW_START_KEYS + REAL_START_KEYS):
        return [summary]
    return []


def first_present(mapping: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = mapping.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return ""


def normalize_time_text(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    value = value.replace("Z", "+00:00")
    return value


def parse_datetime_flexible(value: str) -> Optional[datetime]:
    value = normalize_time_text(value)
    if not value:
        return None
    # HH:MM or HH:MM:SS only; use neutral date.
    if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", value):
        fmt = "%H:%M:%S" if value.count(":") == 2 else "%H:%M"
        t = datetime.strptime(value, fmt).time()
        return datetime(2000, 1, 1, t.hour, t.minute, t.second)
    # ISO variants.
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def time_key(value: str) -> str:
    dt = parse_datetime_flexible(value)
    if not dt:
        return ""
    return f"{dt.hour:02d}:{dt.minute:02d}"


def minutes_between(raw: str, real: str) -> Optional[int]:
    raw_dt = parse_datetime_flexible(raw)
    real_dt = parse_datetime_flexible(real)
    if raw_dt is None or real_dt is None:
        return None
    # Normalize both to the same date for replay shift detection.
    raw_base = datetime(2000, 1, 1, raw_dt.hour, raw_dt.minute, raw_dt.second)
    real_base = datetime(2000, 1, 1, real_dt.hour, real_dt.minute, real_dt.second)
    delta = int((raw_base - real_base).total_seconds() // 60)
    # Choose the shortest circular day shift.
    if delta > 720:
        delta -= 1440
    if delta < -720:
        delta += 1440
    return delta


def build_replay_remap(replay_report: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    if not replay_report:
        return {}
    rows: List[Dict[str, Any]] = []
    for key in ("moments", "sequence_moments", "windows", "replay_moments", "table", "rows"):
        if isinstance(replay_report.get(key), list):
            rows.extend([r for r in replay_report[key] if isinstance(r, dict)])
    if isinstance(replay_report.get("data"), dict):
        for key in ("moments", "rows", "windows"):
            val = replay_report["data"].get(key)
            if isinstance(val, list):
                rows.extend([r for r in val if isinstance(r, dict)])
    mapping: Dict[str, Dict[str, str]] = {}
    for row in rows:
        raw_start = first_present(row, RAW_START_KEYS + ("shifted_start", "replay_start"))
        raw_end = first_present(row, RAW_END_KEYS + ("shifted_end", "replay_end"))
        real_start = first_present(row, REAL_START_KEYS)
        real_end = first_present(row, REAL_END_KEYS)
        if not raw_start or not real_start:
            # Support window label matching like 0800_0900 with orig_start fields.
            raw_start = first_present(row, ("replay_time_start", "shifted_time_start")) or raw_start
        if raw_start and real_start:
            mapping[time_key(raw_start)] = {"start": real_start, "end": real_end or real_start}
        # Also map by label when available.
        label = first_present(row, LABEL_KEYS)
        if label and real_start:
            mapping[f"label::{label}"] = {"start": real_start, "end": real_end or real_start}
    return mapping


def detect_global_shift(summary: Dict[str, Any]) -> Optional[int]:
    meta = summary.get("metadata") if isinstance(summary.get("metadata"), dict) else {}
    for obj in (summary, meta):
        for key in ("replay_shift_minutes", "shift_minutes", "timestamp_shift_minutes"):
            val = obj.get(key)
            if val is None:
                continue
            try:
                return int(val)
            except (TypeError, ValueError):
                pass
    return None


def apply_shift(raw: str, shift_minutes: Optional[int]) -> str:
    if raw == "" or shift_minutes is None:
        return ""
    dt = parse_datetime_flexible(raw)
    if dt is None:
        return ""
    # Real = raw - shift.
    real = dt - timedelta(minutes=shift_minutes)
    if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", raw.strip()):
        return f"{real.hour:02d}:{real.minute:02d}"
    if "T" in raw:
        return real.isoformat()
    return real.strftime("%Y-%m-%d %H:%M:%S")


def has_forbidden_language(data: Any) -> List[str]:
    text = json.dumps(data, ensure_ascii=False).upper()
    hits = []
    for term in FORBIDDEN_TERMS:
        if term.upper() in text:
            hits.append(term)
    return sorted(set(hits))


def classify_policy(raw_start: str, real_start: str, source: str, explicit_policy: str, replay_shift: Optional[int]) -> Tuple[str, bool, int, str]:
    explicit_policy = (explicit_policy or "").strip()
    if explicit_policy in {"TIMESTAMP_POLICY_OK", "TIMESTAMP_SHIFT_DETECTED", "TIMESTAMP_REMAP_REQUIRED", "TIMESTAMP_REAL_UNKNOWN"}:
        policy = explicit_policy
    else:
        policy = ""
    delta = minutes_between(raw_start, real_start) if raw_start and real_start else None
    is_shifted = bool(delta and abs(delta) >= 2)
    shift = int(delta or replay_shift or 0)
    if not policy:
        if not raw_start:
            policy = "TIMESTAMP_REAL_UNKNOWN"
        elif real_start and is_shifted:
            policy = "TIMESTAMP_SHIFT_DETECTED"
        elif real_start:
            policy = "TIMESTAMP_POLICY_OK"
        else:
            policy = "TIMESTAMP_REMAP_REQUIRED" if (source.startswith("REPLAY") or replay_shift is not None) else "TIMESTAMP_REAL_UNKNOWN"
    if policy == "TIMESTAMP_SHIFT_DETECTED":
        is_shifted = True
    limit = {
        "TIMESTAMP_POLICY_OK": "Horodatage utilisable; raw et real cohérents ou explicitement identiques.",
        "TIMESTAMP_SHIFT_DETECTED": "Décalage replay détecté; utiliser time_*_real pour lecture terrain.",
        "TIMESTAMP_REMAP_REQUIRED": "Résumé probablement replay/shifted sans heure réelle fiable; remap requis avant lecture terrain.",
        "TIMESTAMP_REAL_UNKNOWN": "Heure réelle inconnue; ne pas utiliser ce moment comme preuve horaire terrain.",
    }[policy]
    return policy, is_shifted, shift, limit


def build_rows(summary: Dict[str, Any], replay_report: Optional[Dict[str, Any]] = None) -> List[TimestampRow]:
    moments = extract_moments(summary)
    remap = build_replay_remap(replay_report)
    global_shift = detect_global_shift(summary)
    rows: List[TimestampRow] = []
    for idx, moment in enumerate(moments, start=1):
        label = first_present(moment, LABEL_KEYS) or f"Moment {idx}"
        raw_start = first_present(moment, RAW_START_KEYS)
        raw_end = first_present(moment, RAW_END_KEYS)
        real_start = first_present(moment, REAL_START_KEYS)
        real_end = first_present(moment, REAL_END_KEYS)
        source = first_present(moment, ("timestamp_source", "time_source"))
        explicit_policy = first_present(moment, ("timestamp_policy", "b9_v4_timestamp_policy"))
        if not source:
            source = "SUMMARY_INLINE" if real_start else "SUMMARY_RAW_ONLY"
        # Replay report remap by raw time then label.
        if not real_start and raw_start:
            mapped = remap.get(time_key(raw_start)) or remap.get(f"label::{label}")
            if mapped:
                real_start = mapped.get("start", "")
                real_end = mapped.get("end", "")
                source = "REPLAY_REPORT_REMAP"
        # Global shift fallback.
        if not real_start and global_shift is not None:
            real_start = apply_shift(raw_start, global_shift)
            real_end = apply_shift(raw_end, global_shift)
            source = "GLOBAL_REPLAY_SHIFT_REMAP"
        if not real_end and real_start:
            real_end = real_start
        policy, is_shifted, shift, limit = classify_policy(raw_start, real_start, source, explicit_policy, global_shift)
        rows.append(TimestampRow(
            moment_index=idx,
            label_fr=label,
            time_start_raw=raw_start,
            time_end_raw=raw_end or raw_start,
            time_start_real=real_start,
            time_end_real=real_end or real_start,
            timestamp_source=source,
            timestamp_policy=policy,
            is_replay_shifted=is_shifted,
            replay_shift_minutes=shift,
            technical_limits=limit,
        ))
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, manifest: Dict[str, Any], rows: List[TimestampRow]) -> None:
    counts = manifest["policy_counts"]
    lines = [
        "# T0127 — B9 Timestamp Remap Guard V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l'effort.",
        "T0127 protège l'heure du film : une scène bien lue mais mal horodatée reste techniquement fragile.",
        "",
        "## Counts",
        "",
        f"- Moments analysés : {manifest['moments_checked']}",
        f"- State : {manifest['timestamp_guard_state']}",
        f"- Shifted/replay détectés : {manifest['shifted_moment_count']}",
        f"- Real unknown : {counts.get('TIMESTAMP_REAL_UNKNOWN', 0)}",
        f"- Remap required : {counts.get('TIMESTAMP_REMAP_REQUIRED', 0)}",
        "",
        "## Politique timestamp",
        "",
        "| index | label | raw start | real start | policy | shift min | source |",
        "|---:|---|---|---|---|---:|---|",
    ]
    for r in rows:
        lines.append(f"| {r.moment_index} | {r.label_fr} | {r.time_start_raw} | {r.time_start_real} | {r.timestamp_policy} | {r.replay_shift_minutes} | {r.timestamp_source} |")
    lines += [
        "",
        "## Limites techniques",
        "",
        "- `TIMESTAMP_SHIFT_DETECTED` : lire le film avec `time_*_real`, pas avec l'heure replay brute.",
        "- `TIMESTAMP_REMAP_REQUIRED` : le fichier peut être utile analytiquement mais pas comme preuve horaire terrain.",
        "- `TIMESTAMP_REAL_UNKNOWN` : ne pas ancrer le moment dans une session sans source horaire externe.",
        "",
        "## Ce que T0127 ne conclut pas",
        "",
        "T0127 ne juge pas la direction, ne produit pas de BUY/SELL et ne calcule aucune probabilité de succès.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def zip_outputs(zip_path: Path, output_dir: Path, filenames: List[str]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in filenames:
            p = output_dir / name
            if p.exists():
                zf.write(p, arcname=name)


def run(sequence_summary_json: Path, output_dir: Path, replay_report_json: Optional[Path] = None) -> Dict[str, Any]:
    summary = load_json(sequence_summary_json)
    replay_report = load_json(replay_report_json) if replay_report_json else None
    rows = build_rows(summary, replay_report)
    row_dicts = [asdict(r) for r in rows]
    policy_counts: Dict[str, int] = {}
    for r in rows:
        policy_counts[r.timestamp_policy] = policy_counts.get(r.timestamp_policy, 0) + 1
    forbidden_hits = has_forbidden_language(summary)
    missing_required = {field: sum(1 for row in row_dicts if row.get(field) in (None, "")) for field in REQUIRED_FIELDS}
    missing_required = {k: v for k, v in missing_required.items() if v}
    hard_fail = bool(missing_required or forbidden_hits or policy_counts.get("TIMESTAMP_REAL_UNKNOWN", 0))
    soft_fail = bool(policy_counts.get("TIMESTAMP_REMAP_REQUIRED", 0))
    state = "PASS"
    if hard_fail:
        state = "FAIL"
    elif soft_fail:
        state = "PASS_WITH_REMAP_REQUIRED"
    elif policy_counts.get("TIMESTAMP_SHIFT_DETECTED", 0):
        state = "PASS_WITH_SHIFT_DETECTED"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "B9_TIMESTAMP_REMAP_GUARD_ROWS_V0.csv", row_dicts, REQUIRED_FIELDS)
    write_csv(output_dir / "B9_TIMESTAMP_REMAP_GUARD_POLICY_COUNTS_V0.csv", [{"timestamp_policy": k, "count": v} for k, v in sorted(policy_counts.items())], ["timestamp_policy", "count"])
    manifest = {
        "version": VERSION,
        "timestamp_guard_state": state,
        "input_file": str(sequence_summary_json),
        "replay_report": str(replay_report_json) if replay_report_json else "",
        "moments_checked": len(rows),
        "policy_counts": policy_counts,
        "shifted_moment_count": sum(1 for r in rows if r.is_replay_shifted),
        "missing_required_field_counts": missing_required,
        "forbidden_language_hits": forbidden_hits,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
        "output_dir": str(output_dir),
    }
    write_json(output_dir / "B9_TIMESTAMP_REMAP_GUARD_V0.json", {"manifest": manifest, "rows": row_dicts})
    write_json(output_dir / "B9_TIMESTAMP_REMAP_GUARD_MANIFEST.json", manifest)
    write_markdown(output_dir / "B9_TIMESTAMP_REMAP_GUARD_V0.md", manifest, rows)
    zip_name = "B9_TIMESTAMP_REMAP_GUARD_V0.zip"
    zip_outputs(output_dir / zip_name, output_dir, [
        "B9_TIMESTAMP_REMAP_GUARD_V0.md",
        "B9_TIMESTAMP_REMAP_GUARD_V0.json",
        "B9_TIMESTAMP_REMAP_GUARD_ROWS_V0.csv",
        "B9_TIMESTAMP_REMAP_GUARD_POLICY_COUNTS_V0.csv",
        "B9_TIMESTAMP_REMAP_GUARD_MANIFEST.json",
    ])
    manifest["zip"] = str(output_dir / zip_name)
    write_json(output_dir / "B9_TIMESTAMP_REMAP_GUARD_MANIFEST.json", manifest)
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="T0127 B9 Timestamp Remap Guard V0")
    parser.add_argument("--sequence-summary-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--replay-report-json", type=Path, default=None)
    args = parser.parse_args(argv)
    manifest = run(args.sequence_summary_json, args.output_dir, args.replay_report_json)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["timestamp_guard_state"].startswith("PASS") else 1

if __name__ == "__main__":
    raise SystemExit(main())
