#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T0112 B9 Proxy/Raw Agreement & Source Quality Score.

Purpose:
- Keep provenance explicit.
- Score agreement between proxy-derived scenes and raw MT5 calibration.
- Penalize RAW_UNAVAILABLE and coarse fallback source timeframes.
- Surface B6 memory candidates without producing trade signals.

This tool only updates output artifacts under an output folder.
It does not read or write powerflow.db / tick_archive.db.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Optional


T0112_VERSION = "T0112_PROXY_RAW_AGREEMENT_SOURCE_QUALITY_V0"

T0112_FIELDS = [
    "t0112_proxy_raw_version",
    "proxy_raw_agreement_state",
    "proxy_raw_agreement_score",
    "source_quality_score",
    "source_quality_state",
    "raw_unavailable_penalty",
    "source_timeframe_penalty",
    "b6_memory_candidate_score",
    "b6_memory_candidate_state",
    "t0112_reason_flags",
]


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None or value == "":
            continue
        return value
    return None


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def normalize_source_mode(row: Mapping[str, Any]) -> str:
    sp = as_dict(row.get("source_profile"))
    zm = as_dict(row.get("zone_memory"))
    zm_sp = as_dict(zm.get("source_profile"))
    return str(first_non_empty(
        row.get("source_mode"),
        sp.get("source_mode"),
        zm.get("source_mode"),
        zm_sp.get("source_mode"),
        "UNKNOWN_SOURCE_MODE",
    ))


def normalize_confidence_cap(row: Mapping[str, Any], source_mode: str) -> float:
    sp = as_dict(row.get("source_profile"))
    zm = as_dict(row.get("zone_memory"))
    zm_sp = as_dict(zm.get("source_profile"))
    raw = first_non_empty(
        row.get("confidence_cap"),
        row.get("b9_confidence_cap"),
        sp.get("confidence_cap"),
        zm.get("confidence_cap"),
        zm_sp.get("confidence_cap"),
    )
    if raw not in (None, ""):
        return as_float(raw, 0.25)
    if source_mode == "M1_BAR_PROXY":
        return 0.35
    if source_mode.startswith("TF"):
        return 0.25
    if row.get("summary_recovery_type") == "RECOVERED_EXISTING_B9_SUMMARY":
        return 0.50
    return 0.35


def source_timeframe_from_mode(source_mode: str, row: Mapping[str, Any]) -> int:
    if row.get("source_timeframe") not in (None, ""):
        return as_int(row.get("source_timeframe"), 0)
    if source_mode == "M1_BAR_PROXY":
        return 1
    if source_mode.startswith("TF") and "_BAR_PROXY" in source_mode:
        text = source_mode.replace("TF", "").replace("_BAR_PROXY", "")
        return as_int(text, 0)
    return 0


def agreement_state(row: Mapping[str, Any]) -> str:
    verdict = str(row.get("proxy_vs_raw_verdict") or "")
    texture = str(row.get("raw_texture_role") or "")
    coverage = str(row.get("raw_coverage") or "")
    moment_type = str(row.get("moment_type") or "")

    if verdict == "RAW_UNAVAILABLE" or coverage == "RAW_UNAVAILABLE" or texture == "RAW_UNAVAILABLE":
        return "PROXY_RAW_UNAVAILABLE"
    if verdict == "CONFIRMED_BY_RAW":
        if texture == "RAW_PROGRESS_CONFIRMED":
            return "PROXY_RAW_CONFIRMED_PROGRESS"
        if texture == "RAW_ROTATION_CONFIRMED":
            return "PROXY_RAW_CONFIRMED_ROTATION"
        if texture == "RAW_FRICTION_CONFIRMED":
            return "PROXY_RAW_CONFIRMED_FRICTION"
        return "PROXY_RAW_CONFIRMED"
    if verdict == "NUANCED_BY_RAW":
        if texture == "RAW_ROTATION_CONFIRMED" and "DIRECTIONAL" in moment_type:
            return "PROXY_DIRECTIONAL_NUANCED_BY_RAW_ROTATION"
        if texture == "RAW_ROTATION_CONFIRMED":
            return "PROXY_RAW_NUANCED_ROTATION"
        if texture == "RAW_FRICTION_CONFIRMED":
            return "PROXY_RAW_NUANCED_FRICTION"
        if texture == "RAW_PROGRESS_CONFIRMED":
            return "PROXY_RAW_NUANCED_PROGRESS"
        return "PROXY_RAW_NUANCED"
    return "PROXY_RAW_UNKNOWN"


