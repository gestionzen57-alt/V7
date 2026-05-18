#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T0103C weekly CSV provenance propagation hotfix.

Reads calibrated B9 JSON outputs and propagates provenance fields into the
weekly aggregate CSV/MD.

This tool is read-only with respect to DBs. It only updates report artifacts
under an output folder.

Required propagated fields:
- summary_recovery_type
- source_mode
- data_visibility
- confidence_cap
- source_table
- source_timeframe
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


PROVENANCE_FIELDS = [
    "summary_recovery_type",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "source_table",
    "source_timeframe",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if value == "":
            continue
        return value
    return None


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def get_nested(d: Mapping[str, Any], *keys: str) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur


def normalize_time(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("+00:00", "Z")


def scalarize(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def root_provenance(payload: Mapping[str, Any]) -> dict:
    summary_meta = as_dict(payload.get("summary_metadata"))
    source_profile = as_dict(payload.get("source_profile"))
    force_meta = as_dict(payload.get("force_snapshot_source"))
    raw_cal = as_dict(payload.get("raw_calibration"))

    return {
        "summary_recovery_type": first_non_empty(
            payload.get("summary_recovery_type"),
            summary_meta.get("summary_recovery_type"),
            source_profile.get("summary_recovery_type"),
            force_meta.get("summary_recovery_type"),
            raw_cal.get("summary_recovery_type"),
        ),
        "source_mode": first_non_empty(
            payload.get("source_mode"),
            summary_meta.get("source_mode"),
            source_profile.get("source_mode"),
            force_meta.get("source_mode"),
            raw_cal.get("source_mode"),
        ),
        "data_visibility": first_non_empty(
            payload.get("data_visibility"),
            summary_meta.get("data_visibility"),
            source_profile.get("data_visibility"),
            force_meta.get("data_visibility"),
            raw_cal.get("data_visibility"),
        ),
        "confidence_cap": first_non_empty(
            payload.get("confidence_cap"),
            summary_meta.get("confidence_cap"),
            source_profile.get("confidence_cap"),
            force_meta.get("confidence_cap"),
            raw_cal.get("confidence_cap"),
        ),
        "source_table": first_non_empty(
            payload.get("source_table"),
            summary_meta.get("source_table"),
            source_profile.get("source_table"),
            force_meta.get("source_table"),
            raw_cal.get("source_table"),
        ),
        "source_timeframe": first_non_empty(
            payload.get("source_timeframe"),
            payload.get("timeframe"),
            summary_meta.get("source_timeframe"),
            summary_meta.get("timeframe"),
            source_profile.get("source_timeframe"),
            source_profile.get("timeframe"),
            force_meta.get("source_timeframe"),
            force_meta.get("timeframe"),
            raw_cal.get("source_timeframe"),
            raw_cal.get("timeframe"),
        ),
    }


def moment_provenance(payload: Mapping[str, Any], moment: Mapping[str, Any]) -> dict:
    root = root_provenance(payload)
    sp = as_dict(moment.get("source_profile"))
    zm = as_dict(moment.get("zone_memory"))
    zm_sp = as_dict(zm.get("source_profile"))

    return {
        "summary_recovery_type": first_non_empty(
            moment.get("summary_recovery_type"),
            sp.get("summary_recovery_type"),
            zm.get("summary_recovery_type"),
            root.get("summary_recovery_type"),
        ),
        "source_mode": first_non_empty(
            moment.get("source_mode"),
            sp.get("source_mode"),
            zm.get("source_mode"),
            zm_sp.get("source_mode"),
            root.get("source_mode"),
        ),
        "data_visibility": first_non_empty(
            moment.get("data_visibility"),
            sp.get("data_visibility"),
            zm.get("data_visibility"),
            zm_sp.get("data_visibility"),
            root.get("data_visibility"),
        ),
        "confidence_cap": first_non_empty(
            moment.get("confidence_cap"),
            sp.get("confidence_cap"),
            zm.get("confidence_cap"),
            zm_sp.get("confidence_cap"),
            root.get("confidence_cap"),
        ),
        "source_table": first_non_empty(
            moment.get("source_table"),
            sp.get("source_table"),
            zm.get("source_table"),
            zm_sp.get("source_table"),
            root.get("source_table"),
        ),
        "source_timeframe": first_non_empty(
            moment.get("source_timeframe"),
            moment.get("timeframe"),
            sp.get("source_timeframe"),
            sp.get("timeframe"),
            zm.get("source_timeframe"),
            zm.get("timeframe"),
            zm_sp.get("source_timeframe"),
            zm_sp.get("timeframe"),
            root.get("source_timeframe"),
        ),
    }


def json_moment_rows(output_root: Path) -> list[dict]:
    rows: list[dict] = []
    for json_path in sorted(output_root.rglob("t009_sequence_summary_raw_calibrated.json")):
        payload = load_json(json_path)
        moments = payload.get("moments", [])
        if not isinstance(moments, list):
            continue

        for idx, moment in enumerate(moments):
            if not isinstance(moment, Mapping):
                continue
            prov = moment_provenance(payload, moment)
            row = {
                "_json_file": str(json_path),
                "_json_parent": json_path.parent.name,
                "_moment_index": str(idx),
                "time_start": normalize_time(moment.get("time_start")),
                "time_end": normalize_time(moment.get("time_end")),
                "moment_type": str(moment.get("moment_type") or ""),
                "label_fr": str(moment.get("label_fr") or ""),
                "moment_id": str(moment.get("moment_id") or ""),
            }
            row.update({k: scalarize(v) for k, v in prov.items()})
            rows.append(row)
    return rows


def lookup_keys(row: Mapping[str, Any]) -> list[Tuple[str, ...]]:
    ts = normalize_time(row.get("time_start"))
    te = normalize_time(row.get("time_end"))
    mt = str(row.get("moment_type") or "")
    label = str(row.get("label_fr") or "")
    mid = str(row.get("moment_id") or "")
    parent = str(row.get("_json_parent") or row.get("window") or "")
    idx = str(row.get("_moment_index") or row.get("moment_index") or "")

    keys: list[Tuple[str, ...]] = []
    if mid:
        keys.append(("moment_id", mid))
    if ts or te or mt or label:
        keys.append(("signature", ts, te, mt, label))
    if parent and idx:
        keys.append(("parent_index", parent, idx))
    if ts or te or mt:
        keys.append(("time_type", ts, te, mt))
    return keys


def build_lookup(json_rows: list[dict]) -> dict[Tuple[str, ...], dict]:
    lookup: dict[Tuple[str, ...], dict] = {}
    for row in json_rows:
        for key in lookup_keys(row):
            # Keep first occurrence; duplicate scene copies should share provenance anyway.
            lookup.setdefault(key, row)
    return lookup


def find_weekly_csv(output_root: Path, explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    candidates = sorted(output_root.glob("B9_WEEK_CALIBRATION_RESULTS_*.csv"))
    if candidates:
        return candidates[0]
    candidates = sorted(output_root.rglob("B9_WEEK_CALIBRATION_RESULTS_*.csv"))
    return candidates[0] if candidates else None


def find_weekly_md(output_root: Path, explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    candidates = sorted(output_root.glob("B9_WEEK_CALIBRATION_RESULTS_*.md"))
    if candidates:
        return candidates[0]
    candidates = sorted(output_root.rglob("B9_WEEK_CALIBRATION_RESULTS_*.md"))
    return candidates[0] if candidates else None


def read_csv_rows(csv_path: Path) -> tuple[list[dict], list[str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


def write_csv_rows(csv_path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    for field in PROVENANCE_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def update_or_create_csv(output_root: Path, csv_path: Optional[Path], json_rows: list[dict]) -> Path:
    lookup = build_lookup(json_rows)

    if csv_path and csv_path.exists():
        rows, fieldnames = read_csv_rows(csv_path)
        matched = 0
        for row in rows:
            source = None
            for key in lookup_keys(row):
                if key in lookup:
                    source = lookup[key]
                    break
            if source:
                matched += 1
                for field in PROVENANCE_FIELDS:
                    row[field] = source.get(field) or row.get(field) or ""
            else:
                for field in PROVENANCE_FIELDS:
                    row.setdefault(field, "")
        write_csv_rows(csv_path, rows, fieldnames)
        return csv_path

    # Create a provenance-first aggregate if no CSV exists.
    new_path = output_root / "B9_WEEK_CALIBRATION_RESULTS_T0103C_PROVENANCE.csv"
    fieldnames = [
        "_json_parent",
        "_moment_index",
        "time_start",
        "time_end",
        "moment_type",
        "label_fr",
        "moment_id",
    ] + PROVENANCE_FIELDS
    write_csv_rows(new_path, json_rows, fieldnames)
    return new_path


def provenance_summary(json_rows: list[dict]) -> list[dict]:
    counter: Counter[Tuple[str, str, str, str, str, str]] = Counter()
    for row in json_rows:
        key = tuple(str(row.get(field) or "") for field in PROVENANCE_FIELDS)
        counter[key] += 1

    result = []
    for key, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
        item = {field: key[idx] for idx, field in enumerate(PROVENANCE_FIELDS)}
        item["moments"] = count
        result.append(item)
    return result


def md_table(rows: list[dict], fields: list[str]) -> str:
    if not rows:
        return "_Aucun élément._"
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        vals = []
        for field in fields:
            value = str(row.get(field, ""))
            value = value.replace("\n", " ").replace("|", "\\|")
            vals.append(value)
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def update_md(md_path: Optional[Path], output_root: Path, json_rows: list[dict], csv_path: Path) -> Path:
    if md_path and md_path.exists():
        text = md_path.read_text(encoding="utf-8")
    else:
        md_path = output_root / "B9_WEEK_CALIBRATION_RESULTS_T0103C_PROVENANCE.md"
        text = "# B9 Weekly Calibration Results\n\n"

    marker_start = "<!-- T0103C_PROVENANCE_START -->"
    marker_end = "<!-- T0103C_PROVENANCE_END -->"

    summary = provenance_summary(json_rows)
    fields = PROVENANCE_FIELDS + ["moments"]

    block = f"""
{marker_start}
## T0103C — Provenance propagated to weekly aggregate

```text
status = T0103C_WEEKLY_CSV_PROVENANCE_PROPAGATED
csv = {csv_path}
json_moments_scanned = {len(json_rows)}
```

{md_table(summary, fields)}

### Communication rule

`FORCE_SNAPSHOT_DERIVED` rows must never be presented as recovered existing B9 summaries.
They are source-aware proxy-derived scenes from `force_snapshots_v2`, then calibrated against raw MT5.

{marker_end}
""".strip() + "\n"

    if marker_start in text and marker_end in text:
        before = text.split(marker_start)[0].rstrip()
        after = text.split(marker_end, 1)[1].lstrip()
        text = before + "\n\n" + block + "\n" + after
    else:
        text = text.rstrip() + "\n\n" + block

    md_path.write_text(text, encoding="utf-8")
    return md_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="T0103C propagate provenance into weekly CSV/MD")
    parser.add_argument("--output-root", required=True, help="Folder containing t009_sequence_summary_raw_calibrated.json outputs")
    parser.add_argument("--csv", default=None, help="Optional aggregate CSV path")
    parser.add_argument("--md", default=None, help="Optional aggregate MD path")
    args = parser.parse_args(argv)

    output_root = Path(args.output_root)
    if not output_root.exists():
        raise FileNotFoundError(output_root)

    json_rows = json_moment_rows(output_root)
    if not json_rows:
        raise RuntimeError(f"No t009_sequence_summary_raw_calibrated.json moments found under {output_root}")

    csv_path = update_or_create_csv(output_root, find_weekly_csv(output_root, args.csv), json_rows)
    md_path = update_md(find_weekly_md(output_root, args.md), output_root, json_rows, csv_path)

    print("T0103C provenance propagation complete")
    print(f"Output root : {output_root}")
    print(f"JSON moments: {len(json_rows)}")
    print(f"CSV        : {csv_path}")
    print(f"MD         : {md_path}")

    for item in provenance_summary(json_rows):
        print(
            "PROVENANCE",
            item.get("summary_recovery_type", ""),
            item.get("source_mode", ""),
            item.get("data_visibility", ""),
            item.get("confidence_cap", ""),
            item.get("source_table", ""),
            item.get("source_timeframe", ""),
            item.get("moments", 0),
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
