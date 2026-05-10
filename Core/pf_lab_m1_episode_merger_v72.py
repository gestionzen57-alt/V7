#!/usr/bin/env python3
"""
PowerFlow V7.2 — M1 Episode Merger V0.4

Purpose
-------
Merge overlapping / nearby M1 zoom windows into readable M1 episodes.

Input:
    output/lab_runs/<run_id>/m1_zoom_index.json

Output:
    m1_episodes.json
    film_m1_episodes.md
    lab_report_m1_episodes.html
    m1_episode_merger_metrics.json

Doctrine:
- No DB write.
- No BUY/SELL.
- No decision.
- No censorship.
- Original m1_zoom_index.json remains untouched.
- M1 remains microscope, now grouped by episode.
"""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


VERSION = "LabM1EpisodeMergerV72.0.4"
METHOD = "lab_v72_m1_episode_merger"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def fmt_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def latest_lab_run(root: Path) -> Path:
    lab_root = root / "output" / "lab_runs"
    if not lab_root.exists():
        raise FileNotFoundError("No output/lab_runs folder found.")
    candidates = [p for p in lab_root.iterdir() if p.is_dir() and (p / "m1_zoom_index.json").exists()]
    if not candidates:
        raise FileNotFoundError("No lab run with m1_zoom_index.json found.")
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def episode_priority(zoom: Dict[str, Any]) -> int:
    scene = zoom.get("scene_id", "UNKNOWN")
    comp = zoom.get("compression", "UNKNOWN")
    fp = zoom.get("footprint", "UNKNOWN")
    outcome = zoom.get("outcome", "UNKNOWN")

    score = 0
    if comp == "COMPRESSION_REAL_CANDIDATE":
        score += 40
    elif comp == "COMPRESSION_FAKE_RISK":
        score += 25
    elif comp == "COMPRESSION_AMBIGUOUS":
        score += 15

    if isinstance(fp, str) and "FOOTPRINT_CANDIDATE" in fp:
        score += 30

    if scene == "FIRST_DETACHMENT_MICRO":
        score += 30
    elif scene == "PULLBACK_ABSORBED":
        score += 25
    elif scene == "PRICE_LAG_CATCH_UP":
        score += 25
    elif scene == "ZONE_BREATH_COMPRESSION":
        score += 20
    elif scene == "LEADER_FOLLOWER_IMBALANCE":
        score += 15

    if outcome in {"RELEASE_CONFIRMED", "SECOND_LEG_CONFIRMED", "DELAYED_RELEASE"}:
        score += 15
    elif outcome in {"REJECTION", "NO_FOLLOW_THROUGH"}:
        score += 10

    return score


def merge_zooms(
    zooms: List[Dict[str, Any]],
    merge_gap_minutes: int = 10,
) -> List[Dict[str, Any]]:
    parsed: List[Dict[str, Any]] = []
    for z in zooms:
        try:
            start = parse_dt(z["start"])
            end = parse_dt(z["end"])
        except Exception:
            continue
        parsed.append({**z, "_start_dt": start, "_end_dt": end})

    parsed.sort(key=lambda z: z["_start_dt"])

    episodes: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    gap = timedelta(minutes=merge_gap_minutes)

    for z in parsed:
        if current is None:
            current = new_episode(z)
            continue

        if z["_start_dt"] <= current["_end_dt"] + gap:
            add_zoom_to_episode(current, z)
        else:
            finalize_episode(current)
            episodes.append(current)
            current = new_episode(z)

    if current is not None:
        finalize_episode(current)
        episodes.append(current)

    # Remove internal dt objects.
    clean = []
    for ep in episodes:
        ep = dict(ep)
        ep.pop("_start_dt", None)
        ep.pop("_end_dt", None)
        for z in ep.get("zooms", []):
            z.pop("_start_dt", None)
            z.pop("_end_dt", None)
        clean.append(ep)

    return clean


def new_episode(z: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "_start_dt": z["_start_dt"],
        "_end_dt": z["_end_dt"],
        "start": fmt_dt(z["_start_dt"]),
        "end": fmt_dt(z["_end_dt"]),
        "anchor_t0s": [z.get("anchor_t0")],
        "zooms": [z],
        "zoom_count": 1,
    }