def agreement_score(state: str) -> float:
    scores = {
        "PROXY_RAW_CONFIRMED_PROGRESS": 0.90,
        "PROXY_RAW_CONFIRMED_ROTATION": 0.82,
        "PROXY_RAW_CONFIRMED_FRICTION": 0.78,
        "PROXY_RAW_CONFIRMED": 0.80,
        "PROXY_RAW_NUANCED_PROGRESS": 0.68,
        "PROXY_RAW_NUANCED_ROTATION": 0.58,
        "PROXY_DIRECTIONAL_NUANCED_BY_RAW_ROTATION": 0.48,
        "PROXY_RAW_NUANCED_FRICTION": 0.54,
        "PROXY_RAW_NUANCED": 0.55,
        "PROXY_RAW_UNAVAILABLE": 0.05,
        "PROXY_RAW_UNKNOWN": 0.30,
    }
    return scores.get(state, 0.30)


def timeframe_penalty(source_mode: str, source_timeframe: int) -> float:
    if source_mode == "M1_BAR_PROXY" or source_timeframe == 1:
        return 0.0
    if source_timeframe <= 0:
        return 0.10
    if source_timeframe <= 5:
        return 0.08
    if source_timeframe <= 15:
        return 0.12
    if source_timeframe <= 30:
        return 0.18
    return 0.22


def raw_penalty(row: Mapping[str, Any]) -> float:
    if str(row.get("proxy_vs_raw_verdict") or "") == "RAW_UNAVAILABLE":
        return 0.45
    if str(row.get("raw_coverage") or "") == "RAW_UNAVAILABLE":
        return 0.45
    if as_int(row.get("raw_tick_count"), 0) <= 0:
        return 0.35
    if as_int(row.get("raw_tick_count"), 0) < 20:
        return 0.12
    return 0.0


def reason_flags(row: Mapping[str, Any], state: str, source_mode: str, source_timeframe: int) -> list[str]:
    flags: list[str] = []
    if state == "PROXY_RAW_UNAVAILABLE":
        flags.append("RAW_UNAVAILABLE")
    if source_mode != "M1_BAR_PROXY":
        flags.append("SOURCE_TIMEFRAME_FALLBACK")
    if source_timeframe > 5:
        flags.append("COARSE_PROXY_TIMEFRAME")
    if "NUANCED" in state:
        flags.append("RAW_NUANCED_PROXY")
    if state == "PROXY_DIRECTIONAL_NUANCED_BY_RAW_ROTATION":
        flags.append("DIRECTIONAL_PROXY_ROTATIONAL_RAW")
    if str(row.get("retest_outcome_hint") or "") == "RETEST_OUTCOME_NOT_VISIBLE":
        flags.append("RETEST_SOURCE_NOT_VISIBLE")
    if str(row.get("summary_recovery_type") or "") == "FORCE_SNAPSHOT_DERIVED":
        flags.append("FORCE_SNAPSHOT_DERIVED_SOURCE")
    return flags


def source_quality_state(score: float, state: str) -> str:
    if state == "PROXY_RAW_UNAVAILABLE":
        return "SOURCE_QUALITY_RAW_MISSING"
    if score >= 0.72:
        return "SOURCE_QUALITY_STRONG_FOR_PROXY"
    if score >= 0.50:
        return "SOURCE_QUALITY_USABLE_WITH_LIMITS"
    if score >= 0.30:
        return "SOURCE_QUALITY_WEAK_REVIEW"
    return "SOURCE_QUALITY_LOW"


