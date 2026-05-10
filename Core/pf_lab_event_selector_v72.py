#!/usr/bin/env python3
"""
PowerFlow V7.2 — Lab Event Selector V0.2

Purpose
-------
Condense Lab Engine V7.2 V0.1 outputs without censoring them.

It reads an existing lab run directory:

    output/lab_runs/<run_id>/

and creates a readable layer:

    key_events.json
    key_events.csv
    key_scene_clusters.json
    events_index_full.json
    film_key_events.md
    lab_report_key_events.html
    event_selector_metrics.json

Doctrine
--------
- Does not modify the V0.1 full replay.
- Does not delete any event.
- Does not filter market alerts.
- Does not write DB.
- Does not produce BUY/SELL.
- Selection is readability-only: every original event remains indexed.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


VERSION = "LabEventSelectorV72.0.2"
METHOD = "lab_v72_key_event_selector_non_blocking"


IMPORTANT_SCENES = {
    "ZONE_BREATH_COMPRESSION",
    "FIRST_DETACHMENT_MICRO",
    "PULLBACK_ABSORBED",
    "COUNTER_BREATH",
    "SECOND_LEG_BIRTH",
    "PRICE_LAG_CATCH_UP",
    "LEADER_FOLLOWER_IMBALANCE",
    "REPULSION_CLEAN",
    "NODE_BIRTH",
    "SPREAD_FRICTION_FIELD",
}

IMPORTANT_COMPRESSION = {
    "COMPRESSION_REAL_CANDIDATE",
    "COMPRESSION_FAKE_RISK",
    "COMPRESSION_AMBIGUOUS",
}

IMPORTANT_FOOTPRINTS = {
    "STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE",
    "ABSORPTION_FOOTPRINT_CANDIDATE",
    "CLEAN_REPULSION_FOOTPRINT_CANDIDATE",
    "DELAYED_CATCH_UP_FOOTPRINT_CANDIDATE",
    "ZONE_DEFENSE_FOOTPRINT_CANDIDATE",
    "LEADER_ACCUMULATION_FOOTPRINT_CANDIDATE",
    "RELATIONAL_PRESSURE_FOOTPRINT_CANDIDATE",
}

IMPORTANT_OUTCOMES = {
    "RELEASE_CONFIRMED",
    "DELAYED_RELEASE",
    "REJECTION",
    "SECOND_LEG_CONFIRMED",
    "NO_FOLLOW_THROUGH",
}

HIGH_VALUE_RISKS = {
    "B4_COMPRESSING_WITH_B3_NOISE_HIGH",
    "B4_COMPRESSING_WITHOUT_EIE",
    "B4_COMPRESSING_WITH_B5_NEUTRAL",
    "B4_COMPRESSING_WITHOUT_HTF_COMPRESSION",
    "B4_FALSE_POSITIVE",
    "B3_NOISE_HIGH",
    "REVERSAL_CONFUSION",
    "COUNTER_MOVE_TOO_STRONG",
    "PRICE_STILL_LAGGING",
    "PULLBACK_TOO_SHORT",
    "ZONE_CONTEXT_MISSING",
    "LEADER_UNCLEAR",
    "FOLLOWER_NOISE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get(obj: Dict[str, Any], path: Sequence[str], default: Any = None) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def latest_lab_run(root: Path) -> Path:
    lab_root = root / "output" / "lab_runs"
    if not lab_root.exists():
        raise FileNotFoundError("No output/lab_runs directory found.")
    runs = [p for p in lab_root.iterdir() if p.is_dir()]
    if not runs:
        raise FileNotFoundError("No lab run directory found in output/lab_runs.")
    return sorted(runs, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def parse_minute(minute: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(minute).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        x = float(v)
        if x != x:
            return None
        return x
    except Exception:
        return None


def extract_event_fields(event: Dict[str, Any]) -> Dict[str, Any]:
    at = event.get("at_event", {})
    scene = at.get("scene_context", {})
    footprint = at.get("structural_footprint", {})
    outcome = event.get("observed_outcome", {})

    return {
        "t0": event.get("t0"),
        "index": event.get("index"),
        "scene_id": event.get("scene_id") or scene.get("scene_id", "UNKNOWN_SCENE"),
        "scene_family": scene.get("scene_family", "UNKNOWN"),
        "scene_confidence": safe_float(scene.get("scene_confidence_non_blocking")) or 0.0,
        "compression": event.get("compression_qualification") or get(scene, ["compression_qualification", "compression_label"], "UNKNOWN"),
        "footprint": footprint.get("footprint_state", "NO_STRUCTURAL_FOOTPRINT"),
        "footprint_confidence": safe_float(footprint.get("confidence_non_blocking")) or 0.0,
        "outcome": outcome.get("outcome", "UNKNOWN"),
        "bars_to_move": outcome.get("bars_to_move"),
        "force_diff": get(at, ["force_diff"]),
        "regime": get(at, ["B1_regime", "regime"], "UNKNOWN"),
        "b4_state": get(at, ["B4_density", "cycle_state"], "UNKNOWN"),
        "b5_direction": get(at, ["B5_relation", "direction"], "UNKNOWN"),
        "eie_state": get(at, ["EIE_zone", "eie_state"], "UNKNOWN"),
        "b7_state": get(at, ["B7_resonance", "resonance_state"], "UNKNOWN"),
        "noise_ratio": get(at, ["B3_kinematics", "noise_ratio"]),
        "technical_risks": event.get("technical_risks", []),
        "expected_outcomes_to_observe": scene.get("expected_outcomes_to_observe", []),
        "memory_tuple_6d": scene.get("memory_tuple_6d", []),
    }


def select_event(
    event: Dict[str, Any],
    prev_kept: Optional[Dict[str, Any]],
    prev_any: Optional[Dict[str, Any]],
    warmup_index: int,
    min_confidence: float,
    include_every_scene_change: bool,
) -> Dict[str, Any]:
    f = extract_event_fields(event)
    reasons: List[str] = []
    non_reasons: List[str] = []

    idx = f["index"]
    if idx is not None and idx < warmup_index:
        non_reasons.append("WARMUP_FRAME")

    scene_id = f["scene_id"]
    comp = f["compression"]
    footprint = f["footprint"]
    outcome = f["outcome"]
    confidence = f["scene_confidence"]
    risks = set(f["technical_risks"] or [])

    if confidence >= min_confidence:
        reasons.append("SCENE_CONFIDENCE_OK")
    else:
        non_reasons.append("LOW_SCENE_CONFIDENCE")

    if scene_id in IMPORTANT_SCENES and confidence >= min_confidence:
        reasons.append("IMPORTANT_SCENE")

    if comp in IMPORTANT_COMPRESSION:
        reasons.append(f"COMPRESSION_{comp}")

    if footprint in IMPORTANT_FOOTPRINTS:
        reasons.append(f"FOOTPRINT_{footprint}")

    if outcome in IMPORTANT_OUTCOMES:
        # Do not keep every RELEASE_CONFIRMED if scene is low signal; still useful if combined with other criteria.
        if outcome != "RELEASE_CONFIRMED" or comp in IMPORTANT_COMPRESSION or footprint in IMPORTANT_FOOTPRINTS:
            reasons.append(f"OUTCOME_{outcome}")

    high_risks = sorted(risks.intersection(HIGH_VALUE_RISKS))
    if high_risks:
        reasons.append("HIGH_VALUE_TECHNICAL_RISK")
        reasons.extend(high_risks[:4])

    if include_every_scene_change and prev_any is not None:
        prev_scene = extract_event_fields(prev_any)["scene_id"]
        if scene_id != prev_scene and confidence >= min_confidence:
            reasons.append("SCENE_CHANGE")

    if prev_kept is not None:
        pk = extract_event_fields(prev_kept)
        if scene_id == pk["scene_id"] and comp == pk["compression"] and footprint == pk["footprint"]:
            # Avoid near-duplicate minute spam unless it has a stronger outcome/risk.
            if not any(r.startswith("OUTCOME_REJECTION") or r.startswith("OUTCOME_SECOND_LEG") or r in high_risks for r in reasons):
                non_reasons.append("DUPLICATE_CONTIGUOUS_CONTEXT")

    keep = bool(reasons) and "WARMUP_FRAME" not in non_reasons and "DUPLICATE_CONTIGUOUS_CONTEXT" not in non_reasons

    return {
        **f,
        "keep": keep,
        "selection_reasons": list(dict.fromkeys(reasons)),
        "non_selection_reasons": list(dict.fromkeys(non_reasons)),
    }


def build_clusters(events_index: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clusters: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for ev in events_index:
        key = (
            ev.get("scene_id"),
            ev.get("compression"),
            ev.get("footprint"),
        )

        if current is None or current["key"] != key:
            if current is not None:
                finalize_cluster(current)
                clusters.append(current)
            current = {
                "key": key,
                "start_t0": ev.get("t0"),
                "end_t0": ev.get("t0"),
                "start_index": ev.get("index"),
                "end_index": ev.get("index"),
                "scene_id": ev.get("scene_id"),
                "compression": ev.get("compression"),
                "footprint": ev.get("footprint"),
                "count": 1,
                "kept_count": 1 if ev.get("keep") else 0,
                "outcomes": Counter([ev.get("outcome", "UNKNOWN")]),
                "risks": Counter(ev.get("technical_risks", [])),
                "max_scene_confidence": ev.get("scene_confidence", 0.0),
                "max_footprint_confidence": ev.get("footprint_confidence", 0.0),
                "sample_events": [ev],
            }
        else:
            current["end_t0"] = ev.get("t0")
            current["end_index"] = ev.get("index")
            current["count"] += 1
            current["kept_count"] += 1 if ev.get("keep") else 0
            current["outcomes"].update([ev.get("outcome", "UNKNOWN")])
            current["risks"].update(ev.get("technical_risks", []))
            current["max_scene_confidence"] = max(current["max_scene_confidence"], ev.get("scene_confidence", 0.0))
            current["max_footprint_confidence"] = max(current["max_footprint_confidence"], ev.get("footprint_confidence", 0.0))
            if len(current["sample_events"]) < 3 and ev.get("keep"):
                current["sample_events"].append(ev)

    if current is not None:
        finalize_cluster(current)
        clusters.append(current)

    # Remove internal tuple key and convert counters.
    cleaned = []
    for c in clusters:
        c = dict(c)
        c.pop("key", None)
        c["dominant_outcome"] = c["outcomes"].most_common(1)[0][0] if c["outcomes"] else "UNKNOWN"
        c["outcomes"] = dict(c["outcomes"])
        c["top_risks"] = dict(c["risks"].most_common(8))
        c.pop("risks", None)
        cleaned.append(c)

    return cleaned


def finalize_cluster(c: Dict[str, Any]) -> None:
    start = c.get("start_index")
    end = c.get("end_index")
    if isinstance(start, int) and isinstance(end, int):
        c["duration_frames"] = end - start + 1
    else:
        c["duration_frames"] = c.get("count", 0)


def summarize_key_events(key_events: List[Dict[str, Any]], events_index: List[Dict[str, Any]], clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total_events": len(events_index),
        "key_events": len(key_events),
        "condensation_ratio": round((len(key_events) / len(events_index)) if events_index else 0.0, 6),
        "non_censored_events_indexed": len(events_index),
        "clusters_count": len(clusters),
        "by_scene_id": dict(Counter(e["scene_id"] for e in key_events)),
        "by_compression": dict(Counter(e["compression"] for e in key_events)),
        "by_footprint": dict(Counter(e["footprint"] for e in key_events)),
        "by_outcome": dict(Counter(e["outcome"] for e in key_events)),
        "top_risks": dict(Counter(r for e in key_events for r in e.get("technical_risks", [])).most_common(15)),
    }


def write_key_events_csv(path: Path, events: List[Dict[str, Any]]) -> None:
    fields = [
        "t0", "index", "scene_id", "scene_confidence", "compression", "footprint",
        "footprint_confidence", "outcome", "bars_to_move", "regime", "b4_state",
        "b5_direction", "eie_state", "b7_state", "noise_ratio", "selection_reasons",
        "technical_risks",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for e in events:
            row = {k: e.get(k) for k in fields}
            row["selection_reasons"] = " | ".join(e.get("selection_reasons", []))
            row["technical_risks"] = " | ".join(e.get("technical_risks", []))
            writer.writerow(row)


def write_film_key_events(path: Path, key_events: List[Dict[str, Any]], summary: Dict[str, Any], run_dir: Path) -> None:
    lines = [
        "# PowerFlow V7.2 — Film Key Events",
        "",
        f"**Generated at:** {utc_now()}",
        f"**Run dir:** `{run_dir}`",
        "",
        "## Doctrine",
        "",
        "Ce fichier condense le film sans censurer le microfilm original.",
        "Tous les événements sont conservés dans `events_index_full.json`.",
        "",
        "## Résumé",
        "",
        f"- Total events indexed: `{summary['total_events']}`",
        f"- Key events retained for reading: `{summary['key_events']}`",
        f"- Condensation ratio: `{summary['condensation_ratio']}`",
        f"- Clusters: `{summary['clusters_count']}`",
        "",
        "## Distribution scènes clés",
        "",
        dict_to_bullets(summary.get("by_scene_id", {})),
        "",
        "## Événements clés",
        "",
    ]

    if not key_events:
        lines.append("Aucun key event selon les règles V0.2.")
    else:
        for e in key_events:
            lines += [
                f"### {e.get('t0')} — {e.get('scene_id')}",
                "",
                f"- Compression: `{e.get('compression')}`",
                f"- Footprint: `{e.get('footprint')}` @ `{e.get('footprint_confidence')}`",
                f"- Outcome: `{e.get('outcome')}` | bars: `{e.get('bars_to_move')}`",
                f"- Regime: `{e.get('regime')}` | B4: `{e.get('b4_state')}` | B5: `{e.get('b5_direction')}` | EIE: `{e.get('eie_state')}` | B7: `{e.get('b7_state')}`",
                f"- Noise: `{e.get('noise_ratio')}`",
                f"- Selection reasons: `{', '.join(e.get('selection_reasons', []))}`",
                "",
                "**Risques techniques**",
                "",
                "\n".join(f"- `{r}`" for r in e.get("technical_risks", [])) or "- Aucun",
                "",
            ]

    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, key_events: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    def pill(text: Any) -> str:
        return f"<span class='pill'>{html.escape(str(text))}</span>"

    cards = []
    for e in key_events:
        risks = " ".join(pill(r) for r in e.get("technical_risks", [])[:12])
        reasons = " ".join(pill(r) for r in e.get("selection_reasons", []))
        cards.append(f"""
