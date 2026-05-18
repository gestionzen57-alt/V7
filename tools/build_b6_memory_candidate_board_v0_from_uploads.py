#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

BOARD_FIELDS = [
    "date",
    "time_start",
    "time_end",
    "source_family",
    "summary_recovery_type",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "proxy_vs_raw_verdict",
    "proxy_raw_agreement_state",
    "source_quality_score",
    "source_quality_state",
    "b6_memory_candidate_score",
    "b6_memory_candidate_state",
    "raw_texture_role",
    "raw_delta_pips",
    "raw_range_pips",
    "raw_tick_count",
    "moment_type",
    "label_fr",
    "memory_candidate_reason",
    "technical_limits",
]

KEEP = "B6_KEEP_CANDIDATE"
REVIEW = "B6_REVIEW_CANDIDATE"
LOW_TRUST = "B6_LOW_TRUST_CANDIDATE"
REJECT_RAW = "B6_REJECT_RAW_UNAVAILABLE"
RAW_UNAVAILABLE = "RAW_UNAVAILABLE"

CAP_PHRASE = (
    "B6 ne pr\u00e9dit pas.\n"
    "B6 compare des films.\n"
    "Chaque candidat m\u00e9moire garde sa provenance, son accord raw et ses limites."
)

SOURCE_QUALITY_BASE = {
    "FULL_DAY_M1_PROXY": 0.73,
    "FULL_DAY_TF5_PROXY": 0.52,
    "PARTIAL_PROXY_COVERAGE": 0.58,
    "SPARSE_PROXY_COVERAGE": 0.32,
}

@dataclass(frozen=True)
class LoadedInputPaths:
    force_csv: Path
    recovered_csv: Path
    recovered_json: Path
    force_root: Path
    recovered_root: Path


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def upper(value: Any) -> str:
    return clean(value).upper()


def to_float(value: Any) -> Optional[float]:
    s = clean(value)
    if not s:
        return None
    s = s.replace(" ", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def to_int(value: Any) -> int:
    n = to_float(value)
    if n is None:
        return 0
    return int(round(n))


def fmt_num(value: Optional[float], ndigits: int = 3) -> str:
    if value is None or math.isnan(value):
        return ""
    return f"{value:.{ndigits}f}"


def clamp(value: float, low: float = 0.0, high: float = 0.95) -> float:
    return max(low, min(high, value))


def derive_date(value: str) -> str:
    s = clean(value)
    match = re.search(r"\d{4}-\d{2}-\d{2}", s)
    if match:
        return match.group(0)
    match = re.search(r"(\d{4})(\d{2})(\d{2})", s)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return s[:10] if len(s) >= 10 else s


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError(f"CSV header missing: {path}")
        return [{clean(k): clean(v) for k, v in row.items()} for row in reader]


def write_csv_dicts(path: Path, rows: Sequence[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BOARD_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field, "")) for field in BOARD_FIELDS})