def b6_candidate_state(score: float, state: str) -> str:
    if state == "PROXY_RAW_UNAVAILABLE":
        return "B6_REJECT_RAW_UNAVAILABLE"
    if score >= 0.72:
        return "B6_KEEP_CANDIDATE"
    if score >= 0.52:
        return "B6_REVIEW_CANDIDATE"
    if score >= 0.35:
        return "B6_LOW_TRUST_CANDIDATE"
    return "B6_REJECT_LOW_TRUST"


def compute_t0112(row: Mapping[str, Any]) -> dict[str, Any]:
    source_mode = normalize_source_mode(row)
    source_timeframe = source_timeframe_from_mode(source_mode, row)
    cap = normalize_confidence_cap(row, source_mode)
    state = agreement_state(row)
    agree = agreement_score(state)
    raw_p = raw_penalty(row)
    tf_p = timeframe_penalty(source_mode, source_timeframe)

    # Source quality is intentionally capped by upstream confidence_cap.
    raw_bonus = 0.12 if str(row.get("raw_coverage") or "") == "FULL" and as_int(row.get("raw_tick_count"), 0) > 0 else 0.0
    quality = clamp((cap + raw_bonus + agree * 0.45) - raw_p - tf_p)

    # B6 memory score gives weight to readable texture and range, but remains capped by source quality.
    raw_range = as_float(row.get("raw_range_pips"), 0.0)
    range_bonus = clamp(raw_range / 35.0, 0.0, 0.18)
    texture_bonus = 0.0
    texture = str(row.get("raw_texture_role") or "")
    if texture == "RAW_PROGRESS_CONFIRMED":
        texture_bonus = 0.08
    elif texture == "RAW_ROTATION_CONFIRMED":
        texture_bonus = 0.06
    elif texture == "RAW_FRICTION_CONFIRMED":
        texture_bonus = 0.06
    b6 = clamp(quality * 0.75 + agree * 0.15 + range_bonus + texture_bonus - raw_p * 0.35)

    flags = reason_flags(row, state, source_mode, source_timeframe)

    return {
        "t0112_proxy_raw_version": T0112_VERSION,
        "proxy_raw_agreement_state": state,
        "proxy_raw_agreement_score": round(agree, 4),
        "source_quality_score": round(quality, 4),
        "source_quality_state": source_quality_state(quality, state),
        "raw_unavailable_penalty": round(raw_p, 4),
        "source_timeframe_penalty": round(tf_p, 4),
        "b6_memory_candidate_score": round(b6, 4),
        "b6_memory_candidate_state": b6_candidate_state(b6, state),
        "t0112_reason_flags": "|".join(flags),
    }


def iter_json_files(output_root: Path) -> list[Path]:
    return sorted(output_root.rglob("t009_sequence_summary_raw_calibrated.json"))