<section class="card">
  <h2>{html.escape(str(e.get('t0')))} — {html.escape(str(e.get('scene_id')))}</h2>
  <div class="row">
    <div><b>Compression</b><br>{html.escape(str(e.get('compression')))}</div>
    <div><b>Footprint</b><br>{html.escape(str(e.get('footprint')))} @ {html.escape(str(e.get('footprint_confidence')))}</div>
    <div><b>Outcome</b><br>{html.escape(str(e.get('outcome')))} | bars={html.escape(str(e.get('bars_to_move')))}</div>
  </div>
  <p><b>Context:</b> B1={html.escape(str(e.get('regime')))} | B4={html.escape(str(e.get('b4_state')))} | B5={html.escape(str(e.get('b5_direction')))} | EIE={html.escape(str(e.get('eie_state')))} | B7={html.escape(str(e.get('b7_state')))} | noise={html.escape(str(e.get('noise_ratio')))}</p>
  <p><b>Selection:</b> {reasons}</p>
  <p><b>Technical risks:</b> {risks or 'None'}</p>
</section>
""")

    doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>PowerFlow V7.2 — Key Events</title>
<style>
body{{background:#090909;color:#e9e9e9;font-family:Courier New,monospace;padding:22px}}
h1,h2{{color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.metric,.card{{background:#111;border:1px solid #262626;border-left:4px solid #00ff66;border-radius:12px;padding:14px;margin:14px 0}}
.value{{font-size:28px;color:#00ff66;font-weight:bold}}
.row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}}
.pill{{display:inline-block;border:1px solid #333;border-radius:999px;padding:2px 7px;margin:2px;color:#ffe46b}}
pre{{white-space:pre-wrap;background:#050505;padding:10px;border-radius:8px}}
</style>
</head>
<body>
<h1>PowerFlow V7.2 — Key Events</h1>
<p>Condensed without censorship. Full event index remains available.</p>
<div class="grid">
  <div class="metric"><div>Total indexed</div><div class="value">{summary.get('total_events')}</div></div>
  <div class="metric"><div>Key events</div><div class="value">{summary.get('key_events')}</div></div>
  <div class="metric"><div>Condensation</div><div class="value">{summary.get('condensation_ratio')}</div></div>
  <div class="metric"><div>Clusters</div><div class="value">{summary.get('clusters_count')}</div></div>
</div>
<h2>Summary raw</h2>
<pre>{html.escape(json.dumps(summary, indent=2, ensure_ascii=False))}</pre>
<h2>Events</h2>
{''.join(cards) if cards else '<p>No key event selected.</p>'}
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


def dict_to_bullets(obj: Dict[str, Any]) -> str:
    if not obj:
        return "- Empty"
    return "\n".join(f"- `{k}`: `{v}`" for k, v in obj.items())


def run_selector(
    lab_run: Path,
    warmup_index: int = 15,
    min_confidence: float = 0.60,
    include_every_scene_change: bool = True,
) -> Dict[str, Any]:
    cause_path = lab_run / "cause_consequence.json"
    metrics_path = lab_run / "lab_metrics.json"

    if not cause_path.exists():
        raise FileNotFoundError(f"Missing {cause_path}")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing {metrics_path}")

    cause = load_json(cause_path)
    lab_metrics = load_json(metrics_path)
    original_events = cause.get("events", [])

    events_index: List[Dict[str, Any]] = []
    key_events: List[Dict[str, Any]] = []
    prev_kept_event: Optional[Dict[str, Any]] = None
    prev_any_event: Optional[Dict[str, Any]] = None

    for event in original_events:
        selected = select_event(
            event=event,
            prev_kept=prev_kept_event,
            prev_any=prev_any_event,
            warmup_index=warmup_index,
            min_confidence=min_confidence,
            include_every_scene_change=include_every_scene_change,
        )
        events_index.append(selected)
        if selected["keep"]:
            key_events.append(selected)
            prev_kept_event = event
        prev_any_event = event

    clusters = build_clusters(events_index)
    summary = summarize_key_events(key_events, events_index, clusters)

    selector_metrics = {
        "valid": True,
        "method": METHOD,
        "version": VERSION,
        "generated_at": utc_now(),
        "lab_run": str(lab_run),
        "source_lab_metrics": {
            "frames_count": lab_metrics.get("frames_count"),
            "scenes_count": lab_metrics.get("scenes_count"),
            "symbol": lab_metrics.get("symbol"),
            "window": lab_metrics.get("window"),
        },
        "config": {
            "warmup_index": warmup_index,
            "min_confidence": min_confidence,
            "include_every_scene_change": include_every_scene_change,
        },
        "summary": summary,
        "no_censorship": True,
        "full_index_available": True,
        "no_trade_decision": True,
        "no_filtering": True,
        "db_write": False,
    }

    write_json(lab_run / "events_index_full.json", events_index)
    write_json(lab_run / "key_events.json", key_events)
    write_json(lab_run / "key_scene_clusters.json", clusters)
    write_json(lab_run / "event_selector_metrics.json", selector_metrics)
    write_key_events_csv(lab_run / "key_events.csv", key_events)
    write_film_key_events(lab_run / "film_key_events.md", key_events, summary, lab_run)
    write_html(lab_run / "lab_report_key_events.html", key_events, summary)

    return selector_metrics


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow V7.2 Lab Event Selector V0.2")
    p.add_argument("--lab-run", default=None, help="Path to output/lab_runs/<run_id>")
    p.add_argument("--latest", action="store_true", help="Use latest output/lab_runs directory")
    p.add_argument("--warmup-index", type=int, default=15)
    p.add_argument("--min-confidence", type=float, default=0.60)
    p.add_argument("--no-scene-change", action="store_true")
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path.cwd()

    if args.latest or not args.lab_run:
        lab_run = latest_lab_run(root)
    else:
        lab_run = Path(args.lab_run)

    result = run_selector(
        lab_run=lab_run,
        warmup_index=args.warmup_index,
        min_confidence=args.min_confidence,
        include_every_scene_change=not args.no_scene_change,
    )

    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
