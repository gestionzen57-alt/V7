#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse, csv, json
from pathlib import Path
from collections import Counter, defaultdict

def load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

def moments(data):
    if isinstance(data, dict):
        if isinstance(data.get("moments"), list):
            return data["moments"]
        if isinstance(data.get("calibrated_moments"), list):
            return data["calibrated_moments"]
    return []

def get(m, *keys, default=""):
    for k in keys:
        if k in m and m[k] is not None:
            return m[k]
    return default

def as_int(x):
    try:
        return int(float(x))
    except Exception:
        return 0

def collect(root):
    rows = []
    for p in root.rglob("*.json"):
        d = load_json(p)
        if not d:
            continue
        for i, m in enumerate(moments(d)):
            rows.append({
                "file": str(p.relative_to(root)),
                "window": p.parent.name,
                "moment_index": i,
                "moment_id": get(m, "moment_id", "id"),
                "time_start": get(m, "time_start", "proxy_time_start_mt4_approx", "start"),
                "time_end": get(m, "time_end", "proxy_time_end_mt4_approx", "end"),
                "moment_type": get(m, "moment_type", "type"),
                "label_fr": get(m, "label_fr", "label"),
                "proxy_vs_raw_verdict": get(m, "proxy_vs_raw_verdict", "verdict"),
                "raw_coverage": get(m, "raw_coverage"),
                "raw_texture_role": get(m, "raw_texture_role"),
                "progressive_wave_state": get(m, "progressive_wave_state"),
                "zero_duration_status": get(m, "zero_duration_status"),
                "raw_tick_count": as_int(get(m, "raw_tick_count", "raw_tick_count_dedup", "tick_count", default=0)),
                "raw_tick_count_raw": as_int(get(m, "raw_tick_count_raw", default=0)),
                "raw_tick_count_dedup": as_int(get(m, "raw_tick_count_dedup", default=0)),
                "raw_duplicate_count": as_int(get(m, "raw_duplicate_count", default=0)),
                "raw_duplicate_ratio": get(m, "raw_duplicate_ratio"),
                "raw_delta_pips": get(m, "raw_delta_pips"),
                "raw_range_pips": get(m, "raw_range_pips"),
            })
    return rows

def counter(rows, key):
    c = Counter()
    for r in rows:
        c[str(r.get(key) or "UNKNOWN")] += 1
    return c

def cblock(c):
    return "\n".join(f"{k}: {v}" for k, v in c.most_common()) if c else "UNKNOWN: 0"

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["file","window","moment_index","moment_id","time_start","time_end","moment_type","label_fr","proxy_vs_raw_verdict","raw_coverage","raw_texture_role","progressive_wave_state","zero_duration_status","raw_tick_count","raw_tick_count_raw","raw_tick_count_dedup","raw_duplicate_count","raw_duplicate_ratio","raw_delta_pips","raw_range_pips"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k:r.get(k,"") for k in fields})

def write_md(path, rows, symbol, broker, shift_min):
    by_day = defaultdict(int)
    for r in rows:
        s = str(r.get("time_start") or "")
        by_day[s[:10] if len(s) >= 10 else "UNKNOWN"] += 1

    lines = []
    lines += ["# T0103 — B9 Weekly Raw Calibration Results", ""]
    lines += [f"- Symbol: `{symbol}`", f"- Broker: `{broker}`", f"- Alignment: `raw_ts_mt5 + {shift_min} minutes = proxy_ts_mt4_approx`", "- Dedup: `DISTINCT ts_utc, bid, ask, mid, spread`", "- DB write: `none`", ""]
    lines += ["## Global counts", "", f"- Moments aggregated: `{len(rows)}`", f"- Raw ticks used: `{sum(as_int(r.get('raw_tick_count')) for r in rows)}`", f"- Duplicates reported: `{sum(as_int(r.get('raw_duplicate_count')) for r in rows)}`", ""]
    lines += ["## Counts by day", "", "| Day | Moments |", "|---|---:|"]
    for d, n in sorted(by_day.items()):
        lines.append(f"| {d} | {n} |")
    lines += ["", "## Verdicts", "", "```text", cblock(counter(rows, "proxy_vs_raw_verdict")), "```", ""]
    lines += ["## Raw coverage", "", "```text", cblock(counter(rows, "raw_coverage")), "```", ""]
    lines += ["## Raw texture roles", "", "```text", cblock(counter(rows, "raw_texture_role")), "```", ""]
    lines += ["## Progressive wave states", "", "```text", cblock(counter(rows, "progressive_wave_state")), "```", ""]
    lines += ["## Lab candidates snapshot", "", "| Time | Moment | Verdict | Texture | Progressive | Ticks | Note |", "|---|---|---|---|---|---:|---|"]
    kept = 0
    for r in rows:
        blob = " ".join(str(r.get(k,"")) for k in ["moment_type","label_fr","proxy_vs_raw_verdict","raw_texture_role","progressive_wave_state"]).upper()
        if any(x in blob for x in ["PROGRESSIVE","DIVERGENCE","ROTATION","FRICTION","COUNTER","SECOND","MEMORY","EXHAUSTION","LOWER","HIGH"]):
            note = "CANDIDAT_B6_LAB"
            if "DIVERGENCE" in blob: note = "PIEGE_RAW_PROXY"
            if "ROTATIONAL" in blob: note = "PROGRESSIVE_ROTATIONAL"
            lines.append(f"| {r.get('time_start','')} → {r.get('time_end','')} | `{r.get('moment_type','')}` {r.get('label_fr','')} | `{r.get('proxy_vs_raw_verdict','')}` | `{r.get('raw_texture_role','')}` | `{r.get('progressive_wave_state','')}` | {r.get('raw_tick_count',0)} | {note} |")
            kept += 1
            if kept >= 40: break
    lines += ["", "## Lab notes", "", "- [PISTE] Compare progressive waves confirmed vs rotational across the week.", "- [PISTE] Keep trap films, not only clean films.", "- [LIMIT] Raw tick is broker-relative; no central FX footprint is claimed.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--broker", default="OneFunded Capital Ltd.")
    ap.add_argument("--shift-min", type=int, default=180)
    a = ap.parse_args()
    rows = collect(Path(a.input_root))
    write_csv(Path(a.out_csv), rows)
    write_md(Path(a.out_md), rows, a.symbol, a.broker, a.shift_min)
    print(f"Wrote: {a.out_md}")
    print(f"Wrote: {a.out_csv}")
    print(f"Moments aggregated: {len(rows)}")

if __name__ == "__main__":
    main()