def update_json_file(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    moments = payload.get("moments", [])
    if not isinstance(moments, list):
        return 0

    changed = 0
    root_meta = {
        "summary_recovery_type": payload.get("summary_recovery_type"),
        "source_mode": payload.get("source_mode"),
        "data_visibility": payload.get("data_visibility"),
        "confidence_cap": payload.get("confidence_cap"),
        "source_table": payload.get("source_table"),
        "source_timeframe": payload.get("source_timeframe"),
    }

    for m in moments:
        if not isinstance(m, dict):
            continue
        row = dict(root_meta)
        row.update(m)
        score = compute_t0112(row)
        m.update(score)
        changed += 1

    payload.setdefault("t0112_proxy_raw_agreement", {})
    payload["t0112_proxy_raw_agreement"].update({
        "version": T0112_VERSION,
        "fields": T0112_FIELDS,
        "policy": "source-aware proxy/raw agreement score; not a trading signal",
        "limits": [
            "FORCE_SNAPSHOT_DERIVED remains proxy-derived",
            "RAW_UNAVAILABLE is not raw evidence",
            "source_quality_score is bounded by source provenance",
            "no BUY/SELL language",
        ],
    })

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def find_csvs(output_root: Path) -> list[Path]:
    return sorted([
        p for p in output_root.glob("*.csv")
        if "CALIBRATION" in p.name.upper() or "RESULT" in p.name.upper()
    ])


def update_csv(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    for field in T0112_FIELDS:
        if field not in fields:
            fields.append(field)

    for row in rows:
        score = compute_t0112(row)
        row.update({k: str(v) for k, v in score.items()})

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "_Aucun élément._"
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        vals = []
        for field in fields:
            val = str(row.get(field, ""))
            val = val.replace("|", "\\|").replace("\n", " ")
            vals.append(val)
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def csv_summary_rows(csv_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    state_counter: Counter[str] = Counter(row.get("proxy_raw_agreement_state", "") for row in rows)
    quality_counter: Counter[str] = Counter(row.get("source_quality_state", "") for row in rows)
    b6_counter: Counter[str] = Counter(row.get("b6_memory_candidate_state", "") for row in rows)

    state_rows = [{"state": k, "moments": v} for k, v in sorted(state_counter.items(), key=lambda x: (-x[1], x[0]))]
    quality_rows = [{"state": k, "moments": v} for k, v in sorted(quality_counter.items(), key=lambda x: (-x[1], x[0]))]
    b6_rows = [{"state": k, "moments": v} for k, v in sorted(b6_counter.items(), key=lambda x: (-x[1], x[0]))]

    return state_rows, quality_rows + b6_rows


def update_md(output_root: Path, csv_paths: list[Path]) -> Path:
    md_paths = sorted(output_root.glob("*.md"))
    target = md_paths[0] if md_paths else output_root / "T0112_PROXY_RAW_AGREEMENT_SOURCE_QUALITY.md"
    text = target.read_text(encoding="utf-8") if target.exists() else "# B9 Calibration Results\n\n"

    marker_start = "<!-- T0112_PROXY_RAW_AGREEMENT_START -->"
    marker_end = "<!-- T0112_PROXY_RAW_AGREEMENT_END -->"

    blocks = []
    for csv_path in csv_paths:
        state_rows, quality_rows = csv_summary_rows(csv_path)
        blocks.append(
            f"### CSV `{csv_path.name}`\n\n"
            "#### Proxy/raw agreement states\n\n"
            + md_table(state_rows, ["state", "moments"])
            + "\n\n#### Source quality / B6 states\n\n"
            + md_table(quality_rows, ["state", "moments"])
        )

    block = f"""
{marker_start}
## T0112 — Proxy/Raw Agreement & Source Quality Score

```text
version = {T0112_VERSION}
policy = source-aware proxy/raw agreement score; not a trading signal
```

{chr(10).join(blocks)}

### Communication rule

`FORCE_SNAPSHOT_DERIVED` remains a proxy-derived source from `force_snapshots_v2`.
`RAW_UNAVAILABLE` is not raw evidence.
B6 candidates are review candidates, not trading signals.

{marker_end}
""".strip() + "\n"

    if marker_start in text and marker_end in text:
        before = text.split(marker_start)[0].rstrip()
        after = text.split(marker_end, 1)[1].lstrip()
        text = before + "\n\n" + block + "\n" + after
    else:
        text = text.rstrip() + "\n\n" + block

    target.write_text(text, encoding="utf-8")
    return target


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Apply T0112 proxy/raw agreement & source quality score")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--csv-only", action="store_true")
    args = parser.parse_args(argv)

    output_root = Path(args.output_root)
    if not output_root.exists():
        raise FileNotFoundError(output_root)

    json_count = 0
    moment_count = 0
    if not args.csv_only:
        for path in iter_json_files(output_root):
            moment_count += update_json_file(path)
            json_count += 1

    csv_paths = []
    csv_rows = 0
    if not args.json_only:
        for path in find_csvs(output_root):
            csv_rows += update_csv(path)
            csv_paths.append(path)
        if csv_paths:
            md_path = update_md(output_root, csv_paths)
        else:
            md_path = None
    else:
        md_path = None

    print("T0112 proxy/raw agreement complete")
    print(f"Output root : {output_root}")
    print(f"JSON files  : {json_count}")
    print(f"JSON moments: {moment_count}")
    print(f"CSV files   : {len(csv_paths)}")
    print(f"CSV rows    : {csv_rows}")
    if md_path:
        print(f"MD          : {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