def add_zoom_to_episode(ep: Dict[str, Any], z: Dict[str, Any]) -> None:
    ep["_start_dt"] = min(ep["_start_dt"], z["_start_dt"])
    ep["_end_dt"] = max(ep["_end_dt"], z["_end_dt"])
    ep["start"] = fmt_dt(ep["_start_dt"])
    ep["end"] = fmt_dt(ep["_end_dt"])
    ep["anchor_t0s"].append(z.get("anchor_t0"))
    ep["zooms"].append(z)
    ep["zoom_count"] += 1


def finalize_episode(ep: Dict[str, Any]) -> None:
    zooms = ep.get("zooms", [])
    scenes = Counter(z.get("scene_id", "UNKNOWN") for z in zooms)
    comps = Counter(z.get("compression", "UNKNOWN") for z in zooms)
    fps = Counter(z.get("footprint", "UNKNOWN") for z in zooms)
    outcomes = Counter(z.get("outcome", "UNKNOWN") for z in zooms)

    internal_scene_counter = Counter()
    internal_comp_counter = Counter()
    internal_fp_counter = Counter()
    internal_outcome_counter = Counter()
    frames_total = 0
    scenes_total = 0

    for z in zooms:
        summary = z.get("summary", {}) or {}
        frames_total += int(summary.get("frames_count") or 0)
        scenes_total += int(summary.get("scenes_count") or 0)
        internal_scene_counter.update(summary.get("by_scene_id", {}) or {})
        internal_comp_counter.update(summary.get("by_compression_qualification", {}) or {})
        internal_fp_counter.update(summary.get("by_structural_footprint", {}) or {})
        internal_outcome_counter.update(summary.get("by_observed_outcome", {}) or {})

    best_anchor = sorted(zooms, key=episode_priority, reverse=True)[0] if zooms else {}
    duration = int((ep["_end_dt"] - ep["_start_dt"]).total_seconds() // 60)

    ep.update({
        "episode_id": None,
        "duration_minutes": duration,
        "main_anchor_t0": best_anchor.get("anchor_t0"),
        "main_scene_id": best_anchor.get("scene_id"),
        "main_compression": best_anchor.get("compression"),
        "main_footprint": best_anchor.get("footprint"),
        "main_outcome": best_anchor.get("outcome"),
        "macro_distribution": {
            "by_anchor_scene_id": dict(scenes),
            "by_anchor_compression": dict(comps),
            "by_anchor_footprint": dict(fps),
            "by_anchor_outcome": dict(outcomes),
        },
        "m1_internal_summary": {
            "frames_total_across_zoom_runs": frames_total,
            "scenes_total_across_zoom_runs": scenes_total,
            "by_scene_id": dict(internal_scene_counter),
            "by_compression_qualification": dict(internal_comp_counter),
            "by_structural_footprint": dict(internal_fp_counter),
            "by_observed_outcome": dict(internal_outcome_counter),
        },
        "recommended_reading": [
            z.get("run_dir") for z in zooms if z.get("run_dir")
        ],
        "interpretation_hint": build_interpretation_hint(best_anchor, internal_scene_counter, internal_fp_counter, internal_outcome_counter),
        "no_trade_decision": True,
    })


def build_interpretation_hint(
    anchor: Dict[str, Any],
    scenes: Counter,
    footprints: Counter,
    outcomes: Counter,
) -> str:
    scene = anchor.get("scene_id", "UNKNOWN")
    comp = anchor.get("compression", "UNKNOWN")
    fp = anchor.get("footprint", "UNKNOWN")
    out = anchor.get("outcome", "UNKNOWN")

    bits = []
    if comp == "COMPRESSION_REAL_CANDIDATE":
        bits.append("Macro compression réelle candidate.")
    elif comp == "COMPRESSION_FAKE_RISK":
        bits.append("Macro compression fake risk.")
    elif comp == "NO_B4_COMPRESSION":
        bits.append("Pas de compression B4 macro sur l’ancre.")

    if fp and fp != "NO_STRUCTURAL_FOOTPRINT":
        bits.append("Footprint structurel candidat présent.")

    if scenes:
        top_scene = scenes.most_common(1)[0][0]
        bits.append(f"M1 interne dominé par {top_scene}.")

    if outcomes:
        top_outcome = outcomes.most_common(1)[0][0]
        bits.append(f"Conséquence observée dominante : {top_outcome}.")

    if scene == "PULLBACK_ABSORBED" and out == "NO_FOLLOW_THROUGH":
        bits.append("Cas pédagogique : absorption sans continuation.")

    return " ".join(bits) if bits else "Épisode M1 à inspecter."


def assign_episode_ids(episodes: List[Dict[str, Any]]) -> None:
    for i, ep in enumerate(episodes, start=1):
        ep["episode_id"] = f"M1_EPISODE_{i:02d}"


def build_metrics(episodes: List[Dict[str, Any]], zoom_count: int, lab_run: Path, merge_gap_minutes: int) -> Dict[str, Any]:
    scenes = Counter(ep.get("main_scene_id", "UNKNOWN") for ep in episodes)
    comps = Counter(ep.get("main_compression", "UNKNOWN") for ep in episodes)
    fps = Counter(ep.get("main_footprint", "UNKNOWN") for ep in episodes)
    outcomes = Counter(ep.get("main_outcome", "UNKNOWN") for ep in episodes)

    return {
        "valid": True,
        "method": METHOD,
        "version": VERSION,
        "generated_at": utc_now(),
        "lab_run": str(lab_run),
        "merge_gap_minutes": merge_gap_minutes,
        "zoom_count_input": zoom_count,
        "episode_count_output": len(episodes),
        "compression_ratio": round((len(episodes) / zoom_count) if zoom_count else 0.0, 6),
        "by_main_scene_id": dict(scenes),
        "by_main_compression": dict(comps),
        "by_main_footprint": dict(fps),
        "by_main_outcome": dict(outcomes),
        "no_censorship": True,
        "original_zoom_index_untouched": True,
        "no_trade_decision": True,
        "db_write": False,
    }


def write_film(path: Path, episodes: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
    lines = [
        "# PowerFlow V7.2 — M1 Episodes Film",
        "",
        f"**Generated at:** {metrics.get('generated_at')}",
        f"**Source run:** `{metrics.get('lab_run')}`",
        "",
        "## Doctrine",
        "",
        "M1 reste le microscope. Cette V0.4 fusionne les zooms voisins en épisodes lisibles.",
        "Le fichier `m1_zoom_index.json` original reste intact.",
        "",
        "## Résumé",
        "",
        f"- Zooms input : `{metrics.get('zoom_count_input')}`",
        f"- Episodes output : `{metrics.get('episode_count_output')}`",
        f"- Merge gap minutes : `{metrics.get('merge_gap_minutes')}`",
        f"- Compression ratio : `{metrics.get('compression_ratio')}`",
        "",
    ]

    if not episodes:
        lines.append("Aucun épisode M1 généré.")
    else:
        for ep in episodes:
            lines += [
                f"## {ep['episode_id']} — {ep.get('start')} → {ep.get('end')}",
                "",
                f"- Main anchor : `{ep.get('main_anchor_t0')}`",
                f"- Main scene : `{ep.get('main_scene_id')}`",
                f"- Compression : `{ep.get('main_compression')}`",
                f"- Footprint : `{ep.get('main_footprint')}`",
                f"- Outcome : `{ep.get('main_outcome')}`",
                f"- Zooms merged : `{ep.get('zoom_count')}`",
                f"- Duration minutes : `{ep.get('duration_minutes')}`",
                "",
                "### Lecture PowerFlow",
                "",
                ep.get("interpretation_hint", ""),
                "",
                "### M1 internal summary",
                "",
                "Scene distribution:",
                "",
                dict_to_bullets(ep.get("m1_internal_summary", {}).get("by_scene_id", {})),
                "",
                "Footprints:",
                "",
                dict_to_bullets(ep.get("m1_internal_summary", {}).get("by_structural_footprint", {})),
                "",
                "Outcomes:",
                "",
                dict_to_bullets(ep.get("m1_internal_summary", {}).get("by_observed_outcome", {})),
                "",
                "### Runs à ouvrir",
                "",
            ]
            for rd in ep.get("recommended_reading", []):
                lines.append(f"- `{rd}`")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, episodes: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
    cards = []
    for ep in episodes:
        cards.append(f"""
<section class="card">
  <h2>{html.escape(ep.get('episode_id',''))} — {html.escape(ep.get('start',''))} → {html.escape(ep.get('end',''))}</h2>
  <div class="grid">
    <div><b>Main scene</b><br>{html.escape(str(ep.get('main_scene_id')))}</div>
    <div><b>Compression</b><br>{html.escape(str(ep.get('main_compression')))}</div>
    <div><b>Footprint</b><br>{html.escape(str(ep.get('main_footprint')))}</div>
    <div><b>Outcome</b><br>{html.escape(str(ep.get('main_outcome')))}</div>
  </div>
  <p><b>Zooms merged:</b> {ep.get('zoom_count')} | <b>Duration:</b> {ep.get('duration_minutes')} min</p>
  <p><b>Lecture:</b> {html.escape(str(ep.get('interpretation_hint')))}</p>
  <h3>M1 internal summary</h3>
  <pre>{html.escape(json.dumps(ep.get('m1_internal_summary', {}), indent=2, ensure_ascii=False))}</pre>
  <h3>Runs</h3>
  <pre>{html.escape(json.dumps(ep.get('recommended_reading', []), indent=2, ensure_ascii=False))}</pre>
</section>
""")

    doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>PowerFlow V7.2 — M1 Episodes</title>
<style>
body{{background:#080808;color:#e8e8e8;font-family:Courier New,monospace;padding:22px}}
h1,h2{{color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}}
.metric,.card{{background:#111;border:1px solid #252525;border-left:4px solid #00ff66;border-radius:12px;padding:14px;margin:14px 0}}
.value{{font-size:28px;color:#00ff66;font-weight:bold}}
pre{{white-space:pre-wrap;background:#050505;padding:10px;border-radius:8px;overflow:auto}}
</style>
</head>
<body>
<h1>PowerFlow V7.2 — M1 Episodes</h1>
<p>M1 zooms merged into readable episodes. No decision. No filtering.</p>
<div class="grid">
  <div class="metric"><div>Zooms input</div><div class="value">{metrics.get('zoom_count_input')}</div></div>
  <div class="metric"><div>Episodes output</div><div class="value">{metrics.get('episode_count_output')}</div></div>
  <div class="metric"><div>Merge gap</div><div class="value">{metrics.get('merge_gap_minutes')}m</div></div>
  <div class="metric"><div>Compression ratio</div><div class="value">{metrics.get('compression_ratio')}</div></div>
</div>
<h2>Metrics</h2>
<pre>{html.escape(json.dumps(metrics, indent=2, ensure_ascii=False))}</pre>
<h2>Episodes</h2>
{''.join(cards) if cards else '<p>No M1 episode generated.</p>'}
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


def dict_to_bullets(d: Dict[str, Any]) -> str:
    if not d:
        return "- Empty"
    return "\n".join(f"- `{k}`: `{v}`" for k, v in d.items())


def run_merger(lab_run: Path, merge_gap_minutes: int = 10) -> Dict[str, Any]:
    zoom_path = lab_run / "m1_zoom_index.json"
    if not zoom_path.exists():
        raise FileNotFoundError(f"Missing {zoom_path}")

    zooms = load_json(zoom_path)
    if not isinstance(zooms, list):
        raise ValueError("m1_zoom_index.json must contain a list")

    episodes = merge_zooms(zooms, merge_gap_minutes=merge_gap_minutes)
    assign_episode_ids(episodes)
    metrics = build_metrics(episodes, len(zooms), lab_run, merge_gap_minutes)

    write_json(lab_run / "m1_episodes.json", episodes)
    write_json(lab_run / "m1_episode_merger_metrics.json", metrics)
    write_film(lab_run / "film_m1_episodes.md", episodes, metrics)
    write_html(lab_run / "lab_report_m1_episodes.html", episodes, metrics)

    return metrics


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow V7.2 M1 Episode Merger V0.4")
    p.add_argument("--lab-run", default=None, help="Path to output/lab_runs/<run_id>")
    p.add_argument("--latest", action="store_true")
    p.add_argument("--merge-gap-minutes", type=int, default=10)
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path.cwd()

    if args.latest or not args.lab_run:
        lab_run = latest_lab_run(root)
    else:
        lab_run = Path(args.lab_run)

    result = run_merger(lab_run, merge_gap_minutes=args.merge_gap_minutes)
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