def safe_json_load(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def unzip_clean(zip_path: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)


def find_one(root: Path, filename: str) -> Path:
    matches = [p for p in root.rglob(filename) if p.is_file()]
    if not matches:
        raise FileNotFoundError(f"Missing expected file {filename} under {root}")
    matches.sort(key=lambda p: (len(str(p)), str(p)))
    return matches[0]


def prepare_inputs(force_zip: Path, recovered_zip: Path, work_dir: Path) -> LoadedInputPaths:
    if not force_zip.exists():
        raise FileNotFoundError(f"Force ZIP not found: {force_zip}")
    if not recovered_zip.exists():
        raise FileNotFoundError(f"Recovered 0605 ZIP not found: {recovered_zip}")

    force_root = work_dir / "force_snapshot"
    recovered_root = work_dir / "recovered_0605"
    unzip_clean(force_zip, force_root)
    unzip_clean(recovered_zip, recovered_root)

    force_csv = find_one(force_root, "B9_FORCE_SNAPSHOT_DERIVED_RAW_CALIBRATION_SHIFT0.csv")
    recovered_csv = find_one(recovered_root, "B9_20260506_0001_0055_SHIFT0_RAW_RESULTS.csv")
    recovered_json = find_one(recovered_root, "t009_sequence_summary_raw_calibrated.json")
    return LoadedInputPaths(
        force_csv=force_csv,
        recovered_csv=recovered_csv,
        recovered_json=recovered_json,
        force_root=force_root,
        recovered_root=recovered_root,
    )


def load_force_folder_quality(force_root: Path) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for path in force_root.rglob("t009_sequence_summary_raw_calibrated.json"):
        parent = path.parent.name
        try:
            data = safe_json_load(path)
        except Exception:
            continue
        out[parent] = {
            "source_quality_raw": clean(data.get("source_quality")),
            "confidence_cap": clean(data.get("confidence_cap")),
            "source_mode": clean(data.get("source_mode")),
            "data_visibility": clean(data.get("data_visibility")),
            "summary_recovery_type": clean(data.get("summary_recovery_type")),
        }
    return out


def raw_unavailable(row: Dict[str, str]) -> bool:
    markers = [
        row.get("proxy_vs_raw_verdict", ""),
        row.get("proxy_raw_agreement_state", ""),
        row.get("raw_coverage", ""),
        row.get("raw_texture_role", ""),
    ]
    return any("RAW_UNAVAILABLE" in upper(v) or upper(v) in {"NO_RAW", "RAW_MISSING"} for v in markers)


def derive_source_quality_score(row: Dict[str, str]) -> float:
    if raw_unavailable(row):
        return 0.0

    family = upper(row.get("source_family"))
    source_mode = upper(row.get("source_mode"))
    source_quality_raw = upper(row.get("source_quality_raw"))
    verdict = upper(row.get("proxy_vs_raw_verdict"))
    ticks = to_int(row.get("raw_tick_count"))
    texture = upper(row.get("raw_texture_role"))

    if family == "RECOVERED_EXISTING_B9_SUMMARY":
        score = 0.76
    elif family == "ORIGINAL_AVAILABLE_SUMMARY":
        score = 0.84
    else:
        score = SOURCE_QUALITY_BASE.get(source_quality_raw, 0.52)

    if source_mode == "M1_BAR_PROXY":
        score += 0.06
    elif source_mode == "TF5_BAR_PROXY":
        score -= 0.03
    elif source_mode == "TF30_BAR_PROXY":
        score -= 0.10

    if verdict == "CONFIRMED_BY_RAW":
        score += 0.14
    elif verdict == "NUANCED_BY_RAW":
        score += 0.06

    if ticks >= 1000:
        score += 0.05
    elif ticks >= 100:
        score += 0.03
    elif 0 < ticks < 100:
        score -= 0.04

    if texture and texture != RAW_UNAVAILABLE:
        score += 0.02

    if family == "FORCE_SNAPSHOT_DERIVED":
        if source_quality_raw == "SPARSE_PROXY_COVERAGE" or source_mode == "TF30_BAR_PROXY":
            score = min(score, 0.42)
        elif source_mode == "TF5_BAR_PROXY":
            score = min(score, 0.68)
        elif source_quality_raw == "PARTIAL_PROXY_COVERAGE":
            score = min(score, 0.76)
        elif source_quality_raw == "FULL_DAY_M1_PROXY":
            score = min(score, 0.88)
    elif family == "RECOVERED_EXISTING_B9_SUMMARY":
        score = min(score, 0.86)

    return round(clamp(score), 3)


def source_quality_state(score: float) -> str:
    if score <= 0.0:
        return "SOURCE_QUALITY_REJECT_RAW_UNAVAILABLE"
    if score >= 0.78:
        return "SOURCE_QUALITY_STRONG"
    if score >= 0.62:
        return "SOURCE_QUALITY_USABLE"
    if score >= 0.45:
        return "SOURCE_QUALITY_LIMITED"
    return "SOURCE_QUALITY_LOW_TRUST"


def derive_b6_score(row: Dict[str, str], source_score: float) -> float:
    if raw_unavailable(row):
        return 0.0
    score = source_score
    family = upper(row.get("source_family"))
    mode = upper(row.get("source_mode"))
    moment_type = upper(row.get("moment_type"))
    label = clean(row.get("label_fr"))
    texture = upper(row.get("raw_texture_role"))
    ticks = to_int(row.get("raw_tick_count"))
    range_pips = to_float(row.get("raw_range_pips")) or 0.0

    if any(token in texture for token in ["PROGRESS", "ROTATION", "FRICTION"]):
        score += 0.05
    if any(token in moment_type for token in ["DIRECTIONAL", "ROTATION", "ABSORPTION", "BALANCED", "PROGRESSIVE", "FRICTION", "FLOW"]):
        score += 0.04
    if ticks >= 50 and range_pips >= 1.5:
        score += 0.03
    if not label:
        score -= 0.08
    if family == "FORCE_SNAPSHOT_DERIVED" and mode == "TF30_BAR_PROXY":
        score -= 0.08
    if family == "FORCE_SNAPSHOT_DERIVED" and mode == "TF5_BAR_PROXY":
        score -= 0.03

    return round(clamp(score), 3)


def derive_candidate_state(row: Dict[str, str], source_score: float, b6_score: float) -> str:
    if raw_unavailable(row):
        return REJECT_RAW
    verdict = upper(row.get("proxy_vs_raw_verdict"))
    source_state = source_quality_state(source_score)

    if source_score < 0.45 or b6_score < 0.48:
        return LOW_TRUST
    if verdict == "CONFIRMED_BY_RAW" and b6_score >= 0.70:
        return KEEP
    if verdict == "NUANCED_BY_RAW" and b6_score >= 0.76 and source_state in {"SOURCE_QUALITY_STRONG", "SOURCE_QUALITY_USABLE"}:
        return KEEP
    if b6_score >= 0.52:
        return REVIEW
    return LOW_TRUST


def infer_recovered_moment_type(moment: Dict[str, Any]) -> str:
    for key in ["moment_type", "scene_role", "b9_natural_flow_role"]:
        value = clean(moment.get(key))
        if value:
            return value
    absorption = upper(moment.get("b9_absorption_like_state"))
    auction = upper(moment.get("b9_auction_state"))
    flow = upper(moment.get("b9_flow_intent_state"))
    texture = upper(moment.get("raw_texture_role"))
    tags = " ".join(clean(t) for t in moment.get("tags", []) if t is not None).upper()

    if "ABSORPTION_LIKE" in absorption or "FRICTION" in texture:
        return "RECOVERED_FRICTION_ABSORPTION_LIKE"
    if "MIXED" in flow or "MIXED" in auction:
        return "RECOVERED_FLOW_MIXED"
    if "PRICE_LAG" in tags:
        return "RECOVERED_PRICE_LAG_OR_ABSORPTION"
    if "FAST_UP" in tags or "FAST_DOWN" in tags:
        return "RECOVERED_FORCE_IMPULSE"
    return "RECOVERED_B9_MOMENT"


def infer_recovered_label(moment: Dict[str, Any]) -> str:
    for key in ["label_fr", "reading_fr", "b9_natural_flow_reading_fr", "b9_retest_source_reading_fr"]:
        value = clean(moment.get(key))
        if value:
            return value
    tags = moment.get("tags")
    if isinstance(tags, list) and tags:
        return "Moment B9 recupere: " + ", ".join(clean(t) for t in tags[:4])
    return "Moment B9 recupere"


def normalize_force_row(raw: Dict[str, str], folder_quality: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    source_folder = clean(raw.get("source_folder"))
    fq = folder_quality.get(source_folder, {})
    row: Dict[str, str] = {
        "date": derive_date(raw.get("time_start", "")),
        "time_start": clean(raw.get("time_start")),
        "time_end": clean(raw.get("time_end")),
        "source_family": "FORCE_SNAPSHOT_DERIVED",
        "summary_recovery_type": clean(raw.get("summary_recovery_type")) or "FORCE_SNAPSHOT_DERIVED",
        "source_mode": clean(raw.get("source_mode")) or fq.get("source_mode", ""),
        "data_visibility": clean(raw.get("data_visibility")) or fq.get("data_visibility", ""),
        "confidence_cap": clean(raw.get("confidence_cap")) or fq.get("confidence_cap", ""),
        "proxy_vs_raw_verdict": clean(raw.get("proxy_vs_raw_verdict")) or RAW_UNAVAILABLE,
        "proxy_raw_agreement_state": clean(raw.get("proxy_vs_raw_verdict")) or RAW_UNAVAILABLE,
        "source_quality_score": "",
        "source_quality_state": "",
        "b6_memory_candidate_score": "",
        "b6_memory_candidate_state": "",
        "raw_texture_role": clean(raw.get("raw_texture_role")),
        "raw_delta_pips": clean(raw.get("raw_delta_pips")),
        "raw_range_pips": clean(raw.get("raw_range_pips")),
        "raw_tick_count": clean(raw.get("raw_tick_count")),
        "moment_type": clean(raw.get("moment_type")),
        "label_fr": clean(raw.get("label_fr")),
        "memory_candidate_reason": "",
        "technical_limits": "",
        "raw_coverage": clean(raw.get("raw_coverage")),
        "source_quality_raw": fq.get("source_quality_raw", clean(raw.get("source_quality"))),
    }
    finalize_candidate(row)
    return {field: row.get(field, "") for field in BOARD_FIELDS}


def load_recovered_raw_metrics(recovered_csv: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    out: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in read_csv_dicts(recovered_csv):
        key = (clean(row.get("time_start")), clean(row.get("time_end")))
        out[key] = row
    return out


def normalize_recovered_moment(moment: Dict[str, Any], metrics: Dict[Tuple[str, str], Dict[str, str]]) -> Dict[str, str]:
    start = clean(moment.get("time_start") or moment.get("start_time"))
    end = clean(moment.get("time_end") or moment.get("end_time"))
    raw = metrics.get((start, end), {})
    row: Dict[str, str] = {
        "date": derive_date(start),
        "time_start": start,
        "time_end": end,
        "source_family": "RECOVERED_EXISTING_B9_SUMMARY",
        "summary_recovery_type": "RECOVERED_EXISTING_B9_SUMMARY",
        "source_mode": clean(moment.get("source_mode") or raw.get("source_mode") or "M1_BAR_PROXY"),
        "data_visibility": clean(moment.get("data_visibility") or raw.get("data_visibility") or "RECONSTRUCTED"),
        "confidence_cap": clean(moment.get("confidence_cap") or moment.get("b9_confidence_cap") or "0.35"),
        "proxy_vs_raw_verdict": clean(raw.get("proxy_vs_raw_verdict") or moment.get("proxy_vs_raw_verdict") or "NUANCED_BY_RAW"),
        "proxy_raw_agreement_state": clean(raw.get("proxy_vs_raw_verdict") or moment.get("proxy_vs_raw_verdict") or "NUANCED_BY_RAW"),
        "source_quality_score": "",
        "source_quality_state": "",
        "b6_memory_candidate_score": "",
        "b6_memory_candidate_state": "",
        "raw_texture_role": clean(raw.get("raw_texture_role") or moment.get("raw_texture_role")),
        "raw_delta_pips": clean(raw.get("raw_delta_pips") or moment.get("raw_delta_pips")),
        "raw_range_pips": clean(raw.get("raw_range_pips") or moment.get("raw_range_pips")),
        "raw_tick_count": clean(raw.get("raw_tick_count") or moment.get("raw_tick_count")),
        "moment_type": infer_recovered_moment_type(moment),
        "label_fr": infer_recovered_label(moment),
        "memory_candidate_reason": "",
        "technical_limits": "",
        "raw_coverage": clean(raw.get("raw_coverage") or moment.get("raw_coverage")),
        "source_quality_raw": "RECOVERED_EXISTING_B9_SUMMARY_SHIFT0_FULL_RAW_ALIGNMENT",
    }
    finalize_candidate(row)
    return {field: row.get(field, "") for field in BOARD_FIELDS}


def finalize_candidate(row: Dict[str, str]) -> None:
    score = derive_source_quality_score(row)
    b6_score = derive_b6_score(row, score)
    row["source_quality_score"] = fmt_num(score, 3)
    row["source_quality_state"] = source_quality_state(score)
    row["b6_memory_candidate_score"] = fmt_num(b6_score, 3)
    row["b6_memory_candidate_state"] = derive_candidate_state(row, score, b6_score)
    row["memory_candidate_reason"] = build_reason(row)
    row["technical_limits"] = build_limits(row)


def build_reason(row: Dict[str, str]) -> str:
    family = row.get("source_family", "")
    state = row.get("b6_memory_candidate_state", "")
    verdict = row.get("proxy_vs_raw_verdict", "")
    texture = row.get("raw_texture_role", "") or "TEXTURE_NOT_EXPLICIT"
    quality = row.get("source_quality_state", "")
    score = row.get("b6_memory_candidate_score", "")

    if state == REJECT_RAW:
        return "Rejet memoire active: raw indisponible; conservation uniquement en trace de couverture."
    if state == LOW_TRUST:
        return f"Audit seulement: provenance {family}, accord {verdict}, qualite {quality}, texture {texture}; score memoire {score}."
    if state == KEEP and verdict == "CONFIRMED_BY_RAW":
        return f"KEEP prioritaire: scene confirmee raw, texture {texture}, provenance {family}, score memoire {score}."
    if state == KEEP and verdict == "NUANCED_BY_RAW":
        return f"KEEP nuance: raw nuance la scene mais qualite/texture suffisantes pour comparaison B6; provenance {family}; score memoire {score}."
    if state == REVIEW:
        return f"REVIEW: scene lisible pour comparaison apres relecture; ne pas durcir {verdict} en verite raw; provenance {family}; score memoire {score}."
    return f"Candidat B6 qualifie read-only; provenance {family}; accord {verdict}; score memoire {score}."


def build_limits(row: Dict[str, str]) -> str:
    limits: List[str] = []
    family = upper(row.get("source_family"))
    mode = upper(row.get("source_mode"))
    visibility = upper(row.get("data_visibility"))
    verdict = upper(row.get("proxy_vs_raw_verdict"))
    source_quality_raw = clean(row.get("source_quality_raw"))

    if family == "FORCE_SNAPSHOT_DERIVED":
        limits.append("FORCE_SNAPSHOT_DERIVED: reconstruction force_snapshots_v2; not recovered existing summary")
    if family == "RECOVERED_EXISTING_B9_SUMMARY":
        limits.append("RECOVERED_EXISTING_B9_SUMMARY: recovered explicit B9 moments; shift0 raw alignment")
    if "PROXY" in mode or "RECONSTRUCTED" in visibility:
        limits.append("proxy/reconstructed reading; not full footprint claim")
    if verdict == "NUANCED_BY_RAW":
        limits.append("NUANCED_BY_RAW: useful but not hard-confirmed raw")
    if verdict == "CONFIRMED_BY_RAW":
        limits.append("CONFIRMED_BY_RAW: raw supports proxy reading")
    if raw_unavailable(row):
        limits.append("RAW_UNAVAILABLE: excluded from active B6 memory")
    if source_quality_raw:
        limits.append(f"source_quality_raw={source_quality_raw}")
    if clean(row.get("confidence_cap")):
        limits.append(f"confidence_cap={row.get('confidence_cap')}")
    limits.append("read-only; no DB write; no dashboard; no Telegram; no BUY/SELL")

    out: List[str] = []
    for item in limits:
        item = clean(item)
        if item and item not in out:
            out.append(item)
    return "; ".join(out)


def is_rejected(row: Dict[str, str]) -> bool:
    return row.get("b6_memory_candidate_state") == REJECT_RAW or raw_unavailable(row)


def bucket_rows(rows: Sequence[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    keep = [r for r in rows if not is_rejected(r) and r.get("b6_memory_candidate_state") == KEEP]
    review = [r for r in rows if not is_rejected(r) and r.get("b6_memory_candidate_state") == REVIEW]
    low = [r for r in rows if not is_rejected(r) and r.get("b6_memory_candidate_state") == LOW_TRUST]
    rejected = [r for r in rows if is_rejected(r)]
    return keep, review, low, rejected


def sort_key(row: Dict[str, str]) -> Tuple[str, str, str, str]:
    return (row.get("date", ""), row.get("time_start", ""), row.get("source_family", ""), row.get("time_end", ""))


def priority_key(row: Dict[str, str]) -> Tuple[int, float, float, int, float, str]:
    state = row.get("b6_memory_candidate_state", "")
    verdict = upper(row.get("proxy_vs_raw_verdict"))
    source_score = to_float(row.get("source_quality_score")) or 0.0
    b6_score = to_float(row.get("b6_memory_candidate_score")) or 0.0
    ticks = to_int(row.get("raw_tick_count"))
    range_pips = to_float(row.get("raw_range_pips")) or 0.0
    rank = 0
    if state == KEEP and verdict == "CONFIRMED_BY_RAW":
        rank = 500
    elif state == KEEP and verdict == "NUANCED_BY_RAW":
        rank = 420
    elif state == REVIEW and ticks > 0:
        rank = 300
    elif state == LOW_TRUST:
        rank = 100
    elif is_rejected(row):
        rank = -100
    return (rank, b6_score, source_score, ticks, range_pips, row.get("time_start", ""))


def md_escape(value: Any) -> str:
    s = clean(value)
    s = s.replace("|", "\\|")
    s = s.replace("\r\n", "<br>").replace("\n", "<br>")
    return s


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]], max_rows: Optional[int] = None) -> str:
    display = list(rows)
    total = len(display)
    if max_rows is not None:
        display = display[:max_rows]
    if not display:
        return "_Aucune ligne._\n"
    lines = ["| " + " | ".join(md_escape(h) for h in headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in display:
        lines.append("| " + " | ".join(md_escape(v) for v in row) + " |")
    if max_rows is not None and total > max_rows:
        lines.append(f"\n_Liste tronquee a {max_rows} lignes sur {total}._")
    return "\n".join(lines) + "\n"


def count_by(rows: Sequence[Dict[str, str]], field: str) -> Counter:
    return Counter(clean(r.get(field)) or "<EMPTY>" for r in rows)


def render_report(rows: Sequence[Dict[str, str]], paths: LoadedInputPaths, output_paths: Dict[str, Path]) -> str:
    keep, review, low, rejected = bucket_rows(rows)
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    lines.append("# B6 Memory Candidate Board V0")
    lines.append("")
    lines.append("## R\u00e9sum\u00e9 ex\u00e9cutif")
    lines.append("")
    lines.append(CAP_PHRASE)
    lines.append("")
    lines.append(f"Generation UTC : `{now}`")
    lines.append("")
    lines.append("Board analytique read-only construit depuis les ZIPs uploades dans `/mnt/data`. Aucun chemin Windows n'a ete lu directement.")
    lines.append("Aucune ecriture `powerflow.db` ou `tick_archive.db`. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilite de succes.")
    lines.append("")
    lines.append(md_table(["Bucket", "Count"], [
        ["Total scenes", len(rows)],
        ["KEEP", len(keep)],
        ["REVIEW", len(review)],
        ["LOW TRUST", len(low)],
        ["Rejected RAW_UNAVAILABLE", len(rejected)],
    ]))

    lines.append("## Sources et provenance")
    lines.append("")
    lines.append("Regle de verrouillage : `FORCE_SNAPSHOT_DERIVED` reste une famille reconstruite depuis force snapshots et ne doit jamais etre presentee comme `RECOVERED_EXISTING_B9_SUMMARY`.")
    lines.append("")
    lines.append(md_table(["Source", "Path extrait"], [
        ["FORCE_SNAPSHOT_DERIVED CSV", str(paths.force_csv)],
        ["0605 recovered raw CSV", str(paths.recovered_csv)],
        ["0605 recovered calibrated JSON", str(paths.recovered_json)],
    ]))
    lines.append("### Counts par source_family")
    lines.append(md_table(["source_family", "count"], count_by(rows, "source_family").most_common()))
    lines.append("### Counts par summary_recovery_type")
    lines.append(md_table(["summary_recovery_type", "count"], count_by(rows, "summary_recovery_type").most_common()))

    lines.append("## Counts globaux")
    lines.append("")
    for field in ["b6_memory_candidate_state", "proxy_vs_raw_verdict", "source_quality_state", "source_mode", "raw_texture_role"]:
        lines.append(f"### {field}")
        lines.append(md_table([field, "count"], count_by(rows, field).most_common()))

    lines.append("## Counts par date")
    lines.append("")
    by_date: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        d = r.get("date") or "<EMPTY>"
        c = by_date[d]
        c["total"] += 1
        if r.get("b6_memory_candidate_state") == KEEP:
            c["keep"] += 1
        elif r.get("b6_memory_candidate_state") == REVIEW:
            c["review"] += 1
        elif r.get("b6_memory_candidate_state") == LOW_TRUST:
            c["low_trust"] += 1
        if is_rejected(r):
            c["rejected"] += 1
        if r.get("proxy_vs_raw_verdict") == "CONFIRMED_BY_RAW":
            c["confirmed"] += 1
        if r.get("proxy_vs_raw_verdict") == "NUANCED_BY_RAW":
            c["nuanced"] += 1
        if raw_unavailable(r):
            c["raw_unavailable"] += 1
        c["raw_ticks"] += to_int(r.get("raw_tick_count"))
    lines.append(md_table(
        ["date", "total", "keep", "review", "low_trust", "rejected", "confirmed", "nuanced", "raw_unavailable", "raw_ticks"],
        [[d, by_date[d]["total"], by_date[d]["keep"], by_date[d]["review"], by_date[d]["low_trust"], by_date[d]["rejected"], by_date[d]["confirmed"], by_date[d]["nuanced"], by_date[d]["raw_unavailable"], by_date[d]["raw_ticks"]] for d in sorted(by_date)],
    ))

    def section(title: str, subset: Sequence[Dict[str, str]], max_rows: int = 35) -> None:
        lines.append(title)
        lines.append("")
        ordered = sorted(subset, key=priority_key, reverse=True)
        lines.append(md_table(
            ["date", "start", "end", "family", "agreement", "quality", "score", "texture", "ticks", "moment_type", "label_fr"],
            [[r.get("date"), r.get("time_start"), r.get("time_end"), r.get("source_family"), r.get("proxy_vs_raw_verdict"), r.get("source_quality_state"), r.get("b6_memory_candidate_score"), r.get("raw_texture_role"), r.get("raw_tick_count"), r.get("moment_type"), r.get("label_fr")] for r in ordered],
            max_rows=max_rows,
        ))

    section("## KEEP candidates", keep)
    section("## REVIEW candidates", review)
    section("## LOW TRUST candidates", low)
    section("## Rejected RAW_UNAVAILABLE", rejected)

    lines.append("## Sc\u00e8nes prioritaires pour m\u00e9moire B6")
    lines.append("")
    pool = [r for r in rows if not is_rejected(r)]
    priority_rows = sorted(pool, key=priority_key, reverse=True)[:30]
    lines.append(md_table(
        ["priority", "date", "start", "end", "state", "agreement", "quality", "score", "texture", "ticks", "moment", "label", "reason"],
        [[i + 1, r.get("date"), r.get("time_start"), r.get("time_end"), r.get("b6_memory_candidate_state"), r.get("proxy_vs_raw_verdict"), r.get("source_quality_state"), r.get("b6_memory_candidate_score"), r.get("raw_texture_role"), r.get("raw_tick_count"), r.get("moment_type"), r.get("label_fr"), r.get("memory_candidate_reason")] for i, r in enumerate(priority_rows)],
        max_rows=30,
    ))
    lines.append("Ordre applique : KEEP confirmes raw, KEEP nuances raw avec source quality forte, REVIEW avec texture lisible, LOW TRUST conserve pour audit, RAW_UNAVAILABLE rejete de la memoire active.")
    lines.append("")

    lines.append("## Limites techniques")
    lines.append("")
    limits = Counter()
    for r in rows:
        for part in r.get("technical_limits", "").split(";"):
            p = clean(part)
            if p:
                limits[p] += 1
    lines.append(md_table(["limite", "count"], limits.most_common(40)))

    lines.append("## Ce que B6 peut comparer")
    lines.append("")
    lines.append("- Films de flux par `moment_type`, `label_fr`, texture raw, range, delta, densite de ticks et provenance.")
    lines.append("- Scenes confirmees ou nuancees sans transformer une nuance raw en confirmation dure.")
    lines.append("- Familles separees : `FORCE_SNAPSHOT_DERIVED` et `RECOVERED_EXISTING_B9_SUMMARY`.")
    lines.append("- Transitions effort/resultat/progres : friction, rotation, progression, absorption-like, respiration de zone.")
    lines.append("")

    lines.append("## Ce que B6 ne doit pas conclure")
    lines.append("")
    lines.append("- Aucun ordre d'execution.")
    lines.append("- Aucune probabilite de succes.")
    lines.append("- Aucun BUY/SELL.")
    lines.append("- Aucun proxy durci en verite raw.")
    lines.append("- Aucune confusion entre `FORCE_SNAPSHOT_DERIVED` et recovered existing summary.")
    lines.append("")

    lines.append("## Prochaine brique recommand\u00e9e")
    lines.append("")
    lines.append("`B6 Film Similarity Reader V0` : indexer uniquement les KEEP/REVIEW actifs par famille, role de texture, moment_type, label_fr et voisinage temporel. Sortie : films proches + limites visibles, sans DB write et sans decision.")
    lines.append("")

    lines.append("## Commandes exactes")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 /mnt/data/build_b6_memory_candidate_board_v0_from_uploads.py \\")
    lines.append("  --force-zip /mnt/data/B9_FORCE_SNAPSHOT_DERIVED_RAW_CALIBRATION_SHIFT0.zip \\")
    lines.append("  --recovered-zip /mnt/data/B9_RAW_CALIBRATION_OUTPUTS_20260506_0001_0055_SHIFT0_RAW.zip \\")
    lines.append("  --output-dir /mnt/data/B6_MEMORY_CANDIDATE_BOARD_V0")
    lines.append("```")
    lines.append("")

    lines.append("## Fichiers produits")
    lines.append("")
    lines.append(md_table(["fichier", "path"], [[name, str(path)] for name, path in output_paths.items()]))
    return "\n".join(lines)


def build_message_claude(rows: Sequence[Dict[str, str]], output_paths: Dict[str, Path]) -> str:
    keep, review, low, rejected = bucket_rows(rows)
    by_family = count_by(rows, "source_family")
    by_verdict = count_by(rows, "proxy_vs_raw_verdict")
    return f"""# MESSAGE CLAUDE / ARCHITECTE - B6 Memory Candidate Board V0

B6 Memory Candidate Board V0 est produit depuis les ZIPs uploades, sans lecture directe des chemins Windows.

Doctrine respectee :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissee par l'effort.
B6 ne predit pas.
B6 compare des films.
```

Outputs :

```text
{output_paths['md'].name}
{output_paths['board'].name}
{output_paths['keep'].name}
{output_paths['review'].name}
{output_paths['low'].name}
{output_paths['rejected'].name}
{output_paths['zip'].name}
```

Counts :

```text
total={len(rows)}
KEEP={len(keep)}
REVIEW={len(review)}
LOW_TRUST={len(low)}
REJECTED_RAW_UNAVAILABLE={len(rejected)}
```

Sources :

```text
source_family={dict(by_family)}
proxy_vs_raw_verdict={dict(by_verdict)}
```

Notes techniques :

```text
- FORCE_SNAPSHOT_DERIVED reste separe de RECOVERED_EXISTING_B9_SUMMARY.
- RAW_UNAVAILABLE est exclu de la memoire active.
- LOW_TRUST est conserve pour audit dans un CSV separe.
- NUANCED_BY_RAW n'est jamais presente comme CONFIRMED_BY_RAW.
- Aucun powerflow.db/tick_archive.db write, aucun dashboard, aucun Telegram.
```
"""


def build_commands_md(output_dir: Path) -> str:
    return f"""# COMMANDES - B6 Memory Candidate Board V0

## Run depuis les ZIPs uploades

```bash
python3 /mnt/data/build_b6_memory_candidate_board_v0_from_uploads.py \\
  --force-zip /mnt/data/B9_FORCE_SNAPSHOT_DERIVED_RAW_CALIBRATION_SHIFT0.zip \\
  --recovered-zip /mnt/data/B9_RAW_CALIBRATION_OUTPUTS_20260506_0001_0055_SHIFT0_RAW.zip \\
  --output-dir {output_dir}
```

## Verifications rapides

```bash
python3 - <<'PY'
import csv
from collections import Counter
path = '{output_dir}/B6_MEMORY_CANDIDATE_BOARD_V0.csv'
rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
print('rows', len(rows))
print('states', Counter(r['b6_memory_candidate_state'] for r in rows))
print('families', Counter(r['source_family'] for r in rows))
print('verdicts', Counter(r['proxy_vs_raw_verdict'] for r in rows))
PY
```

## ZIP final

```bash
ls -lah {output_dir}/B6_MEMORY_CANDIDATE_BOARD_V0.zip
```
"""


def build_pack(force_zip: Path, recovered_zip: Path, output_dir: Path) -> Dict[str, Any]:
    work_dir = output_dir / "_extracted_inputs"
    paths = prepare_inputs(force_zip, recovered_zip, work_dir)
    folder_quality = load_force_folder_quality(paths.force_root)

    force_rows = [normalize_force_row(r, folder_quality) for r in read_csv_dicts(paths.force_csv)]

    recovered_data = safe_json_load(paths.recovered_json)
    recovered_metrics = load_recovered_raw_metrics(paths.recovered_csv)
    recovered_rows = [normalize_recovered_moment(m, recovered_metrics) for m in recovered_data.get("moments", [])]

    rows = sorted(force_rows + recovered_rows, key=sort_key)
    keep, review, low, rejected = bucket_rows(rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "md": output_dir / "B6_MEMORY_CANDIDATE_BOARD_V0.md",
        "board": output_dir / "B6_MEMORY_CANDIDATE_BOARD_V0.csv",
        "keep": output_dir / "B6_MEMORY_CANDIDATE_KEEP.csv",
        "review": output_dir / "B6_MEMORY_CANDIDATE_REVIEW.csv",
        "low": output_dir / "B6_MEMORY_CANDIDATE_LOW_TRUST.csv",
        "rejected": output_dir / "B6_MEMORY_REJECTED_RAW_UNAVAILABLE.csv",
        "commands": output_dir / "COMMANDES_B6_MEMORY_CANDIDATE_BOARD_V0.md",
        "message": output_dir / "MESSAGE_CLAUDE_B6_MEMORY_CANDIDATE_BOARD_V0_FINAL.md",
        "script": output_dir / "build_b6_memory_candidate_board_v0_from_uploads.py",
        "zip": output_dir / "B6_MEMORY_CANDIDATE_BOARD_V0.zip",
    }

    write_csv_dicts(output_paths["board"], rows)
    write_csv_dicts(output_paths["keep"], sorted(keep, key=sort_key))
    write_csv_dicts(output_paths["review"], sorted(review, key=sort_key))
    write_csv_dicts(output_paths["low"], sorted(low, key=sort_key))
    write_csv_dicts(output_paths["rejected"], sorted(rejected, key=sort_key))

    output_paths["md"].write_text(render_report(rows, paths, output_paths), encoding="utf-8")
    output_paths["commands"].write_text(build_commands_md(output_dir), encoding="utf-8")
    output_paths["message"].write_text(build_message_claude(rows, output_paths), encoding="utf-8")
    shutil.copyfile(Path(__file__).resolve(), output_paths["script"])

    with zipfile.ZipFile(output_paths["zip"], "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for key in ["md", "board", "keep", "review", "low", "rejected", "commands", "message", "script"]:
            zf.write(output_paths[key], arcname=output_paths[key].name)

    return {
        "counts": {
            "total": len(rows),
            "keep": len(keep),
            "review": len(review),
            "low_trust": len(low),
            "rejected_raw_unavailable": len(rejected),
        },
        "source_family": dict(count_by(rows, "source_family")),
        "proxy_vs_raw_verdict": dict(count_by(rows, "proxy_vs_raw_verdict")),
        "output_paths": {key: str(value) for key, value in output_paths.items()},
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build B6 Memory Candidate Board V0 from uploaded ZIP packs.")
    parser.add_argument("--force-zip", type=Path, default=Path("/mnt/data/B9_FORCE_SNAPSHOT_DERIVED_RAW_CALIBRATION_SHIFT0.zip"))
    parser.add_argument("--recovered-zip", type=Path, default=Path("/mnt/data/B9_RAW_CALIBRATION_OUTPUTS_20260506_0001_0055_SHIFT0_RAW.zip"))
    parser.add_argument("--output-dir", type=Path, default=Path("/mnt/data/B6_MEMORY_CANDIDATE_BOARD_V0"))
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        summary = build_pack(args.force_zip, args.recovered_zip, args.output_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
